import logging
import webbrowser

import typer
import uvicorn
from typing_extensions import Annotated

from DashAI.back.server import create_app

logging.basicConfig(level=logging.DEBUG)
_logger = logging.getLogger(__name__)


def open_browser():
    url = "http://localhost:8000/app/"
    webbrowser.open(url, new=0, autoraise=True)


def main(
    dev_mode: Annotated[
        bool, typer.Option(help="Run DashAI in development mode.")
    ] = True,
):
    if dev_mode:
        logging.info("DashAI was set to development mode.")

    uvicorn.run(create_app(), host="127.0.0.1", port=8000)


if __name__ == "__main__":
    typer.run(main)
