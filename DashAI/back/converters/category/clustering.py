from typing import Final

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.core.utils import MultilingualString
from DashAI.back.static.icons import Icon


class ClusteringConverter(BaseConverter):
    """Base class for converters that assign clusters to dataset rows.

    Clustering converters learn an unsupervised grouping from the selected
    feature columns and typically enrich the dataset with a new categorical
    column containing the cluster label assigned to each row.

    Use these converters when you want to discover natural groupings in the
    data or create new features based on similarity, without relying on any target
    variable.
    """

    CATEGORY = MultilingualString(
        en="Clustering",
        es="Agrupamiento",
        pt="Agrupamento",
        de="Clustering",
        zh="聚类",
    )
    ICON: Final[str] = Icon.Psychology.value
    COLOR: Final[str] = "rgb(72, 149, 239)"
    COLUMN_OPERATION = "add"
