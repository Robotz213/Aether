"""ThreaderWSGI main entry point."""

import platform
from contextlib import suppress
from importlib import import_module
from typing import Annotated
from wsgiref.types import WSGIApplication

from rich import print
from typer import Argument, Typer

from threaderwsgi._processpoolwsgi import ProcessPoolWSGIServer
from threaderwsgi._threadpoolwsgi import ThreadPoolWSGIServer
from threaderwsgi._types import Host, Port

th = Typer(name="TheaderWSGI")


def _runapp(host: Host, port: Port, app: str) -> None:
    if ":" in app:
        module_name, app_name = app.split(":", 1)

        with suppress(ImportError):
            app_module: WSGIApplication = import_module(
                module_name,
                __package__,
            )

            app_instance = getattr(app_module, app_name)

            if app_name != "app" and callable(app_instance):
                app_instance = app_instance()

            ThreadPoolWSGIServer(host=host, port=port, app=app_instance).run()
            return

        print(f"[red]Error:[/red] Module '{module_name}' not found.")


@th.command(name="run")
def run(
    app: Annotated[
        str,
        Argument(help="App WSGI no formato module:app"),
    ] = "app:app",
    host: Annotated[
        str,
        Argument(help="Api host"),
    ] = "localhost",
    port: Annotated[
        int,
        Argument(help="Api port"),
    ] = 5000,
) -> None:
    """Executa o servidor WSGI com ThreadPool."""
    _runapp(host, port, app)


@th.command(name="serve", deprecated=True)
def serve(
    app: Annotated[
        str,
        Argument(help="App WSGI no formato module:app"),
    ] = "app:app",
    host: Annotated[
        str,
        Argument(help="Api host"),
    ] = "localhost",
    port: Annotated[
        int,
        Argument(help="Api port"),
    ] = 5000,
) -> None:
    """Executa o servidor WSGI com ThreadPool."""
    _runapp(host, port, app)


if platform.system() == "Linux":

    @th.command(name="runserver")
    def runserver(
        app: str = "app:app",
        host: str = "localhost",
        port: int = 5000,
    ) -> None:
        """Executa o servidor WSGI com ProcessPool."""
        if ":" in app:
            module_name, app_name = app.split(":", 1)
            app_module: WSGIApplication = import_module(module_name)

            app_instance = getattr(app_module, app_name)

            if app_name != "app" and callable(app_instance):
                app_instance = app_instance()

            ProcessPoolWSGIServer(host=host, port=port, app=app_instance).run()
