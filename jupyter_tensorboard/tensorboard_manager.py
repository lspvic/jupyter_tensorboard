# -*- coding: utf-8 -*-

import os
import sys
import threading
import time
import itertools
from collections import namedtuple
import logging

sys.argv = ["tensorboard"]

from tensorboard.backend import application   # noqa

try:
    # Tensorboard 0.4.x above series
    from tensorboard import default
    if hasattr(default, 'PLUGIN_LOADERS') or hasattr(default, '_PLUGINS'):
        # Tensorflow 1.10 or above series
        logging.debug("Tensorboard 1.10 or above series detected")
        from tensorboard import program

        def create_tb_app(logdir, reload_interval, purge_orphaned_data):
            argv = [
                        "",
                        "--logdir", logdir,
                        "--reload_interval", str(reload_interval),
                        "--purge_orphaned_data", str(purge_orphaned_data),
                   ]
            tensorboard = program.TensorBoard()
            tensorboard.configure(argv)
            return application.standard_tensorboard_wsgi(
                tensorboard.flags,
                tensorboard.plugin_loaders,
                tensorboard.assets_zip_provider)
    else:
        logging.debug("Tensorboard 0.4.x series detected")

        def create_tb_app(logdir, reload_interval, purge_orphaned_data):
            return application.standard_tensorboard_wsgi(
                logdir=logdir, reload_interval=reload_interval,
                purge_orphaned_data=purge_orphaned_data,
                plugins=default.get_plugins())

except ImportError:
    # Tensorboard 0.3.x series
    from tensorboard.plugins.audio import audio_plugin
    from tensorboard.plugins.core import core_plugin
    from tensorboard.plugins.distribution import distributions_plugin
    from tensorboard.plugins.graph import graphs_plugin
    from tensorboard.plugins.histogram import histograms_plugin
    from tensorboard.plugins.image import images_plugin
    from tensorboard.plugins.profile import profile_plugin
    from tensorboard.plugins.projector import projector_plugin
    from tensorboard.plugins.scalar import scalars_plugin
    from tensorboard.plugins.text import text_plugin
    logging.debug("Tensorboard 0.3.x series detected")

    _plugins = [
                core_plugin.CorePlugin,
                scalars_plugin.ScalarsPlugin,
                images_plugin.ImagesPlugin,
                audio_plugin.AudioPlugin,
                graphs_plugin.GraphsPlugin,
                distributions_plugin.DistributionsPlugin,
                histograms_plugin.HistogramsPlugin,
                projector_plugin.ProjectorPlugin,
                text_plugin.TextPlugin,
                profile_plugin.ProfilePlugin,
            ]

    def create_tb_app(logdir, reload_interval, purge_orphaned_data):
        return application.standard_tensorboard_wsgi(
            logdir=logdir, reload_interval=reload_interval,
            purge_orphaned_data=purge_orphaned_data,
            plugins=_plugins)


from .handlers import notebook_dir   # noqa

TensorBoardInstance = namedtuple(
    'TensorBoardInstance', ['name', 'logdir', 'tb_app', 'thread'])


def start_reloading_multiplexer(multiplexer, path_to_run, reload_interval):
    def _ReloadForever():
        current_thread = threading.currentThread()
        while not current_thread.stop:
            application.reload_multiplexer(multiplexer, path_to_run)
            current_thread.reload_time = time.time()
            time.sleep(reload_interval)
    thread = threading.Thread(target=_ReloadForever)
    thread.reload_time = None
    thread.stop = False
    thread.daemon = True
    thread.start()
    return thread


def TensorBoardWSGIApp(logdir, plugins, multiplexer,
                       reload_interval, path_prefix=""):
    path_to_run = application.parse_event_files_spec(logdir)
    if reload_interval:
        thread = start_reloading_multiplexer(
            multiplexer, path_to_run, reload_interval)
    else:
        application.reload_multiplexer(multiplexer, path_to_run)
        thread = None
    tb_app = application.TensorBoardWSGI(plugins)
    manager.add_instance(logdir, tb_app, thread)
    return tb_app


application.TensorBoardWSGIApp = TensorBoardWSGIApp


class TensorboardManger(dict):

    def __init__(self):
        self._logdir_dict = {}

    def _next_available_name(self):
        for n in itertools.count(start=1):
            name = "%d" % n
            if name not in self:
                return name

    def new_instance(self, logdir, reload_interval):
        if not os.path.isabs(logdir) and notebook_dir:
            logdir = os.path.join(notebook_dir, logdir)

        if logdir not in self._logdir_dict:
            purge_orphaned_data = True
            reload_interval = reload_interval or 30
            create_tb_app(
                logdir=logdir, reload_interval=reload_interval,
                purge_orphaned_data=purge_orphaned_data)

        return self._logdir_dict[logdir]

    def add_instance(self, logdir, tb_application, thread):
        name = self._next_available_name()
        instance = TensorBoardInstance(name, logdir, tb_application, thread)
        self[name] = instance
        self._logdir_dict[logdir] = instance

    def terminate(self, name, force=True):
        if name in self:
            instance = self[name]
            if instance.thread is not None:
                instance.thread.stop = True
            del self[name], self._logdir_dict[instance.logdir]
        else:
            raise Exception("There's no tensorboard instance named %s" % name)


manager = TensorboardManger()
