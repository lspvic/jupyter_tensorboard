# -*- coding: utf-8 -*-

from .handlers import load_jupyter_server_extension   # noqa

__version__ = "0.1"


def _jupyter_nbextension_paths():
    section = "tree"
    src = "static"
    return [dict(
        section=section,
        src=src,
        dest=__name__,
        require="%s/%s" % (__name__, section))]


def _jupyter_server_extension_paths():
    return [{
        "module": __name__
    }]
