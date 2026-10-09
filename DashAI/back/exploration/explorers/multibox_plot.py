from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.schema_fields import (
    bool_field,
    enum_field,
    int_field,
    none_type,
    schema_field,
    string_field,
    union_type,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import (
    NON_NUMERIC_DTYPES,
    BaseExplorerSchema,
)
from DashAI.back.exploration.multidimensional_explorer import MultidimensionalExplorer
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class MultiColumnBoxPlotSchema(BaseExplorerSchema):
    """Schema for MultiColumnBoxPlotExplorer configuration.

    Configures the layout and optional grouping axis for the multi-column box
    plot.  ``horizontal`` flips all boxes so that the value axis runs
    left to right, which is convenient when column names are long.  ``points``
    controls whether individual data points are overlaid on each box (``"all"``
    shows every point, ``"outliers"`` shows only outliers, and ``"False"``
    hides all points).  ``opposite_axis`` specifies a column whose distinct
    values are used as a shared grouping axis for all selected columns,
    producing grouped boxes within each column trace.
    """

    horizontal: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en=("If True, the box plot will be horizontal; otherwise vertical."),
            es=(
                "Si es True, el diagrama de caja será horizontal; en caso "
                "contrario, vertical."
            ),
            pt=(
                "Se True, o diagrama de caixa será horizontal; caso "
                "contrário, vertical."
            ),
            zh="如果为True，箱线图将水平显示；否则垂直显示。",
            de=(
                "Wenn True, wird das Boxplot horizontal dargestellt; "
                "andernfalls vertikal."
            ),
        ),
        alias=MultilingualString(
            en="Horizontal plot",
            es="Gráfico horizontal",
            pt="Gráfico horizontal",
            zh="水平图",
            de="Horizontales Diagramm",
        ),
    )  # type: ignore
    points: schema_field(
        enum_field(["all", "outliers", "False"]),
        "outliers",
        description=MultilingualString(
            en=(
                "One of 'all', 'outliers', or 'False'. Determines which points "
                "are shown."
            ),
            es=(
                "Una de 'all', 'outliers' o 'False'. Determina qué puntos se muestran."
            ),
            pt=(
                "Um de 'all', 'outliers' ou 'False'. Determina quais pontos "
                "são exibidos."
            ),
            zh="'all'、'outliers'或'False'之一。确定显示哪些数据点。",
            de=(
                "Eines von 'all', 'outliers' oder 'False'. Bestimmt, welche "
                "Punkte angezeigt werden."
            ),
        ),
        alias=MultilingualString(
            en="Points shown",
            es="Puntos mostrados",
            pt="Pontos exibidos",
            zh="显示的点",
            de="Angezeigte Punkte",
        ),
    )  # type: ignore
    opposite_axis: schema_field(
        none_type(union_type(string_field(), int_field(ge=0))),
        None,
        description=MultilingualString(
            en=("Column name or index to use for the opposite axis."),
            es=("Nombre o índice de columna para el eje opuesto."),
            pt=("Nome ou índice de coluna para usar no eixo oposto."),
            zh="用于对立轴的列名或索引。",
            de="Spaltenname oder Index für die gegenüberliegende Achse.",
        ),
        alias=MultilingualString(
            en="Opposite axis",
            es="Eje opuesto",
            pt="Eixo oposto",
            zh="对立轴",
            de="Gegenüberliegende Achse",
        ),
    )  # type: ignore


class MultiColumnBoxPlotExplorer(MultidimensionalExplorer):
    """Explorer that renders one box plot trace per selected column on a shared figure.

    While the single-column BoxPlotExplorer is suited to examining one variable
    at a time, this explorer places multiple box plot traces side by side in the
    same figure, making it straightforward to compare the distributional
    properties (median, spread, and outliers) of several numeric columns
    simultaneously.

    Each box trace summarises its column through the five-number summary (Q1,
    median, Q3, lower whisker, upper whisker) and optionally overlays individual
    data points.  When an ``opposite_axis`` column is provided, every trace is
    additionally split by the distinct categories of that column, producing
    grouped boxes that reveal how the distribution of each numeric column varies
    across groups.

    Use this explorer when you need a compact, side-by-side comparison of
    multiple numeric features, for example to detect scale differences between
    model input features or to contrast the spread of several metrics across
    experimental conditions.
    """

    DISPLAY_NAME = MultilingualString(
        en="Multiple Column Box Plot",
        es="Diagrama de Caja Multicolumna",
        pt="Diagrama de Caixa Múltiplo",
        zh="多列箱线图",
        de="Mehrspaltiges Boxplot",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Shows a box plot for multiple columns on one axis, using another "
            "column as the opposite axis (if provided)."
        ),
        es=(
            "Muestra un diagrama de caja para múltiples columnas en un eje, "
            "usando otra columna como eje opuesto (si se proporciona)."
        ),
        pt=(
            "Exibe um diagrama de caixa para múltiplas colunas em um eixo, "
            "usando outra coluna como eixo oposto (se fornecida)."
        ),
        zh="在一个轴上显示多列箱线图，使用另一列作为对立轴（如果提供）。",
        de=(
            "Zeigt ein Boxplot für mehrere Spalten auf einer Achse, "
            "optional mit einer weiteren Spalte als gegenüberliegende Achse."
        ),
    )
    IMAGE_PREVIEW = "multi_column_box_plot.png"

    SCHEMA = MultiColumnBoxPlotSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Float, Integer, Categorical],
        "allowed_dtypes": [],
        "non_allowed_dtypes": NON_NUMERIC_DTYPES,
        "input_cardinality": {"min": 1},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the MultiColumnBoxPlotExplorer with layout and grouping options.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments. Recognized keys:
            horizontal (bool, optional): If True, render horizontal box plots.
            Defaults to False.
            points (str, optional): Which data points to overlay on each box.
            One of ``"all"``, ``"outliers"``, or ``"False"`` (no points).
            Defaults to ``"outliers"``.
            opposite_axis (str or int, optional): Column name or zero-based
            index to use as the shared opposite axis across all boxes.
            Defaults to None.
        """
        self.horizontal = kwargs.get("horizontal", False)

        if kwargs.get("points") == "False":
            kwargs["points"] = False
        self.points = kwargs.get("points", "outliers")
        self.opposite_axis = kwargs.get("opposite_axis")

        super().__init__(**kwargs)

    def prepare_dataset(
        self, loaded_dataset: "DashAIDataset", columns: List[Dict[str, Any]]
    ) -> "DashAIDataset":
        """Extend the column list to include the opposite-axis column if specified.

        If ``opposite_axis`` was given as an integer index, it is resolved to the
        corresponding column name. The resolved column is appended to ``columns``
        when it is not already present, so that the base class loads it along with
        the selected columns.

        Parameters
        ----------
        loaded_dataset : DashAIDataset
            The full dataset being explored.
        columns : List[Dict[str, Any]]
            List of column descriptors already
            selected by the user.

        Returns
        -------
        DashAIDataset
            Dataset slice containing all required columns, as
            returned by the parent ``prepare_dataset`` implementation.
        """
        explorer_columns = [col["columnName"] for col in columns]
        dataset_columns = loaded_dataset.column_names

        if self.opposite_axis is not None and self.opposite_axis != "":
            if isinstance(self.opposite_axis, int):
                idx = self.opposite_axis
                col = dataset_columns[idx]
                if col not in explorer_columns:
                    columns.append({"id": idx, "columnName": col})
            else:
                col = self.opposite_axis
                if col not in explorer_columns:
                    columns.append({"columnName": col})
            self.opposite_axis = col
        else:
            self.opposite_axis = None

        return super().prepare_dataset(loaded_dataset, columns)

    def launch_exploration(self, dataset: "DashAIDataset", explorer_info: Explorer):
        """Generate a Plotly figure with a box plot trace for each selected column.

        All selected columns are rendered on a single shared axis. If an
        ``opposite_axis`` column was provided it is used as the grouping axis
        for every trace. Orientation is controlled by the ``horizontal`` parameter.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset containing the selected columns and,
            if configured, the opposite-axis column.
        explorer_info : Explorer
            Explorer record with column names and optional
            display name.

        Returns
        -------
        plotly.graph_objects.Figure
            An interactive multi-box plot figure with
            one box trace per selected column.
        """
        import plotly.graph_objects as go

        _df = dataset.to_pandas()
        cols = [col["columnName"] for col in explorer_info.columns]

        opposite_axis = (
            _df[self.opposite_axis] if self.opposite_axis is not None else None
        )

        fig = go.Figure()
        for col in cols:
            fig.add_trace(
                go.Box(
                    x=_df[col] if self.horizontal else opposite_axis,
                    y=opposite_axis if self.horizontal else _df[col],
                    name=col,
                    boxpoints=self.points,
                )
            )

        fig.update_layout(
            title=f"Boxplot of {len(cols)} columns",
            xaxis_title=None if self.horizontal else self.opposite_axis,
            yaxis_title=self.opposite_axis if self.horizontal else None,
            boxmode="group",
        )

        if explorer_info.name is not None and explorer_info.name != "":
            fig.update_layout(title=f"{explorer_info.name}")

        return fig

    def save_notebook(
        self,
        __notebook_info__: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Save the multi-column box plot figure to disk
        (JSON content, ``.pickle`` extension).

        Notes
        -----
        Despite the ``.pickle`` file extension, the file is written using
        ``write_json`` and contains JSON-serialized Plotly figure data.

        Parameters
        ----------
        __notebook_info__ : Notebook
            The notebook database record (unused).
        explorer_info : Explorer
            The explorer record used for filename generation.
        save_path : Path
            Directory where the file will be saved.
        result : Any
            The Plotly figure returned by `launch_exploration`.

        Returns
        -------
        str
            The path of the saved file as a POSIX string.
        """
        import os
        from pathlib import Path

        filename = f"{explorer_info.id}.pickle"
        path = Path(os.path.join(save_path, filename))

        result.write_json(path.as_posix())

        return path.as_posix()

    def get_results(
        self, exploration_path: str, options: Dict[str, Any]
    ) -> List[Artifact]:
        """Load and return the saved multi-column box plot for the frontend.

        Parameters
        ----------
        exploration_path : str
            Path to the JSON file saved by `save_notebook`.
        options : Dict[str, Any]
            Rendering options from the frontend (unused).

        Returns
        -------
        List[Artifact]
            A single-element list with the plotly artifact of the saved
            figure.
        """
        with open(exploration_path, "r", encoding="utf-8") as f:
            result = f.read()

        return [PlotlyArtifact(payload=result)]
