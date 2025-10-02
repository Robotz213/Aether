"""Threaded WSGI Server com graceful shutdown."""

from tqdm import tqdm
from typer import Typer

from ._requesthandlerwsgi import WSGIRequestHandler
from ._threadpoolwsgi import ThreadPoolWSGIServer

app = Typer(name="TheaderWSGI")


@app.command()
def about() -> None:
    tqdm.write("ok")


def _main_function() -> None:
    return app()


__all__ = [ThreadPoolWSGIServer, WSGIRequestHandler, _main_function]
