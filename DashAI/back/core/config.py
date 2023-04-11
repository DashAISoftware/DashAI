from pydantic import BaseSettings

from DashAI.back.registries import ModelRegistry, TaskRegistry


class Settings(BaseSettings):
    DB_PATH: str = "DashAI/back/database/DashAI.sqlite"
    FRONT_BUILD_PATH: str = "DashAI/front/build"
    USER_DATASET_PATH: str = "DashAI/back/user_datasets"
    API_V0_STR: str = "/api/v0"
    API_V1_STR: str = "/api/v1"
    PLUGINS: bool = False


settings = Settings()

# "Plugin mode" should not load any specific component, just initialize the registries
if settings.PLUGINS:
    task_registry = TaskRegistry(
        initial_components=[],
    )
    model_registry = ModelRegistry(
        task_registry=task_registry,
        initial_components=[],
    )

else:
    from DashAI.back.models import SVC, KNeighborsClassifier, RandomForestClassifier
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


# Registries getters
def get_task_registry():
    return task_registry


def get_model_registry():
    return model_registry
