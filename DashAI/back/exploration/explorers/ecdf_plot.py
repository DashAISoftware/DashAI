from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Union

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.schema_fields import (
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
from DashAI.back.exploration.distribution_explorer import DistributionExplorer
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ECDFNorm(Enum):
    NONE = "none"
    PERCENT = "percent"
    PROBABILITY = "probability"


class ECDFPlotSchema(BaseExplorerSchema):
    """Schema for ECDFPlotExplorer configuration.

    Controls grouping, faceting, and the normalisation of the y-axis.
    ``color_column`` splits the ECDF into separate colour-coded traces for each
    distinct value of the chosen column, making it easy to compare distributions
    across groups on the same axes.  ``facet_col`` and ``facet_row`` create a
    grid of subplots, one per category, for column wise and row wise faceting
    respectively.

    ``ecdf_norm`` sets how the y-axis is scaled: ``"probability"`` maps the
    y-axis to [0, 1] and is the most common choice for comparing shapes across
    groups; ``"percent"`` scales it to [0, 100]; ``"none"`` shows the raw
    cumulative count.
    """

    color_column: schema_field(
        none_type(union_type(string_field(), int_field(ge=0))),
        None,
        description=MultilingualString(
            en=("Column used to color the ECDF plot."),
            es=("Columna usada para colorear el gráfico ECDF."),
            pt=("Coluna usada para colorir o gráfico ECDF."),
            de=("Spalte zur Einfärbung des ECDF-Diagramms."),
            zh="用于为ECDF图着色的列。",
        ),
        alias=MultilingualString(
            en="Color column",
            es="Columna de color",
            pt="Coluna de cor",
            de="Farbspalte",
            zh="颜色列",
        ),
    )  # type: ignore
    facet_col: schema_field(
        none_type(union_type(string_field(), int_field(ge=0))),
        None,
        description=MultilingualString(
            en=("Column used to facet the ECDF plot by columns."),
            es=("Columna usada para facetar el gráfico ECDF por columnas."),
            pt=("Coluna usada para facetar o gráfico ECDF por colunas."),
            de=("Spalte zur spaltenseitigen Facettierung des ECDF-Diagramms."),
            zh="用于按列对ECDF图进行分面的列。",
        ),
        alias=MultilingualString(
            en="Facet column",
            es="Facetear por columnas",
            pt="Facetar por colunas",
            de="Facettenspalte",
            zh="分面列",
        ),
    )  # type: ignore
    facet_row: schema_field(
        none_type(union_type(string_field(), int_field(ge=0))),
        None,
        description=MultilingualString(
            en=("Column used to facet the ECDF plot by rows."),
            es=("Columna usada para facetar el gráfico ECDF por filas."),
            pt=("Coluna usada para facetar o gráfico ECDF por linhas."),
            de=("Spalte zur zeilenseitigen Facettierung des ECDF-Diagramms."),
            zh="用于按行对ECDF图进行分面的列。",
        ),
        alias=MultilingualString(
            en="Facet row",
            es="Facetear por filas",
            pt="Facetar por linhas",
            de="Facettenzeile",
            zh="分面行",
        ),
    )  # type: ignore
    ecdf_norm: schema_field(
        enum_field([e.value for e in ECDFNorm]),
        ECDFNorm.PROBABILITY.value,
        description=MultilingualString(
            en=("Type of normalization used for the ECDF plot."),
            es=("Tipo de normalización usada en el gráfico ECDF."),
            pt=("Tipo de normalização usada no gráfico ECDF."),
            de=("Normalisierungstyp für das ECDF-Diagramm."),
            zh="ECDF图使用的归一化类型。",
        ),
        alias=MultilingualString(
            en="ECDF normalization",
            es="Normalización ECDF",
            pt="Normalização ECDF",
            de="ECDF-Normalisierung",
            zh="ECDF归一化",
        ),
    )  # type: ignore


class ECDFPlotExplorer(DistributionExplorer):
    """Explorer that creates an Empirical Cumulative Distribution Function (ECDF) plot.

    The ECDF is a non-parametric, step-function estimate of the cumulative
    distribution of a numeric variable.  For each unique observed value x, the
    y-coordinate gives the proportion (or count, depending on normalisation) of
    data points that are less than or equal to x.  Because it uses the actual
    data without binning, the ECDF preserves every observation and does not
    require a choice of bandwidth or bin width.

    The plot reveals the full shape of a distribution: a steep rise in a region
    indicates many observations concentrated there, while a flat segment
    indicates few observations.  Comparing ECDFs for two groups on the same axes
    immediately shows differences in median, spread, and tail behaviour.

    Use this explorer when you need a precise, assumption-free view of a
    distribution, or to compare distributions across subgroups without the
    distortion that binning can introduce in histograms.
    """

    DISPLAY_NAME = MultilingualString(
        en="Empirical Cumulative Distribution Plot",
        es="Gráfico ECDF (Distribución Acumulada Empírica)",
        pt="Gráfico ECDF",
        de="Empirisches Kumulatives Verteilungsdiagramm",
        zh="经验累积分布函数图",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Nonparametric plot showing the proportion or count of "
            "observations below each unique value."
        ),
        es=(
            "Gráfico no paramétrico que muestra la proporción o el conteo de "
            "observaciones por debajo de cada valor único."
        ),
        pt=(
            "Gráfico não paramétrico que mostra a proporção ou a contagem de "
            "observações abaixo de cada valor único."
        ),
        de=(
            "Nicht-parametrisches Diagramm, das den Anteil oder die Anzahl der "
            "Beobachtungen unterhalb jedes eindeutigen Wertes zeigt."
        ),
        zh="非参数图，显示每个唯一值以下的观测比例或计数。",
    )
    IMAGE_PREVIEW = "ecdf_plot.png"

    SCHEMA = ECDFPlotSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Float, Integer, Categorical],
        "allowed_dtypes": [],
        "non_allowed_dtypes": NON_NUMERIC_DTYPES,
        "input_cardinality": {"min": 1},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the ECDFPlotExplorer with coloring, faceting, and normalization.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments. Recognized keys:
            color_column (str or int, optional): Column name or zero-based index
            used to split the ECDF into color-coded traces. Defaults to None.
            facet_col (str or int, optional): Column name or zero-based index used
            to create column wise subplot facets. Defaults to None.
            facet_row (str or int, optional): Column name or zero-based index used
            to create row wise subplot facets. Defaults to None.
            ecdf_norm (str, optional): Y-axis normalization. One of ``"none"``
            (cumulative count), ``"percent"``, or ``"probability"``.
            Defaults to ``"probability"``.
        """
        self.color_column: Union[str, int, None] = kwargs.get("color_column")
        self.facet_col: Union[str, int, None] = kwargs.get("facet_col")
        self.facet_row: Union[str, int, None] = kwargs.get("facet_row")
        self.ecdf_norm: ECDFNorm = ECDFNorm(kwargs.get("ecdf_norm"))
        super().__init__(**kwargs)

    def prepare_dataset(
        self, loaded_dataset: "DashAIDataset", columns: List[Dict[str, Any]]
    ) -> "DashAIDataset":
        """Extend the column list to include color and facet grouping columns.

        If ``color_column``, ``facet_col``, or ``facet_row`` was given as an
        integer index, each is resolved to the corresponding column name. Resolved
        columns are appended to ``columns`` when not already present, so the base
        class loads them alongside the primary selected columns.

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

        if self.facet_col is not None:
            if isinstance(self.facet_col, int):
                idx = self.facet_col
                col = dataset_columns[idx]
                if col not in explorer_columns:
                    columns.append({"id": idx, "columnName": col})
            else:
                col = self.facet_col
                if col not in explorer_columns:
                    columns.append({"columnName": col})
            self.facet_col = col

        if self.facet_row is not None:
            if isinstance(self.facet_row, int):
                idx = self.facet_row
                col = dataset_columns[idx]
                if col not in explorer_columns:
                    columns.append({"id": idx, "columnName": col})
            else:
                col = self.facet_row
                if col not in explorer_columns:
                    columns.append({"columnName": col})
            self.facet_row = col

        return super().prepare_dataset(loaded_dataset, columns)

    def launch_exploration(self, dataset: "DashAIDataset", explorer_info: Explorer):
        """Generate a Plotly empirical cumulative distribution function (ECDF) plot.

        With one column, the ECDF is plotted for that column. With multiple columns,
        each column is rendered as a separate ECDF trace. Optional color coding,
        column facets, and row facets are applied when configured.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset containing the selected numeric columns
            and any grouping or faceting columns.
        explorer_info : Explorer
            Explorer record with column names and optional
            display name.

        Returns
        -------
        plotly.graph_objects.Figure
            An interactive ECDF figure.
        """
        import plotly.express as px

        _df = dataset.to_pandas()
        columns = [col["columnName"] for col in explorer_info.columns]

        fig = px.ecdf(
            _df,
            x=columns[0] if len(columns) == 1 else columns,
            color=self.color_column,
            facet_col=self.facet_col,
            facet_row=self.facet_row,
            ecdfnorm=(
                self.ecdf_norm.value if self.ecdf_norm is not ECDFNorm.NONE else None
            ),
            title=(
                f"ECDF Plot of {len(columns)} columns"
                if len(columns) > 1
                else f"ECDF Plot of {columns[0]}"
            ),
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
        """Save the ECDF figure to a JSON file on disk.

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
        """Load and return the saved ECDF plot for the frontend.

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
