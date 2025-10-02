from rich import print
from typer import Typer

app = Typer(name="TheaderWSGI")


@app.command(name="teste")
def teste() -> None:
    print("ok")


@app.command(name="teste2")
def teste2() -> None:
    print("ok")
