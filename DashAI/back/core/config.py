from typing import Dict

from pydantic import BaseSettings

from DashAI.back.dataloaders import CSVDataLoader, JSONDataLoader
from DashAI.back.metrics import Accuracy, F1Score, Precision, Recall
from DashAI.back.models import SVC, KNeighborsClassifier, RandomForestClassifier
from DashAI.back.registries import (
    BaseRegistry,
    DataloaderRegistry,
    MetricRegistry,
    ModelRegistry,
    TaskRegistry,
)
from DashAI.back.tasks import (
    TabularClassificationTask,
    TextClassificationTask,
    TranslationTask,
)

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

dataloader_registry = DataloaderRegistry(
    task_registry=task_registry,
    initial_components=[
        CSVDataLoader,
        JSONDataLoader,
    ],
)

metric_registry = MetricRegistry(
    task_registry=task_registry,
    initial_components=[Accuracy, Precision, Recall, F1Score],
)

name_registry_mapping: Dict[str, BaseRegistry] = {
    "task": task_registry,
    "model": model_registry,
    "dataloader": dataloader_registry,
    "metric": metric_registry,
}


class Settings(BaseSettings):
    DB_PATH: str = "DashAI/back/database/DashAI.sqlite"
    FRONT_BUILD_PATH: str = "DashAI/front/build"
    USER_DATASET_PATH: str = "DashAI/back/user_datasets"
    USER_RUN_PATH: str = "DashAI/back/user_runs"
    API_V0_STR: str = "/api/v0"
    API_V1_STR: str = "/api/v1"


settings = Settings()
