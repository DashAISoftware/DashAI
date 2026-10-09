from typing import Dict, Optional, Tuple

import pandas as pd
from beartype import beartype


@beartype
def validate_type_change(
    column_data: pd.Series,
    current_type: str,
    new_type: str,
    new_dtype: Optional[str] = None,
) -> Tuple[bool, str, Optional[pd.Series]]:
    """
    Validates if a column can be safely converted to a new type.

    Parameters
    ----------
    column_data : pd.Series
        The column data to validate
    current_type : str
        Current DashAI type of the column
    new_type : str
        Target DashAI type
    new_dtype : str, optional
        Target PyArrow dtype

    Returns
    -------
    Tuple[bool, str, pd.Series]
        - is_valid: Whether the conversion is valid
        - error_message: Error message if invalid (empty string if valid)
        - converted_data: The converted data if successful (None if invalid)
    """

    # Drop NaN values for validation
    non_null_data = column_data.dropna()

    if len(non_null_data) == 0:
        return True, "", column_data

    # Categorical conversions are always allowed (just string conversion)
    if new_type == "Categorical":
        return _validate_categorical_conversion(non_null_data)

    # Define conversion rules
    conversion_rules = {
        ("Integer", "Float"): _validate_numeric_conversion,
        ("Integer", "Text"): lambda x: (True, "", x.astype(str)),
        ("Float", "Integer"): _validate_float_to_int,
        ("Float", "Text"): lambda x: (True, "", x.astype(str)),
        ("Text", "Integer"): _validate_text_to_int,
        ("Text", "Float"): _validate_text_to_float,
        ("Text", "Date"): lambda x: _validate_text_to_date(x, new_dtype),
        ("Date", "Text"): lambda x: (True, "", x.astype(str)),
        # Time and Timestamp stay disabled: no format can be inferred for them.
        # ("Text", "Time"): lambda x: _validate_text_to_time(x, new_dtype),
        # ("Text", "Timestamp"): lambda x: _validate_text_to_timestamp(x, new_dtype),
        ("Categorical", "Text"): lambda x: (True, "", x.astype(str)),
        ("Categorical", "Integer"): _validate_categorical_to_int,
        ("Categorical", "Float"): _validate_categorical_to_float,
        # A date column with few enough distinct values is inferred as
        # Categorical. Its values are the same date strings a Text column
        # holds, so the check is identical, and without this the user has to
        # detour through Text to correct the type.
        ("Categorical", "Date"): lambda x: _validate_text_to_date(x, new_dtype),
    }

    # Get the appropriate validation function
    conversion_key = (current_type, new_type)

    if conversion_key not in conversion_rules:
        return (
            False,
            f"Conversion from {current_type} to {new_type} is not supported",
            None,
        )

    try:
        return conversion_rules[conversion_key](non_null_data)
    except Exception as e:
        return False, f"Conversion failed: {str(e)}", None


def _validate_categorical_conversion(
    data: pd.Series,
) -> Tuple[bool, str, Optional[pd.Series]]:
    """Validate conversion to Categorical."""
    try:
        # Convert to string first
        str_data = data.astype(str)
        unique_values = str_data.nunique()

        # Warn if too many unique values (but still allow)
        if unique_values > 100:
            warning = (
                f"Column has {unique_values} unique values. "
                "Consider if this should really be categorical."
            )
            return True, warning, str_data

        return True, "", str_data
    except Exception as e:
        return False, f"Cannot convert to Categorical: {str(e)}", None


def _validate_numeric_conversion(
    data: pd.Series,
) -> Tuple[bool, str, Optional[pd.Series]]:
    """Validate conversion between numeric types."""
    try:
        # Check if all values are numeric
        if pd.api.types.is_numeric_dtype(data):
            return True, "", data
        return False, "Column contains non-numeric values", None
    except Exception as e:
        return False, f"Numeric conversion failed: {str(e)}", None


def _validate_float_to_int(data: pd.Series) -> Tuple[bool, str, Optional[pd.Series]]:
    """Validate conversion from Float to Integer."""
    try:
        # Check if values are effectively integers
        if not pd.api.types.is_numeric_dtype(data):
            return False, "Column contains non-numeric values", None

        # Check if there's decimal information that would be lost
        has_decimals = (data != data.astype(int)).any()

        if has_decimals:
            return False, "Column contains decimal values that would be lost", None

        return True, "", data.astype(int)
    except Exception as e:
        return False, f"Float to Integer conversion failed: {str(e)}", None


def _validate_text_to_int(data: pd.Series) -> Tuple[bool, str, Optional[pd.Series]]:
    """Validate conversion from Text to Integer."""
    try:
        # Try to convert to int
        converted = pd.to_numeric(data, errors="coerce")

        # Check if any values failed conversion (became NaN)
        failed_conversions = converted.isna().sum()

        if failed_conversions > 0:
            return (
                False,
                f"{failed_conversions} values cannot be converted to Integer",
                None,
            )

        # Check if there are decimal parts
        has_decimals = (converted != converted.astype(int)).any()

        if has_decimals:
            return (
                False,
                "Some values have decimal parts and would lose precision",
                None,
            )

        return True, "", converted.astype(int)
    except Exception as e:
        return False, f"Text to Integer conversion failed: {str(e)}", None


def _validate_text_to_float(data: pd.Series) -> Tuple[bool, str, Optional[pd.Series]]:
    """Validate conversion from Text to Float."""
    try:
        converted = pd.to_numeric(data, errors="coerce")

        failed_conversions = converted.isna().sum()

        if failed_conversions > 0:
            return (
                False,
                f"{failed_conversions} values cannot be converted to Float",
                None,
            )

        return True, "", converted
    except Exception as e:
        return False, f"Text to Float conversion failed: {str(e)}", None


def _validate_text_to_date(
    data: pd.Series, format_str: str = None
) -> Tuple[bool, str, Optional[pd.Series]]:
    """Validate conversion from Text to Date.

    A Date column is stored as text plus a strptime format, so a successful
    conversion returns the original strings untouched. Only the parse is
    checked.

    Parameters
    ----------
    data : pd.Series
        The column values, already stripped of nulls by the caller.
    format_str : str, optional
        The strptime format to check against. Detected from the values when
        absent.

    Returns
    -------
    Tuple[bool, str, Optional[pd.Series]]
        Whether the conversion is valid, an error message when it is not, and
        the unchanged values when it is.
    """
    from DashAI.back.types.date_utils import detect_date_format, parse_date_column

    resolved = format_str or detect_date_format(data)
    if not resolved:
        return (
            False,
            "No known date format reads every value in this column",
            None,
        )

    try:
        parse_date_column(data, resolved)
    except ValueError as e:
        return False, str(e), None

    return True, "", data


def _validate_text_to_time(
    data: pd.Series, format_str: str = None
) -> Tuple[bool, str, Optional[pd.Series]]:
    """Validate conversion from Text to Time."""
    try:
        # For time, we might need custom parsing
        converted = pd.to_datetime(data, format=format_str, errors="coerce").dt.time

        failed_conversions = pd.Series(converted).isna().sum()

        if failed_conversions > 0:
            return (
                False,
                f"{failed_conversions} values cannot be converted to Time",
                None,
            )

        return True, "", pd.Series(converted)
    except Exception as e:
        return False, f"Text to Time conversion failed: {str(e)}", None


def _validate_text_to_timestamp(
    data: pd.Series, format_str: str = None
) -> Tuple[bool, str, Optional[pd.Series]]:
    """Validate conversion from Text to Timestamp."""
    try:
        converted = pd.to_datetime(data, format=format_str, errors="coerce")

        failed_conversions = converted.isna().sum()

        if failed_conversions > 0:
            return (
                False,
                f"{failed_conversions} values cannot be converted to Timestamp",
                None,
            )

        return True, "", converted
    except Exception as e:
        return False, f"Text to Timestamp conversion failed: {str(e)}", None


def _validate_categorical_to_int(
    data: pd.Series,
) -> Tuple[bool, str, Optional[pd.Series]]:
    """Validate conversion from Categorical to Integer."""
    try:
        # Categorical might be string labels that can't convert to int
        converted = pd.to_numeric(data, errors="coerce")

        failed_conversions = converted.isna().sum()

        if failed_conversions > 0:
            return (
                False,
                (
                    f"{failed_conversions} categorical values "
                    "cannot be converted to Integer"
                ),
                None,
            )

        return True, "", converted.astype(int)
    except Exception as e:
        return False, f"Categorical to Integer conversion failed: {str(e)}", None


def _validate_categorical_to_float(
    data: pd.Series,
) -> Tuple[bool, str, Optional[pd.Series]]:
    """Validate conversion from Categorical to Float."""
    try:
        converted = pd.to_numeric(data, errors="coerce")

        failed_conversions = converted.isna().sum()

        if failed_conversions > 0:
            return (
                False,
                f"{failed_conversions} categorical values cannot be converted to Float",
                None,
            )

        return True, "", converted
    except Exception as e:
        return False, f"Categorical to Float conversion failed: {str(e)}", None


@beartype
def validate_multiple_type_changes(
    data: pd.DataFrame, type_changes: Dict[str, Dict[str, str]]
) -> Tuple[bool, Dict[str, str], Dict[str, str]]:
    """
    Validate multiple column type changes at once.

    Parameters
    ----------
    data : pd.DataFrame
        The dataset to validate
    type_changes : Dict[str, Dict[str, str]]
        Dictionary mapping column names to their new type specs
        Example: {"col1": {"current_type": "Text", "new_type": "Integer"}}

    Returns
    -------
    Tuple[bool, Dict[str, str], Dict[str, str]]
        - all_valid: Whether all changes are valid
        - errors: Dictionary of column names to error messages
        - resolved_dtypes: Dictionary of column names to the dtype actually
          used. For a Date column this is the detected strptime format, which
          the caller has no other way to learn.
    """
    errors = {}
    resolved_dtypes = {}

    for column_name, change in type_changes.items():
        if column_name not in data.columns:
            errors[column_name] = f"Column '{column_name}' not found in dataset"
            continue

        current_type = change.get("current_type")
        new_type = change.get("new_type")
        new_dtype = change.get("new_dtype")

        if new_type == "Date" and not new_dtype:
            # The user picks the type; the layout is read off the data, so a
            # Date column works whatever format it happens to use.
            from DashAI.back.types.date_utils import detect_date_format

            new_dtype = detect_date_format(data[column_name].dropna())
            if not new_dtype:
                # A Date column is meaningless without a format, and
                # validate_type_change would wave an all-null column through:
                # it answers "valid" for any target before looking at the
                # values. Saying yes here hands the frontend a change with no
                # dtype, which crashes the dataset job when it builds the type.
                errors[column_name] = (
                    "No known date format reads every value in this column"
                )
                continue

        is_valid, error_msg, _ = validate_type_change(
            data[column_name], current_type, new_type, new_dtype
        )

        if not is_valid:
            errors[column_name] = error_msg
        elif new_dtype:
            resolved_dtypes[column_name] = new_dtype

    return len(errors) == 0, errors, resolved_dtypes


def validate_categorical_suitability(
    data: pd.Series, max_unique_ratio: float = 0.5, max_unique_count: int = 100
) -> Tuple[bool, str, Dict]:
    """
    Check if a column is suitable to be categorical.

    Parameters
    ----------
    data : pd.Series
        The column data
    max_unique_ratio : float
        Maximum ratio of unique values to total values
    max_unique_count : int
        Maximum number of unique values

    Returns
    -------
    Tuple[bool, str, Dict]
        - is_suitable: Whether the column should be categorical
        - message: Explanation or warning
        - stats: Statistics about the column
    """
    str_data = data.astype(str)
    unique_count = str_data.nunique()
    total_count = len(str_data)
    unique_ratio = unique_count / total_count if total_count > 0 else 0

    stats = {
        "unique_count": unique_count,
        "total_count": total_count,
        "unique_ratio": round(unique_ratio, 3),
        "most_common": str_data.value_counts().head(5).to_dict(),
    }

    if unique_count > max_unique_count:
        return (
            False,
            (
                f"Too many unique values ({unique_count}). "
                "Consider using Text type instead."
            ),
            stats,
        )

    if unique_ratio > max_unique_ratio:
        return (
            False,
            (
                f"High unique ratio ({unique_ratio:.1%}). "
                "This might not be truly categorical."
            ),
            stats,
        )

    return (
        True,
        f"Column appears suitable for categorical type ({unique_count} categories)",
        stats,
    )
