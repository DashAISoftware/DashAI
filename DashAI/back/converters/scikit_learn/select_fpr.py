from sklearn.feature_selection import SelectFpr as SelectFprOperation

from DashAI.back.converters.category.feature_selection import FeatureSelectionConverter
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import float_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.value_types import Float, Integer


class SelectFprSchema(BaseSchema):
    """Configuration schema for the SelectFpr converter.

    Defines and validates the hyperparameters passed to
    ``sklearn.feature_selection.SelectFpr``.
    """

    alpha: schema_field(
        float_field(ge=0.0, le=1.0),
        0.05,
        description=MultilingualString(
            en="The highest p-value for features to be kept.",
            es="El p-valor más alto para conservar características.",
            pt="O p-valor mais alto para manter características.",
            de="Der höchste p-Wert für beizubehaltende Merkmale.",
            zh="保留特征的最高 p 值。",
        ),
    )  # type: ignore


class SelectFpr(FeatureSelectionConverter, SklearnWrapper, SelectFprOperation):
    """Select features whose p-value is below a False Positive Rate threshold.

    SelectFpr retains every feature whose p-value, computed by a univariate
    scoring function against the target, is strictly less than ``alpha``. Under
    the null hypothesis that a feature is independent of the target, the
    expected proportion of falsely retained features (false positives) is at
    most ``alpha``. No multiple-testing correction is applied; each feature is
    tested at the raw significance level.

    This selector is the most permissive of the three p-value-based filters
    (FPR, FDR, FWE). It is appropriate when the cost of missing a true feature
    outweighs the cost of including a small number of irrelevant ones, and when
    the number of features is moderate enough that the uncorrected type-I error
    rate is acceptable.

    Key properties:

    - Supervised: requires the target array ``y`` at fit time.
    - ``alpha`` is the significance threshold in [0, 1]; typical values are
      0.05 or 0.10.
    - No correction for multiple comparisons: more liberal than FDR and FWE.
    - The number of retained features is data-driven and not fixed in advance.

    Wraps scikit-learn's ``SelectFpr``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.SelectFpr.html
    """

    SCHEMA = SelectFprSchema
    DESCRIPTION = MultilingualString(
        en="Filter: Select features according to a false positive rate test.",
        es=(
            "Filtro: Selecciona características según una prueba de tasa de "
            "falsos positivos (FPR)."
        ),
        pt=(
            "Filtro: Seleciona características de acordo com um teste de taxa "
            "de falso positivo (FPR)."
        ),
        de="Filter: Merkmale gemäß einem Test der Falsch-Positiv-Rate (FPR) auswählen.",
        zh="过滤器：根据假阳性率（FPR）检验选择特征。",
    )
    SUPERVISED = True
    DISPLAY_NAME = MultilingualString(
        en="Select FPR",
        es="Seleccionar FPR",
        pt="Seleção por FPR",
        de="FPR-Auswahl",
        zh="FPR 特征选择",
    )
    IMAGE_PREVIEW = "select_fpr.png"
    metadata = {"allowed_types": [Float, Integer], "allowed_dtypes": []}

    def __init__(self, **kwargs):
        """Initialize the SelectFpr converter.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments matching the converter's
            schema fields. Forwarded to the underlying scikit-learn class.
        """
        super().__init__(**kwargs)
