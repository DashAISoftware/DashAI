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
from DashAI.back.registries.component_registry import ComponentRegistry
from DashAI.back.tasks import (
    ImageClassificationTask,
    TabularClassificationTask,
    TextClassificationTask,
    TranslationTask,
)

component_registry = ComponentRegistry(
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
