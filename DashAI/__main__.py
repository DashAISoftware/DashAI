import logging
import sys
import threading
import webbrowser

import typer
import uvicorn
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.sql import text
from typing_extensions import Annotated

from DashAI.back.core.app import create_app
from DashAI.back.core.config import settings

logging.basicConfig(level=logging.DEBUG)
_logger = logging.getLogger(__name__)


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
    # Init database
    # ---------------------------------------------------------------------------------
    from DashAI.back.database.models import Base
    from DashAI.back.database.session import SessionLocal, engine

    db = SessionLocal()
    Base.metadata.create_all(engine)

    try:
        db.execute(text("SELECT 1"))
    except (SQLAlchemyError, DBAPIError):
        _logger.error("There was an error checking database health")
        sys.exit(1)

    # ---------------------------------------------------------------------------------
    # Launch navigator
    # ---------------------------------------------------------------------------------
    timer = threading.Timer(3, open_browser)
    timer.start()

    # ---------------------------------------------------------------------------------
    # Init FastAPI APP
    # ---------------------------------------------------------------------------------
    app = create_app(settings=settings)
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    typer.run(main)
