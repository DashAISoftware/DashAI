# isort: skip_file
import json
import os

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.responses import FileResponse

from DashAI.back.tasks import (
    BaseTask,
    TabularClassificationTask,
    TextClassificationTask,
    TranslationTask,
)
from DashAI.back.models import (
    SVC,
    KNeighborsClassifier,
    RandomForestClassifier,
)
from DashAI.back.models.classes.getters import (
    filter_by_parent,
    get_model_params_from_task,
)
from DashAI.back.registries import ModelRegistry, TaskRegistry
from DashAI.back.routers import datasets, experiments


task_registry = TaskRegistry(
    initial_components=[
        TabularClassificationTask,
        TextClassificationTask,
        TranslationTask,
    ],
)

model_registry = ModelRegistry(
    task_registry=task_registry,
    initial_components=[
        SVC,
        KNeighborsClassifier,
        RandomForestClassifier,
    ],
)


app = FastAPI(title="DashAI")
api = FastAPI(title="DashAI API")

api.include_router(datasets.router)
api.include_router(experiments.router)
app.mount("/api", api)


# Frontend should handle unknown paths under /app
@app.get("/app/{full_path:path}")
async def read_index():
    return FileResponse("DashAI/front/build/index.html")


@app.get("/{full_path:path}")
async def serve_files(full_path: str):
    try:
        if full_path == "":
            return RedirectResponse(url="/app/")
        path = f"DashAI/front/build/{full_path}"
        os.stat(path)  # This checks if the file exists
        return FileResponse(path)  # You can't catch the exception here
    except FileNotFoundError:
        return RedirectResponse(url="/app/")
