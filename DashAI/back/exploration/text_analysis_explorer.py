from typing import Any, Dict, Final, List

from DashAI.back.core.utils import MultilingualString
from DashAI.back.exploration.base_explorer import BaseExplorer
from DashAI.back.static.icons import Icon


class TextAnalysisExplorer(BaseExplorer):
    """Base class for explorers that analyse the text items of a document.

    On a document the explorer receives the selected items with their
    ``kind``, ``page`` and ``position`` columns, so results can be broken
    down by element kind and by page. On a dataset only the selected text
    column is available.
    """

    CATEGORY: Final[str] = MultilingualString(
        en="Text Analysis",
        es="Análisis de Texto",
        pt="Análise de Texto",
        de="Textanalyse",
        zh="文本分析",
    )
    ICON: Final[str] = Icon.TextSnippet.value
    COLOR: Final[str] = "rgb(230, 126, 34)"

    def prepare_dataset(
        self, loaded_dataset: Any, columns: List[Dict[str, Any]]
    ) -> Any:
        """Keep the selected column and the item columns a document provides.

        Parameters
        ----------
        loaded_dataset : DashAIDataset
            The loaded explorer input.
        columns : List[Dict[str, Any]]
            The selected columns.

        Returns
        -------
        DashAIDataset
            The selected columns, followed by ``kind``, ``page`` and
            ``position`` when the input has them.
        """
        from DashAI.back.dataloaders.classes.document_items import ITEM_COLUMNS

        names = list(dict.fromkeys(column["columnName"] for column in columns))
        names += [
            name
            for name in ITEM_COLUMNS
            if name in loaded_dataset.column_names and name not in names
        ]
        return loaded_dataset.select_columns(names)
