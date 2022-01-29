# -*- coding: utf-8 -*-

import os
import sys
import threading
import time
import inspect
import itertools
from collections import namedtuple
import logging

import six

sys.argv = ["tensorboard"]

from tensorboard.backend import application   # noqa

try:
    # Tensorboard 0.4.x above series
    from tensorboard import default

    if not hasattr(application, "reload_multiplexer"):
        # Tensorflow 1.12 removed reload_multiplexer, patch it
        def reload_multiplexer(multiplexer, path_to_run):
            for path, name in six.iteritems(path_to_run):
                multiplexer.AddRunsFromDirectory(path, name)
            multiplexer.Reload()
        application.reload_multiplexer = reload_multiplexer

    if not hasattr(application, 'standard_tensorboard_wsgi'):
        # Tensorflow 2.3+ removed reload_multiplexer, patch it
        from tensorboard.backend.event_processing import (
            data_provider as event_data_provider,
        )
        from tensorboard.backend.event_processing import (
            plugin_event_multiplexer as event_multiplexer,
        )
        from tensorboard.backend.event_processing.data_ingester import (
            DEFAULT_TENSOR_SIZE_GUIDANCE
        )
        def _apply_tensor_size_guidance(sampling_hints):
            """Apply user per-summary size guidance overrides."""
            tensor_size_guidance = dict(DEFAULT_TENSOR_SIZE_GUIDANCE)
            tensor_size_guidance.update(sampling_hints)
            return tensor_size_guidance
        def _get_event_file_active_filter(flags):
            """Returns a predicate for whether an event file load timestamp is active.

            Returns:
              A predicate function accepting a single UNIX timestamp float argument, or
              None if multi-file loading is not enabled.
            """
            if not flags.reload_multifile:
                return None
            inactive_secs = flags.reload_multifile_inactive_secs
            if inactive_secs == 0:
                return None
            if inactive_secs < 0:
                return lambda timestamp: True
            return lambda timestamp: timestamp + inactive_secs >= time.time()
        def standard_tensorboard_wsgi(flags, plugin_loaders, assets_zip_provider):
            data_provider = None
            multiplexer = None
            reload_interval = flags.reload_interval
            # Regular logdir loading mode.
            sampling_hints = flags.samples_per_plugin
            multiplexer = event_multiplexer.EventMultiplexer(
                tensor_size_guidance=_apply_tensor_size_guidance(sampling_hints),
                purge_orphaned_data=flags.purge_orphaned_data,
                max_reload_threads=flags.max_reload_threads,
                event_file_active_filter=_get_event_file_active_filter(flags),
            )
            if reload_interval >= 0:
                # We either reload the multiplexer once when TensorBoard starts up, or we
                # continuously reload the multiplexer.
                if flags.logdir:
                    path_to_run = {os.path.expanduser(flags.logdir): None}
                else:
                    path_to_run = parse_event_files_spec(flags.logdir_spec)
                application.reload_multiplexer(multiplexer, path_to_run)
                #start_reloading_multiplexer(
                #    multiplexer, path_to_run, reload_interval
                #)
            data_provider = event_data_provider.MultiplexerDataProvider(
                multiplexer, flags.logdir or flags.logdir_spec
            )

            return application.TensorBoardWSGIApp(
                flags, plugin_loaders, data_provider, assets_zip_provider, multiplexer
            )
        application.standard_tensorboard_wsgi = standard_tensorboard_wsgi

    if not hasattr(application, 'parse_event_files_spec'):
        def parse_event_files_spec(logdir_spec):
            from tensorboard.backend.event_processing.data_ingester import (
                _parse_event_files_spec
            )
            return _parse_event_files_spec(logdir_spec)
        application.parse_event_files_spec = parse_event_files_spec

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


def is_tensorboard_greater_than_or_equal_to20():
    # tensorflow<1.4 will be
    # (logdir, plugins, multiplexer, reload_interval)

    # tensorflow>=1.4, <1.12 will be
    # (logdir, plugins, multiplexer, reload_interval, path_prefix)

    # tensorflow>=1.12, <1.14 will be
    # (logdir, plugins, multiplexer, reload_interval,
    #  path_prefix='', reload_task='auto')

    # tensorflow 2.0 will be
    # (flags, plugins, data_provider=None, assets_zip_provider=None,
    #  deprecated_multiplexer=None)

    s = inspect.signature(application.TensorBoardWSGIApp)
    first_parameter_name = list(s.parameters.keys())[0]
    return first_parameter_name == 'flags'


def TensorBoardWSGIApp_2x(
        flags, plugins,
        data_provider=None,
        assets_zip_provider=None,
        deprecated_multiplexer=None):

    logdir = flags.logdir
    multiplexer = deprecated_multiplexer
    reload_interval = flags.reload_interval

    path_to_run = application.parse_event_files_spec(logdir)
    if reload_interval:
        thread = start_reloading_multiplexer(
            multiplexer, path_to_run, reload_interval)
    else:
        application.reload_multiplexer(multiplexer, path_to_run)
        thread = None

    plugin_name_to_instance = {}

    from tensorboard.plugins import base_plugin
    context = base_plugin.TBContext(
        data_provider=data_provider,
        flags=flags,
        logdir=flags.logdir,
        multiplexer=deprecated_multiplexer,
        assets_zip_provider=assets_zip_provider,
        plugin_name_to_instance=plugin_name_to_instance,
        window_title=flags.window_title)

    tbplugins = []
    for loader in plugins:
        plugin = loader.load(context)
        if plugin is None:
            continue
        tbplugins.append(plugin)
        plugin_name_to_instance[plugin.plugin_name] = plugin

    tb_app = application.TensorBoardWSGI(tbplugins, data_provider=data_provider)
    manager.add_instance(logdir, tb_app, thread)
    return tb_app


def TensorBoardWSGIApp_1x(
        logdir, plugins, multiplexer,
        reload_interval, path_prefix="", reload_task="auto"):
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


if is_tensorboard_greater_than_or_equal_to20():
    application.TensorBoardWSGIApp = TensorBoardWSGIApp_2x
else:
    application.TensorBoardWSGIApp = TensorBoardWSGIApp_1x


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
