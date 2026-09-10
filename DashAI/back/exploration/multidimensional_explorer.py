from typing import Final

from DashAI.back.core.utils import MultilingualString
from DashAI.back.exploration.base_explorer import BaseExplorer
from DashAI.back.static.icons import Icon


class MultidimensionalExplorer(BaseExplorer):
    """Base class for explorers that visualize data
    across many dimensions simultaneously.

    Multidimensional explorers generate visualizations such as parallel
    categories plots that allow comparison of multiple categorical variables
    at once, useful for understanding how categories interact across dimensions.

    Subclass this and implement `launch_exploration`, `save_notebook`, and
    `get_results` to create a new multidimensional explorer.
    """

    CATEGORY: Final[str] = MultilingualString(
        en="Multidimensional Analysis",
        es="Análisis Multidimensional",
        pt="Análise Multidimensional",
        de="Multidimensionale Analyse",
        zh="多维分析",
    )
    ICON: Final[str] = Icon.Timeline.value
    COLOR: Final[str] = "rgb(241, 196, 15)"
