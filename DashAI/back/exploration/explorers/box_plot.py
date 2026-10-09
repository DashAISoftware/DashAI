from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.schema_fields import bool_field, enum_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.distribution_explorer import DistributionExplorer
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class BoxPlotSchema(BaseExplorerSchema):
    """Schema for BoxPlotExplorer configuration.

    Configures the orientation and point-visibility options of the box plot.
    The ``horizontal`` flag flips the plot axis so that the value axis runs
    left to right instead of bottom to top, which can be useful when column
    names are long.  The ``points`` option controls whether individual data
    points are drawn on top of each box, letting users inspect the raw
    distribution alongside the summary statistics.
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
                "Se True, o diagrama de caixa será horizontal; caso contrário, "
                "vertical."
            ),
            de=(
                "Wenn True, wird das Boxdiagramm horizontal dargestellt; sonst "
                "vertikal."
            ),
            zh="如果为True，箱线图将水平显示；否则垂直显示。",
        ),
        alias=MultilingualString(
            en="Horizontal plot",
            es="Gráfico horizontal",
            pt="Gráfico horizontal",
            de="Horizontales Diagramm",
            zh="水平图",
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
                "Uma de 'all', 'outliers' ou 'False'. Determina quais pontos "
                "são exibidos."
            ),
            de=(
                "Eines von 'all', 'outliers' oder 'False'. Bestimmt, welche "
                "Punkte angezeigt werden."
            ),
            zh="'all'、'outliers'或'False'之一。确定显示哪些数据点。",
        ),
        alias=MultilingualString(
            en="Points shown",
            es="Puntos mostrados",
            pt="Pontos exibidos",
            de="Angezeigte Punkte",
            zh="显示的点",
        ),
    )  # type: ignore


class BoxPlotExplorer(DistributionExplorer):
    """Explorer that produces an interactive box plot for one or two numeric columns.

    A box plot summarises a numeric distribution through five key statistics: the
    lower quartile (Q1), median (Q2), upper quartile (Q3), and the lower and upper
    whiskers that extend to the most extreme non-outlier values.  Points lying
    beyond the whiskers are drawn individually as outliers.

    When a single column is selected the explorer renders one box for the whole
    column.  When two columns are provided the second column is treated as a
    grouping variable, producing one box per distinct category, which makes it
    easy to compare how the distribution of the numeric column varies across groups.

    Use this explorer to quickly spot skewness, spread, and outliers in numeric
    data, or to compare distributions across categorical groups (e.g. comparing
    a target variable across different classes).
    """

    DISPLAY_NAME = MultilingualString(
        en="Box Plot",
        es="Diagrama de Caja",
        pt="Diagrama de Caixa",
        de="Boxdiagramm",
        zh="箱线图",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Returns a box plot of selected columns in the dataset to visualize "
            "distribution and outliers."
        ),
        es=(
            "Devuelve un diagrama de caja de columnas seleccionadas del dataset "
            "para visualizar distribución y valores atípicos."
        ),
        pt=(
            "Retorna um diagrama de caixa das colunas selecionadas no conjunto "
            "de dados para visualizar a distribuição e os valores atípicos."
        ),
        de=(
            "Gibt ein Boxdiagramm der ausgewählten Spalten im Datensatz zurück, "
            "um Verteilung und Ausreißer zu visualisieren."
        ),
        zh="返回数据集中所选列的箱线图，以可视化分布和异常值。",
    )
    IMAGE_PREVIEW = "box_plot.png"

    SCHEMA = BoxPlotSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Float, Integer],
        "allowed_dtypes": [],
        "input_cardinality": {"min": 1, "max": 2},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the BoxPlotExplorer with orientation and point visibility options.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments. Recognized keys:
            horizontal (bool, optional): If True, render a horizontal box
            plot. Defaults to False.
            points (str, optional): Which data points to overlay on the
            box. One of ``"all"``, ``"outliers"``, or ``"False"``
            (no points). Defaults to ``"outliers"``.
        """
        self.horizontal = kwargs.get("horizontal", False)

        if kwargs.get("points") == "False":
            kwargs["points"] = False
        self.points = kwargs.get("points", "outliers")

        super().__init__(**kwargs)

    def launch_exploration(self, dataset: "DashAIDataset", explorer_info: Explorer):
        """Generate a Plotly box plot for one or two selected numeric columns.

        With one column, displays a single box. With two columns, the second
        column is used as a grouping axis. Orientation is controlled by the
        ``horizontal`` parameter.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset containing the selected numeric columns.
        explorer_info : Explorer
            Explorer record with column names and optional
            display name.

        Returns
        -------
        plotly.graph_objects.Figure
            An interactive box plot figure.

        Raises
        ------
        ValueError
            If more than two columns are selected.
        """
        import plotly.express as px

        _df = dataset.to_pandas()
        cols = [col["columnName"] for col in explorer_info.columns]

        if len(cols) == 1:
            fig = px.box(
                _df,
                x=cols[0] if self.horizontal else None,
                y=None if self.horizontal else cols[0],
                title=f"Boxplot of {cols[0]}",
                points=self.points,
            )
        elif len(cols) == 2:
            fig = px.box(
                _df,
                x=cols[1] if self.horizontal else cols[0],
                y=cols[0] if self.horizontal else cols[1],
                title=f"Boxplot of {cols[0]} vs {cols[1]}",
                points=self.points,
            )
        else:
            raise ValueError("BoxPlotExplorer can only handle 1 or 2 columns")

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
        """Save the box plot figure to a JSON file on disk.

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
            The path of the saved JSON file as a POSIX string.
        """
        import os
        from pathlib import Path

        filename = f"{explorer_info.id}.json"
        path = Path(os.path.join(save_path, filename))

        result.write_json(path.as_posix())
        return path.as_posix()

    def get_results(
        self, exploration_path: str, options: Dict[str, Any]
    ) -> List[Artifact]:
        """Load and return the saved box plot for the frontend.

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
