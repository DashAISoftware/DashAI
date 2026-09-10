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
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.distribution_explorer import DistributionExplorer
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class HistFunc(Enum):
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"


class HistNorm(Enum):
    NONE = ""
    PERCENT = "percent"
    PROBABILITY = "probability"
    DENSITY = "density"
    PROBABILITY_DENSITY = "probability density"


class HistogramPlotSchema(BaseExplorerSchema):
    """Schema for HistogramPlotExplorer configuration.

    Controls the bin count, the aggregation function applied within each bin,
    the normalisation of bar heights, and optional grouping columns.

    ``nbins`` sets the number of equally-spaced bins; leaving it as ``None``
    lets Plotly choose automatically.  ``histfunc`` determines what is plotted
    per bin: ``"count"`` (default) counts observations, while ``"sum"``,
    ``"avg"``, ``"min"``, and ``"max"`` aggregate a numeric value within each
    bin.  ``histnorm`` rescales the y-axis: ``""`` shows raw counts;
    ``"percent"`` and ``"probability"`` normalise to 100 and 1 respectively;
    ``"density"`` and ``"probability density"`` divide by the bin width so that
    the area under the histogram integrates to the total count or 1.
    ``color_group`` and ``pattern_group`` split bars by the values of an
    additional column, producing grouped or stacked histograms.
    """

    nbins: schema_field(
        none_type(int_field(ge=1)),
        None,
        description=MultilingualString(
            en=("Number of bins to use for the histogram."),
            es=("Número de bins a usar en el histograma."),
            pt=("Número de bins a usar no histograma."),
            de=("Anzahl der Klassen im Histogramm."),
            zh="直方图使用的分箱数量。",
        ),
        alias=MultilingualString(
            en="Number of bins",
            es="Número de bins",
            pt="Número de bins",
            de="Anzahl der Klassen",
            zh="分箱数量",
        ),
    )  # type: ignore
    histfunc: schema_field(
        enum_field([e.value for e in HistFunc]),
        HistFunc.COUNT.value,
        description=MultilingualString(
            en=("Binning function used for this histogram trace."),
            es=("Función de agrupación usada para este trazo de histograma."),
            pt=("Função de agrupamento usada para este traço de histograma."),
            de=("Klassierungsfunktion für diesen Histogramm-Trace."),
            zh="此直方图轨迹使用的分箱函数。",
        ),
        alias=MultilingualString(
            en="Binning function",
            es="Función de binning",
            pt="Função de agrupamento",
            de="Klassierungsfunktion",
            zh="分箱函数",
        ),
    )  # type: ignore
    histnorm: schema_field(
        # HistNorm.NONE is plotly's empty string, which means "raw counts". Left
        # unlabelled it renders as a blank row in the dropdown, indistinguishable
        # from a null value, and the option nobody can see is also the default.
        enum_field(
            [e.value for e in HistNorm],
            labels={
                HistNorm.NONE.value: MultilingualString(
                    en="Count", es="Cuenta", pt="Contagem", de="Anzahl", zh="计数"
                ),
                HistNorm.PERCENT.value: MultilingualString(
                    en="Percent",
                    es="Porcentaje",
                    pt="Porcentagem",
                    de="Prozent",
                    zh="百分比",
                ),
                HistNorm.PROBABILITY.value: MultilingualString(
                    en="Probability",
                    es="Probabilidad",
                    pt="Probabilidade",
                    de="Wahrscheinlichkeit",
                    zh="概率",
                ),
                HistNorm.DENSITY.value: MultilingualString(
                    en="Density", es="Densidad", pt="Densidade", de="Dichte", zh="密度"
                ),
                HistNorm.PROBABILITY_DENSITY.value: MultilingualString(
                    en="Probability density",
                    es="Densidad de probabilidad",
                    pt="Densidade de probabilidade",
                    de="Wahrscheinlichkeitsdichte",
                    zh="概率密度",
                ),
            },
        ),
        HistNorm.NONE.value,
        description=MultilingualString(
            en=("Type of normalization used for this histogram trace."),
            es=("Tipo de normalización usada en este histograma."),
            pt=("Tipo de normalização usada neste histograma."),
            de=("Normalisierungstyp für diesen Histogramm-Trace."),
            zh="此直方图轨迹使用的归一化类型。",
        ),
        alias=MultilingualString(
            en="Normalization",
            es="Normalización",
            pt="Normalização",
            de="Normalisierung",
            zh="归一化",
        ),
    )  # type: ignore
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
    pattern_group: schema_field(
        none_type(union_type(string_field(), int_field(ge=0))),
        None,
        description=MultilingualString(
            en=("Column name or index used to group point patterns."),
            es=("Nombre o índice de columna para agrupar patrones de puntos."),
            pt=("Nome ou índice de coluna para agrupar padrões de pontos."),
            de=("Spaltenname oder -index zur Mustergruppierung der Punkte."),
            zh="用于按图案分组数据点的列名或索引。",
        ),
        alias=MultilingualString(
            en="Pattern group column",
            es="Columna para grupo de patrón",
            pt="Coluna para grupo de padrão",
            de="Mustergruppen-Spalte",
            zh="图案分组列",
        ),
    )  # type: ignore


class HistogramPlotExplorer(DistributionExplorer):
    """Explorer that renders an interactive histogram for a single column.

    A histogram divides the value range of the selected column into adjacent
    bins and represents the number (or aggregated value) of observations falling
    into each bin as a bar height.  It is the most direct way to visualise the
    frequency distribution of a numeric variable: the overall shape reveals
    whether the data are roughly symmetric, skewed, bimodal, or uniform, while
    the spread of the bars indicates the range and variability of the values.

    Normalisation options allow the y-axis to be expressed as raw counts,
    percentages, probabilities, or probability densities, making it easy to
    compare distributions with different sample sizes on the same scale.  The
    optional colour and pattern grouping parameters produce stacked or
    side-by-side histograms that compare frequency distributions across
    categorical subgroups.

    Use this explorer as a first step in univariate data exploration or to
    verify the distributional assumptions of a model (e.g. checking normality
    of residuals).
    """

    DISPLAY_NAME = MultilingualString(
        en="Histogram Plot",
        es="Histograma",
        pt="Histograma",
        de="Histogramm",
        zh="直方图",
    )
    DESCRIPTION = MultilingualString(
        en=("Displays a histogram for a selected column to explore its distribution."),
        es=(
            "Muestra un histograma de una columna seleccionada para explorar su "
            "distribución."
        ),
        pt=(
            "Exibe um histograma de uma coluna selecionada para explorar sua "
            "distribuição."
        ),
        de=(
            "Zeigt ein Histogramm einer ausgewählten Spalte zur Erkundung "
            "ihrer Verteilung an."
        ),
        zh="显示所选列的直方图，以探索其分布。",
    )
    IMAGE_PREVIEW = "histogram_plot.png"

    SCHEMA = HistogramPlotSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Float, Integer, Categorical],
        "allowed_dtypes": [],
        "input_cardinality": {"exact": 1},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the HistogramPlotExplorer with binning and grouping options.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments. Recognized keys:
            nbins (int, optional): Number of bins to use. If None, Plotly
            chooses automatically. Defaults to None.
            histfunc (str, optional): Aggregation function applied to each bin.
            One of ``"count"``, ``"sum"``, ``"avg"``, ``"min"``, or
            ``"max"``. Defaults to ``"count"``.
            histnorm (str, optional): Normalization method. One of ``""``
            (counts), ``"percent"``, ``"probability"``, ``"density"``,
            or ``"probability density"``. Defaults to ``""`` (counts).
            color_group (str or int, optional): Column name or zero-based index
            used to color-group histogram bars. Defaults to None.
            pattern_group (str or int, optional): Column name or zero-based
            index used to pattern-group histogram bars. Defaults to None.
        """
        self.nbins: Union[int, None] = kwargs.get("nbins")
        self.histfunc: HistFunc = HistFunc(kwargs.get("histfunc"))
        self.histnorm: HistNorm = HistNorm(kwargs.get("histnorm"))
        self.color_column: Union[str, int, None] = kwargs.get("color_group")
        self.pattern_column: Union[str, int, None] = kwargs.get("pattern_group")
        super().__init__(**kwargs)

    def prepare_dataset(
        self, loaded_dataset: "DashAIDataset", columns: List[Dict[str, Any]]
    ) -> "DashAIDataset":
        """Extend the column list to include color and pattern grouping columns.

        If ``color_group`` or ``pattern_group`` was given as an integer index,
        each is resolved to the corresponding column name. Resolved columns are
        appended to ``columns`` when not already present, so the base class loads
        them alongside the primary selected column.

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

        if self.pattern_column is not None:
            if isinstance(self.pattern_column, int):
                idx = self.pattern_column
                col = dataset_columns[idx]
                if col not in explorer_columns:
                    columns.append({"id": idx, "columnName": col})
            else:
                col = self.pattern_column
                if col not in explorer_columns:
                    columns.append({"columnName": col})
            self.pattern_column = col

        return super().prepare_dataset(loaded_dataset, columns)

    def launch_exploration(self, dataset: "DashAIDataset", explorer_info: Explorer):
        """Generate a Plotly histogram for the selected column.

        The histogram is configured with the binning function, normalization,
        optional color grouping, and optional pattern grouping set during
        initialization. Exactly one primary column is supported.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset containing the selected column and any
            grouping columns.
        explorer_info : Explorer
            Explorer record with column names and optional
            display name.

        Returns
        -------
        plotly.graph_objects.Figure
            An interactive histogram figure.
        """
        import plotly.express as px

        _df = dataset.to_pandas()
        columns = [col["columnName"] for col in explorer_info.columns]

        fig = px.histogram(
            _df,
            x=columns[0],
            nbins=self.nbins,
            histnorm=self.histnorm.value,
            histfunc=self.histfunc.value,
            color=self.color_column,
            pattern_shape=self.pattern_column,
            title=f"Histogram of {columns[0]}",
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
        """Save the histogram figure to a JSON file on disk.

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
        """Load and return the saved histogram for the frontend.

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
