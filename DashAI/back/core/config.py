import os

from pydantic_settings import BaseSettings

from DashAI.back.dataloaders import CSVDataLoader, JSONDataLoader
from DashAI.back.metrics import F1, Accuracy, Precision, Recall
from DashAI.back.models import (
    SVC,
    DecisionTreeClassifier,
    DistilBertTransformer,
    DummyClassifier,
    HistGradientBoostingClassifier,
    KNeighborsClassifier,
    LogisticRegression,
    RandomForestClassifier,
)
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
        DecisionTreeClassifier,
        DummyClassifier,
        HistGradientBoostingClassifier,
        KNeighborsClassifier,
        LogisticRegression,
        RandomForestClassifier,
        DistilBertTransformer,
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

curr_path = os.path.dirname(os.path.realpath(__file__))
parent_path = os.path.dirname(curr_path)
dashai_path = os.path.dirname(parent_path)


class Settings(BaseSettings):
    DB_PATH: str = os.path.join(dashai_path, "back/database/DashAI.sqlite")
    FRONT_BUILD_PATH: str = os.path.join(dashai_path, "front/build")
    USER_DATASET_PATH: str = os.path.join(dashai_path, "back/user_datasets")
    USER_RUN_PATH: str = os.path.join(dashai_path, "back/user_runs")
    API_V0_STR: str = "/api/v0"
    API_V1_STR: str = "/api/v1"


settings = Settings()
