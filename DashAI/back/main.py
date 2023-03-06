import os

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.responses import FileResponse

from DashAI.back.routers import datasets, experiments

# TODO These imports should be removed because they are unused, but currently needed.
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask
from DashAI.back.tasks.task import Task
from DashAI.back.tasks.text_classification_task import TextClassificationTask
from DashAI.back.tasks.translation_task import TranslationTask

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
