from typing import TYPE_CHECKING, Dict, List, Union

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.converters.category.feature_engineering import (
    FeatureEngineeringConverter,
)
from DashAI.back.core.schema_fields import bool_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Date, Float, Integer

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

FEATURE_SUFFIXES: Dict[str, str] = {
    "year": "year",
    "month": "month",
    "day": "day",
    "weekday": "weekday",
    "quarter": "quarter",
    "week_of_year": "week",
    "day_of_year": "day_of_year",
}

CYCLICAL_PERIODS: Dict[str, int] = {
    "month": 12,
    "day": 31,
    "weekday": 7,
    "quarter": 4,
    "week_of_year": 53,
    "day_of_year": 366,
}


class DateFeaturesSchema(BaseSchema):
    """Schema for DateFeaturesConverter hyperparameters."""

    year: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en="Add the calendar year of each date as an integer column.",
            es="Agrega el año calendario de cada fecha como columna entera.",
            pt="Adiciona o ano civil de cada data como coluna inteira.",
            de="Fügt das Kalenderjahr jedes Datums als Ganzzahlspalte hinzu.",
            zh="将每个日期的日历年份添加为整数列。",
        ),
        alias=MultilingualString(en="Year", es="Año", pt="Ano", de="Jahr", zh="年份"),
    )  # type: ignore
    month: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en="Add the month of the year (1 to 12) as an integer column.",
            es="Agrega el mes del año (1 a 12) como columna entera.",
            pt="Adiciona o mês do ano (1 a 12) como coluna inteira.",
            de="Fügt den Monat des Jahres (1 bis 12) als Ganzzahlspalte hinzu.",
            zh="将月份（1 到 12）添加为整数列。",
        ),
        alias=MultilingualString(en="Month", es="Mes", pt="Mês", de="Monat", zh="月份"),
    )  # type: ignore
    day: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en="Add the day of the month (1 to 31) as an integer column.",
            es="Agrega el día del mes (1 a 31) como columna entera.",
            pt="Adiciona o dia do mês (1 a 31) como coluna inteira.",
            de="Fügt den Tag des Monats (1 bis 31) als Ganzzahlspalte hinzu.",
            zh="将月内日期（1 到 31）添加为整数列。",
        ),
        alias=MultilingualString(
            en="Day of month",
            es="Día del mes",
            pt="Dia do mês",
            de="Tag des Monats",
            zh="月内日期",
        ),
    )  # type: ignore
    weekday: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en=(
                "Add the day of the week as an integer column, with Monday as "
                "0 and Sunday as 6."
            ),
            es=(
                "Agrega el día de la semana como columna entera, con lunes "
                "como 0 y domingo como 6."
            ),
            pt=(
                "Adiciona o dia da semana como coluna inteira, com segunda "
                "como 0 e domingo como 6."
            ),
            de=(
                "Fügt den Wochentag als Ganzzahlspalte hinzu, mit Montag als "
                "0 und Sonntag als 6."
            ),
            zh="将星期几添加为整数列，周一为 0，周日为 6。",
        ),
        alias=MultilingualString(
            en="Weekday",
            es="Día de la semana",
            pt="Dia da semana",
            de="Wochentag",
            zh="星期几",
        ),
    )  # type: ignore
    quarter: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en="Add the quarter of the year (1 to 4) as an integer column.",
            es="Agrega el trimestre del año (1 a 4) como columna entera.",
            pt="Adiciona o trimestre do ano (1 a 4) como coluna inteira.",
            de="Fügt das Quartal des Jahres (1 bis 4) als Ganzzahlspalte hinzu.",
            zh="将年度季度（1 到 4）添加为整数列。",
        ),
        alias=MultilingualString(
            en="Quarter",
            es="Trimestre",
            pt="Trimestre",
            de="Quartal",
            zh="季度",
        ),
    )  # type: ignore
    week_of_year: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en="Add the ISO week number (1 to 53) as an integer column.",
            es="Agrega el número de semana ISO (1 a 53) como columna entera.",
            pt="Adiciona o número da semana ISO (1 a 53) como coluna inteira.",
            de="Fügt die ISO Kalenderwoche (1 bis 53) als Ganzzahlspalte hinzu.",
            zh="将 ISO 周数（1 到 53）添加为整数列。",
        ),
        alias=MultilingualString(
            en="Week of year",
            es="Semana del año",
            pt="Semana do ano",
            de="Kalenderwoche",
            zh="年内周数",
        ),
    )  # type: ignore
    day_of_year: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en="Add the day of the year (1 to 366) as an integer column.",
            es="Agrega el día del año (1 a 366) como columna entera.",
            pt="Adiciona o dia do ano (1 a 366) como coluna inteira.",
            de="Fügt den Tag des Jahres (1 bis 366) als Ganzzahlspalte hinzu.",
            zh="将年内第几天（1 到 366）添加为整数列。",
        ),
        alias=MultilingualString(
            en="Day of year",
            es="Día del año",
            pt="Dia do ano",
            de="Tag des Jahres",
            zh="年内第几天",
        ),
    )  # type: ignore
    cyclical: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en=(
                "Also encode every periodic feature that is on as a sine and "
                "cosine pair, so that December sits next to January instead "
                "of eleven units away from it."
            ),
            es=(
                "Codifica además cada característica periódica activada como "
                "un par seno y coseno, de modo que diciembre quede junto a "
                "enero en lugar de a once unidades de distancia."
            ),
            pt=(
                "Codifica também cada característica periódica ativada como "
                "um par seno e cosseno, de modo que dezembro fique ao lado de "
                "janeiro em vez de a onze unidades de distância."
            ),
            de=(
                "Kodiert zusätzlich jedes aktivierte periodische Merkmal als "
                "Sinus und Kosinus Paar, sodass Dezember neben Januar liegt "
                "statt elf Einheiten entfernt."
            ),
            zh=(
                "另外将每个启用的周期性特征编码为正弦和余弦对，"
                "使十二月与一月相邻，而不是相距十一个单位。"
            ),
        ),
        alias=MultilingualString(
            en="Cyclical encoding",
            es="Codificación cíclica",
            pt="Codificação cíclica",
            de="Zyklische Kodierung",
            zh="周期编码",
        ),
    )  # type: ignore


class DateFeaturesConverter(FeatureEngineeringConverter, BaseConverter):
    """Break a ``Date`` column into the calendar numbers hidden inside it.

    A date is stored as text and a format, which no model can read. What a
    forecast needs from it is calendar position: which month, which weekday,
    which week of the year. This converter writes those out as integer
    columns named ``<column>_<feature>``, one set per ``Date`` column in
    scope, and leaves the original column untouched.

    The columns it produces are exactly what ``ExogenousForecastingTask``
    takes beside the series: variables known for every period being forecast,
    since a calendar is known in advance. That is what separates them from an
    exogenous variable such as a price, which has to be planned or forecast
    first.

    Cyclical encoding answers the one problem plain calendar numbers have.
    Month 12 and month 1 are one step apart in the calendar and eleven apart
    as integers, so a model reading the integer treats the year end as the
    furthest point from the year start. Encoding a periodic feature of period
    ``p`` as ``sin(2*pi*v/p)`` and ``cos(2*pi*v/p)`` puts consecutive values
    next to each other on a circle, which is where they belong.
    """

    SCHEMA = DateFeaturesSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Extracts calendar features from each date column: year, month, "
            "day, weekday, quarter, ISO week and day of year, as chosen. "
            "Optionally adds a sine and cosine encoding of the periodic ones. "
            "The date column itself is kept."
        ),
        es=(
            "Extrae características de calendario de cada columna de fecha: "
            "año, mes, día, día de la semana, trimestre, semana ISO y día del "
            "año, según se elija. Opcionalmente agrega una codificación seno "
            "y coseno de las periódicas. La columna de fecha se conserva."
        ),
        pt=(
            "Extrai características de calendário de cada coluna de data: "
            "ano, mês, dia, dia da semana, trimestre, semana ISO e dia do "
            "ano, conforme escolhido. Opcionalmente adiciona uma codificação "
            "seno e cosseno das periódicas. A coluna de data é mantida."
        ),
        de=(
            "Extrahiert Kalendermerkmale aus jeder Datumsspalte: Jahr, Monat, "
            "Tag, Wochentag, Quartal, ISO Woche und Tag des Jahres, je nach "
            "Auswahl. Optional wird eine Sinus und Kosinus Kodierung der "
            "periodischen Merkmale ergänzt. Die Datumsspalte bleibt erhalten."
        ),
        zh=(
            "从每个日期列中提取日历特征：年、月、日、星期几、季度、"
            "ISO 周数和年内第几天，按所选项生成。"
            "可选择为周期性特征添加正弦和余弦编码。日期列本身会保留。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Turns a date column into calendar features.",
        es="Convierte una columna de fecha en características de calendario.",
        pt="Transforma uma coluna de data em características de calendário.",
        de="Macht aus einer Datumsspalte Kalendermerkmale.",
        zh="将日期列转换为日历特征。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Date Features",
        es="Características de Fecha",
        pt="Características de Data",
        de="Datumsmerkmale",
        zh="日期特征",
    )

    metadata = {
        "allowed_types": [Date],
        "allowed_dtypes": [],
    }

    def __init__(
        self,
        year: bool = True,
        month: bool = True,
        day: bool = False,
        weekday: bool = True,
        quarter: bool = False,
        week_of_year: bool = False,
        day_of_year: bool = False,
        cyclical: bool = False,
    ):
        """Initialise the converter with the calendar features to extract.

        Parameters
        ----------
        year : bool, optional
            Extract the calendar year. Defaults to True.
        month : bool, optional
            Extract the month of the year. Defaults to True.
        day : bool, optional
            Extract the day of the month. Defaults to False.
        weekday : bool, optional
            Extract the day of the week, Monday as 0. Defaults to True.
        quarter : bool, optional
            Extract the quarter of the year. Defaults to False.
        week_of_year : bool, optional
            Extract the ISO week number. Defaults to False.
        day_of_year : bool, optional
            Extract the day of the year. Defaults to False.
        cyclical : bool, optional
            Also encode every periodic feature that is on as a sine and
            cosine pair. Defaults to False.

        Raises
        ------
        ValueError
            If no calendar feature is selected.
        """
        super().__init__()
        self.features = {
            "year": year,
            "month": month,
            "day": day,
            "weekday": weekday,
            "quarter": quarter,
            "week_of_year": week_of_year,
            "day_of_year": day_of_year,
        }
        if not any(self.features.values()):
            raise ValueError(
                "DateFeaturesConverter needs at least one calendar feature "
                "turned on, but every one of them is off."
            )
        self.cyclical = cyclical
        self._date_columns: List[str] = []
        self._output_types: Dict[str, DashAIDataType] = {}

    def _selected_features(self) -> List[str]:
        """List the calendar features that are turned on.

        Returns
        -------
        List[str]
            The feature keys, in the fixed order they are written out.
        """
        return [name for name in FEATURE_SUFFIXES if self.features[name]]

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DateFeaturesConverter":
        """Find the ``Date`` columns in scope and name the columns to be added.

        Parameters
        ----------
        x : DashAIDataset
            The scoped columns.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        DateFeaturesConverter
            The fitted converter instance (self).
        """
        import pyarrow as pa

        self._date_columns = [
            name for name in x.column_names if isinstance(x.types.get(name), Date)
        ]
        self._output_types = {}
        for column in self._date_columns:
            for feature in self._selected_features():
                suffix = FEATURE_SUFFIXES[feature]
                self._output_types[f"{column}_{suffix}"] = Integer(
                    arrow_type=pa.int64()
                )
                if self.cyclical and feature in CYCLICAL_PERIODS:
                    self._output_types[f"{column}_{suffix}_sin"] = Float(
                        arrow_type=pa.float64()
                    )
                    self._output_types[f"{column}_{suffix}_cos"] = Float(
                        arrow_type=pa.float64()
                    )

        if not self._date_columns:
            print(
                "Warning: DateFeaturesConverter did not find any Date column "
                "in the provided scope, so no feature was extracted."
            )
        return self

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Append the selected calendar features of every fitted date column.

        Parameters
        ----------
        x : DashAIDataset
            The dataset to transform.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        DashAIDataset
            The dataset with one integer column per selected feature and date
            column, plus a sine and cosine column per periodic feature when
            cyclical encoding is on. A row whose date is missing gets a null
            in every one of them.

        Raises
        ------
        ValueError
            If the values of a date column do not match the format it
            declares.
        """
        import numpy as np
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import modify_table
        from DashAI.back.types.date_utils import DEFAULT_DATE_FORMAT, parse_date_column

        if not self._date_columns:
            return x

        frame = x.to_pandas()
        new_columns = {}
        new_types = dict(x.types)

        for column in self._date_columns:
            date_format = (
                getattr(x.types[column], "format", None) or DEFAULT_DATE_FORMAT
            )
            dates = parse_date_column(frame[column], date_format)
            for feature in self._selected_features():
                suffix = FEATURE_SUFFIXES[feature]
                values = _calendar_values(dates, feature)
                name = f"{column}_{suffix}"
                new_columns[name] = pa.array(values, type=pa.int64())
                new_types[name] = self._output_types[name]

                if not (self.cyclical and feature in CYCLICAL_PERIODS):
                    continue

                angles = np.array(
                    [np.nan if value is None else float(value) for value in values]
                )
                angles = 2 * np.pi * angles / CYCLICAL_PERIODS[feature]
                for part, function in (("sin", np.sin), ("cos", np.cos)):
                    cyclical_name = f"{name}_{part}"
                    new_columns[cyclical_name] = pa.array(
                        function(angles), type=pa.float64()
                    )
                    new_types[cyclical_name] = self._output_types[cyclical_name]

        return modify_table(x, new_columns, types=new_types)

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the type of one extracted column.

        Parameters
        ----------
        column_name : str, optional
            Name of the output column, such as ``"date_month"`` or
            ``"date_month_sin"``. Defaults to None.

        Returns
        -------
        DashAIDataType
            ``Float`` for a sine or cosine column, ``Integer`` for every
            plain calendar feature.
        """
        import pyarrow as pa

        if column_name in self._output_types:
            return self._output_types[column_name]
        return Integer(arrow_type=pa.int64())


def _calendar_values(dates, feature: str) -> List[Union[int, None]]:
    """Read one calendar feature off a parsed date series.

    Parameters
    ----------
    dates : pandas.Series
        Parsed datetimes, where a missing date is ``NaT``.
    feature : str
        One of the keys of ``FEATURE_SUFFIXES``.

    Returns
    -------
    List[int or None]
        The feature value per row, ``None`` where the date is missing.
    """
    import pandas as pd

    accessor = dates.dt
    if feature == "year":
        values = accessor.year
    elif feature == "month":
        values = accessor.month
    elif feature == "day":
        values = accessor.day
    elif feature == "weekday":
        values = accessor.dayofweek
    elif feature == "quarter":
        values = accessor.quarter
    elif feature == "week_of_year":
        values = accessor.isocalendar().week
    else:
        values = accessor.dayofyear

    return [None if pd.isna(value) else int(value) for value in values]
