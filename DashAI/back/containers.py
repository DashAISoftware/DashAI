from dependency_injector import containers, providers

from DashAI.back.dataloaders import CSVDataLoader, JSONDataLoader
from DashAI.back.dependencies.database import SQLiteDatabase
from DashAI.back.dependencies.job_queues import SimpleJobQueue
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.job.model_job import ModelJob
from DashAI.back.metrics import F1, Accuracy, Precision, Recall  # Bleu,
from DashAI.back.models import (  # DistilBertTransformer,; OpusMtEnESTransformer,; ViTTransformer,
    SVC,
    DecisionTreeClassifier,
    DummyClassifier,
    HistGradientBoostingClassifier,
    KNeighborsClassifier,
    LogisticRegression,
    RandomForestClassifier,
)
from DashAI.back.tasks import (  # ImageClassificationTask,
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

    db = providers.Singleton(SQLiteDatabase, db_path=config.SQLITE_DB_PATH)
    job_queue = providers.Singleton(SimpleJobQueue)
    component_registry = providers.Singleton(
        ComponentRegistry,
        initial_components=[
            # Tasks
            TabularClassificationTask,
            TextClassificationTask,
            TranslationTask,
            # ImageClassificationTask,
            # Models
            SVC,
            DecisionTreeClassifier,
            DummyClassifier,
            HistGradientBoostingClassifier,
            KNeighborsClassifier,
            LogisticRegression,
            RandomForestClassifier,
            # DistilBertTransformer,
            # ViTTransformer,
            # OpusMtEnESTransformer,
            # Dataloaders
            CSVDataLoader,
            JSONDataLoader,
            # ImageDataLoader,
            # Metrics
            F1,
            Accuracy,
            Precision,
            Recall,
            # Bleu,
            # Jobs
            ModelJob,
        ],
    )
