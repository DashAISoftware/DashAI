from typing import TYPE_CHECKING, Dict, List, Union

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.converters.category.basic_preprocessing import (
    BasicPreprocessingConverter,
)
from DashAI.back.core.schema_fields import enum_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Date, Float, Integer

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

FREQUENCIES: Dict[str, str] = {
    "day": "D",
    "week": "W",
    "month": "MS",
    "quarter": "QS",
    "year": "YS",
}

AGGREGATIONS: List[str] = ["mean", "sum", "median", "min", "max", "first", "last"]

FILLS: List[str] = ["none", "forward", "backward", "interpolate", "zero"]

EXACT_AGGREGATIONS: List[str] = ["sum", "min", "max", "first", "last"]


class TimeResamplerSchema(BaseSchema):
    """Schema for TimeResamplerConverter hyperparameters."""

    frequency: schema_field(
        enum_field(list(FREQUENCIES)),
        "day",
        description=MultilingualString(
            en=(
                "The calendar grid to put the rows on: one row per day, week, "
                "month, quarter or year."
            ),
            es=(
                "La grilla de calendario sobre la que quedan las filas: una "
                "fila por día, semana, mes, trimestre o año."
            ),
            pt=(
                "A grade de calendário em que as linhas ficam: uma linha por "
                "dia, semana, mês, trimestre ou ano."
            ),
            de=(
                "Das Kalenderraster für die Zeilen: eine Zeile pro Tag, "
                "Woche, Monat, Quartal oder Jahr."
            ),
            zh="行所落在的日历网格：每天、每周、每月、每季度或每年一行。",
        ),
        alias=MultilingualString(
            en="Frequency",
            es="Frecuencia",
            pt="Frequência",
            de="Frequenz",
            zh="频率",
        ),
    )  # type: ignore
    aggregation: schema_field(
        enum_field(AGGREGATIONS),
        "mean",
        description=MultilingualString(
            en=(
                "How several readings falling in the same period are reduced "
                "to the single value of that period."
            ),
            es=(
                "Cómo se reducen a un solo valor las varias mediciones que "
                "caen en el mismo período."
            ),
            pt=(
                "Como várias leituras que caem no mesmo período são "
                "reduzidas ao único valor desse período."
            ),
            de=(
                "Wie mehrere Messwerte desselben Zeitraums auf den einen Wert "
                "dieses Zeitraums reduziert werden."
            ),
            zh="将落在同一时间段内的多条读数归约为该时间段单一取值的方式。",
        ),
        alias=MultilingualString(
            en="Aggregation",
            es="Agregación",
            pt="Agregação",
            de="Aggregation",
            zh="聚合方式",
        ),
    )  # type: ignore
    fill: schema_field(
        enum_field(FILLS),
        "none",
        description=MultilingualString(
            en=(
                "What to write into a period the data never covered: nothing, "
                "the previous value, the next value, a straight line between "
                "the two, or zero."
            ),
            es=(
                "Qué escribir en un período que los datos nunca cubrieron: "
                "nada, el valor anterior, el valor siguiente, una recta entre "
                "ambos o cero."
            ),
            pt=(
                "O que escrever em um período que os dados nunca cobriram: "
                "nada, o valor anterior, o valor seguinte, uma reta entre os "
                "dois ou zero."
            ),
            de=(
                "Was in einen Zeitraum geschrieben wird, den die Daten nie "
                "abdecken: nichts, der vorherige Wert, der nächste Wert, eine "
                "Gerade dazwischen oder null."
            ),
            zh=(
                "对数据从未覆盖的时间段写入什么："
                "不写入、前一个值、后一个值、两者之间的直线插值，或零。"
            ),
        ),
        alias=MultilingualString(
            en="Fill gaps with",
            es="Rellenar huecos con",
            pt="Preencher lacunas com",
            de="Lücken füllen mit",
            zh="缺口填充方式",
        ),
    )  # type: ignore


class TimeResamplerConverter(BasicPreprocessingConverter, BaseConverter):
    """Put a dated table on a regular calendar grid, one row per period.

    Almost every forecasting model assumes the series it is given is a value
    per period with no period missing and none repeated. Real data rarely
    arrives that way: a shop closes on Sunday, a sensor drops out for two
    days, two readings land on the same afternoon. ARIMA and exponential
    smoothing read such a table by position, so a missing week silently
    shortens the calendar and every seasonal claim after it is wrong.

    This converter rebuilds the table on the grid the user names. Rows
    falling in the same period are reduced by the chosen aggregation, periods
    the data never covered appear as their own rows, and the fill setting
    decides what those rows hold. Leaving them empty is honest and refused by
    most models; carrying the previous value forward suits a stock level;
    interpolating suits a smooth physical measurement; zero suits a count of
    events that simply did not happen.

    The date column keeps its name and its format, so the result is still a
    dated table that ``ForecastingTask`` and the exploration side can read.
    Columns that are neither the date nor numeric are dropped, since there is
    no meaningful way to average a piece of text over a week.
    """

    SCHEMA = TimeResamplerSchema
    CHANGES_ROW_COUNT = True
    DESCRIPTION = MultilingualString(
        en=(
            "Puts a dated table on a regular calendar grid: one row per day, "
            "week, month, quarter or year. Readings in the same period are "
            "aggregated, uncovered periods become rows of their own, and the "
            "chosen fill decides what those rows hold. Non numeric columns "
            "are dropped."
        ),
        es=(
            "Coloca una tabla con fechas sobre una grilla de calendario "
            "regular: una fila por día, semana, mes, trimestre o año. Las "
            "mediciones del mismo período se agregan, los períodos no "
            "cubiertos pasan a ser filas propias y el relleno elegido decide "
            "qué contienen. Las columnas no numéricas se descartan."
        ),
        pt=(
            "Coloca uma tabela com datas em uma grade de calendário regular: "
            "uma linha por dia, semana, mês, trimestre ou ano. As leituras do "
            "mesmo período são agregadas, os períodos não cobertos viram "
            "linhas próprias e o preenchimento escolhido decide o que elas "
            "contêm. Colunas não numéricas são descartadas."
        ),
        de=(
            "Legt eine datierte Tabelle auf ein regelmäßiges Kalenderraster: "
            "eine Zeile pro Tag, Woche, Monat, Quartal oder Jahr. Messwerte "
            "desselben Zeitraums werden aggregiert, nicht abgedeckte "
            "Zeiträume werden zu eigenen Zeilen, und die gewählte Füllung "
            "bestimmt deren Inhalt. Nicht numerische Spalten entfallen."
        ),
        zh=(
            "将带日期的表格放到规则的日历网格上：每天、每周、每月、"
            "每季度或每年一行。同一时间段内的读数会被聚合，"
            "未被覆盖的时间段成为独立的行，并由所选填充方式决定其取值。"
            "非数值列会被丢弃。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Puts a dated table on a regular calendar grid.",
        es="Coloca una tabla con fechas en una grilla de calendario regular.",
        pt="Coloca uma tabela com datas em uma grade de calendário regular.",
        de="Legt eine datierte Tabelle auf ein regelmäßiges Kalenderraster.",
        zh="将带日期的表格放到规则的日历网格上。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Time Resampler",
        es="Remuestreo Temporal",
        pt="Reamostragem Temporal",
        de="Zeitliches Resampling",
        zh="时间重采样",
    )

    metadata = {
        "allowed_types": [Date, Float, Integer],
        "allowed_dtypes": [],
    }

    def __init__(
        self,
        frequency: str = "day",
        aggregation: str = "mean",
        fill: str = "none",
    ):
        """Initialise the converter with the grid, the aggregation and the fill.

        Parameters
        ----------
        frequency : str, optional
            One of ``"day"``, ``"week"``, ``"month"``, ``"quarter"``,
            ``"year"``. Defaults to ``"day"``.
        aggregation : str, optional
            How readings of the same period are reduced. One of
            ``"mean"``, ``"sum"``, ``"median"``, ``"min"``, ``"max"``,
            ``"first"``, ``"last"``. Defaults to ``"mean"``.
        fill : str, optional
            What an uncovered period holds. One of ``"none"``,
            ``"forward"``, ``"backward"``, ``"interpolate"``, ``"zero"``.
            Defaults to ``"none"``.

        Raises
        ------
        ValueError
            If any of the three settings is not one of its allowed values.
        """
        super().__init__()
        if frequency not in FREQUENCIES:
            raise ValueError(
                f"'frequency' must be one of {list(FREQUENCIES)}, got '{frequency}'."
            )
        if aggregation not in AGGREGATIONS:
            raise ValueError(
                f"'aggregation' must be one of {AGGREGATIONS}, got '{aggregation}'."
            )
        if fill not in FILLS:
            raise ValueError(f"'fill' must be one of {FILLS}, got '{fill}'.")

        self.frequency = frequency
        self.aggregation = aggregation
        self.fill = fill
        self._date_column = None
        self._date_format = None
        self._value_columns: List[str] = []
        self._integer_columns: List[str] = []
        self._output_types: Dict[str, DashAIDataType] = {}

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "TimeResamplerConverter":
        """Identify the date column and the numeric columns to aggregate.

        Parameters
        ----------
        x : DashAIDataset
            The scoped columns. Exactly one must be a ``Date``.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        TimeResamplerConverter
            The fitted converter instance (self).

        Raises
        ------
        ValueError
            If the scope does not hold exactly one ``Date`` column.
        """
        from DashAI.back.types.date_utils import DEFAULT_DATE_FORMAT

        date_columns = [
            name for name in x.column_names if isinstance(x.types.get(name), Date)
        ]
        if len(date_columns) != 1:
            raise ValueError(
                "TimeResamplerConverter needs one Date column to build the "
                f"calendar grid from, got {len(date_columns)}."
            )

        self._date_column = date_columns[0]
        self._date_format = (
            getattr(x.types[self._date_column], "format", None) or DEFAULT_DATE_FORMAT
        )
        self._value_columns = [
            name
            for name in x.column_names
            if name != self._date_column
            and isinstance(x.types.get(name), (Float, Integer))
        ]
        self._integer_columns = [
            name
            for name in self._value_columns
            if isinstance(x.types.get(name), Integer)
        ]

        dropped = [
            name
            for name in x.column_names
            if name != self._date_column and name not in self._value_columns
        ]
        if dropped:
            print(
                "Warning: TimeResamplerConverter has no way to aggregate the "
                f"non numeric column(s) {', '.join(dropped)} over a period, "
                "so they are dropped."
            )
        return self

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Rebuild the table with one row per period of the chosen grid.

        Parameters
        ----------
        x : DashAIDataset
            The dataset to transform.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        DashAIDataset
            The date column followed by the aggregated numeric columns, one
            row per period from the first date to the last, in chronological
            order.

        Raises
        ------
        ValueError
            If any row has no date, or if the dates do not match the format
            the column declares.
        """
        import pandas as pd
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
        from DashAI.back.types.date_utils import parse_date_column

        frame = x.to_pandas()
        dates = parse_date_column(frame[self._date_column], self._date_format)

        undated = int(dates.isna().sum())
        if undated:
            raise ValueError(
                f"The date column holds {undated} row(s) with no date, so "
                "there is no period to put them in. Fill them in or drop "
                "those rows before resampling."
            )

        indexed = frame[self._value_columns].copy()
        indexed.index = dates
        resampled = indexed.sort_index().resample(FREQUENCIES[self.frequency])
        aggregated = (
            resampled.sum(min_count=1)
            if self.aggregation == "sum"
            else resampled.agg(self.aggregation)
        )
        aggregated = _fill_gaps(aggregated, self.fill)

        result = {
            self._date_column: aggregated.index.strftime(self._date_format).tolist()
        }
        self._output_types = {
            self._date_column: Date(arrow_type=pa.string(), format=self._date_format)
        }
        for name in self._value_columns:
            values = aggregated[name]
            keeps_integer = (
                name in self._integer_columns
                and self.aggregation in EXACT_AGGREGATIONS
                and not values.isna().any()
            )
            result[name] = values.astype("int64") if keeps_integer else values
            self._output_types[name] = (
                Integer(arrow_type=pa.int64())
                if keeps_integer
                else Float(arrow_type=pa.float64())
            )

        return to_dashai_dataset(
            pd.DataFrame(result).reset_index(drop=True), types=self._output_types
        )

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the type of one column of the resampled table.

        Parameters
        ----------
        column_name : str, optional
            Name of the output column. Defaults to None.

        Returns
        -------
        DashAIDataType
            ``Date`` for the date column, ``Integer`` for an integer column
            that stayed exact through the aggregation and the fill, and
            ``Float`` for every other numeric column.
        """
        import pyarrow as pa

        if column_name in self._output_types:
            return self._output_types[column_name]
        return Float(arrow_type=pa.float64())


def _fill_gaps(aggregated, fill: str):
    """Write values into the periods the data never covered.

    Parameters
    ----------
    aggregated : pandas.DataFrame
        The resampled table, where an uncovered period is a row of ``NaN``.
    fill : str
        One of ``"none"``, ``"forward"``, ``"backward"``, ``"interpolate"``,
        ``"zero"``.

    Returns
    -------
    pandas.DataFrame
        The table with its gaps filled as asked.
    """
    if fill == "forward":
        return aggregated.ffill()
    if fill == "backward":
        return aggregated.bfill()
    if fill == "interpolate":
        return aggregated.interpolate(method="linear")
    if fill == "zero":
        return aggregated.fillna(0)
    return aggregated
