from sklearn.feature_selection import (
    GenericUnivariateSelect as GenericUnivariateSelectOperation,
)

from DashAI.back.converters.category.feature_selection import FeatureSelectionConverter
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import (
    enum_field,
    float_field,
    int_field,
    none_type,
    schema_field,
    union_type,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.value_types import Float, Integer


class GenericUnivariateSelectSchema(BaseSchema):
    """Schema for Generic Univariate Select hyperparameters."""

    mode: schema_field(
        enum_field(["percentile", "k_best", "fpr", "fdr", "fwe"]),
        "percentile",
        description=MultilingualString(
            en="Select features according to a percentile of the highest scores.",
            es=(
                "Selecciona características según un percentil de las "
                "puntuaciones más altas."
            ),
            pt=(
                "Seleciona características de acordo com um percentil das "
                "pontuações mais altas."
            ),
            de="Merkmale gemäß einem Perzentil der höchsten Bewertungen auswählen.",
            zh="根据最高得分的百分位数选择特征。",
        ),
    )  # type: ignore
    param: schema_field(
        none_type(
            union_type(enum_field(["all"]), union_type(float_field(), int_field()))
        ),
        1e-5,
        description=MultilingualString(
            en="Parameter of the mode.",
            es="Parámetro del modo.",
            pt="Parâmetro do modo.",
            de="Parameter des Modus.",
            zh="模式的参数。",
        ),
    )  # type: ignore


class GenericUnivariateSelect(
    FeatureSelectionConverter, SklearnWrapper, GenericUnivariateSelectOperation
):
    """Select features using a configurable univariate statistical test and mode.

    Supports multiple selection modes: ``k_best``, ``percentile``, ``fpr``,
    ``fdr``, and ``fwe``. The scoring function and mode are configurable.
    Supervised: requires ``y`` at fit time.

    Wraps scikit-learn's ``GenericUnivariateSelect``.
    """

    SCHEMA = GenericUnivariateSelectSchema
    DESCRIPTION = MultilingualString(
        en="Univariate feature selector with configurable strategy.",
        es="Selector univariante de características con estrategia configurable.",
        pt="Seletor univariado de características com estratégia configurável.",
        de="Univariater Merkmalsselektor mit konfigurierbarer Strategie.",
        zh="具有可配置策略的单变量特征选择器。",
    )
    SUPERVISED = True
    DISPLAY_NAME = MultilingualString(
        en="Generic Univariate Select",
        es="Selección Univariante Genérica",
        pt="Seletor Univariado Genérico",
        de="Generische Univariate Auswahl",
        zh="通用单变量特征选择",
    )
    IMAGE_PREVIEW = "generic_univariate_select.png"
    metadata = {"allowed_types": [Float, Integer], "allowed_dtypes": []}
