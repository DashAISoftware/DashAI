import logging
import threading
import webbrowser

import typer
import uvicorn
from typing_extensions import Annotated

from DashAI.back.core.app import create_app
from DashAI.back.core.config import settings


def open_browser() -> None:
    url = "http://localhost:8000/app/"
    webbrowser.open(url, new=0, autoraise=True)


def main(
    dev_mode: Annotated[
        bool, typer.Option(help="Run DashAI in development mode.")
    ] = False,
) -> None:
    # ---------------------------------------------------------------------------------
    # Init configs
    # ---------------------------------------------------------------------------------
    if dev_mode:
        logging.info("Starting DashAI in development mode.")
        settings.DASHAI_DEV_MODE = True
    else:
        settings.DASHAI_DEV_MODE = False

    # ---------------------------------------------------------------------------------
    # Init database, job_queue and component registry
    # ---------------------------------------------------------------------------------
    from DashAI.back.core.core_components import (  # noqa: F401
        component_registry,
        db,
        job_queue,
    )

    # Launch navigator
    timer = threading.Timer(3, open_browser)
    timer.start()

    # Init FastAPI APP
    app = create_app(settings=settings)
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    typer.run(main)
