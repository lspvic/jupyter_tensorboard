# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019, Shengpeng Liu.  All rights reserved.
# Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.

import os
import sys
import time
import inspect
import itertools
from collections import namedtuple
import logging

import six

sys.argv = ["tensorboard"]

from tensorboard.backend import application   # noqa

def get_plugins():
    # Gather up core plugins as well as dynamic plugins.
    # The way this was done varied several times in the later 1.x series
    if hasattr(default, 'PLUGIN_LOADERS'): # TB 1.10
        return default.PLUGIN_LOADERS[:]

    if hasattr(default, 'get_plugins') and inspect.isfunction(default.get_plugins): # TB 1.11+
        if not ( hasattr(default, 'get_static_plugins') and inspect.isfunction(default.get_static_plugins) ):
            # in TB 1.11 through 2.2, get_plugins is really just the static plugins
            plugins = default.get_plugins()
        else:
            # in TB 2.3 and later, get_plugins was renamed to get_static_plugins and
            # a new get_plugins was created that returns the static+dynamic set
            plugins = default.get_static_plugins()

        if hasattr(default, 'get_dynamic_plugins') and inspect.isfunction(default.get_dynamic_plugins):
            # in TB 1.14 there are also dynamic plugins that should be included
            plugins += default.get_dynamic_plugins()

        return plugins

    return None

try:
    # Tensorboard 0.4.x above series
    from tensorboard import default

    if hasattr(default, 'PLUGIN_LOADERS') or hasattr(default, '_PLUGINS'):
        # TensorBoard 1.10 or above series
        from tensorboard import program

        def create_tb_app(logdir, reload_interval, purge_orphaned_data):
            argv = [
                        "",
                        "--logdir", logdir,
                        "--reload_interval", str(reload_interval),
                        "--purge_orphaned_data", str(purge_orphaned_data),
                   ]
            tensorboard = program.TensorBoard(get_plugins())
            tensorboard.configure(argv)

            if ( hasattr(application, 'standard_tensorboard_wsgi') and inspect.isfunction(application.standard_tensorboard_wsgi)):
                logging.debug("TensorBoard 1.10 or above series detected")
                standard_tensorboard_wsgi = application.standard_tensorboard_wsgi
            else:
                logging.debug("TensorBoard 2.3 or above series detected")
                def standard_tensorboard_wsgi(flags, plugin_loaders, assets_zip_provider):
                    from tensorboard.backend.event_processing import data_ingester
                    ingester = data_ingester.LocalDataIngester(flags)
                    ingester.start()
                    return application.TensorBoardWSGIApp(flags, plugin_loaders, ingester.data_provider,
                        assets_zip_provider, ingester.deprecated_multiplexer)
        
            return manager.add_instance(logdir, standard_tensorboard_wsgi(
                tensorboard.flags,
                tensorboard.plugin_loaders,
                tensorboard.assets_zip_provider))
    else:
        logging.debug("TensorBoard 0.4.x series detected")

        def create_tb_app(logdir, reload_interval, purge_orphaned_data):
            return manager.add_instance(logdir, application.standard_tensorboard_wsgi(
                logdir=logdir, reload_interval=reload_interval,
                purge_orphaned_data=purge_orphaned_data,
                plugins=default.get_plugins()))

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
    'TensorBoardInstance', ['name', 'logdir', 'tb_app'])

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

    def add_instance(self, logdir, tb_application):
        name = self._next_available_name()
        instance = TensorBoardInstance(name, logdir, tb_application)
        self[name] = instance
        self._logdir_dict[logdir] = instance
        return tb_application

    def terminate(self, name, force=True):
        if name in self:
            instance = self[name]
            del self[name], self._logdir_dict[instance.logdir]
        else:
            raise Exception("There's no tensorboard instance named %s" % name)


manager = TensorboardManger()
