from dependency_injector import containers, providers

from DashAI.back.database.database import SQLiteDatabase
from DashAI.back.dataloaders import CSVDataLoader, ImageDataLoader, JSONDataLoader
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
from DashAI.back.services.registry import ComponentRegistry
from DashAI.back.tasks import (
    ImageClassificationTask,
    TabularClassificationTask,
    TextClassificationTask,
    TranslationTask,
)


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["DashAI"], auto_wire=True)

    config = providers.Configuration(yaml_files=["DashAI/back/core/config.yaml"])

    db = providers.Singleton(
        SQLiteDatabase,
        db_path=config.SQLITE_DB_PATH,
    )

    component_registry = providers.Singleton(
        ComponentRegistry,
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
