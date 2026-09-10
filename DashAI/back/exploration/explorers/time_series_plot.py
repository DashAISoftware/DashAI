from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.schema_fields import bool_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.relationship_explorer import RelationshipExplorer
from DashAI.back.types.value_types import Date, Float, Integer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

# Semantic types that can be plotted as a series against time.
_VALUE_TYPES = ("Float", "Integer")


class TimeSeriesPlotSchema(BaseExplorerSchema):
    """Schema for TimeSeriesPlotExplorer hyperparameters."""

    markers: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en=(
                "Draw a point at each observation as well as the line. Useful "
                "for short or irregular series, where the line alone hides "
                "how many readings there actually are."
            ),
            es=(
                "Dibuja un punto en cada observacion ademas de la linea. Util "
                "para series cortas o irregulares, donde la linea por si sola "
                "oculta cuantas mediciones hay en realidad."
            ),
            pt=(
                "Desenha um ponto em cada observacao alem da linha. Util para "
                "series curtas ou irregulares, nas quais a linha sozinha "
                "esconde quantas leituras existem de fato."
            ),
            de=(
                "Zeichnet zusaetzlich zur Linie einen Punkt pro Beobachtung. "
                "Nuetzlich bei kurzen oder unregelmaessigen Reihen, wo die "
                "Linie allein verbirgt, wie viele Messwerte es wirklich gibt."
            ),
            zh=(
                "除折线外，在每个观测点绘制一个标记。"
                "对于较短或不规则的序列很有用，"
                "因为仅有折线会掩盖实际的观测数量。"
            ),
        ),
        alias=MultilingualString(
            en="Show markers",
            es="Mostrar marcadores",
            pt="Mostrar marcadores",
            de="Markierungen anzeigen",
            zh="显示标记",
        ),
    )  # type: ignore


class TimeSeriesPlotExplorer(RelationshipExplorer):
    """Plot one or more numeric columns against a date column, over time.

    Select the date column plus the series to look at. The dates are read with
    the format the column already carries, sorted, and handed to the plot as
    real datetimes, so the horizontal axis is a genuine time axis: gaps show
    up as gaps and irregular spacing is visible rather than flattened into
    evenly spaced categories.

    This is the plot to look at before forecasting anything, since trend,
    seasonality, level shifts, missing stretches and outliers are all obvious
    here and nearly invisible in a summary table.

    Several numeric columns can be selected at once and are drawn as separate
    lines sharing the time axis.
    """

    DISPLAY_NAME = MultilingualString(
        en="Time Series Plot",
        es="Grafico de Serie Temporal",
        pt="Grafico de Serie Temporal",
        de="Zeitreihendiagramm",
        zh="时间序列图",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Draws one or more numeric columns against a date column as lines "
            "over time. The dates are sorted and plotted on a real time axis, "
            "so gaps and uneven spacing are visible instead of being "
            "flattened into evenly spaced points. Select the date column and "
            "the columns to plot."
        ),
        es=(
            "Dibuja una o mas columnas numericas frente a una columna de fecha "
            "como lineas en el tiempo. Las fechas se ordenan y se grafican en "
            "un eje temporal real, de modo que los huecos y el espaciado "
            "irregular quedan visibles en lugar de aplanarse en puntos "
            "equidistantes. Selecciona la columna de fecha y las columnas a "
            "graficar."
        ),
        pt=(
            "Desenha uma ou mais colunas numericas em relacao a uma coluna de "
            "data como linhas ao longo do tempo. As datas sao ordenadas e "
            "plotadas em um eixo temporal real, de modo que lacunas e "
            "espacamento irregular ficam visiveis em vez de serem achatados em "
            "pontos equidistantes. Selecione a coluna de data e as colunas a "
            "plotar."
        ),
        de=(
            "Zeichnet eine oder mehrere numerische Spalten gegen eine "
            "Datumsspalte als Linien ueber die Zeit. Die Daten werden sortiert "
            "und auf einer echten Zeitachse dargestellt, sodass Luecken und "
            "ungleichmaessige Abstaende sichtbar bleiben, statt zu "
            "gleichmaessigen Punkten zusammengedrueckt zu werden. Waehlen Sie "
            "die Datumsspalte und die zu zeichnenden Spalten aus."
        ),
        zh=(
            "将一列或多列数值列相对于日期列绘制为随时间变化的折线。"
            "日期会被排序并绘制在真实的时间轴上，"
            "因此间隔和不规则的时间间距清晰可见，而不会被压缩为等距的点。"
            "请选择日期列以及要绘制的列。"
        ),
    )

    SCHEMA = TimeSeriesPlotSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Date, Float, Integer],
        "allowed_dtypes": [],
        "input_cardinality": {"min": 2},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the explorer.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments. Recognized keys:
            markers (bool, optional): Draw a point per observation in addition
            to the line. Defaults to False.
        """
        self.markers = bool(kwargs.get("markers", False))
        super().__init__(**kwargs)

    @classmethod
    def validate_columns(
        cls, explorer_info: Explorer, column_spec: Dict[str, Dict[str, str]]
    ) -> bool:
        """Check the selection is one date column plus at least one series.

        The inherited check only asks that every column is of an allowed type,
        which would pass a selection of two numbers and no date, or of two
        dates and no series. Neither can be plotted, so both are refused here
        rather than failing later with an unhelpful error.

        Parameters
        ----------
        explorer_info : Explorer
            The database record for the explorer instance, including the
            selected columns.
        column_spec : Dict[str, Dict[str, str]]
            A mapping from column name to a dict with at least ``"type"`` and
            ``"dtype"``.

        Returns
        -------
        bool
            True if the selection holds exactly one Date column and at least
            one numeric column, and the inherited checks also pass.
        """
        if not super().validate_columns(explorer_info, column_spec):
            return False

        types = [
            column_spec.get(column["columnName"], {}).get("type", "")
            for column in explorer_info.columns
        ]
        return types.count("Date") == 1 and any(t in _VALUE_TYPES for t in types)

    def launch_exploration(self, dataset: "DashAIDataset", explorer_info: Explorer):
        """Draw the selected series against the selected date column.

        Parameters
        ----------
        dataset : DashAIDataset
            The prepared dataset holding the selected columns.
        explorer_info : Explorer
            Explorer record with the column names and optional display name.

        Returns
        -------
        plotly.graph_objects.Figure
            An interactive line plot with a time axis.

        Raises
        ------
        ValueError
            If no selected column is a Date, or if the date values do not
            match the format the column declares.
        """
        import plotly.express as px

        from DashAI.back.types.date_utils import DEFAULT_DATE_FORMAT, parse_date_column

        columns = [column["columnName"] for column in explorer_info.columns]
        date_columns = [
            name for name in columns if isinstance(dataset.types.get(name), Date)
        ]
        if not date_columns:
            raise ValueError(
                "TimeSeriesPlotExplorer needs a Date column among the selected "
                f"columns, got {', '.join(columns)}."
            )

        date_column = date_columns[0]
        value_columns = [name for name in columns if name != date_column]

        frame = dataset.to_pandas()
        # Read with the format the column already declares rather than
        # guessing, so the plot can never disagree with the stored type. A
        # column whose format is wrong raises here instead of drawing a
        # plausible but wrong picture.
        date_format = (
            getattr(dataset.types[date_column], "format", None) or DEFAULT_DATE_FORMAT
        )
        frame[date_column] = parse_date_column(frame[date_column], date_format)
        frame = frame.sort_values(date_column)

        figure = px.line(
            frame,
            x=date_column,
            y=value_columns,
            markers=self.markers,
            title=f"{', '.join(value_columns)} over {date_column}",
        )
        figure.update_layout(xaxis_title=date_column, yaxis_title="")

        if explorer_info.name is not None and explorer_info.name != "":
            figure.update_layout(title=f"{explorer_info.name}")

        return figure

    def save_notebook(
        self,
        __notebook_info__: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Save the figure to disk (JSON content, ``.pickle`` extension).

        Notes
        -----
        Despite the ``.pickle`` file extension, the file is written using
        ``write_json`` and contains JSON-serialized Plotly figure data. This
        matches every other plot explorer.

        Parameters
        ----------
        __notebook_info__ : Notebook
            The notebook database record (unused).
        explorer_info : Explorer
            The explorer record used for filename generation.
        save_path : Path
            Directory where the file will be saved.
        result : Any
            The Plotly figure returned by ``launch_exploration``.

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
        """Load and return the saved figure for the frontend.

        Parameters
        ----------
        exploration_path : str
            Path to the JSON file saved by ``save_notebook``.
        options : Dict[str, Any]
            Rendering options from the frontend (unused).

        Returns
        -------
        List[Artifact]
            A single-element list with the plotly artifact of the saved figure.
        """
        with open(exploration_path, "r", encoding="utf-8") as f:
            result = f.read()

        return [PlotlyArtifact(payload=result)]
