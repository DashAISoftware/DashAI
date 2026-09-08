from typing import Final

from DashAI.back.core.utils import MultilingualString
from DashAI.back.exploration.base_explorer import BaseExplorer
from DashAI.back.static.icons import Icon


class DataComplexityExplorer(BaseExplorer):
    """Base class for explorers that measure how hard a dataset is to learn.

    Complexity explorers describe the geometry of a supervised problem without
    training any model: how much the classes overlap, how large the boundary
    between them is, how tight each class is relative to its neighbours. They
    answer a question that comes before model evaluation, namely whether the
    data supports the task at all.

    Subclass this and implement `launch_exploration`, `save_notebook`, and
    `get_results` to create a new complexity explorer.
    """

    CATEGORY: Final[str] = MultilingualString(
        en="Data Complexity",
        es="Complejidad de los Datos",
        pt="Complexidade dos Dados",
        de="Datenkomplexität",
        zh="数据复杂度",
    )
    ICON: Final[str] = Icon.Layers.value
    COLOR: Final[str] = "rgb(230, 126, 34)"
