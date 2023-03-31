from DashAI.back.tasks import (
    BaseTask,
    TabularClassificationTask,
    TextClassificationTask,
    TranslationTask,
)
from DashAI.back.models import (
    #SVC, # SVC removed from default_models above. Let's say it's an external plugin
    #KNeighborsClassifier,
    #RandomForestClassifier,
    NumericalWrapperForText,
    tcTransformerEngSpa,
)
from DashAI.back.registries import ModelRegistry, TaskRegistry

task_registry = TaskRegistry(
    tasks=[
        TabularClassificationTask,
        TextClassificationTask,
        TranslationTask,
    ],
)

model_registry = ModelRegistry(
    task_registry,
    models=[
        #SVC, # SVC removed from default_models above. Let's say it's an external plugin
        # KNeighborsClassifier,
        # RandomForestClassifier,
        NumericalWrapperForText,
        tcTransformerEngSpa,
    ],
)

def get_task_registry():
    return task_registry

def get_model_registry():
    return model_registry