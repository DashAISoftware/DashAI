from dependency_injector import containers, providers

from DashAI.back.dataloaders import CSVDataLoader, ImageDataLoader, JSONDataLoader
from DashAI.back.dependencies.database import SQLiteDatabase
from DashAI.back.dependencies.job_queues import SimpleJobQueue
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
    LinearRegression,
    LinearSVR,
    LogisticRegression,
    OpusMtEnESTransformer,
    RandomForestClassifier,
    RandomForestRegression,
    RidgeRegression,
    ViTTransformer,
)
from DashAI.back.tasks import (
    ImageClassificationTask,
    RegressionTask,
    TabularClassificationTask,
    TextClassificationTask,
    TranslationTask,
)


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["DashAI", "tests"],
        auto_wire=True,
    )

    config = providers.Configuration()

    db = providers.Singleton(
        provides=SQLiteDatabase,
        db_path=config.SQLITE_DB_PATH,
        logging_level=config.LOGGING_LEVEL,
    )
    job_queue = providers.Singleton(SimpleJobQueue)
    component_registry = providers.Singleton(
        ComponentRegistry,
        initial_components=[
            # Tasks
            TabularClassificationTask,
            TextClassificationTask,
            TranslationTask,
            ImageClassificationTask,
            RegressionTask,
            # Models
            SVC,
            DecisionTreeClassifier,
            DummyClassifier,
            HistGradientBoostingClassifier,
            KNeighborsClassifier,
            LogisticRegression,
            RandomForestClassifier,
            RandomForestRegression,
            DistilBertTransformer,
            ViTTransformer,
            OpusMtEnESTransformer,
            RidgeRegression,
            LinearSVR,
            LinearRegression,
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
