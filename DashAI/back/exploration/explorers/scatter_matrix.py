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


class ScatterMatrixSchema(BaseExplorerSchema):
    """Schema for ScatterMatrixExplorer hyperparameters.

    Configures the optional colour-group and symbol-group columns used to
    differentiate sample clusters in the pairwise scatter matrix. All numeric
    columns to display on the axes are selected via the base schema.
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


class ScatterMatrixExplorer(RelationshipExplorer):
    """Display pairwise scatter plots for all selected numeric columns.

    Generates a grid of scatter plots (also known as a SPLOM, short for Scatter
    PLOt Matrix) where each cell shows the relationship between one pair of numeric
    columns. The diagonal cells can optionally show the distribution of a single
    variable. Colour and symbol encodings can be mapped to a grouping column to
    reveal class separation or cluster structure across all feature pairs at once.

    This explorer is the standard first step for discovering linear and nonlinear
    pairwise correlations in tabular datasets before applying feature selection or
    dimensionality reduction.
    """

    DISPLAY_NAME = MultilingualString(
        en="Multiple Scatter Plot",
        es="Matriz de Dispersión",
        pt="Matriz de Dispersão",
        de="Streudiagramm-Matrix",
        zh="散点矩阵",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Returns a scatter matrix for selected columns. Multiple scatter plots "
            "are generated for each pair, with histograms on the diagonal."
        ),
        es=(
            "Devuelve una matriz de dispersión para columnas seleccionadas. Se "
            "generan gráficos de dispersión por cada par, con histogramas en la "
            "diagonal."
        ),
        pt=(
            "Retorna uma matriz de dispersão para colunas selecionadas. São "
            "gerados gráficos de dispersão para cada par, com histogramas na "
            "diagonal."
        ),
        de=(
            "Gibt eine Streudiagramm-Matrix für ausgewählte Spalten zurück. Für "
            "jedes Paar werden Streudiagramme erzeugt, mit Histogrammen auf der "
            "Diagonale."
        ),
        zh=("返回所选列的散点矩阵。为每对列生成散点图，对角线为直方图。"),
    )
    IMAGE_PREVIEW = "scatter_matrix.png"

    SHORT_DESCRIPTION = MultilingualString(
        en="Display a scatter matrix plot of selected columns.",
        es="Muestra una matriz de dispersión de columnas seleccionadas.",
        pt="Exibe uma matriz de dispersão das colunas selecionadas.",
        de="Zeigt eine Streudiagramm-Matrix der ausgewählten Spalten an.",
        zh="显示所选列的散点矩阵图。",
    )

    SCHEMA = ScatterMatrixSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Float, Integer, Categorical],
        "allowed_dtypes": [],
        "non_allowed_dtypes": NON_NUMERIC_DTYPES,
        "input_cardinality": {"min": 2},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the ScatterMatrixExplorer with optional grouping columns.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments. Recognized keys:
            color_group (str or int, optional): Column name or index to
            color-code data points. Defaults to None.
            simbol_group (str or int, optional): Column name or index to
            assign point symbols. Defaults to None.
        """
        self.color_column = kwargs.get("color_group")
        self.simbol_column = kwargs.get("simbol_group")
        super().__init__(**kwargs)

    def prepare_dataset(
        self, loaded_dataset: "DashAIDataset", columns: List[Dict[str, Any]]
    ) -> "DashAIDataset":
        """Extend column selection to include optional color
        and symbol grouping columns.

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

        return super().prepare_dataset(loaded_dataset, columns)

    def launch_exploration(self, dataset: "DashAIDataset", explorer_info: Explorer):
        """Generate a Plotly scatter matrix for N selected columns.

        Produces pairwise scatter plots for all selected columns, with
        histograms on the diagonal.

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
            An interactive scatter matrix figure.
        """
        import plotly.express as px

        _df = dataset.to_pandas()
        dimensions = [col["columnName"] for col in explorer_info.columns]

        colorColumn = self.color_column if self.color_column in _df.columns else None
        simbolColumn = self.simbol_column if self.simbol_column in _df.columns else None

        fig = px.scatter_matrix(
            _df,
            dimensions=dimensions,
            color=colorColumn,
            symbol=simbolColumn,
            title=f"Scatter Matrix of {len(dimensions)} columns",
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
        """Save the scatter matrix figure to a JSON file on disk.

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
        """Load and return the saved scatter matrix for the frontend.

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
