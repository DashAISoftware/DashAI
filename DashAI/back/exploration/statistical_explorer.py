from typing import Final

from DashAI.back.core.utils import MultilingualString
from DashAI.back.exploration.base_explorer import BaseExplorer
from DashAI.back.static.icons import Icon


class StatisticalExplorer(BaseExplorer):
    """Base class for explorers that compute statistical summaries of a dataset.

    Statistical explorers produce aggregate results such as descriptive
    statistics tables, correlation matrices, and covariance matrices that
    summarize numerical properties across one or more columns.

    Subclass this and implement `launch_exploration`, `save_notebook`, and
    `get_results` to create a new statistical explorer.
    """

    CATEGORY: Final[str] = MultilingualString(
        en="Statistical Analysis",
        es="Análisis Estadístico",
        pt="Análise Estatística",
        de="Statistische Analyse",
        zh="统计分析",
    )
    ICON: Final[str] = Icon.Functions.value
    COLOR: Final[str] = "rgb(231, 76, 60)"
