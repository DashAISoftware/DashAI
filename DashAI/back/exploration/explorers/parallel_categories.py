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
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.multidimensional_explorer import MultidimensionalExplorer
from DashAI.back.types.categorical import Categorical

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ParallelCategoriesSchema(BaseExplorerSchema):
    """Schema for ParallelCategoriesExplorer hyperparameters.

    Configures the optional colour dimension used to differentiate flows in the
    parallel categories diagram. All other columns are selected via the base
    schema's column-selection mechanism.
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


class ParallelCategoriesExplorer(MultidimensionalExplorer):
    """Visualise categorical data flows across multiple dimensions simultaneously.

    A parallel categories diagram represents each row of the dataset as a ribbon
    flowing through a series of vertical axes, one per selected column. The width
    of each ribbon is proportional to the number of samples that share that
    combination of categories. An optional colour axis further segments the flows
    by a continuous or categorical variable, making patterns of cooccurrence and
    class distribution immediately visible.

    Best suited for exploring relationships between three or more categorical
    columns, such as demographic cross tabulations or multilabel feature analysis.
    """

    DISPLAY_NAME = MultilingualString(
        en="Parallel Categories Plot",
        es="Gráfico de Categorías Paralelas",
        pt="Categorias Paralelas",
        de="Parallele Kategoriendiagramm",
        zh="平行坐标类别图",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Visualizes high dimensional categorical data. Each vertical line is "
            "a category level and connections show combinations across columns."
        ),
        es=(
            "Visualiza datos categóricos de alta dimensión. Cada línea vertical "
            "es un nivel de categoría y las conexiones muestran combinaciones "
            "entre columnas."
        ),
        pt=(
            "Visualiza dados categóricos de alta dimensão. Cada linha vertical "
            "é um nível de categoria e as conexões mostram combinações "
            "entre colunas."
        ),
        de=(
            "Visualisiert hochdimensionale kategorische Daten. Jede vertikale "
            "Linie ist eine Kategorienstufe und Verbindungen zeigen Kombinationen "
            "über Spalten hinweg."
        ),
        zh=("可视化高维类别数据。每条垂直线是一个类别级别，连接线显示列间的组合关系。"),
    )
    IMAGE_PREVIEW = "parallel_categories.png"

    SCHEMA = ParallelCategoriesSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Categorical],
        "allowed_dtypes": [],
        "input_cardinality": {"min": 2},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the ParallelCategoriesExplorer with an optional color column.

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
        """Generate a Plotly parallel categories plot for the selected columns.

        Each line represents a flow between category values across multiple
        categorical axes, making it easy to visualize cooccurrence patterns
        in high dimensional categorical data.

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
            An interactive parallel categories figure.
        """
        import plotly.express as px

        _df = dataset.to_pandas()
        columns = [col["columnName"] for col in explorer_info.columns]

        fig = px.parallel_categories(
            _df,
            dimensions=columns,
            color=self.color_column,
            title=(f"Parallel Categories Plot of {len(columns)} columns"),
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
        """Save the parallel categories figure to a JSON file on disk.

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
        """Load and return the saved parallel categories plot for the frontend.

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
