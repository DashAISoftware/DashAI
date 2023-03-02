# Este archivo corre al hacer import DashAI
import uvicorn
import webbrowser
import logging
import sys
from subprocess import Popen
from DashAI.back.main import app
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.sql import text
import threading
from DashAI.back.database import db
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def open_browser():
    url = "http://localhost:8000/app/"
    webbrowser.open(url, new=0, autoraise=True)

def run():
    db.Base.metadata.create_all(db.engine)
    timer = threading.Timer(1,open_browser)
    timer.start()
    try:
        db.session.execute(text("SELECT 1"))
    except (SQLAlchemyError, DBAPIError):
        log.error("There was an error checking database health")
        sys.exit(1)
    uvicorn.run(app, host="127.0.0.1", port=8000)
