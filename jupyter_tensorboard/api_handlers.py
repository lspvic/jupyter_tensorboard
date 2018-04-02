# -*- coding: utf-8 -*-

import json
import os

from tornado import web
from notebook.base.handlers import APIHandler

from .handlers import notebook_dir


def _trim_notebook_dir(dir):
    return os.path.join("<notebook_dir>", os.path.relpath(dir, notebook_dir))


class TbRootHandler(APIHandler):

    @web.authenticated
    def get(self):
        terms = [
            {
                'name': entry.name,
                'logdir': _trim_notebook_dir(entry.logdir),
                "reload_time": entry.thread.reload_time,
            } for entry in
            self.settings["tensorboard_manager"].values()
        ]
        self.finish(json.dumps(terms))

    @web.authenticated
    def post(self):
        data = self.get_json_body()
        reload_interval = data.get("reload_interval", None)
        entry = (
            self.settings["tensorboard_manager"]
            .new_instance(data["logdir"], reload_interval=reload_interval)
        )
        self.finish(json.dumps({
                'name': entry.name,
                'logdir':  _trim_notebook_dir(entry.logdir),
                'reload_time': entry.thread.reload_time}))


class TbInstanceHandler(APIHandler):

    SUPPORTED_METHODS = ('GET', 'DELETE')

    @web.authenticated
    def get(self, name):
        manager = self.settings["tensorboard_manager"]
        if name in manager:
            entry = manager[name]
            self.finish(json.dumps({
                'name': entry.name,
                'logdir':  _trim_notebook_dir(entry.logdir),
                'reload_time': entry.thread.reload_time}))
        else:
            raise web.HTTPError(
                404, "TensorBoard instance not found: %r" % name)

    @web.authenticated
    def delete(self, name):
        manager = self.settings["tensorboard_manager"]
        if name in manager:
            manager.terminate(name, force=True)
            self.set_status(204)
            self.finish()
        else:
            raise web.HTTPError(
                404, "TensorBoard instance not found: %r" % name)
