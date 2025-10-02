"""ThreaderWSGI main entry point."""

from contextlib import suppress
from importlib import import_module
from wsgiref.types import WSGIApplication

from rich import print
from typer import Typer

from threaderwsgi._threadpoolwsgi import ThreadPoolWSGIServer

app = Typer(name="TheaderWSGI")


@app.command(name="run")
def run(
    app: str = "app:app",
    host: str = "localhost",
    port: int = 5000,
) -> None:
    """Executa o servidor WSGI com ThreadPool."""
    if ":" in app:
        module_name, app_name = app.split(":", 1)
        app_module: WSGIApplication = import_module(module_name)

        app_instance = getattr(app_module, app_name)

        if callable(app_instance):
            app_instance = app_instance()

        ThreadPoolWSGIServer(host=host, port=port, app=app_instance).run()


@app.command(name="serve", deprecated=True)
def serve(
    app: str = "app:app",
    host: str = "localhost",
    port: int = 5000,
) -> None:
    """Executa o servidor WSGI com ThreadPool."""
    if ":" in app:
        module_name, app_name = app.split(":", 1)

        with suppress(ImportError):
            app_module: WSGIApplication = import_module(module_name)

            app_instance = getattr(app_module, app_name)

            if callable(app_instance):
                app_instance = app_instance()

            ThreadPoolWSGIServer(host=host, port=port, app=app_instance).run()
            return

        print(f"[red]Error:[/red] Module '{module_name}' not found.")
