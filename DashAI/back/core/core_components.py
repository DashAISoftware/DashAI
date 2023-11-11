"""DashAI core components orquestator module."""
import logging
import sys
from typing import Final

from pydantic_settings import BaseSettings
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.sql import text

from DashAI.back.core.config import settings
from DashAI.back.database.models import Base
from DashAI.back.database.session import SessionLocal, engine
from DashAI.back.dataloaders import CSVDataLoader, ImageDataLoader, JSONDataLoader
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

logging.basicConfig(level=logging.DEBUG)
_logger = logging.getLogger(__name__)

# -----------------------------------------------
# Factories


def create_component_registry(settings: BaseSettings) -> ComponentRegistry:
    """Construct a component registry based on the specified settings.

    Parameters
    ----------
    settings : BaseSettings
        DashAI base settings object.

    Returns
    -------
    ComponentRegistry
        The instantiated component registry.
    """
    if settings.DASHAI_DEV_MODE:
        return ComponentRegistry(
            [
                # Tasks
                TabularClassificationTask,
                TextClassificationTask,
                # Models
                SVC,
                DecisionTreeClassifier,
                DummyClassifier,
                # Dataloaders
                CSVDataLoader,
                JSONDataLoader,
                # Metrics
                F1,
                Accuracy,
                Precision,
                Recall,
            ]
        )

    return ComponentRegistry(
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
        ],
    )


# -----------------------------------------------
# Start database

db = SessionLocal()
Base.metadata.create_all(engine)

try:
    db.execute(text("SELECT 1"))
except (SQLAlchemyError, DBAPIError):
    _logger.error("There was an error checking database health")
    sys.exit(1)

# -----------------------------------------------
# Start component registry

component_registry: Final[ComponentRegistry] = create_component_registry(settings)

# -----------------------------------------------
# Start job queue

job_queue: Final[BaseJobQueue] = SimpleJobQueue()
