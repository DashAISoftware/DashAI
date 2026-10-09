from typing import TYPE_CHECKING, Any, Dict, List, Union

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.schema_fields import (
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


class ParallelCordinatesSchema(BaseExplorerSchema):
    """Schema for ParallelCordinatesExplorer hyperparameters.

    Configures the optional colour dimension used to colour-code lines in the
    parallel coordinates plot. All numeric columns to be displayed are selected
    via the base schema's column-selection mechanism.
    """

    color_column: schema_field(
        none_type(union_type(string_field(), int_field(ge=0))),
        None,
        description=MultilingualString(
            en=("Column used to color the data points."),
            es=("Columna usada para colorear los puntos."),
            pt=("Coluna usada para colorir os pontos de dados."),
            de=("Spalte zur Einfärbung der Datenpunkte."),
            zh="用于为数据点着色的列。",
        ),
        alias=MultilingualString(
            en="Color column",
            es="Columna de color",
            pt="Coluna de cor",
            de="Farbspalte",
            zh="颜色列",
        ),
    )  # type: ignore


class ParallelCordinatesExplorer(MultidimensionalExplorer):
    """Visualise multi-dimensional numeric data as a parallel coordinates plot.

    Each row in the dataset is drawn as a polyline that passes through a series
    of parallel vertical axes, one per selected numeric column. The position of
    each line segment on an axis encodes the value of the corresponding feature
    for that sample. Lines can be coloured by a separate column to reveal class
    separation or clustering structure across all dimensions simultaneously.

    Parallel coordinates are particularly effective for identifying correlated
    features, detecting outliers, and exploring high dimensional datasets where
    a scatter matrix would become too large to interpret.
    """

    DISPLAY_NAME = MultilingualString(
        en="Parallel Coordinates Plot",
        es="Gráfico de Coordenadas Paralelas",
        pt="Coordenadas Paralelas",
        de="Parallele Koordinatendiagramm",
        zh="平行坐标图",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Common way to visualize high dimensional numeric data. Each line is "
            "a data point crossing axes for each feature."
        ),
        es=(
            "Forma común de visualizar datos numéricos de alta dimensión. Cada "
            "línea es un dato que cruza ejes para cada característica."
        ),
        pt=(
            "Forma comum de visualizar dados numéricos de alta dimensão. Cada "
            "linha é um ponto de dados cruzando eixos para cada característica."
        ),
        de=(
            "Gängige Methode zur Visualisierung hochdimensionaler numerischer Daten. "
            "Jede Linie ist ein Datenpunkt, der die Achsen jedes Merkmals kreuzt."
        ),
        zh="可视化高维数值数据的常用方法。每条线是一个数据点，穿越每个特征的轴。",
    )
    IMAGE_PREVIEW = "parallel_cordinates.png"

    SCHEMA = ParallelCordinatesSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Float, Integer, Categorical],
        "allowed_dtypes": [],
        "non_allowed_dtypes": NON_NUMERIC_DTYPES,
        "input_cardinality": {"min": 2},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the ParallelCordinatesExplorer with an optional color column.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments. Recognized keys:
            color_column (str or int, optional): Column name or index used
            to color each line. Defaults to None.
        """
        self.color_column: Union[str, int, None] = kwargs.get("color_column")
        super().__init__(**kwargs)

    def prepare_dataset(
        self, loaded_dataset: "DashAIDataset", columns: List[Dict[str, Any]]
    ) -> "DashAIDataset":
        """Extend column selection to include the optional color column.

        Parameters
        ----------
        loaded_dataset : DashAIDataset
            The full dataset.
        columns : List[Dict[str, Any]]
            Explicitly selected column descriptors.

        Returns
        -------
        DashAIDataset
            Dataset containing the selected columns plus the
            optional color column.
        """
        explorer_columns = [col["columnName"] for col in columns]
        dataset_columns = loaded_dataset.column_names

        if self.color_column is not None:
            if isinstance(self.color_column, int):
                idx = self.color_column
                col = dataset_columns[idx]
                if col not in explorer_columns:
                    columns.append({"id": idx, "columnName": col})
            else:
                col = self.color_column
                if col not in explorer_columns:
                    columns.append({"columnName": col})
            self.color_column = col

        return super().prepare_dataset(loaded_dataset, columns)

    def launch_exploration(self, dataset: "DashAIDataset", explorer_info: Explorer):
        """Generate a Plotly parallel coordinates plot for the selected columns.

        Each line in the plot represents one data row, crossing a vertical axis
        for each selected feature. Useful for visualizing patterns across many
        numeric dimensions simultaneously.

        Parameters
        ----------
        dataset : DashAIDataset
            The prepared dataset with at least two columns.
        explorer_info : Explorer
            Explorer record with column names and optional
            display name.

        Returns
        -------
        plotly.graph_objects.Figure
            An interactive parallel coordinates figure.
        """
        import plotly.express as px

        _df = dataset.to_pandas()
        columns = [col["columnName"] for col in explorer_info.columns]

        fig = px.parallel_coordinates(
            _df,
            dimensions=columns,
            color=self.color_column,
            title=(f"Parallel Cordinates Plot of {len(columns)} columns"),
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
        """Save the parallel coordinates figure to a JSON file on disk.

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
        """Load and return the saved parallel coordinates plot for the frontend.

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
