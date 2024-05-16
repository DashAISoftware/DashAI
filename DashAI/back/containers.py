from dependency_injector import containers, providers

from DashAI.back.dataloaders import CSVDataLoader, JSONDataLoader
from DashAI.back.dependencies.database import SQLiteDatabase
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
            # ImageClassificationTask,
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
            # ImageDataLoader,
            # Metrics
            F1,
            Accuracy,
            Precision,
            Recall,
            Bleu,
            # Jobs
            ExplainerJob,
            ModelJob,
            # Explainers
            KernelShap,
            PartialDependence,
            PermutationFeatureImportance,
            # Explainers Fit Schema
            FitKernelShap,
        ],
    )
