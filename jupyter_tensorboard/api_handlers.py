# -*- coding: utf-8 -*-

import json
import os

from tornado import web
from notebook.base.handlers import APIHandler, json_errors

from .handlers import notebook_dir


def _trim_notebook_dir(dir):
    return os.path.join("<notebook_dir>", os.path.relpath(dir, notebook_dir))


class TbRootHandler(APIHandler):

    @json_errors
    @web.authenticated
    def get(self):
        terms = [
            {
                'name': name,
                'logdir': _trim_notebook_dir(logdir)
            } for name, logdir, *_ in
            self.settings["tensorboard_manager"].values()
        ]
        self.finish(json.dumps(terms))

    @json_errors
    @web.authenticated
    def post(self):
        data = self.get_json_body()
        name, logdir, *_ = (
            self.settings["tensorboard_manager"]
            .new_instance(data["logdir"])
        )

        self.finish(json.dumps(
            {'name': name, 'logdir': _trim_notebook_dir(logdir)}))


class TbInstanceHandler(APIHandler):

    SUPPORTED_METHODS = ('GET', 'DELETE')

    @json_errors
    @web.authenticated
    def get(self, name):
        manager = self.settings["tensorboard_manager"]
        if name in manager:
            name, logdir, *_ = manager[name]
            self.finish(json.dumps({
                'name': name,
                'logdir':  _trim_notebook_dir(logdir)}))
        else:
            raise web.HTTPError(
                404, "TensorBoard instance not found: %r" % name)

    @json_errors
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
