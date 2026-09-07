from typing import TYPE_CHECKING, Union

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.converters.category.feature_engineering import (
    FeatureEngineeringConverter,
)
from DashAI.back.core.schema_fields import int_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Date, Float, Integer

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class TimeSeriesWindowConverterSchema(BaseSchema):
    """Schema for TimeSeriesWindowConverter hyperparameters."""

    window_size: schema_field(
        int_field(ge=1),
        3,
        description=MultilingualString(
            en=(
                "How many past values each row carries. A window of 3 turns "
                "the series into rows of lag_3, lag_2, lag_1 and target, "
                "where target is the value that followed those three."
            ),
            es=(
                "Cuantos valores pasados lleva cada fila. Una ventana de 3 "
                "convierte la serie en filas de lag_3, lag_2, lag_1 y target, "
                "donde target es el valor que siguio a esos tres."
            ),
            pt=(
                "Quantos valores passados cada linha carrega. Uma janela de 3 "
                "transforma a serie em linhas de lag_3, lag_2, lag_1 e target, "
                "onde target e o valor que veio depois desses tres."
            ),
            de=(
                "Wie viele vergangene Werte jede Zeile enthaelt. Ein Fenster "
                "von 3 macht aus der Reihe Zeilen mit lag_3, lag_2, lag_1 und "
                "target, wobei target der Wert ist, der auf diese drei folgte."
            ),
            zh=(
                "每行包含多少个过去的值。窗口为 3 时，序列被转换为 "
                "lag_3、lag_2、lag_1 和 target 组成的行，"
                "其中 target 是紧随这三个值之后的值。"
            ),
        ),
        alias=MultilingualString(
            en="Window size",
            es="Tamano de ventana",
            pt="Tamanho da janela",
            de="Fenstergroesse",
            zh="窗口大小",
        ),
    )  # type: ignore


class TimeSeriesWindowConverter(FeatureEngineeringConverter, BaseConverter):
    """Turn a time series into the supervised rows a regression model needs.

    A forecasting dataset is a date column and a value column: one row per
    point in time, with nothing to regress on. This converter reshapes it into
    ``lag_k, ..., lag_1, target``, where each row carries the ``k`` values that
    came before ``target``. That is a plain tabular regression problem, so the
    result is used with ``RegressionTask`` and any regressor DashAI already
    has.

    Given a window of 3 and the series 100, 120, 115, 140, 150, 160::

        lag_3, lag_2, lag_1, target
        100, 120, 115, 140
        120, 115, 140, 150
        115, 140, 150, 160

    The scope selects the date column and the target column is chosen
    separately, the way every supervised converter takes its target. Rows are
    sorted by date before windowing, so the source ordering does not matter.

    Two things to know before using the result:

    * Everything else is discarded. The output holds the lag columns and the
      target and nothing more, including the date column, because the rows no
      longer line up with the original ones.
    * Consecutive rows overlap by ``k - 1`` values. A splitter that shuffles
      will therefore put near duplicate rows on both sides of the split and
      report a score that is too good. The output is regression data, so split
      it chronologically by turning shuffling off on the splitter rather than
      leaving it on.
    """

    SCHEMA = TimeSeriesWindowConverterSchema
    SUPERVISED = True
    CHANGES_ROW_COUNT = True
    DESCRIPTION = MultilingualString(
        en=(
            "Turns a time series into supervised rows: each row holds the "
            "previous values of the target and the value that followed them, "
            "so a regression model can be trained on it. Only the lag columns "
            "and the target are kept; the date column and any other column "
            "are dropped, since the rows no longer match the original ones. "
            "Consecutive rows share values, so split the result "
            "chronologically rather than at random."
        ),
        es=(
            "Convierte una serie temporal en filas supervisadas: cada fila "
            "contiene los valores previos del objetivo y el valor que los "
            "siguio, de modo que se pueda entrenar un modelo de regresion. "
            "Solo se conservan las columnas de rezago y el objetivo; la "
            "columna de fecha y cualquier otra se eliminan, porque las filas "
            "ya no corresponden a las originales. Las filas consecutivas "
            "comparten valores, asi que divide el resultado cronologicamente "
            "y no al azar."
        ),
        pt=(
            "Transforma uma serie temporal em linhas supervisionadas: cada "
            "linha contem os valores anteriores do alvo e o valor que veio "
            "depois deles, para que um modelo de regressao possa ser "
            "treinado. Apenas as colunas de defasagem e o alvo sao mantidos; "
            "a coluna de data e qualquer outra sao removidas, pois as linhas "
            "ja nao correspondem as originais. Linhas consecutivas "
            "compartilham valores, entao divida o resultado cronologicamente "
            "e nao aleatoriamente."
        ),
        de=(
            "Macht aus einer Zeitreihe ueberwachte Zeilen: jede Zeile "
            "enthaelt die vorherigen Werte der Zielgroesse und den Wert, der "
            "auf sie folgte, sodass ein Regressionsmodell trainiert werden "
            "kann. Nur die Lag-Spalten und die Zielgroesse bleiben erhalten; "
            "die Datumsspalte und alle anderen werden entfernt, da die Zeilen "
            "nicht mehr den urspruenglichen entsprechen. Aufeinanderfolgende "
            "Zeilen teilen sich Werte, teilen Sie das Ergebnis daher "
            "chronologisch und nicht zufaellig auf."
        ),
        zh=(
            "将时间序列转换为监督学习的行：每行包含目标的历史值以及紧随其后的值，"
            "从而可以训练回归模型。仅保留滞后列和目标列；日期列和其他列都会被删除，"
            "因为这些行不再与原始行对应。相邻的行共享数值，"
            "因此请按时间顺序划分结果，而不要随机划分。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Turns a time series into lag columns and a target.",
        es="Convierte una serie temporal en columnas de rezago y un objetivo.",
        pt="Transforma uma serie temporal em colunas de defasagem e um alvo.",
        de="Macht aus einer Zeitreihe Lag-Spalten und eine Zielgroesse.",
        zh="将时间序列转换为滞后列和目标列。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Time Series Window",
        es="Ventana de Serie Temporal",
        pt="Janela de Serie Temporal",
        de="Zeitreihenfenster",
        zh="时间序列窗口",
    )

    metadata = {
        "allowed_types": [Date],
        "allowed_dtypes": [],
    }

    def __init__(self, window_size: int):
        """Initialise the converter with the number of past values per row.

        Parameters
        ----------
        window_size : int
            How many lag columns each row carries. Must be at least 1.

        Raises
        ------
        ValueError
            If ``window_size`` is less than 1.
        """
        super().__init__()
        if window_size < 1:
            raise ValueError(f"'window_size' must be at least 1, got {window_size}.")
        self.window_size = window_size
        self._date_column = None
        self._date_format = None
        self._target_column = None
        self._target_is_integer = False

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "TimeSeriesWindowConverter":
        """Identify the date column and the target, and check both are usable.

        Parameters
        ----------
        x : DashAIDataset
            The scoped columns. Exactly one must be a ``Date``.
        y : DashAIDataset, optional
            The target column, holding the series to window.

        Returns
        -------
        TimeSeriesWindowConverter
            The fitted converter instance (self).

        Raises
        ------
        ValueError
            If the scope does not hold exactly one ``Date`` column, if no
            target was chosen, or if the target is not numeric.
        """
        from DashAI.back.types.date_utils import DEFAULT_DATE_FORMAT

        date_columns = [
            name for name in x.column_names if isinstance(x.types.get(name), Date)
        ]
        if len(date_columns) != 1:
            raise ValueError(
                "TimeSeriesWindowConverter needs exactly one Date column in "
                f"scope, found {len(date_columns)} "
                f"({', '.join(date_columns) or 'none'}) among "
                f"{', '.join(x.column_names)}."
            )

        if y is None or not y.column_names:
            raise ValueError(
                "TimeSeriesWindowConverter needs a target column: choose the "
                "series to forecast as the target."
            )

        self._date_column = date_columns[0]
        self._date_format = (
            getattr(x.types[self._date_column], "format", None) or DEFAULT_DATE_FORMAT
        )

        self._target_column = y.column_names[0]
        target_type = y.types.get(self._target_column)
        if not isinstance(target_type, (Float, Integer)):
            raise ValueError(
                "The target of TimeSeriesWindowConverter must be Float or "
                f"Integer, but '{self._target_column}' is "
                f"{type(target_type).__name__}."
            )
        self._target_is_integer = isinstance(target_type, Integer)

        return self

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Reshape the series into lag columns and a target.

        Parameters
        ----------
        x : DashAIDataset
            The scoped columns, holding the date column found during ``fit``.
        y : DashAIDataset, optional
            The target column.

        Returns
        -------
        DashAIDataset
            A dataset of ``window_size + 1`` columns, ``lag_k`` down to
            ``lag_1`` followed by ``target``. Every other column is gone, and
            the first ``window_size`` rows are too, since no complete window
            precedes them.

        Raises
        ------
        ValueError
            If any date is missing or repeated, if the series has gaps, or if
            the window leaves no complete row.
        """
        import pandas as pd

        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
        from DashAI.back.types.date_utils import infer_frequency, parse_date_column

        dates = parse_date_column(x.to_pandas()[self._date_column], self._date_format)
        values = y.to_pandas()[self._target_column]

        # A row with no date is the same problem as a repeated one, except it
        # fails quietly: sort_values sends every NaT to the end, so the value
        # is windowed as the most recent point of the series instead of
        # wherever it belongs. With no date at all on any row there is no
        # order left, and the rows would be windowed in file order, which is
        # exactly what sorting is here to stop mattering.
        undated = int(dates.isna().sum())
        if undated:
            raise ValueError(
                f"The date column holds {undated} row(s) with no date, so "
                "there is no single order to take lags along. Fill them in or "
                "drop those rows before windowing."
            )

        duplicated = dates[dates.duplicated()].dropna()
        if not duplicated.empty:
            sample = ", ".join(str(d.date()) for d in duplicated.unique()[:3])
            raise ValueError(
                "The date column holds repeated dates, so there is no single "
                f"order to take lags along: {sample}."
            )

        # A hole in the series cannot be windowed: it turns into a missing lag
        # for the rows that reach over it. An integer series fails the cast at
        # the end of this method with a message about non-finite values, and a
        # float one keeps going and hands the model NaN, so say it here.
        missing_values = int(values.isna().sum())
        if missing_values:
            raise ValueError(
                f"The target column holds {missing_values} row(s) with no "
                "value, so the windows reaching over them would be "
                "incomplete. Fill the gaps or drop those rows before "
                "windowing."
            )

        ordered = pd.DataFrame({"date": dates, "value": values}).sort_values("date")

        if self.window_size >= len(ordered):
            raise ValueError(
                f"A window of {self.window_size} needs more than "
                f"{self.window_size} rows to leave a complete row, but the "
                f"series has {len(ordered)}."
            )

        # A frequency alias means the dates sit on a regular grid. Anything
        # else means infer_frequency fell back to the most common gap, which
        # is exactly the case worth mentioning. None means it could not tell,
        # usually too few rows, and guessing out loud there would be noise.
        spacing = infer_frequency(ordered["date"])
        if spacing is not None and not isinstance(spacing, str):
            print(
                "Warning: the dates are irregularly spaced, so a lag covers a "
                "different span of time for different rows. The windows are "
                "still built by position."
            )

        series = ordered["value"].reset_index(drop=True)
        windowed = {
            f"lag_{lag}": series.shift(lag) for lag in range(self.window_size, 0, -1)
        }
        windowed["target"] = series

        frame = pd.DataFrame(windowed).iloc[self.window_size :].reset_index(drop=True)
        if self._target_is_integer:
            frame = frame.astype("int64")

        types = {name: self.get_output_type(name) for name in frame.columns}
        return to_dashai_dataset(frame, types=types)

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the type of a lag or target column.

        Every output column comes from the same source series, so they all
        share its type: ``Integer`` when the target was an integer, ``Float``
        otherwise.

        Parameters
        ----------
        column_name : str, optional
            Name of the output column. Unused, since every output column of
            this converter has the same type. Defaults to None.

        Returns
        -------
        DashAIDataType
            ``Integer`` or ``Float``, matching the target column.
        """
        import pyarrow as pa

        if self._target_is_integer:
            return Integer(arrow_type=pa.int64())
        return Float(arrow_type=pa.float64())
