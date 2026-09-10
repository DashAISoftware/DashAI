from typing import Final

from DashAI.back.core.utils import MultilingualString
from DashAI.back.exploration.base_explorer import BaseExplorer
from DashAI.back.static.icons import Icon


class RelationshipExplorer(BaseExplorer):
    """Base class for explorers that analyze relationships between dataset columns.

    Relationship explorers generate visualizations such as scatter plots,
    scatter matrices, and parallel coordinates that reveal correlations,
    clusters, or trends between two or more numeric or categorical columns.

    Subclass this and implement `launch_exploration`, `save_notebook`, and
    `get_results` to create a new relationship explorer.
    """

    CATEGORY: Final[str] = MultilingualString(
        en="Relationship Analysis",
        es="Análisis de Relaciones",
        pt="Análise de Relações",
        de="Beziehungsanalyse",
        zh="关系分析",
    )
    ICON: Final[str] = Icon.ScatterPlot.value
    COLOR: Final[str] = "rgb(46, 204, 113)"
