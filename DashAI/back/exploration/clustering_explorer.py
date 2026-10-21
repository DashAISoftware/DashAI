from typing import Final, Optional

from DashAI.back.core.utils import MultilingualString
from DashAI.back.exploration.base_explorer import BaseExplorer
from DashAI.back.static.icons import Icon


class ClusteringExplorer(BaseExplorer):
    """Base class for explorers that interpret clustering results.

    Clustering explorers operate on a dataset that has already been enriched
    with a cluster label column by a ``Clustering`` converter. They require the
    execution report produced by that converter (algorithm name, metrics,
    cluster profiles, and optional algorithm-specific artefacts such as cluster
    centres or linkage data) to generate visualisations and summaries that go
    beyond what the dataset alone can provide.

    All subclasses automatically inherit ``REQUIRES_CONVERTER_REPORT = True``
    and ``REQUIRES_CONVERTER_CLASS = "Clustering"``, so the job infrastructure
    will locate the most recent finished ``Clustering`` converter in the same
    notebook and pass its report through ``set_context`` before calling
    ``launch_exploration``.

    Subclass this and implement `launch_exploration`, `save_notebook`, and
    `get_results` to create a new clustering explorer.
    """

    CATEGORY: Final[str] = MultilingualString(
        en="Clustering Analysis",
        es="Análisis de Agrupamiento",
        pt="Análise de Agrupamento",
        de="Clustering-Analyse",
        zh="聚类分析",
    )
    ICON: Final[str] = Icon.ScatterPlot.value
    COLOR: Final[str] = "rgb(72, 149, 239)"
    REQUIRES_CONVERTER_REPORT: Final[bool] = True
    REQUIRES_CONVERTER_CLASS: Final[Optional[str]] = "Clustering"
