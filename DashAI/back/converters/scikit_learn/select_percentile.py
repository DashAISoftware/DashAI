from sklearn.feature_selection import SelectPercentile as SelectPercentileOperation

from DashAI.back.converters.category.feature_selection import FeatureSelectionConverter
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import int_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.value_types import Float, Integer


class SelectPercentileSchema(BaseSchema):
    """Configuration schema for the SelectPercentile converter.

    Defines and validates the hyperparameters passed to
    ``sklearn.feature_selection.SelectPercentile``.
    """

    percentile: schema_field(
        int_field(ge=1, le=100),
        10,
        description=MultilingualString(
            en="Percent of features to keep.",
            es="Porcentaje de características a conservar.",
            pt="Percentual de características a manter.",
            de="Prozentsatz der beizubehaltenden Merkmale.",
            zh="要保留的特征百分比。",
        ),
    )  # type: ignore


class SelectPercentile(
    FeatureSelectionConverter, SklearnWrapper, SelectPercentileOperation
):
    """Select the top percentile of features by a univariate statistical test.

    SelectPercentile applies the same univariate scoring approach as
    ``SelectKBest`` but expresses the number of features to retain as a
    percentage of all available features rather than as an absolute count.
    Each feature is scored independently against the target using a chosen
    statistical function, and the top ``percentile`` percent are kept.

    This makes the selector robust to datasets with varying numbers of input
    features, since the number of retained features scales automatically with
    the input dimensionality. It is particularly convenient for grid search
    experiments where the feature set size may change across cross-validation
    folds or preprocessing stages.

    Key properties:

    - Supervised: requires the target array ``y`` at fit time.
    - ``percentile`` is an integer in [1, 100]; setting it to 100 passes all
      features through unchanged.
    - Uses the same family of scoring functions as ``SelectKBest``
      (``f_classif``, ``chi2``, ``mutual_info_classif``, etc.).
    - Feature ranking is univariate and does not capture interactions.

    Wraps scikit-learn's ``SelectPercentile``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.SelectPercentile.html
    """

    SCHEMA = SelectPercentileSchema
    DESCRIPTION = MultilingualString(
        en="Select features according to a percentile of the highest scores.",
        es=(
            "Selecciona características según un percentil de las puntuaciones "
            "más altas."
        ),
        pt=(
            "Seleciona características de acordo com um percentil das pontuações "
            "mais altas."
        ),
        de="Merkmale gemäß einem Perzentil der höchsten Bewertungen auswählen.",
        zh="根据最高得分的百分位数选择特征。",
    )
    SUPERVISED = True
    DISPLAY_NAME = MultilingualString(
        en="Select Percentile",
        es="Seleccionar Percentil",
        pt="Seleção por Percentil",
        de="Perzentil-Auswahl",
        zh="百分位数特征选择",
    )
    IMAGE_PREVIEW = "select_percentile.png"
    metadata = {"allowed_types": [Float, Integer], "allowed_dtypes": []}

    def __init__(self, **kwargs):
        """Initialize the SelectPercentile converter.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments matching the converter's
            schema fields. Forwarded to the underlying scikit-learn class.
        """
        super().__init__(**kwargs)
