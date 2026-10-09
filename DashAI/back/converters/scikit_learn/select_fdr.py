from sklearn.feature_selection import SelectFdr as SelectFdrOperation

from DashAI.back.converters.category.feature_selection import FeatureSelectionConverter
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import float_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.value_types import Float, Integer


class SelectFdrSchema(BaseSchema):
    """Configuration schema for the SelectFdr converter.

    Defines and validates the hyperparameters passed to
    ``sklearn.feature_selection.SelectFdr``.
    """

    alpha: schema_field(
        float_field(ge=0.0, le=1.0),
        0.05,
        description=MultilingualString(
            en="The highest uncorrected p-value for features to be kept.",
            es=(
                "El p-valor sin corregir más alto para que una característica "
                "sea conservada."
            ),
            pt=(
                "O p-valor não corrigido mais alto para que uma característica "
                "seja mantida."
            ),
            de="Der höchste unkorrigierte p-Wert für beizubehaltende Merkmale.",
            zh="保留特征的最高未校正 p 值。",
        ),
    )  # type: ignore


class SelectFdr(FeatureSelectionConverter, SklearnWrapper, SelectFdrOperation):
    """Select features by controlling the expected False Discovery Rate (FDR).

    SelectFdr applies the Benjamini-Hochberg procedure to the p-values produced
    by a univariate scoring function, retaining only those features whose
    (adjusted) p-value is at most ``alpha``. The FDR criterion bounds the
    expected proportion of selected features that are actually uninformative,
    offering a less conservative rejection policy than Family-Wise Error control
    while still providing statistical guarantees.

    This filter is well suited to high dimensional settings (e.g. genomics,
    metabolomics) where many features are tested simultaneously and a small
    fraction of false positives among the selected set is acceptable in
    exchange for higher sensitivity.

    Key properties:

    - Supervised: requires the target array ``y`` at fit time.
    - ``alpha`` is the target FDR level in [0, 1]; typical values are 0.05
      or 0.10.
    - Less conservative than FWE (Bonferroni) correction: retains more features
      at the same nominal ``alpha`` when the number of tests is large.
    - The number of retained features is data-driven and not fixed in advance.

    Wraps scikit-learn's ``SelectFdr``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.SelectFdr.html
    """

    SCHEMA = SelectFdrSchema
    DESCRIPTION = MultilingualString(
        en="Filter: Select features according to a false discovery rate test.",
        es=(
            "Filtro: Selecciona características según una prueba de tasa de "
            "falsos descubrimientos (FDR)."
        ),
        pt=(
            "Filtro: Seleciona características de acordo com um teste de taxa "
            "de falsa descoberta (FDR)."
        ),
        de=(
            "Filter: Merkmale gemäß einem Test der Falschentdeckungsrate (FDR) "
            "auswählen."
        ),
        zh="过滤器：根据错误发现率（FDR）检验选择特征。",
    )
    SUPERVISED = True
    DISPLAY_NAME = MultilingualString(
        en="Select FDR",
        es="Seleccionar FDR",
        pt="Seleção por FDR",
        de="FDR-Auswahl",
        zh="FDR 特征选择",
    )
    IMAGE_PREVIEW = "select_fdr.png"
    metadata = {"allowed_types": [Float, Integer], "allowed_dtypes": []}

    def __init__(self, **kwargs):
        """Initialize the SelectFdr converter.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments matching the converter's
            schema fields. Forwarded to the underlying scikit-learn class.
        """
        super().__init__(**kwargs)
