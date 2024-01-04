import os

from pydantic_settings import BaseSettings

from DashAI.back.dataloaders import CSVDataLoader, ImageDataLoader, JSONDataLoader
from DashAI.back.job.model_job import ModelJob
from DashAI.back.job_queues import BaseJobQueue, SimpleJobQueue
from DashAI.back.metrics import F1, Accuracy, Bleu, Precision, Recall
from DashAI.back.models import (
    SVC,
    DecisionTreeClassifier,
    DistilBertTransformer,
    DummyClassifier,
    HistGradientBoostingClassifier,
    KNeighborsClassifier,
    LogisticRegression,
    OpusMtEnESTransformer,
    RandomForestClassifier,
    ViTTransformer,
)
from DashAI.back.registries.component_registry import ComponentRegistry
from DashAI.back.tasks import (
    ImageClassificationTask,
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
        ImageClassificationTask,
        # Models
        SVC,
        DecisionTreeClassifier,
        DummyClassifier,
        HistGradientBoostingClassifier,
        KNeighborsClassifier,
        LogisticRegression,
        RandomForestClassifier,
        DistilBertTransformer,
        ViTTransformer,
        OpusMtEnESTransformer,
        # Dataloaders
        CSVDataLoader,
        JSONDataLoader,
        ImageDataLoader,
        # Metrics
        F1,
        Accuracy,
        Precision,
        Recall,
        Bleu,
        # Jobs
        ModelJob,
    ],
)

curr_path = os.path.dirname(os.path.realpath(__file__))
parent_path = os.path.dirname(curr_path)
dashai_path = os.path.dirname(parent_path)

job_queue: BaseJobQueue = SimpleJobQueue()


class Settings(BaseSettings):
    DB_PATH: str = os.path.join(dashai_path, "back/database/DashAI.sqlite")
    FRONT_BUILD_PATH: str = os.path.join(dashai_path, "front/build")
    USER_DATASET_PATH: str = os.path.join(dashai_path, "back/user_datasets")
    USER_RUN_PATH: str = os.path.join(dashai_path, "back/user_runs")
    API_V0_STR: str = "/api/v0"
    API_V1_STR: str = "/api/v1"


settings = Settings()
