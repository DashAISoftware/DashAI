from typing import TYPE_CHECKING, Any, Dict, List, Optional

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.schema_fields import enum_field, int_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.relationship_explorer import RelationshipExplorer
from DashAI.back.types.value_types import Date, Float, Integer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

_VALUE_TYPES = ("Float", "Integer")

METHODS = ["stl", "moving_average"]

MODELS = ["additive", "multiplicative"]

PANEL_TITLES = ["Observed", "Trend", "Seasonal", "Residual"]

ALIAS_PERIODS = {
    "H": 24,
    "B": 5,
    "D": 7,
    "W": 52,
    "M": 12,
    "Q": 4,
}


class SeasonalDecompositionSchema(BaseExplorerSchema):
    """Schema for SeasonalDecompositionExplorer hyperparameters."""

    method: schema_field(
        enum_field(METHODS),
        "stl",
        description=MultilingualString(
            en=(
                "How the series is split. STL fits a season that is allowed "
                "to change shape over the years and shrugs off outliers. The "
                "moving average is the classic split, faster and stricter: "
                "one fixed seasonal shape repeated unchanged."
            ),
            es=(
                "Cómo se separa la serie. STL ajusta una estación que puede "
                "cambiar de forma con los años y resiste los valores "
                "atípicos. La media móvil es la separación clásica, más "
                "rápida y estricta: una forma estacional fija repetida sin "
                "cambios."
            ),
            pt=(
                "Como a série é separada. O STL ajusta uma estação que pode "
                "mudar de forma ao longo dos anos e resiste a valores "
                "atípicos. A média móvel é a separação clássica, mais rápida "
                "e estrita: uma forma sazonal fixa repetida sem alteração."
            ),
            de=(
                "Wie die Reihe zerlegt wird. STL passt eine Saison an, die "
                "ihre Form über die Jahre ändern darf, und steckt Ausreißer "
                "weg. Der gleitende Durchschnitt ist die klassische Zerlegung, "
                "schneller und strenger: eine feste Saisonform, unverändert "
                "wiederholt."
            ),
            zh=(
                "序列的分解方式。STL 拟合的季节形态可随年份变化，并能抵抗离群值。"
                "移动平均是经典分解，更快也更严格：一个固定的季节形态原样重复。"
            ),
        ),
        alias=MultilingualString(
            en="Method",
            es="Método",
            pt="Método",
            de="Methode",
            zh="方法",
        ),
    )  # type: ignore
    period: schema_field(
        int_field(ge=0),
        0,
        description=MultilingualString(
            en=(
                "How many periods one season lasts: 12 for months in a year, "
                "7 for days in a week. Leave it at 0 to read it from the "
                "spacing of the dates."
            ),
            es=(
                "Cuántos períodos dura una estación: 12 para meses de un año, "
                "7 para días de una semana. Déjalo en 0 para leerlo del "
                "espaciado de las fechas."
            ),
            pt=(
                "Quantos períodos dura uma estação: 12 para meses de um ano, "
                "7 para dias de uma semana. Deixe em 0 para ler do espaçamento "
                "das datas."
            ),
            de=(
                "Wie viele Perioden eine Saison dauert: 12 für Monate im "
                "Jahr, 7 für Tage in der Woche. Bei 0 wird sie aus dem "
                "Abstand der Daten gelesen."
            ),
            zh=(
                "一个季节持续多少个周期：一年按月为 12，一周按天为 7。"
                "保持为 0 则从日期间隔中读取。"
            ),
        ),
        alias=MultilingualString(
            en="Season length",
            es="Largo de la estación",
            pt="Duração da estação",
            de="Saisonlänge",
            zh="季节长度",
        ),
    )  # type: ignore
    model: schema_field(
        enum_field(MODELS),
        "additive",
        description=MultilingualString(
            en=(
                "Whether the season adds a fixed amount to the trend or "
                "multiplies it. Use multiplicative when the swings grow with "
                "the level of the series. Only the moving average reads this."
            ),
            es=(
                "Si la estación suma una cantidad fija a la tendencia o la "
                "multiplica. Usa multiplicativo cuando las oscilaciones crecen "
                "con el nivel de la serie. Solo la media móvil lo usa."
            ),
            pt=(
                "Se a estação soma uma quantidade fixa à tendência ou a "
                "multiplica. Use multiplicativo quando as oscilações crescem "
                "com o nível da série. Só a média móvel usa isto."
            ),
            de=(
                "Ob die Saison einen festen Betrag zum Trend addiert oder ihn "
                "multipliziert. Multiplikativ passt, wenn die Ausschläge mit "
                "dem Niveau der Reihe wachsen. Nur der gleitende Durchschnitt "
                "liest das."
            ),
            zh=(
                "季节是对趋势加上固定量，还是与之相乘。"
                "当波动幅度随序列水平增长时使用乘性。仅移动平均会读取该设置。"
            ),
        ),
        alias=MultilingualString(
            en="Model",
            es="Modelo",
            pt="Modelo",
            de="Modell",
            zh="模型",
        ),
    )  # type: ignore


class SeasonalDecompositionExplorer(RelationshipExplorer):
    """Split a series into the trend, the season and what is left over.

    A line plot shows a series moving, not why. Decomposition answers that by
    pulling the three apart: the slow level the series drifts along, the
    shape it repeats every season, and the residual neither explains. Each
    one leads somewhere different. A trend means differencing or a model with
    a trend term. A season standing clearly above the residual is the ``m``
    that ``SeasonalNaive`` and the seasonal part of SARIMAX need. A residual
    that still holds structure means the split is wrong, usually the wrong
    season length.

    The season length is read from the spacing of the dates when it is left
    at 0, so monthly dates give 12 and daily dates 7. Naming it directly is
    the way to check a season the calendar does not imply, such as a fortnight
    of 14 days on daily data.

    STL and the moving average disagree in a way worth knowing. STL lets the
    seasonal shape drift from year to year and is not thrown by an outlier,
    which suits real series. The moving average fits one fixed seasonal
    shape and repeats it unchanged, which is stricter and shows more plainly
    when a season is not stable. Only the moving average reads the
    multiplicative setting, for series whose swings grow with their level.
    """

    SCHEMA = SeasonalDecompositionSchema
    DISPLAY_NAME = MultilingualString(
        en="Seasonal Decomposition",
        es="Descomposición Estacional",
        pt="Decomposição Sazonal",
        de="Saisonale Zerlegung",
        zh="季节性分解",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Splits a series into trend, season and residual, drawn as four "
            "panels sharing a time axis. The season length is read from the "
            "spacing of the dates unless it is named. Select the date column "
            "and the series."
        ),
        es=(
            "Separa una serie en tendencia, estación y residuo, dibujados como "
            "cuatro paneles que comparten un eje temporal. El largo de la "
            "estación se lee del espaciado de las fechas salvo que se indique. "
            "Selecciona la columna de fecha y la serie."
        ),
        pt=(
            "Separa uma série em tendência, estação e resíduo, desenhados como "
            "quatro painéis que compartilham um eixo temporal. A duração da "
            "estação é lida do espaçamento das datas salvo indicação. "
            "Selecione a coluna de data e a série."
        ),
        de=(
            "Zerlegt eine Reihe in Trend, Saison und Rest, gezeichnet als vier "
            "Felder mit gemeinsamer Zeitachse. Die Saisonlänge wird aus dem "
            "Abstand der Daten gelesen, sofern sie nicht angegeben ist. Wählen "
            "Sie die Datumsspalte und die Reihe aus."
        ),
        zh=(
            "将序列分解为趋势、季节和残差，绘制为共享时间轴的四个面板。"
            "若未指定，季节长度将从日期间隔中读取。请选择日期列和序列列。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Splits a series into trend, season and residual.",
        es="Separa una serie en tendencia, estación y residuo.",
        pt="Separa uma série em tendência, estação e resíduo.",
        de="Zerlegt eine Reihe in Trend, Saison und Rest.",
        zh="将序列分解为趋势、季节和残差。",
    )

    metadata: Dict[str, Any] = {
        "allowed_types": [Date, Float, Integer],
        "allowed_dtypes": [],
        "input_cardinality": {"exact": 2},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the explorer.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments. Recognized keys:
            method (str, optional): ``"stl"`` or ``"moving_average"``.
            Defaults to ``"stl"``.
            period (int, optional): How many periods one season lasts, or 0
            to read it from the spacing of the dates. Defaults to 0.
            model (str, optional): ``"additive"`` or ``"multiplicative"``,
            read by the moving average only. Defaults to ``"additive"``.

        Raises
        ------
        ValueError
            If ``method`` or ``model`` is not one of the supported values, or
            if ``period`` is 1 or negative.
        """
        self.method = kwargs.get("method", "stl")
        self.period = int(kwargs.get("period", 0))
        self.model = kwargs.get("model", "additive")

        if self.method not in METHODS:
            raise ValueError(f"'method' must be one of {METHODS}, got '{self.method}'.")
        if self.model not in MODELS:
            raise ValueError(f"'model' must be one of {MODELS}, got '{self.model}'.")
        if self.period != 0 and self.period < 2:
            raise ValueError(
                "A season has to be at least 2 periods long, or 0 to read it "
                f"from the dates, got {self.period}."
            )
        super().__init__(**kwargs)

    @classmethod
    def validate_columns(
        cls, explorer_info: Explorer, column_spec: Dict[str, Dict[str, str]]
    ) -> bool:
        """Check the selection is one date column plus one series.

        The inherited check only asks that every column is of an allowed type
        and that there are two of them, which a selection of two numbers or
        two dates also passes. Neither can be decomposed over time, so both
        are refused here.

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
            True if the selection holds exactly one Date column and exactly
            one numeric column, and the inherited checks also pass.
        """
        if not super().validate_columns(explorer_info, column_spec):
            return False

        types = [
            column_spec.get(column["columnName"], {}).get("type", "")
            for column in explorer_info.columns
        ]
        return (
            types.count("Date") == 1
            and len([t for t in types if t in _VALUE_TYPES]) == 1
        )

    def launch_exploration(self, dataset: "DashAIDataset", explorer_info: Explorer):
        """Decompose the selected series and draw its parts.

        Parameters
        ----------
        dataset : DashAIDataset
            The prepared dataset holding the selected columns.
        explorer_info : Explorer
            Explorer record with the column names and optional display name.

        Returns
        -------
        plotly.graph_objects.Figure
            Four panels sharing a time axis: the series as given, its trend,
            its season and the residual.

        Raises
        ------
        ValueError
            If no selected column is a Date, if the dates do not match the
            format the column declares, if the series holds a missing value,
            if the season length cannot be read from the dates, or if the
            series is shorter than two seasons.
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        from DashAI.back.types.date_utils import DEFAULT_DATE_FORMAT, parse_date_column

        columns = [column["columnName"] for column in explorer_info.columns]
        date_columns = [
            name for name in columns if isinstance(dataset.types.get(name), Date)
        ]
        if not date_columns:
            raise ValueError(
                "SeasonalDecompositionExplorer needs a Date column among the "
                f"selected columns, got {', '.join(columns)}."
            )

        date_column = date_columns[0]
        value_column = next(name for name in columns if name != date_column)

        frame = dataset.to_pandas()
        date_format = (
            getattr(dataset.types[date_column], "format", None) or DEFAULT_DATE_FORMAT
        )
        frame[date_column] = parse_date_column(frame[date_column], date_format)
        frame = frame.sort_values(date_column).reset_index(drop=True)
        series = frame[value_column].astype("float64")

        missing = int(series.isna().sum())
        if missing:
            raise ValueError(
                f"The series holds {missing} row(s) with no value, and a "
                "decomposition cannot reach over a hole. Fill the gaps or "
                "drop those rows before decomposing."
            )

        period = self.period or _read_period(frame[date_column])
        if period is None:
            raise ValueError(
                "The dates do not sit on a spacing that implies a season "
                "length, so there is no season to look for. Name the season "
                "length instead, or resample the dataset onto a regular grid."
            )
        if len(series) < 2 * period:
            raise ValueError(
                f"A season of {period} periods needs at least {2 * period} "
                f"observations to be seen twice, but the series is too short "
                f"at {len(series)}."
            )

        parts = _decompose(series, period, self.method, self.model)

        figure = make_subplots(
            rows=4, cols=1, shared_xaxes=True, subplot_titles=PANEL_TITLES
        )
        panels = zip(PANEL_TITLES, parts, strict=True)
        for row, (title, values) in enumerate(panels, start=1):
            figure.add_trace(
                go.Scatter(x=frame[date_column], y=values, mode="lines", name=title),
                row=row,
                col=1,
            )

        title = f"{value_column} split into trend, season and residual"
        if explorer_info.name is not None and explorer_info.name != "":
            title = f"{explorer_info.name}"
        figure.update_layout(title=title, showlegend=False, height=800)
        figure.update_xaxes(title_text=date_column, row=4, col=1)

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
            A single element list with the plotly artifact of the saved
            figure.
        """
        with open(exploration_path, "r", encoding="utf-8") as f:
            result = f.read()

        return [PlotlyArtifact(payload=result)]


def _read_period(dates) -> Optional[int]:
    """Read how many periods a season lasts from the spacing of the dates.

    Parameters
    ----------
    dates : pandas.Series
        Parsed datetimes in ascending order.

    Returns
    -------
    int or None
        The number of periods in one season, or ``None`` when the spacing
        implies no season.
    """
    from DashAI.back.types.date_utils import infer_frequency

    spacing = infer_frequency(dates)
    if spacing is None:
        return None

    if isinstance(spacing, str):
        alias = spacing.split("-")[0].rstrip("SE") or spacing[0]
        return ALIAS_PERIODS.get(alias.upper())

    days = spacing.days
    if days == 1:
        return 7
    if days == 7:
        return 52
    if 28 <= days <= 31:
        return 12
    if 89 <= days <= 92:
        return 4
    return None


def _decompose(series, period: int, method: str, model: str):
    """Split a series into its observed, trend, seasonal and residual parts.

    Parameters
    ----------
    series : pandas.Series
        The series in time order, with no missing value.
    period : int
        How many periods one season lasts.
    method : str
        ``"stl"`` or ``"moving_average"``.
    model : str
        ``"additive"`` or ``"multiplicative"``, read by the moving average
        only.

    Returns
    -------
    tuple
        The observed values followed by the trend, the season and the
        residual, each as a list the length of the series.
    """
    if method == "stl":
        from statsmodels.tsa.seasonal import STL

        result = STL(series, period=period).fit()
    else:
        from statsmodels.tsa.seasonal import seasonal_decompose

        result = seasonal_decompose(
            series, model=model, period=period, extrapolate_trend="freq"
        )

    return (
        series.tolist(),
        result.trend.tolist(),
        result.seasonal.tolist(),
        result.resid.tolist(),
    )
