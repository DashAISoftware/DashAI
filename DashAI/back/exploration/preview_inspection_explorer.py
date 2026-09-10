from typing import Final

from DashAI.back.core.utils import MultilingualString
from DashAI.back.exploration.base_explorer import BaseExplorer
from DashAI.back.static.icons import Icon


class PreviewInspectionExplorer(BaseExplorer):
    """Base class for explorers that provide a direct preview of dataset contents.

    Preview inspection explorers surface raw dataset contents in a structured
    way, such as tabular row views or word clouds, allowing users to inspect
    data quality and content without running complex analyses.

    Subclass this and implement `launch_exploration`, `save_notebook`, and
    `get_results` to create a new preview inspection explorer.
    """

    CATEGORY: Final[str] = MultilingualString(
        en="Preview Inspection",
        es="Inspección Previa",
        pt="Inspeção Prévia",
        de="Vorschauinspektion",
        zh="预览与检查",
    )
    ICON: Final[str] = Icon.TableChart.value
    COLOR: Final[str] = "rgb(52, 152, 219)"
