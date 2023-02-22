import json

import uvicorn
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from DashAI.back.config_object import ConfigObject
from DashAI.back.database import db
from DashAI.back.models.classes.getters import filter_by_parent
from DashAI.back.models.enums.squema_types import SquemaTypes
from DashAI.back.routers import datasets, experiments
from DashAI.back.routers.session_class import session_info

# TODO These imports should be removed because they are unused, but currently needed.
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask
from DashAI.back.tasks.task import Task
from DashAI.back.tasks.text_classification_task import TextClassificationTask
from DashAI.back.tasks.translation_task import TranslationTask

app = FastAPI(title="DashAI")

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(datasets.router)
app.include_router(experiments.router)


if __name__ == "__main__":
    db.Base.metadata.create_all(db.engine)
    uvicorn.run(app, host="127.0.0.1", port=8000)
