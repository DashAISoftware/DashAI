from typing import TYPE_CHECKING, List, Union

from DashAI.back.core.utils import MultilingualString
from DashAI.back.tasks.base_task import BaseTask
from DashAI.back.types.value_types import Date, Float, Integer

if TYPE_CHECKING:
    from datasets import DatasetDict
    from numpy import ndarray

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ForecastingTask(BaseTask):
    """Task for predicting the future values of a single time series.

    The input is one ``Date`` column and the output is one numeric column: the
    series to forecast. Nothing else is offered to the model, so the only
    information it has is the history of the series itself.

    That restriction is the point. Models that take a date and nothing more,
    such as ARIMA or exponential smoothing, are a different family from models
    that also take explanatory variables.

    Two routes lead to a forecast in DashAI, and this is only one of them. The
    other is ``TimeSeriesWindowConverter``, which reshapes the same data into
    lag columns and hands it to ``RegressionTask``, making every existing
    regressor usable. This task exists for the models that read a date column
    directly and cannot be expressed that way.
    """

    PREDICTS_FORWARD_ONLY: bool = True

    DESCRIPTION: str = MultilingualString(
        en=(
            "Predict the future values of a time series from its own history. "
            "Takes one date column and one numeric column, with no other "
            "variables."
        ),
        es=(
            "Predice los valores futuros de una serie temporal a partir de su "
            "propia historia. Toma una columna de fecha y una columna "
            "numerica, sin ninguna otra variable."
        ),
        pt=(
            "Preve os valores futuros de uma serie temporal a partir da sua "
            "propria historia. Recebe uma coluna de data e uma coluna "
            "numerica, sem nenhuma outra variavel."
        ),
        de=(
            "Sagt die zukuenftigen Werte einer Zeitreihe aus ihrer eigenen "
            "Vergangenheit voraus. Nimmt eine Datumsspalte und eine numerische "
            "Spalte, ohne weitere Variablen."
        ),
        zh=(
            "根据时间序列自身的历史预测其未来值。"
            "接受一个日期列和一个数值列，不使用其他变量。"
        ),
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Forecasting",
        es="Pronostico",
        pt="Previsao",
        de="Zeitreihenprognose",
        zh="时间序列预测",
    )

    metadata: dict = {
        "inputs_types": [Date],
        "outputs_types": [Float, Integer],
        "inputs_cardinality": 1,
        "outputs_cardinality": 1,
    }

    def prepare_for_task(
        self,
        dataset: Union["DatasetDict", "DashAIDataset"],
        input_columns: List[str],
        output_columns: List[str],
    ) -> "DashAIDataset":
        """Convert the dataset to a DashAIDataset and validate its types.

        Parameters
        ----------
        dataset : DatasetDict or DashAIDataset
            Dataset to prepare.
        input_columns : list of str
            The single date column.
        output_columns : list of str
            The single numeric column holding the series.

        Returns
        -------
        DashAIDataset
            Dataset with validated types, in date order.
        """
        prepared = super().prepare_for_task(dataset, input_columns, output_columns)
        return self._sort_by_date(prepared, input_columns[0])

    @staticmethod
    def _sort_by_date(dataset: "DashAIDataset", date_column: str) -> "DashAIDataset":
        """Put the rows in date order.

        Everything downstream reads row order as time order and none of it
        checks: the temporal splitter carves its partitions by position, and
        the models hand their values to statsmodels in the order they arrive.
        A file that is not sorted by its date column therefore produces
        partitions that are not periods of time and a model fitted on a
        scrambled series, with nothing reporting a problem.

        This is the task's job rather than the splitter's. The splitter is
        handed the selected input columns, which on the windowed route through
        ``TimeSeriesWindowConverter`` are lag columns with no date among them.

        Sorting reads the format the column declares. Text order only matches
        time order for ISO layouts: as text, "01/02/2020" precedes
        "31/01/2020" while following it in time.

        Parameters
        ----------
        dataset : DashAIDataset
            The validated dataset.
        date_column : str
            The single input column, which the task has already checked is a
            ``Date``.

        Returns
        -------
        DashAIDataset
            The same rows and types, ordered by date.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
        from DashAI.back.types.date_utils import DEFAULT_DATE_FORMAT, parse_date_column

        date_format = (
            getattr(dataset.types[date_column], "format", None) or DEFAULT_DATE_FORMAT
        )
        frame = dataset.to_pandas()
        order = parse_date_column(frame[date_column], date_format).sort_values().index

        if list(order) == list(frame.index):
            return dataset

        return to_dashai_dataset(
            frame.loc[order].reset_index(drop=True), types=dict(dataset.types)
        )

    def process_predictions(
        self, dataset: "DashAIDataset", predictions: "ndarray", output_column: str
    ):
        """Return the forecast values unchanged.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset used for training.
        predictions : np.ndarray
            Predictions from the model.
        output_column : str
            Output column.

        Returns
        -------
        np.ndarray
            The predictions as they were produced. A forecast is already a
            number on the scale of the series, so there is nothing to decode.
        """
        return predictions

    def num_labels(self, dataset: "DashAIDataset", output_column: str) -> int | None:
        """Report that this task has no labels.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset used for training.
        output_column : str
            Output column.

        Returns
        -------
        int | None
            Always ``None``: the output is continuous, so there is no class
            count for a model to size itself against.
        """
        return None
