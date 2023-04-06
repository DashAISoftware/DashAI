# Este archivo corre al hacer import DashAI
import logging
import sys
import threading
import webbrowser
import subprocess
import os

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

def set_db():
    Base.metadata.create_all(db.engine)
    timer = threading.Timer(1, open_browser)
    timer.start()
    try:
        db.session.execute(text("SELECT 1"))
    except (SQLAlchemyError, DBAPIError):
        log.error("There was an error checking database health")
        sys.exit(1)

def run():
    set_db()
    uvicorn.run(app, host="127.0.0.1", port=8000)

def run_plugins():
    set_db()
    os.environ["PLUGINS"]="True"
    subprocess.run(['gunicorn', 'DashAI.back.main:app', "-k", 'uvicorn.workers.UvicornWorker'])
    # uvicorn.run(app, host="127.0.0.1", UVICORN_PORT=8000)
    # subprocess.run(["export", "PLUGINS=True"], shell=True)

