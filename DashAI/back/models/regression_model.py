from DashAI.back.models.supervised_model import SupervisedModel


class RegressionModel(SupervisedModel):
    """Base class for models that perform regression tasks.

    Concrete regression models must extend this class and implement ``save``,
    ``load``, and ``train``. Compatible with ``RegressionTask``.
    """

    COMPATIBLE_COMPONENTS = ["RegressionTask"]
