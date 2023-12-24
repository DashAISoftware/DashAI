"""Main module for DashAI package.

Contains the main function that is executed when the package is called from the
command line.
"""
import logging
import pathlib
import webbrowser
from enum import Enum

import typer
import uvicorn
from typing_extensions import Annotated

from DashAI.back.app import create_app


class LoggingLevel(str, Enum):
    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def open_browser():
    url = "http://localhost:8000/app/"
    webbrowser.open(url, new=0, autoraise=True)


def main(
    local_path: Annotated[
        pathlib.Path, typer.Option(help="Path where DashAI files will be stored.")
    ] = "~/.DashAI",
    logging_level: Annotated[
        LoggingLevel, typer.Option(help="Logging level.")
    ] = LoggingLevel.INFO,
):
    uvicorn.run(
        create_app(local_path=local_path, logging_level=logging_level),
        host="127.0.0.1",
        port=8000,
    )


if __name__ == "__main__":
    typer.run(main)
