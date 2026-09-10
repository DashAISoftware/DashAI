from typing import Final

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.core.utils import MultilingualString
from DashAI.back.static.icons import Icon


class DimensionalityReductionConverter(BaseConverter):
    """Base class for converters that reduce the number of features in a dataset.

    Dimensionality reduction converters project the input feature space into a
    lower dimensional representation, reducing noise and computational cost.
    Examples include PCA, TruncatedSVD, FastICA, Nystroem approximation, and
    VarianceThreshold.

    Use these converters before training on high dimensional datasets to improve
    performance and reduce overfitting.
    """

    CATEGORY = MultilingualString(
        en="Dimensionality Reduction",
        es="Reducción de Dimensionalidad",
        pt="Redução de Dimensionalidade",
        de="Dimensionsreduktion",
        zh="降维",
    )
    ICON: Final[str] = Icon.Layers.value
    COLOR: Final[str] = "rgb(255, 99, 132)"
    N_COMPONENTS_FEATURES_BOUNDED: bool = True
