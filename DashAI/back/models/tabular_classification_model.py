from DashAI.back.models.supervised_model import SupervisedModel


class TabularClassificationModel(SupervisedModel):
    """Base mixin for models that perform tabular classification tasks.

    Concrete tabular classification models should extend this class alongside
    a model implementation class. Compatible with ``TabularClassificationTask``.
    """

    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]
