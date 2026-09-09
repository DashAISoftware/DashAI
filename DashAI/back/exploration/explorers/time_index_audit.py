from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.artifacts import Artifact, TableArtifact, TablePayload
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.statistical_explorer import StatisticalExplorer
from DashAI.back.types.value_types import Date

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class TimeIndexAuditSchema(BaseExplorerSchema):
    """Schema for TimeIndexAuditExplorer hyperparameters."""


class TimeIndexAuditExplorer(StatisticalExplorer):
    """Report whether a date column can carry a forecast at all.

    Every model in ``ForecastingTask`` reads the series by position and
    assumes one value per period, no period missing and none repeated. A date
    column rarely says so out loud: a shop closed on Sundays, a sensor that
    dropped out for a week and two readings on the same afternoon all look
    like an ordinary column of dates until a model quietly forecasts the
    wrong calendar.

    This explorer answers that question before any model is fitted. It names
    the spacing the dates actually sit on, counts the periods missing from
    that grid, the repeated dates and the rows carrying no date at all, and
    reports the largest hole in the series.

    A report with a named frequency, no missing period and no duplicate is
    ready to forecast. Anything else is what ``TimeResamplerConverter`` is
    for: it rebuilds the table on a regular grid, aggregating the repeats and
    filling the holes the way the data deserves.
    """

    SCHEMA = TimeIndexAuditSchema
    DISPLAY_NAME = MultilingualString(
        en="Time Index Audit",
        es="Auditoría del Índice Temporal",
        pt="Auditoria do Índice Temporal",
        de="Prüfung des Zeitindex",
        zh="时间索引审查",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Checks whether a date column is fit to forecast from. Reports "
            "the number of observations, the span, the spacing the dates sit "
            "on, how many periods of that grid are missing, how many dates "
            "are repeated, how many rows carry no date and the largest gap "
            "in the series. Select the date column."
        ),
        es=(
            "Revisa si una columna de fecha sirve para pronosticar. Informa "
            "la cantidad de observaciones, el rango cubierto, el espaciado "
            "sobre el que caen las fechas, cuántos períodos de esa grilla "
            "faltan, cuántas fechas se repiten, cuántas filas no tienen fecha "
            "y el hueco más grande de la serie. Selecciona la columna de "
            "fecha."
        ),
        pt=(
            "Verifica se uma coluna de data serve para prever. Informa a "
            "quantidade de observações, o intervalo coberto, o espaçamento em "
            "que as datas caem, quantos períodos dessa grade faltam, quantas "
            "datas se repetem, quantas linhas não têm data e a maior lacuna "
            "da série. Selecione a coluna de data."
        ),
        de=(
            "Prüft, ob eine Datumsspalte für eine Prognose taugt. Meldet die "
            "Anzahl der Beobachtungen, den abgedeckten Zeitraum, das Raster, "
            "auf dem die Daten liegen, wie viele Perioden dieses Rasters "
            "fehlen, wie viele Daten sich wiederholen, wie viele Zeilen kein "
            "Datum tragen und die größte Lücke der Reihe. Wählen Sie die "
            "Datumsspalte aus."
        ),
        zh=(
            "检查日期列是否适合用于预测。报告观测数量、覆盖跨度、"
            "日期所处的间隔、该网格上缺失的时间段数量、重复日期数量、"
            "没有日期的行数，以及序列中最大的缺口。请选择日期列。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Checks a date column for gaps, repeats and irregular spacing.",
        es="Revisa huecos, repeticiones y espaciado irregular en una fecha.",
        pt="Verifica lacunas, repetições e espaçamento irregular numa data.",
        de="Prüft eine Datumsspalte auf Lücken, Wiederholungen und Abstände.",
        zh="检查日期列的缺口、重复和不规则间隔。",
    )

    metadata: Dict[str, Any] = {
        "allowed_types": [Date],
        "allowed_dtypes": [],
        "input_cardinality": {"exact": 1},
    }

    def launch_exploration(self, dataset: "DashAIDataset", explorer_info: Explorer):
        """Audit the selected date column.

        Parameters
        ----------
        dataset : DashAIDataset
            The prepared dataset holding the selected column.
        explorer_info : Explorer
            Explorer record with the column names.

        Returns
        -------
        pandas.DataFrame
            A two column frame, ``metric`` and ``value``, holding one row per
            checked property.

        Raises
        ------
        ValueError
            If no selected column is a Date, or if the date values do not
            match the format the column declares.
        """
        import pandas as pd

        from DashAI.back.types.date_utils import DEFAULT_DATE_FORMAT, parse_date_column

        columns = [column["columnName"] for column in explorer_info.columns]
        date_columns = [
            name for name in columns if isinstance(dataset.types.get(name), Date)
        ]
        if not date_columns:
            raise ValueError(
                f"TimeIndexAuditExplorer needs a Date column, got {', '.join(columns)}."
            )

        column = date_columns[0]
        date_format = (
            getattr(dataset.types[column], "format", None) or DEFAULT_DATE_FORMAT
        )
        raw = dataset.to_pandas()[column]
        dates = parse_date_column(raw, date_format).dropna().sort_values()

        report = {
            "Observations": int(len(raw)),
            "Rows without a date": int(len(raw) - len(dates)),
            "First date": dates.min().strftime(date_format) if len(dates) else None,
            "Last date": dates.max().strftime(date_format) if len(dates) else None,
            "Span (days)": (
                int((dates.max() - dates.min()).days) if len(dates) else None
            ),
        }
        report.update(_spacing_report(dates))

        return pd.DataFrame(
            {"metric": list(report), "value": list(report.values())}, dtype=object
        )

    def save_notebook(
        self,
        __notebook_info__: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Save the audit table to a JSON file on disk.

        Parameters
        ----------
        __notebook_info__ : Notebook
            The notebook database record (unused).
        explorer_info : Explorer
            The explorer record used for filename generation.
        save_path : Path
            Directory where the file will be saved.
        result : Any
            The ``pandas.DataFrame`` returned by ``launch_exploration``.

        Returns
        -------
        str
            The path of the saved JSON file as a POSIX string.
        """
        import os
        from pathlib import Path

        filename = f"{explorer_info.id}.json"
        path = Path(os.path.join(save_path, filename))

        result.to_json(path.as_posix(), orient="records")
        return path.as_posix()

    def get_results(
        self, exploration_path: str, options: Dict[str, Any]
    ) -> List[Artifact]:
        """Load and return the saved audit for the frontend.

        Parameters
        ----------
        exploration_path : str
            Path to the JSON file saved by ``save_notebook``.
        options : Dict[str, Any]
            Rendering options from the frontend (unused).

        Returns
        -------
        List[Artifact]
            A single element list with the table artifact of the audit.
        """
        from pathlib import Path

        import numpy as np
        import pandas as pd

        report = pd.read_json(Path(exploration_path), orient="records").replace(
            {np.nan: None}
        )
        return [
            TableArtifact(
                payload=TablePayload(
                    columns=["metric", "value"],
                    rows=[
                        [str(metric), _as_cell(value)]
                        for metric, value in zip(
                            report["metric"], report["value"], strict=True
                        )
                    ],
                )
            )
        ]


def _as_cell(value: Any) -> Any:
    """Render one audited value for the results table.

    Parameters
    ----------
    value : Any
        The value read back from the saved audit.

    Returns
    -------
    Any
        The value as text, or ``None`` when the audit could not answer.
    """
    return None if value is None else str(value)


def _render_spacing(spacing) -> str:
    """Name the spacing the dates sit on, the way a person would say it.

    Parameters
    ----------
    spacing : str or pandas.Timedelta
        A pandas frequency alias, or the most common gap between consecutive
        dates when the dates sit on no regular grid.

    Returns
    -------
    str
        The alias unchanged, or the gap in days when it is a whole number of
        them, since a clock time on a date column says nothing.
    """
    if isinstance(spacing, str):
        return spacing
    if spacing.seconds == 0 and spacing.microseconds == 0 and spacing.nanoseconds == 0:
        return f"{spacing.days} days"
    return str(spacing)


def _spacing_report(dates) -> Dict[str, Any]:
    """Describe the grid the dates sit on and what is missing from it.

    Parameters
    ----------
    dates : pandas.Series
        Parsed datetimes, already sorted and with the missing ones dropped.

    Returns
    -------
    Dict[str, Any]
        The spacing part of the audit. ``None`` marks a question a series
        this short cannot answer.
    """
    import pandas as pd

    from DashAI.back.types.date_utils import infer_frequency

    unique = pd.Series(dates.unique())
    duplicates = int(len(dates) - len(unique))
    unanswerable = {
        "Inferred frequency": "Unknown",
        "Regularly spaced": "No" if duplicates else "Yes",
        "Duplicate dates": duplicates,
        "Missing periods": None,
        "Largest gap (days)": None,
    }
    if len(unique) < 2:
        return unanswerable

    spacing = infer_frequency(unique)
    if spacing is None:
        return unanswerable

    gaps = unique.diff().dropna()
    grid = pd.date_range(start=unique.min(), end=unique.max(), freq=spacing)
    missing = int(len(set(grid) - set(unique)))
    # The grid and the dates have to be the same set, in both directions. An
    # empty ``set(grid) - set(unique)`` alone would call a series regular that
    # merely ends early: dates on the 1st, 8th, 15th and 20th sit on no weekly
    # grid, but the grid a 7 day spacing builds stops at the 15th and so misses
    # nothing. Comparing gap lengths instead is what a calendar spacing breaks,
    # since a month is 28 to 31 days long and every month of the year is still
    # regularly spaced.
    regular = duplicates == 0 and set(grid) == set(unique)

    return {
        "Inferred frequency": _render_spacing(spacing),
        "Regularly spaced": "Yes" if regular else "No",
        "Duplicate dates": duplicates,
        "Missing periods": missing,
        "Largest gap (days)": int(gaps.max().days),
    }
