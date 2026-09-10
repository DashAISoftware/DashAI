from typing import Final

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.core.utils import MultilingualString
from DashAI.back.static.icons import Icon


class FeatureEngineeringConverter(BaseConverter):
    """Base class for converters that derive new features from existing columns.

    Feature engineering converters compute new columns out of one or more
    existing columns instead of modifying them in place. Examples include
    ColumnArithmetic (arithmetic combinations of two numeric columns),
    NumericExpansion (log1p, square, and square-root expansions of a numeric
    column), and ColumnConcat (string concatenation of two text/categorical
    columns).

    Use these converters to craft new signals for models when the raw
    columns alone are not expressive enough.
    """

    CATEGORY = MultilingualString(
        en="Feature Engineering",
        es="Ingeniería de Características",
        pt="Engenharia de Características",
        de="Feature-Engineering",
        zh="特征工程",
    )
    ICON: Final[str] = Icon.Functions.value
    COLOR: Final[str] = "rgb(0, 188, 212)"
