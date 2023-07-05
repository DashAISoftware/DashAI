from pydantic import BaseSettings

from DashAI.back.dataloaders import CSVDataLoader, JSONDataLoader
from DashAI.back.job_queues import BaseJobQueue, SimpleJobQueue
from DashAI.back.metrics import F1, Accuracy, Precision, Recall
from DashAI.back.models import SVC, KNeighborsClassifier, RandomForestClassifier
from DashAI.back.registries.component_registry import ComponentRegistry
from DashAI.back.tasks import (
    TabularClassificationTask,
    TextClassificationTask,
    TranslationTask,
)

component_registry = ComponentRegistry(
    initial_components=[
        # Tasks
        TabularClassificationTask,
        TextClassificationTask,
        TranslationTask,
        # Models
        SVC,
        KNeighborsClassifier,
        RandomForestClassifier,
        # Dataloaders
        CSVDataLoader,
        JSONDataLoader,
        # Metrics
        F1,
        Accuracy,
        Precision,
        Recall,
    ],
)

job_queue: BaseJobQueue = SimpleJobQueue()


class Settings(BaseSettings):
    DB_PATH: str = "DashAI/back/database/DashAI.sqlite"
    FRONT_BUILD_PATH: str = "DashAI/front/build"
    USER_DATASET_PATH: str = "DashAI/back/user_datasets"
    USER_RUN_PATH: str = "DashAI/back/user_runs"
    API_V0_STR: str = "/api/v0"
    API_V1_STR: str = "/api/v1"


settings = Settings()
