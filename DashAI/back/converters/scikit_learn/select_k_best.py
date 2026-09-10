from sklearn.feature_selection import SelectKBest as SelectKBestOperation

from DashAI.back.converters.category.feature_selection import FeatureSelectionConverter
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import (
    enum_field,
    int_field,
    schema_field,
    union_type,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.value_types import Float, Integer


class SelectKBestSchema(BaseSchema):
    """Configuration schema for the SelectKBest converter.

    Defines and validates the hyperparameters passed to
    ``sklearn.feature_selection.SelectKBest``.
    """

    k: schema_field(
        union_type(enum_field(["all"]), int_field(ge=1)),
        10,
        description=MultilingualString(
            en="Number of top features to select.",
            es="Número de características superiores a seleccionar.",
            pt="Número de melhores características a selecionar.",
            de="Anzahl der besten auszuwählenden Merkmale.",
            zh="要选择的最高得分特征数量。",
        ),
    )  # type: ignore


class SelectKBest(FeatureSelectionConverter, SklearnWrapper, SelectKBestOperation):
    """Select the K highest-scoring features using a univariate statistical test.

    SelectKBest evaluates each input feature independently against the target
    variable using a scoring function (e.g. ``f_classif`` for ANOVA F-statistic,
    ``chi2`` for chi-squared, or ``mutual_info_classif`` for mutual information),
    then retains the ``k`` features with the highest scores, discarding the rest.

    This filter method is computationally cheap and can substantially reduce
    dimensionality before feeding data to a more expensive estimator. It is
    particularly useful as a first-pass feature selection step in classification
    and regression pipelines.

    Key properties:

    - Supervised: requires the target array ``y`` at fit time.
    - Setting ``k='all'`` is a no-op that passes every feature through;
      useful for pipeline grid searches where ``k`` is a tuned parameter.
    - Feature ranking is based solely on univariate statistics; it does not
      account for feature interactions.
    - The choice of scoring function should match the problem type
      (classification vs. regression) and the scale of the features.

    Wraps scikit-learn's ``SelectKBest``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.SelectKBest.html
    """

    SCHEMA = SelectKBestSchema
    DESCRIPTION = MultilingualString(
        en="Select features according to the k highest scores.",
        es="Selecciona características según las k puntuaciones más altas.",
        pt="Seleciona características de acordo com as k pontuações mais altas.",
        de="Merkmale gemäß den k höchsten Bewertungen auswählen.",
        zh="根据 k 个最高得分选择特征。",
    )
    SUPERVISED = True
    DISPLAY_NAME = MultilingualString(
        en="Select K Best",
        es="Seleccionar K Mejores",
        pt="Seleção K Melhores",
        de="K-Beste Auswahl",
        zh="K 最优特征选择",
    )
    IMAGE_PREVIEW = "select_k_best.png"
    metadata = {"allowed_types": [Float, Integer], "allowed_dtypes": []}

    def __init__(self, **kwargs):
        """Initialize the SelectKBest converter.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments matching the converter's
            schema fields. Forwarded to the underlying scikit-learn class.
        """
        super().__init__(**kwargs)
