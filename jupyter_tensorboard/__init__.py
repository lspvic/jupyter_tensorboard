# -*- coding: utf-8 -*-

from .handlers import load_jupyter_server_extension   # noqa

__version__ = "0.1.8"


def _jupyter_nbextension_paths():
    name = __name__
    section = "tree"
    src = "static"
    return [dict(
        section=section,
        src=src,
        dest=name,
        require="%s/%s" % (name, section))]


def _jupyter_server_extension_paths():
    return [{
        "module": __name__
    }]
