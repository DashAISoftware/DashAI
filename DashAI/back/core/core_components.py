"""DashAI core components orquestator module."""
import logging
import sys
from typing import Final

from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from DashAI.back.config import settings
from DashAI.back.database.models import Base
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
logger = logging.getLogger(__name__)

# -----------------------------------------------
# Factories


def create_component_registry(settings: BaseSettings) -> ComponentRegistry:
    """Construct a component registry based on the specified settings.

    Parameters
    ----------
    settings : BaseSettings
        The current app settings.

    Returns
    -------
    ComponentRegistry
        The instantiated component registry.
    """
    if settings.DASHAI_TEST_MODE:
        logger.info("Starting the test component registry.")
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

    logger.info("Starting the component registry.")
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


def create_db(settings: BaseSettings) -> Engine:
    """Factory function to create a database and instantiate a session.

    Parameters
    ----------
    settings : BaseSettings
        The current app settings.

    Returns
    -------
    Engine
        The generated database session.
    """
    db_path = f"sqlite:///{settings.DB_PATH}"
    logger.info(
        "Starting %sdatabase on %s.",
        "test " if settings.DASHAI_TEST_MODE else "",
        db_path,
    )

    engine = create_engine(db_path)

    session_local = sessionmaker(bind=engine)
    db = session_local()
    Base.metadata.create_all(engine)

    try:
        db.execute(text("SELECT 1"))
    except (SQLAlchemyError, DBAPIError):
        logger.error("There was an error checking database health")
        sys.exit(1)

    return session_local


# -----------------------------------------------
# Start core components

component_registry: Final[ComponentRegistry] = create_component_registry(settings)
job_queue: Final[BaseJobQueue] = SimpleJobQueue()
db_session: Final[Engine] = create_db(settings)
