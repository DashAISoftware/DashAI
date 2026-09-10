from typing import Final

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.core.utils import MultilingualString
from DashAI.back.static.icons import Icon


class ScalingAndNormalizationConverter(BaseConverter):
    """Base class for converters that scale or normalize feature values.

    Scaling converters adjust the range or distribution of numeric features.
    Examples include StandardScaler (zero mean, unit variance), MinMaxScaler
    (range [0,1]), MaxAbsScaler (range [-1,1]), and Normalizer (unit norm rows).

    Use these converters when training models that are sensitive to feature
    magnitude, such as SVMs, logistic regression, or neural networks.
    """

    CATEGORY = MultilingualString(
        en="Scaling and Normalization",
        es="Escalado y Normalización",
        pt="Escalonamento e Normalização",
        de="Skalierung und Normalisierung",
        zh="缩放与归一化",
    )
    ICON: Final[str] = Icon.TrendingUp.value
    COLOR: Final[str] = "rgb(255, 165, 0)"
