# -*- coding: utf-8 -*-

from tornado import web
from tornado.wsgi import WSGIContainer
from notebook.base.handlers import IPythonHandler
from notebook.utils import url_path_join as ujoin
from notebook.base.handlers import path_regex

notebook_dir = None


def load_jupyter_server_extension(nb_app):

    global notebook_dir
    notebook_dir = nb_app.notebook_dir

    from . import api_handlers
    from .tensorboard_manager import manager

    web_app = nb_app.web_app
    base_url = web_app.settings['base_url']
    web_app.settings["tensorboard_manager"] = manager

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
    nb_app.log.info("nb_tensorboard extension loaded.")


class TensorboardHandler(IPythonHandler):

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
