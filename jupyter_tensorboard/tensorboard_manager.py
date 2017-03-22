# -*- coding: utf-8 -*-

import os
import threading
import time
import itertools
from collections import namedtuple

from tensorboard.backend import application
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

from .handlers import notebook_dir

TensorBoardInstance = namedtuple(
    'TensorBoardInstance', ['name', 'logdir', 'tb_app', 'thread'])


def start_reloading_multiplexer(multiplexer, path_to_run, reload_interval):
    def _ReloadForever():
        current_thread = threading.currentThread()
        current_thread.stop = False
        while not current_thread.stop:
            application.reload_multiplexer(multiplexer, path_to_run)
            time.sleep(reload_interval)
    thread = threading.Thread(target=_ReloadForever)
    thread.daemon = True
    thread.start()
    return thread


def TensorBoardWSGIApp(logdir, plugins, multiplexer, reload_interval):
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

    def new_instance(self, logdir):
        if not os.path.isabs(logdir) and notebook_dir:
            logdir = os.path.join(notebook_dir, logdir)

        if logdir not in self._logdir_dict:

            purge_orphaned_data = True
            reload_interval = 30
            plugins = [
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
            application.standard_tensorboard_wsgi(
                logdir=logdir, reload_interval=reload_interval,
                purge_orphaned_data=purge_orphaned_data, plugins=plugins)

            return self._logdir_dict[logdir]
        else:
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
