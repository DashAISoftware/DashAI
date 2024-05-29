import logging
from typing import Dict

from kink import Container, di
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from DashAI.back.dataloaders import CSVDataLoader, ImageDataLoader, JSONDataLoader
from DashAI.back.dependencies.database.sqlite_database import setup_sqlite_db
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.job.model_job import ModelJob
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
from DashAI.back.tasks import (
    ImageClassificationTask,
    TabularClassificationTask,
    TextClassificationTask,
    TranslationTask,
)

logger = logging.getLogger(__name__)


def get_component_registry() -> ComponentRegistry:
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
            # Jobs
            ModelJob,
        ],
    )


def build_container(config: Dict[str, str]) -> Container:
    engine, session_maker = setup_sqlite_db(config)

    di["config"] = config
    di[Engine] = engine
    di[sessionmaker] = session_maker
    di[ComponentRegistry] = get_component_registry()

    return di
