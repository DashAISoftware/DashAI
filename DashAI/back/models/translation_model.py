from DashAI.back.models.supervised_model import SupervisedModel


class TranslationModel(SupervisedModel):
    """Base class for models that perform text translation tasks.

    Concrete translation models must extend this class and implement ``save``,
    ``load``, and ``train``. Compatible with ``TranslationTask``.
    """

    COMPATIBLE_COMPONENTS = ["TranslationTask"]
