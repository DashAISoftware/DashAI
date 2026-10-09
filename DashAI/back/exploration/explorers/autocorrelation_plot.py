from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.schema_fields import (
    enum_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.statistical_explorer import StatisticalExplorer
from DashAI.back.types.value_types import Date, Float, Integer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

_VALUE_TYPES = ("Float", "Integer")

FUNCTIONS = ["both", "acf", "pacf"]

PANEL_TITLES = {
    "acf": "Autocorrelation (ACF)",
    "pacf": "Partial autocorrelation (PACF)",
}


class AutocorrelationPlotSchema(BaseExplorerSchema):
    """Schema for AutocorrelationExplorer hyperparameters."""

    n_lags: schema_field(
        int_field(ge=1),
        20,
        description=MultilingualString(
            en=(
                "How many lags to draw. A lag is one step back along the "
                "series, so 20 asks how today relates to each of the last 20 "
                "periods. More lags than the series can answer are trimmed."
            ),
            es=(
                "Cuántos rezagos dibujar. Un rezago es un paso hacia atrás en "
                "la serie, así que 20 pregunta cómo se relaciona hoy con cada "
                "uno de los últimos 20 períodos. Los rezagos que la serie no "
                "puede responder se recortan."
            ),
            pt=(
                "Quantas defasagens desenhar. Uma defasagem é um passo atrás "
                "na série, então 20 pergunta como hoje se relaciona com cada "
                "um dos últimos 20 períodos. As defasagens que a série não "
                "pode responder são cortadas."
            ),
            de=(
                "Wie viele Verzögerungen gezeichnet werden. Eine Verzögerung "
                "ist ein Schritt zurück in der Reihe, 20 fragt also, wie "
                "heute mit jeder der letzten 20 Perioden zusammenhängt. Was "
                "die Reihe nicht beantworten kann, wird gekürzt."
            ),
            zh=(
                "绘制多少阶滞后。一阶滞后表示沿序列回退一步，"
                "因此 20 表示考察今天与过去 20 个周期各自的关系。"
                "序列无法支持的滞后阶数会被裁剪。"
            ),
        ),
        alias=MultilingualString(
            en="Lags",
            es="Rezagos",
            pt="Defasagens",
            de="Verzögerungen",
            zh="滞后阶数",
        ),
    )  # type: ignore
    function: schema_field(
        enum_field(FUNCTIONS),
        "both",
        description=MultilingualString(
            en=(
                "Which correlogram to draw. The ACF counts every route from "
                "one period to another, so a strong lag 1 echoes into lag 2. "
                "The PACF removes the shorter routes and shows what each lag "
                "adds on its own."
            ),
            es=(
                "Qué correlograma dibujar. La ACF cuenta todas las rutas de un "
                "período a otro, así que un rezago 1 fuerte se refleja en el "
                "rezago 2. La PACF quita las rutas más cortas y muestra lo que "
                "cada rezago aporta por sí mismo."
            ),
            pt=(
                "Qual correlograma desenhar. A ACF conta todos os caminhos de "
                "um período a outro, então uma defasagem 1 forte ecoa na "
                "defasagem 2. A PACF remove os caminhos curtos e mostra o que "
                "cada defasagem acrescenta sozinha."
            ),
            de=(
                "Welches Korrelogramm gezeichnet wird. Die ACF zählt jeden Weg "
                "von einer Periode zur anderen, ein starker Lag 1 hallt also "
                "in Lag 2 nach. Die PACF entfernt die kürzeren Wege und zeigt, "
                "was jeder Lag für sich beiträgt."
            ),
            zh=(
                "绘制哪种相关图。ACF 统计从一个周期到另一个周期的所有路径，"
                "因此较强的一阶滞后会在二阶滞后中回响。"
                "PACF 剔除较短路径，显示每个滞后单独的贡献。"
            ),
        ),
        alias=MultilingualString(
            en="Function",
            es="Función",
            pt="Função",
            de="Funktion",
            zh="函数",
        ),
    )  # type: ignore
    confidence: schema_field(
        float_field(gt=0.0, lt=1.0),
        0.95,
        description=MultilingualString(
            en=(
                "The confidence level of the band drawn around the bars. A bar "
                "inside the band is not distinguishable from noise."
            ),
            es=(
                "El nivel de confianza de la banda dibujada alrededor de las "
                "barras. Una barra dentro de la banda no se distingue del "
                "ruido."
            ),
            pt=(
                "O nível de confiança da banda desenhada ao redor das barras. "
                "Uma barra dentro da banda não se distingue do ruído."
            ),
            de=(
                "Das Konfidenzniveau des Bandes um die Balken. Ein Balken "
                "innerhalb des Bandes ist nicht von Rauschen zu unterscheiden."
            ),
            zh="柱状图周围置信带的置信水平。落在带内的柱与噪声无法区分。",
        ),
        alias=MultilingualString(
            en="Confidence level",
            es="Nivel de confianza",
            pt="Nível de confiança",
            de="Konfidenzniveau",
            zh="置信水平",
        ),
    )  # type: ignore


class AutocorrelationExplorer(StatisticalExplorer):
    """Show how a series relates to its own past, one lag at a time.

    Forecasting a series from its own history only works when the history
    says something about the present, and a correlogram is where that shows
    up. A bar reaching out of the confidence band at lag 12 on monthly data
    is a year long season; a slow decay across every lag is a trend; bars
    that stay inside the band throughout mean the series is noise and no
    amount of model tuning will forecast it.

    The two functions answer different questions. The autocorrelation counts
    every route from one period to another, so a strong lag 1 echoes into lag
    2 and lag 3 whether or not those lags carry anything of their own. The
    partial autocorrelation removes the shorter routes and shows what each
    lag adds by itself, which is why ARIMA orders are read off it: the last
    lag standing out of the band on the PACF is a candidate for ``p``, and on
    the ACF for ``q``.

    The same reading sets ``window_size`` for ``TimeSeriesWindowConverter``,
    which is otherwise a guess: a window shorter than the last useful lag
    throws away the information the correlogram just found.
    """

    SCHEMA = AutocorrelationPlotSchema
    DISPLAY_NAME = MultilingualString(
        en="Autocorrelation Plot",
        es="Gráfico de Autocorrelación",
        pt="Gráfico de Autocorrelação",
        de="Autokorrelationsdiagramm",
        zh="自相关图",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Draws the autocorrelation and partial autocorrelation of a "
            "series against its own past, with a confidence band. Bars "
            "reaching out of the band mark the lags worth modelling, which is "
            "how ARIMA orders and a window size are chosen. Select the date "
            "column and the series."
        ),
        es=(
            "Dibuja la autocorrelación y la autocorrelación parcial de una "
            "serie contra su propio pasado, con una banda de confianza. Las "
            "barras que salen de la banda marcan los rezagos que vale la pena "
            "modelar, que es como se eligen los órdenes de ARIMA y el tamaño "
            "de ventana. Selecciona la columna de fecha y la serie."
        ),
        pt=(
            "Desenha a autocorrelação e a autocorrelação parcial de uma série "
            "contra o seu próprio passado, com uma banda de confiança. As "
            "barras que saem da banda marcam as defasagens que valem a pena "
            "modelar, que é como se escolhem as ordens do ARIMA e o tamanho "
            "da janela. Selecione a coluna de data e a série."
        ),
        de=(
            "Zeichnet die Autokorrelation und die partielle Autokorrelation "
            "einer Reihe gegen ihre eigene Vergangenheit, mit einem "
            "Konfidenzband. Balken, die aus dem Band ragen, markieren die "
            "Verzögerungen, die sich zu modellieren lohnen, und damit die "
            "ARIMA Ordnungen und die Fenstergröße. Wählen Sie die "
            "Datumsspalte und die Reihe aus."
        ),
        zh=(
            "绘制序列相对于自身历史的自相关与偏自相关，并带有置信带。"
            "越出置信带的柱标示值得建模的滞后阶数，"
            "也是选择 ARIMA 阶数和窗口大小的依据。请选择日期列和序列列。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Correlogram of a series against its own past.",
        es="Correlograma de una serie contra su propio pasado.",
        pt="Correlograma de uma série contra o seu próprio passado.",
        de="Korrelogramm einer Reihe gegen ihre eigene Vergangenheit.",
        zh="序列相对于自身历史的相关图。",
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
            n_lags (int, optional): How many lags to draw. Defaults to 20.
            function (str, optional): ``"acf"``, ``"pacf"`` or ``"both"``.
            Defaults to ``"both"``.
            confidence (float, optional): Confidence level of the band around
            the bars. Defaults to 0.95.

        Raises
        ------
        ValueError
            If ``function`` is not one of the supported functions, if
            ``n_lags`` is less than 1, or if ``confidence`` is not strictly
            between 0 and 1.
        """
        self.n_lags = int(kwargs.get("n_lags", 20))
        self.function = kwargs.get("function", "both")
        self.confidence = float(kwargs.get("confidence", 0.95))

        if self.function not in FUNCTIONS:
            raise ValueError(
                f"'function' must be one of {FUNCTIONS}, got '{self.function}'."
            )
        if self.n_lags < 1:
            raise ValueError(f"'n_lags' must be at least 1, got {self.n_lags}.")
        if not 0.0 < self.confidence < 1.0:
            raise ValueError(
                f"'confidence' must lie between 0 and 1, got {self.confidence}."
            )
        super().__init__(**kwargs)

    @classmethod
    def validate_columns(
        cls, explorer_info: Explorer, column_spec: Dict[str, Dict[str, str]]
    ) -> bool:
        """Check the selection is one date column plus one series.

        The inherited check only asks that every column is of an allowed type
        and that there are two of them, which a selection of two numbers or
        two dates also passes. Neither has a series to correlate against a
        time order, so both are refused here.

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
        """Draw the correlogram of the selected series.

        Parameters
        ----------
        dataset : DashAIDataset
            The prepared dataset holding the selected columns.
        explorer_info : Explorer
            Explorer record with the column names and optional display name.

        Returns
        -------
        plotly.graph_objects.Figure
            One correlogram per requested function, drawn as bars per lag
            inside a confidence band.

        Raises
        ------
        ValueError
            If no selected column is a Date, if the dates do not match the
            format the column declares, if the series holds a missing value,
            or if the series is too short to have a lag.
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
                "AutocorrelationExplorer needs a Date column among the "
                f"selected columns, got {', '.join(columns)}."
            )

        date_column = date_columns[0]
        value_column = next(name for name in columns if name != date_column)

        frame = dataset.to_pandas()
        date_format = (
            getattr(dataset.types[date_column], "format", None) or DEFAULT_DATE_FORMAT
        )
        frame[date_column] = parse_date_column(frame[date_column], date_format)
        frame = frame.sort_values(date_column)
        series = frame[value_column].astype("float64").reset_index(drop=True)

        missing = int(series.isna().sum())
        if missing:
            raise ValueError(
                f"The series holds {missing} row(s) with no value, and a "
                "correlation cannot be taken across a hole. Fill the gaps or "
                "drop those rows before looking at the correlogram."
            )
        if len(series) < 3:
            raise ValueError(
                f"A series of {len(series)} observation(s) is too short to "
                "correlate against its own past."
            )

        panels = ["acf", "pacf"] if self.function == "both" else [self.function]
        figure = make_subplots(
            rows=len(panels),
            cols=1,
            subplot_titles=[PANEL_TITLES[panel] for panel in panels]
            if len(panels) > 1
            else None,
        )

        for row, panel in enumerate(panels, start=1):
            lags, values, upper, lower = _correlogram(
                series, panel, self.n_lags, 1.0 - self.confidence
            )
            figure.add_trace(
                go.Bar(x=lags, y=values, name=panel.upper()), row=row, col=1
            )
            figure.add_trace(
                go.Scatter(
                    x=lags,
                    y=upper,
                    mode="lines",
                    line={"dash": "dot", "color": "rgba(120, 120, 120, 0.8)"},
                    name=f"{int(self.confidence * 100)}% band",
                    showlegend=row == 1,
                ),
                row=row,
                col=1,
            )
            figure.add_trace(
                go.Scatter(
                    x=lags,
                    y=lower,
                    mode="lines",
                    line={"dash": "dot", "color": "rgba(120, 120, 120, 0.8)"},
                    showlegend=False,
                ),
                row=row,
                col=1,
            )
            figure.update_xaxes(title_text="Lag", row=row, col=1)

        title = f"{value_column} against its own past"
        if explorer_info.name is not None and explorer_info.name != "":
            title = f"{explorer_info.name}"
        figure.update_layout(title=title, bargap=0.6)

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


def _correlogram(series, function: str, n_lags: int, alpha: float):
    """Compute one correlogram and the confidence band around it.

    Parameters
    ----------
    series : pandas.Series
        The series in time order, with no missing value.
    function : str
        ``"acf"`` or ``"pacf"``.
    n_lags : int
        How many lags were asked for. Trimmed to what the series can answer.
    alpha : float
        One minus the confidence level of the band.

    Returns
    -------
    tuple
        The lags, the correlation at each lag, and the upper and lower edge
        of the band around each lag.
    """
    from statsmodels.tsa.stattools import acf, pacf

    observations = len(series)
    if function == "acf":
        usable = min(n_lags, observations - 1)
        values, interval = acf(series, nlags=usable, alpha=alpha)
    else:
        usable = min(n_lags, max(1, observations // 2 - 1))
        values, interval = pacf(series, nlags=usable, alpha=alpha)

    lags = list(range(1, usable + 1))
    correlations = values[1:]
    upper = interval[1:, 1] - correlations
    lower = interval[1:, 0] - correlations
    return lags, list(correlations), list(upper), list(lower)
