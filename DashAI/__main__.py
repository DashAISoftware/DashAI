import pathlib
import webbrowser

import typer
import uvicorn
from typing_extensions import Annotated

from DashAI.back.app import create_app


def open_browser():
    url = "http://localhost:8000/app/"
    webbrowser.open(url, new=0, autoraise=True)


def main(
    local_path: Annotated[
        pathlib.Path, typer.Option(help="Path where DashAI files will be stored.")
    ] = "~/.DashAI",
):
    uvicorn.run(
        create_app(local_path=local_path),
        host="127.0.0.1",
        port=8000,
    )


if __name__ == "__main__":
    typer.run(main)
