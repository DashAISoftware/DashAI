"""What counts as a missing value, shared across DashAI.

NanRemover drops rows with missing values, and a prediction whose model
cannot handle them explains which rows and columns are missing; both must
agree on what "missing" means.
"""

from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

# Strings that stand for a missing value in text or categorical columns.
NULL_VALUES = {
    "none",
    "null",
    "nan",
    "na",
    "n/a",
    "",
    "missing",
    "undefined",
    "<na>",
    "nil",
    ".",
}


def is_null_value(value) -> bool:
    """Whether a single value is missing: None, NaN or a null-like string.

    Parameters
    ----------
    value : object
        The value to test.

    Returns
    -------
    bool
        True for ``None``, a float NaN, or a string in ``NULL_VALUES``
        (case and surrounding spaces ignored).
    """
    import numpy as np

    if value is None:
        return True
    if isinstance(value, float) and np.isnan(value):
        return True
    return str(value).lower().strip() in NULL_VALUES


def missing_columns_by_row(
    dataset: "DashAIDataset", columns: List[str]
) -> Dict[int, List[str]]:
    """Map each row with a missing value to the columns missing in it.

    A value is missing when pandas reports it as NA, or, in an object or
    Categorical column, when it is a null-like string (see NULL_VALUES).

    Parameters
    ----------
    dataset : DashAIDataset
        The rows to inspect.
    columns : list of str
        The columns to inspect.

    Returns
    -------
    dict
        0-based row position to the names of its missing columns, in
        ``columns`` order, sorted by position; rows with nothing missing
        are left out.
    """
    from DashAI.back.types.categorical import Categorical

    frame = dataset.select_columns(columns).to_pandas()
    missing: Dict[int, List[str]] = {}
    for column in columns:
        series = frame[column]
        mask = series.isna()
        if isinstance(dataset.types.get(column), Categorical) or (
            series.dtype == object
        ):
            mask = mask | series.apply(is_null_value)
        for position in mask[mask].index:
            missing.setdefault(int(position), []).append(column)
    return dict(sorted(missing.items()))


def missing_values_message(
    dataset: "DashAIDataset", columns: List[str], limit: int = 10
) -> Optional[str]:
    """Explain which rows have missing values, or None if none do.

    Parameters
    ----------
    dataset : DashAIDataset
        The rows a model was asked to predict.
    columns : list of str
        The model's input columns.
    limit : int, optional
        How many rows to list at most. Defaults to 10.

    Returns
    -------
    str or None
        A message naming each incomplete row (numbered from 1, as the user
        sees it) and its missing columns, or None when nothing is missing.
    """
    missing = missing_columns_by_row(dataset, columns)
    if not missing:
        return None
    parts = [
        f"Row {position + 1}: {', '.join(names)}."
        for position, names in list(missing.items())[:limit]
    ]
    if len(missing) > limit:
        parts.append(f"And {len(missing) - limit} more rows.")
    return "The model cannot predict rows with missing values. " + " ".join(parts)
