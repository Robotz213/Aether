from rich import print
from typer import Typer

app = Typer(name="TheaderWSGI")


@app.command(name="about")
def about() -> None:
    print("ok")


def typer_app() -> object:
    return app()
