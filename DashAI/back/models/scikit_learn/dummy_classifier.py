from sklearn.dummy import DummyClassifier as _DummyClassifier

from DashAI.back.core.schema_fields import BaseSchema, enum_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class DummyClassifierSchema(BaseSchema):
    """Schema that configures the Dummy Classifier.

    DummyClassifier is a baseline classification model that makes predictions by
    applying simple rules that completely ignore the input features. It is used to
    establish a trivial performance baseline for comparison with more complex
    classifiers. The underlying implementation is ``sklearn.dummy.DummyClassifier``.
    """

    strategy: schema_field(
        enum_field(enum=["most_frequent", "prior", "stratified", "uniform"]),
        placeholder="prior",
        description=MultilingualString(
            en="Strategy to use to generate predictions.",
            es="Estrategia a utilizar para generar predicciones.",
            pt="Estratégia a usar para gerar predições.",
            de="Strategie zur Generierung von Vorhersagen.",
            zh="用于生成预测的策略。",
        ),
        alias=MultilingualString(
            en="Strategy", es="Estrategia", pt="Estratégia", de="Strategie", zh="策略"
        ),
    )  # type: ignore


class DummyClassifier(
    TabularClassificationModel, SklearnLikeClassifier, _DummyClassifier
):
    """Baseline classifier that makes predictions ignoring the input features.

    DummyClassifier generates predictions using one of several simple strategies
    that do not use the input features at all: always predicting the most frequent
    class (``most_frequent``), sampling from the training class distribution
    (``stratified``), or predicting uniformly at random (``uniform``). It is used
    as a sanity-check baseline: any meaningful classifier should outperform it.

    The only configurable hyperparameter is ``strategy``. The implementation wraps
    scikit-learn's ``DummyClassifier``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyClassifier.html
    """

    SCHEMA = DummyClassifierSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Dummy Classifier",
        es="Clasificador Dummy",
        pt="Classificador Fictício",
        de="Dummy-Klassifikator",
        zh="基准分类器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Baseline classifier using simple rules for comparison.",
        es=("Clasificador base que utiliza reglas simples para comparación."),
        pt=("Classificador de referência que usa regras simples para comparação."),
        de=("Basis-Klassifikator, der einfache Regeln zum Vergleich verwendet."),
        zh="使用简单规则进行对比的基准分类器。",
    )
    COLOR: str = "#4DB6AC"
    ICON: str = "Science"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.  See
            the associated schema class for available keys and their defaults.
        """
        kwargs = self.validate_and_transform(kwargs)
        super().__init__(**kwargs)
