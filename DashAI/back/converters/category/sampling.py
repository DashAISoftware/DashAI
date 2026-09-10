from typing import Final

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.core.utils import MultilingualString
from DashAI.back.static.icons import Icon


class SamplingConverter(BaseConverter):
    """Base class for converters that resample dataset rows to address class imbalance.

    Sampling converters add or remove rows from the dataset, unlike most other
    converters which only transform column values. Examples include
    RandomUnderSampler, SMOTE, and SMOTEENN.

    Use these converters when training on imbalanced classification datasets
    where minority classes are underrepresented.
    """

    CATEGORY = MultilingualString(
        en="Resampling & Class Balancing",
        es="Remuestreo y Balanceo de Clases",
        pt="Reamostragem e Balanceamento de Classes",
        de="Resampling und Klassenausgleich",
        zh="重采样与类别平衡",
    )
    ICON: Final[str] = Icon.Casino.value
    COLOR: Final[str] = "rgb(255, 159, 64)"
