import logging
from typing import Dict

from kink import Container, di

from DashAI.back.converters import Binarizer, StandardScaler

from DashAI.back.dataloaders import (
    CSVDataLoader,
    ExcelDataLoader,
    ImageDataLoader,
    JSONDataLoader,
)
from DashAI.back.dependencies.database import setup_sqlite_db
from DashAI.back.dependencies.job_queues import SimpleJobQueue
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.explainability import (
    FitKernelShap,
    KernelShap,
    PartialDependence,
    PermutationFeatureImportance,
)
from DashAI.back.job import ExplainerJob, ModelJob
from DashAI.back.metrics import F1, Accuracy, Bleu, Precision, Recall
from DashAI.back.models import (
    SVC,
    BagOfWordsTextClassificationModel,
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
from DashAI.back.optimizers import (
    HyperOptOptimizer,
    OptunaOptimizer,
)
from DashAI.back.tasks import (
    ImageClassificationTask,
    TabularClassificationTask,
    TextClassificationTask,
    TranslationTask,
)

logger = logging.getLogger(__name__)


INITIAL_COMPONENTS = [
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
    BagOfWordsTextClassificationModel,
    # Dataloaders
    CSVDataLoader,
    JSONDataLoader,
    ImageDataLoader,
    ExcelDataLoader,
    # Metrics
    F1,
    Accuracy,
    Precision,
    Recall,
    Bleu,
    # Optimizers
    OptunaOptimizer,
    HyperOptOptimizer,
    # Jobs
    ExplainerJob,
    ModelJob,
    # Explainers
    KernelShap,
    PartialDependence,
    PermutationFeatureImportance,
    # Explainers Fit Schema
    FitKernelShap,
    # Converters
    Binarizer,
    StandardScaler,
]


def build_container(config: Dict[str, str]) -> Container:
    """
    Creates a dependency injection container for the application.

    Parameters
    ----------
    config : Dict[str, str]
        A dictionary containing configuration settings.

    Returns
    -------
    Container
        A dependency injection container instance populated with
        essential services. These services include:
            * 'config': The provided configuration dictionary.
            * Engine: The created SQLAlchemy engine for the SQLite database.
            * sessionmaker: A session factory for creating database sessions.
            * ComponentRegistry: The app component registry.
            * BaseJobQueue: The app job queue.
    """
    engine, session_factory = setup_sqlite_db(config)

    di["config"] = config
    di["engine"] = engine
    di["session_factory"] = session_factory
    di["component_registry"] = ComponentRegistry(initial_components=INITIAL_COMPONENTS)
    di["job_queue"] = SimpleJobQueue()

    return di
