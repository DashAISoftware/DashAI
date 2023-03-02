import logging
import sys

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import FileResponse

from DashAI.back.routers import datasets, experiments

# TODO These imports should be removed because they are unused, but currently needed.
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask
from DashAI.back.tasks.task import Task
from DashAI.back.tasks.text_classification_task import TextClassificationTask
from DashAI.back.tasks.translation_task import TranslationTask

app = FastAPI(title="DashAI")


@app.get("/")
async def redirect():
    return RedirectResponse(url="/app")


api = FastAPI(title="DashAI API")

api.include_router(datasets.router)
api.include_router(experiments.router)

app.mount("/static", StaticFiles(directory="DashAI/front/build/static"), name="static")
app.mount("/images", StaticFiles(directory="DashAI/front/build/images"), name="images")
app.mount("/api", api)


@app.get("/app/{full_path:path}")
async def read_index():
    return FileResponse("DashAI/front/build/index.html")
