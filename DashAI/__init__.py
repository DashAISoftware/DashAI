# Este archivo corre al hacer import DashAI
import logging
import sys
import threading
import webbrowser
from subprocess import Popen

import uvicorn
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.sql import text

from DashAI.back.database import db
from DashAI.back.main import app
from DashAI.back.database.models import Base
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def open_browser():
    url = "http://localhost:8000/app/"
    webbrowser.open(url, new=0, autoraise=True)


def run():
    Base.metadata.create_all(db.engine)
    timer = threading.Timer(1, open_browser)
    timer.start()
    try:
        db.session.execute(text("SELECT 1"))
    except (SQLAlchemyError, DBAPIError):
        log.error("There was an error checking database health")
        sys.exit(1)
    uvicorn.run(app, host="127.0.0.1", port=8000)
