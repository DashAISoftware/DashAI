import logging
import sys
import threading
import webbrowser

import typer
import uvicorn
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.sql import text
from typing_extensions import Annotated

from DashAI.back.database.models import Base
from DashAI.back.database.session import SessionLocal, engine
from DashAI.back.main import app

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

    db = SessionLocal()
    Base.metadata.create_all(engine)
    timer = threading.Timer(1, open_browser)
    timer.start()

    try:
        db.execute(text("SELECT 1"))
    except (SQLAlchemyError, DBAPIError):
        _logger.error("There was an error checking database health")
        sys.exit(1)
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    typer.run(main)
