"""Main module for DashAI package.

Contains the main function that is executed when the package is called from the
command line.
"""
import logging
import pathlib
import threading
import webbrowser
from enum import Enum

import typer
import uvicorn
from typing_extensions import Annotated

from DashAI.back.app import create_app


class LoggingLevel(str, Enum):
    """Enumeration for logging levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def open_browser() -> None:
    url = "http://localhost:8000/app/"
    webbrowser.open(url=url, new=0, autoraise=True)


def main(
    local_path: Annotated[
        pathlib.Path, typer.Option(help="Path where DashAI files will be stored.")
    ] = "~/.DashAI",  # type: ignore
    logging_level: Annotated[
        LoggingLevel, typer.Option(help="Logging level.")
    ] = LoggingLevel.INFO,
) -> None:
    """Main function for DashAI package.

    This function is executed when the package is called from the command line.
    It starts a timer to open the browser and runs the Dash application using Uvicorn.


    Parameters
    ----------
    local_path : pathlib.Path,
        Path where DashAI local files will be stored, by default "~/.DashAI".
    logging_level : LoggingLevel
        Logging level. Defaults to LoggingLevel.INFO.

    """
    logging.getLogger(name=__package__).setLevel(level=logging_level.value)
    logger = logging.getLogger(__name__)

    logger.info("Starting DashAI application.")
    logger.info("Opening browser.")
    timer = threading.Timer(interval=1, function=open_browser)
    timer.start()

    logger.info("Starting Uvicorn server application.")
    uvicorn.run(
        app=create_app(local_path=local_path, logging_level=logging_level.value),
        host="127.0.0.1",
        port=8000,
    )


if __name__ == "__main__":
    typer.run(main)
