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

    def save_notebook(
        self,
        notebook_info: Any,
        explorer_info: Any,
        save_path: Any,
        result: Any,
    ) -> str:
        """Save the plotly figure of the exploration as JSON.

        Parameters
        ----------
        notebook_info : Notebook
            The notebook record (unused).
        explorer_info : Explorer
            The explorer record, whose id names the file.
        save_path : Path
            The directory to save into.
        result : plotly.graph_objects.Figure
            The figure from ``launch_exploration``.

        Returns
        -------
        str
            The saved file path as a POSIX string.
        """
        from pathlib import Path

        path = Path(save_path) / f"{explorer_info.id}.json"
        result.write_json(path.as_posix())
        return path.as_posix()

    def get_results(self, exploration_path: str, options: Dict[str, Any]) -> List[Any]:
        """Load the saved figure as a plotly artifact.

        Parameters
        ----------
        exploration_path : str
            The file written by ``save_notebook``.
        options : Dict[str, Any]
            Rendering options (unused).

        Returns
        -------
        List[Artifact]
            One plotly artifact.
        """
        from DashAI.back.core.artifacts import PlotlyArtifact

        with open(exploration_path, encoding="utf-8") as f:
            return [PlotlyArtifact(payload=f.read())]

    @staticmethod
    def text_column(dataset: Any, explorer_info: Any) -> List[str]:
        """Return the selected text values, with missing values as empty text.

        Parameters
        ----------
        dataset : DashAIDataset
            The prepared dataset.
        explorer_info : Explorer
            The explorer record naming the selected column.

        Returns
        -------
        List[str]
            The values of the first selected column.
        """
        name = explorer_info.columns[0]["columnName"]
        return [value or "" for value in dataset.arrow_table.column(name).to_pylist()]
