from typing import TYPE_CHECKING, Any, Dict, List

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
from DashAI.back.exploration.relationship_explorer import RelationshipExplorer
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ScatterPlotSchema(BaseExplorerSchema):
    """Schema for ScatterPlotExplorer hyperparameters.

    Configures the two axis columns plus optional visual channels: ``color_group``
    for categorical colour encoding, ``simbol_group`` for marker-shape encoding,
    and ``point_size`` for size-encoding by a third numeric variable.
    """

    color_group: schema_field(
        none_type(union_type(string_field(), int_field(ge=0))),
        None,
        description=MultilingualString(
            en=("Column name or index used to group colored points."),
            es=("Nombre o índice de columna para agrupar puntos por color."),
            pt=("Nome ou índice de coluna para agrupar pontos por cor."),
            de=("Spaltenname oder -index zur Farbgruppierung der Punkte."),
            zh="用于按颜色分组数据点的列名或索引。",
        ),
        alias=MultilingualString(
            en="Color group column",
            es="Columna para grupo de color",
            pt="Coluna para grupo de cor",
            de="Farbgruppen-Spalte",
            zh="颜色分组列",
        ),
    )  # type: ignore
    simbol_group: schema_field(
        none_type(union_type(string_field(), int_field(ge=0))),
        None,
        description=MultilingualString(
            en=("Column name or index used to group point symbols."),
            es=("Nombre o índice de columna para agrupar símbolos de puntos."),
            pt=("Nome ou índice de coluna para agrupar símbolos de pontos."),
            de=("Spaltenname oder -index zur Symbolgruppierung der Punkte."),
            zh="用于按符号分组数据点的列名或索引。",
        ),
        alias=MultilingualString(
            en="Symbol group column",
            es="Columna para grupo de símbolo",
            pt="Coluna para grupo de símbolo",
            de="Symbolgruppen-Spalte",
            zh="符号分组列",
        ),
    )  # type: ignore
    point_size: schema_field(
        none_type(union_type(string_field(), int_field(ge=0))),
        None,
        description=MultilingualString(
            en=("Column name or index to set the size of each point."),
            es=("Nombre o índice de columna para definir el tamaño de cada punto."),
            pt=("Nome ou índice de coluna para definir o tamanho de cada ponto."),
            de=("Spaltenname oder -index zur Festlegung der Punktgröße."),
            zh="用于设置每个数据点大小的列名或索引。",
        ),
        alias=MultilingualString(
            en="Point size column",
            es="Columna tamaño punto",
            pt="Coluna tamanho ponto",
            de="Punktgröße-Spalte",
            zh="点大小列",
        ),
    )  # type: ignore


class ScatterPlotExplorer(RelationshipExplorer):
    """Display a two-dimensional scatter plot to explore relationships between columns.

    Renders each dataset row as a point in a 2-D plane defined by two selected
    numeric columns. Additional visual channels (colour, marker symbol, point size)
    can be mapped to further columns to reveal clustering, class separation, or a
    third quantitative dimension without requiring a higher-dimensional plot.

    A scatter plot is the primary tool for detecting linear and nonlinear
    correlations between two variables and for spotting outliers, heteroscedasticity,
    or discrete groupings in the joint distribution.
    """

    DISPLAY_NAME = MultilingualString(
        en="Scatter Plot",
        es="Gráfico de Dispersión",
        pt="Gráfico de Dispersão",
        de="Streudiagramm",
        zh="散点图",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Displays a scatter plot for two selected columns to explore their "
            "relationship."
        ),
        es=(
            "Muestra un gráfico de dispersión para dos columnas seleccionadas "
            "a fin de explorar su relación."
        ),
        pt=(
            "Exibe um gráfico de dispersão para duas colunas selecionadas "
            "para explorar sua relação."
        ),
        de=(
            "Zeigt ein Streudiagramm für zwei ausgewählte Spalten zur Erkundung "
            "ihrer Beziehung an."
        ),
        zh="显示两个所选列的散点图，以探索它们之间的关系。",
    )
    IMAGE_PREVIEW = "scatter_plot.png"

    SCHEMA = ScatterPlotSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Float, Integer, Categorical],
        "allowed_dtypes": [],
        "non_allowed_dtypes": NON_NUMERIC_DTYPES,
        "input_cardinality": {"exact": 2},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the ScatterPlotExplorer with optional grouping columns.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments. Recognized keys:
            color_group (str or int, optional): Column name or index to
            color-code data points. Defaults to None.
            simbol_group (str or int, optional): Column name or index to
            assign point symbols. Defaults to None.
            point_size (str or int, optional): Column name or index to
            set the size of each point. Defaults to None.
        """
        self.color_column = kwargs.get("color_group")
        self.simbol_column = kwargs.get("simbol_group")
        self.size_column = kwargs.get("point_size")
        super().__init__(**kwargs)

    def prepare_dataset(
        self, loaded_dataset: "DashAIDataset", columns: List[Dict[str, Any]]
    ) -> "DashAIDataset":
        """Extend column selection to include optional grouping columns.

        Appends color, symbol, and size columns to the selection list if they
        are configured and not already present.

        Parameters
        ----------
        loaded_dataset : DashAIDataset
            The full dataset.
        columns : List[Dict[str, Any]]
            Explicitly selected column descriptors.

        Returns
        -------
        DashAIDataset
            Dataset containing the selected columns plus any
            optional grouping columns.
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

        if self.simbol_column is not None:
            if isinstance(self.simbol_column, int):
                idx = self.simbol_column
                col = dataset_columns[idx]
                if col not in explorer_columns:
                    columns.append({"id": idx, "columnName": col})
            else:
                col = self.simbol_column
                if col not in explorer_columns:
                    columns.append({"columnName": col})
            self.simbol_column = col

        if self.size_column is not None:
            if isinstance(self.size_column, (int, float)):
                idx = self.size_column
                col = dataset_columns[idx]
                if col not in explorer_columns:
                    columns.append({"id": idx, "columnName": col})
            else:
                col = self.size_column
                if col not in explorer_columns:
                    columns.append({"columnName": col})
            self.size_column = col

        return super().prepare_dataset(loaded_dataset, columns)

    def launch_exploration(self, dataset: "DashAIDataset", explorer_info: Explorer):
        """Generate a Plotly scatter plot for two selected columns.

        Parameters
        ----------
        dataset : DashAIDataset
            The prepared dataset with the required columns.
        explorer_info : Explorer
            Explorer record with column names and optional
            display name.

        Returns
        -------
        plotly.graph_objects.Figure
            An interactive scatter plot figure.
        """
        import plotly.express as px

        _df = dataset.to_pandas()
        cols = [col["columnName"] for col in explorer_info.columns]

        colorColumn = self.color_column if self.color_column in _df.columns else None
        simbolColumn = self.simbol_column if self.simbol_column in _df.columns else None
        sizeColumn = self.size_column if self.size_column in _df.columns else None

        fig = px.scatter(
            _df,
            x=cols[0],
            y=cols[1],
            color=colorColumn,
            symbol=simbolColumn,
            size=sizeColumn,
            title=f"Scatter Plot of {cols[0]} vs {cols[1]}",
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
        """Save the scatter plot figure to disk (JSON content, ``.pickle`` extension).

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
        """Load and return the saved scatter plot for the frontend.

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
