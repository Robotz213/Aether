"""Threaded WSGI Server com graceful shutdown."""

import tqdm

from ._requesthandlerwsgi import WSGIRequestHandler
from ._threadpoolwsgi import ThreadPoolWSGIServer


def _main_function() -> None:
    tqdm.tqdm.write("ok")


__all__ = [ThreadPoolWSGIServer, WSGIRequestHandler, _main_function]
