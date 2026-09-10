from typing import Final

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.core.utils import MultilingualString
from DashAI.back.static.icons import Icon


class AdvancedPreprocessingConverter(BaseConverter):
    """Base class for converters that apply advanced preprocessing transformations.

    Advanced preprocessing converters handle complex feature transformations
    beyond basic scaling or encoding. Examples include CCA (Canonical Correlation
    Analysis), BagOfWords, and TF-IDF text vectorization.

    Use these converters when standard preprocessing is insufficient and the
    dataset requires more sophisticated feature engineering pipelines.
    """

    CATEGORY: Final[str] = MultilingualString(
        en="Advanced Preprocessing",
        es="Preprocesamiento Avanzado",
        pt="Pré-processamento Avançado",
        de="Erweiterte Vorverarbeitung",
        zh="高级预处理",
    )
    ICON: Final[str] = Icon.Psychology.value
    COLOR: Final[str] = "rgb(70, 130, 180)"
