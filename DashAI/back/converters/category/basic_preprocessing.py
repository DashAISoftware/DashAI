from typing import Final

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.core.utils import MultilingualString
from DashAI.back.static.icons import Icon


class BasicPreprocessingConverter(BaseConverter):
    """Base class for converters that apply fundamental preprocessing transformations.

    Basic preprocessing converters perform straightforward feature preparation
    steps commonly applied as the first stage of a pipeline. Examples include
    SimpleImputer, KNNImputer, and MissingIndicator.

    Use these converters to handle missing values and apply essential column
    transformations before more specialized preprocessing or model training.
    """

    CATEGORY = MultilingualString(
        en="Basic Preprocessing",
        es="Preprocesamiento Básico",
        pt="Pré-processamento Básico",
        de="Grundlegende Vorverarbeitung",
        zh="基础预处理",
    )
    ICON: Final[str] = Icon.Build.value
    COLOR: Final[str] = "rgb(60, 179, 113)"
