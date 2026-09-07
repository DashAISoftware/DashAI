import pandas as pd

from DashAI.back.types.inf.type_inference import infer_types


def _infer(values):
    one_column = pd.DataFrame({"col": values})
    return infer_types(one_column, "DashAIPtype")["col"]


def test_iso_dates_are_inferred_as_date():
    result = _infer(
        [
            "2020-01-01",
            "2020-01-02",
            "2020-01-03",
            "2020-01-04",
            "2020-01-05",
            "2020-01-06",
        ]
    )

    assert result["type"] == "Date"
    assert result["dtype"] == "%Y-%m-%d"


def test_dash_separated_eu_dates_keep_their_separator():
    result = _infer(
        [
            "01-01-2020",
            "02-01-2020",
            "03-01-2020",
            "04-01-2020",
            "05-01-2020",
            "06-01-2020",
        ]
    )

    assert result["type"] == "Date"
    assert result["dtype"] == "%d-%m-%Y"


def test_slash_separated_eu_dates_keep_their_separator():
    # ptype labels this "date-eu" too, so only detection tells the two apart.
    result = _infer(
        [
            "01/02/2020",
            "02/02/2020",
            "03/02/2020",
            "04/02/2020",
            "05/02/2020",
            "06/02/2020",
        ]
    )

    assert result["type"] == "Date"
    assert result["dtype"] == "%d/%m/%Y"


def test_two_digit_years_are_inferred_as_date():
    # ptype labels these "date-eu"; guess_datetime_format cannot read them, so
    # this proves the EXTRA_DATE_FORMATS fallback runs inside inference too.
    result = _infer(["1/31/20", "2/28/20", "3/15/20", "4/02/20", "5/19/20", "6/07/20"])

    assert result["type"] == "Date"
    assert result["dtype"] == "%m/%d/%y"


def test_month_name_dates_are_not_reached_by_inference():
    # A documented limit, not a wish. ptype labels "31 January 2020" as
    # "string", so it never enters the date branch at all. Such a column
    # becomes a Date only through a manual type change, where
    # detect_date_format does read it. If ptype is ever taught to label these
    # as a date type, this test starts failing and should become an assertion
    # that the column is a Date with format "%d %B %Y".
    result = _infer(
        [
            "31 January 2020",
            "01 February 2020",
            "15 March 2020",
            "02 April 2020",
            "19 May 2020",
            "07 June 2020",
        ]
    )

    assert result["type"] != "Date"


def test_numeric_columns_are_untouched():
    result = _infer([100, 120, 115, 140, 150, 160])

    assert result["type"] == "Integer"
