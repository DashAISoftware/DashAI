from pydantic import BaseSettings

from DashAI.back.dataloaders import CSVDataLoader, JSONDataLoader
from DashAI.back.models import SVC, KNeighborsClassifier, RandomForestClassifier
from DashAI.back.registries.base_registry_v2 import BaseRegistry
from DashAI.back.registries.relationship_manager import TaskComponentRelationshipManager
from DashAI.back.tasks import (
    TabularClassificationTask,
    TextClassificationTask,
    TranslationTask,
)

task_component_relationship_manager = TaskComponentRelationshipManager()

task_registry = BaseRegistry(
    initial_components=[
        TabularClassificationTask,
        TextClassificationTask,
        TranslationTask,
    ],
    task_component_relationship_manager=task_component_relationship_manager,
)

component_registry = BaseRegistry(
    initial_components=[
        SVC,
        KNeighborsClassifier,
        RandomForestClassifier,
        CSVDataLoader,
        JSONDataLoader,
    ],
    task_component_relationship_manager=task_component_relationship_manager,
)


class Settings(BaseSettings):
    DB_PATH: str = "DashAI/back/database/DashAI.sqlite"
    FRONT_BUILD_PATH: str = "DashAI/front/build"
    USER_DATASET_PATH: str = "DashAI/back/user_datasets"
    API_V0_STR: str = "/api/v0"
    API_V1_STR: str = "/api/v1"


settings = Settings()
