# -*- coding: utf-8 -*-

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
        ]

    web_app.add_handlers('.*$', handlers)
    nb_app.log.info("jupyter_tensorboard extension loaded.")


class TensorboardHandler(IPythonHandler):

    @web.authenticated
    def get(self, name, path):

        if path == "":
            uri = self.request.path + "/"
            if self.request.query:
                uri += "?" + self.request.query
            self.redirect(uri, permanent=True)
            return

        self.request.path = (
            path if self.request.query
            else "%s?%s" % (path, self.request.query))

        manager = self.settings["tensorboard_manager"]
        if name in manager:
            tb_app = manager[name].tb_app
            WSGIContainer(tb_app)(self.request)
        else:
            raise web.HTTPError(404)

    @web.authenticated
    def post(self, name, path):

        if path == "":
            uri = self.request.path + "/"
            if self.request.query:
                uri += "?" + self.request.query
            self.redirect(uri, permanent=True)
            return

        self.request.path = (
            path if self.request.query
            else "%s?%s" % (path, self.request.query))

        manager = self.settings["tensorboard_manager"]
        if name in manager:
            tb_app = manager[name].tb_app
            WSGIContainer(tb_app)(self.request)
        else:
            raise web.HTTPError(404)

    def check_xsrf_cookie(self):
        """Expand xsrf check exception for POST requests.

        Expand xsrf_cookie exceptions, normally only applied to GET and HEAD
        requests, to POST requests for tensorboard api.

        Provides support for hparams plugin, which uses POST to retrieve
        experiment information but can't be trivially extended to include xsrf
        information in these POST requests.

        """

        try:
            return super(TensorboardHandler, self).check_xsrf_cookie()
        except web.HTTPError:
            if self.request.method in {"GET", "POST", "HEAD"}:
                # Consider Referer a sufficient cross-origin check for GET
                # requests, mirrors logic in IPythonHandler.check_xsrf_cookie.
                # Extended to POST for Tensorboard API.
                if not self.check_referer():
                    referer = self.request.headers.get("Referer")
                    if referer:
                        msg = (
                            "Blocking Cross Origin request from {}."
                            .format(referer)
                        )
                    else:
                        msg = "Blocking request from unknown origin"
                    raise web.HTTPError(403, msg)
            else:
                raise


class TensorboardErrorHandler(IPythonHandler):
    pass
