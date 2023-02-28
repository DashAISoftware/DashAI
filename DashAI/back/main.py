import logging
import sys

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.sql import text

from DashAI.back.database import db
from DashAI.back.routers import datasets, experiments

# TODO These imports should be removed because they are unused, but currently needed.
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask
from DashAI.back.tasks.task import Task
from DashAI.back.tasks.text_classification_task import TextClassificationTask
from DashAI.back.tasks.translation_task import TranslationTask

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

app = FastAPI(title="DashAI")


@app.get("/")
async def redirect():
    return RedirectResponse(url="/app")


api = FastAPI(title="DashAI API")

api.include_router(datasets.router)
api.include_router(experiments.router)

app.mount("/static", StaticFiles(directory="DashAI/front/build/static"), name="static")
app.mount("/images", StaticFiles(directory="DashAI/front/build/images"), name="images")
templates = Jinja2Templates(directory="DashAI/front/build")

app.mount("/api", api)


@app.get("/app/{full_path:path}")
async def serve_app(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    db.Base.metadata.create_all(db.engine)
    try:
        db.session.execute(text("SELECT 1"))
    except (SQLAlchemyError, DBAPIError):
        log.error("There was an error checking database health")
        sys.exit(1)
    uvicorn.run(app, host="127.0.0.1", port=8000)
