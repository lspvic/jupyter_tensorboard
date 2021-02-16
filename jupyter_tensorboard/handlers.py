# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019, Shengpeng Liu.  All rights reserved.
# Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.

from tornado import web
from tornado.wsgi import WSGIContainer
from notebook.base.handlers import IPythonHandler
from notebook.utils import url_path_join as ujoin
from notebook.base.handlers import path_regex

notebook_dir = None


def load_jupyter_server_extension(nb_app):

    global notebook_dir
    # notebook_dir should be root_dir of contents_manager
    notebook_dir = nb_app.contents_manager.root_dir

    web_app = nb_app.web_app
    base_url = web_app.settings['base_url']

    try:
        from .tensorboard_manager import manager
    except ImportError:
        nb_app.log.info("import tensorboard error, check tensorflow install")
        handlers = [
            (ujoin(
                base_url, r"/tensorboard.*"),
                TensorboardErrorHandler),
        ]
    else:
        web_app.settings["tensorboard_manager"] = manager
        from . import api_handlers

        handlers = [
            (ujoin(
                base_url, r"/tensorboard/(?P<name>\w+)%s" % path_regex),
                TensorboardHandler),
            (ujoin(
                base_url, r"/api/tensorboard"),
                api_handlers.TbRootHandler),
            (ujoin(
                base_url, r"/api/tensorboard/(?P<name>\w+)"),
                api_handlers.TbInstanceHandler),
            (ujoin(
                base_url, r"/font-roboto/.*"),
                TbFontHandler),
        ]

    web_app.add_handlers('.*$', handlers)
    nb_app.log.info("jupyter_tensorboard extension loaded.")


class TensorboardHandler(IPythonHandler):


    def _impl(self, name, path):

        self.request.path = path

        manager = self.settings["tensorboard_manager"]
        if name in manager:
            tb_app = manager[name].tb_app
            WSGIContainer(tb_app)(self.request)
        else:
            raise web.HTTPError(404)

    @web.authenticated
    def get(self, name, path):

        if path == "":
            uri = self.request.path + "/"
            if self.request.query:
                uri += "?" + self.request.query
            self.redirect(uri, permanent=True)
            return

        self._impl(name, path)

    @web.authenticated
    def post(self, name, path):

        if path == "":
            raise web.HTTPError(403)

        self._impl(name, path)


class TbFontHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        manager = self.settings["tensorboard_manager"]
        if "1" in manager:
            tb_app = manager["1"].tb_app
            WSGIContainer(tb_app)(self.request)
        else:
            raise web.HTTPError(404)


class TensorboardErrorHandler(IPythonHandler):
    pass
