import pandas as pd
import pytest

from DashAI.back.types.date_utils import (
    detect_date_format,
    infer_frequency,
    parse_date_column,
)


def test_parse_date_column_reads_iso_dates():
    parsed = parse_date_column(["2020-01-31", "2020-02-29"], "%Y-%m-%d")

    assert list(parsed.astype(str)) == ["2020-01-31", "2020-02-29"]


def test_parse_date_column_reads_month_names():
    parsed = parse_date_column(["31 January 2020"], "%d %B %Y")

    assert list(parsed.astype(str)) == ["2020-01-31"]


def test_parse_date_column_keeps_nulls_as_nat():
    parsed = parse_date_column(["2020-01-31", None, ""], "%Y-%m-%d")

    assert parsed.isna().tolist() == [False, True, True]


def test_parse_date_column_names_the_values_it_cannot_read():
    with pytest.raises(ValueError, match="banana"):
        parse_date_column(["2020-01-31", "banana"], "%Y-%m-%d")


def test_detect_date_format_finds_iso():
    assert detect_date_format(["2020-01-31", "2020-02-29"]) == "%Y-%m-%d"


def test_detect_date_format_separates_dash_and_slash_eu_dates():
    # ptype labels both of these "date-eu"; only the data tells them apart.
    assert detect_date_format(["31-01-2020"], hint="date-eu") == "%d-%m-%Y"
    assert detect_date_format(["31/01/2020"], hint="date-eu") == "%d/%m/%Y"


def test_detect_date_format_finds_month_names():
    assert detect_date_format(["31 January 2020"]) == "%d %B %Y"


def test_detect_date_format_finds_two_digit_years():
    # guess_datetime_format returns None here, so this exercises the
    # EXTRA_DATE_FORMATS fallback.
    assert detect_date_format(["1/31/20", "2/28/20"]) == "%m/%d/%y"


def test_detect_date_format_honours_the_day_first_hint_for_two_digit_years():
    # Every value here reads both ways, so only the hint can decide.
    assert detect_date_format(["01/02/20", "05/02/20"], hint="date-eu") == "%d/%m/%y"
    assert detect_date_format(["01/02/20", "05/02/20"]) == "%m/%d/%y"


def test_detect_date_format_resolves_ambiguity_from_the_whole_column():
    # The first value alone guesses month first. The third value rules it out.
    detected = detect_date_format(["01/02/2020", "05/02/2020", "13/02/2020"])

    assert detected == "%d/%m/%Y"


TEST_COLUMNS = [
    (["2026-01-05", "2026-02-14", "2026-12-25"], "%Y-%m-%d"),
    (["01/05/2026", "02/14/2026", "12/25/2026"], "%m/%d/%Y"),
    (["05/01/2026", "14/02/2026", "25/12/2026"], "%d/%m/%Y"),
    (["05/01/26", "14/02/26", "25/12/26"], "%d/%m/%y"),
    (["January 5 2026", "February 14 2026", "December 25 2026"], "%B %d %Y"),
    (["5 Jan 2026", "14 Feb 2026", "25 Dec 2026"], "%d %b %Y"),
    (
        ["2026-01-05T09:30:00", "2026-02-14T14:20:00", "2026-12-25T16:30:00"],
        "%Y-%m-%dT%H:%M:%S",
    ),
    (
        ["2026-01-05 09:30:00", "2026-02-14 14:20:00", "2026-12-25 16:30:00"],
        "%Y-%m-%d %H:%M:%S",
    ),
    (
        ["01/05/2026 09:30 AM", "02/14/2026 02:20 PM", "12/25/2026 04:30 PM"],
        "%m/%d/%Y %I:%M %p",
    ),
    (
        ["05/01/2026 09:30", "14/02/2026 14:20", "25/12/2026 16:30"],
        "%d/%m/%Y %H:%M",
    ),
    (
        [
            "2026-01-05T09:30:00-03:00",
            "2026-02-14T14:20:00-03:00",
            "2026-12-25T16:30:00-03:00",
        ],
        "%Y-%m-%dT%H:%M:%S%z",
    ),
    # A year and a month name no day, so reading them as dates would invent one.
    (["2026-01", "2026-02", "2026-12"], None),
    (["Jan-2026", "Feb-2026", "Dec-2026"], None),
    (["1767616200", "1771093200", "1798227000"], None),
]


@pytest.mark.parametrize(("values", "expected"), TEST_COLUMNS)
def test_detect_date_format_on_test_columns(values, expected):
    assert detect_date_format(values) == expected


def test_detect_date_format_rejects_a_column_with_one_odd_value():
    # A single stray value is enough to disqualify a format, which is what
    # makes whole column validation worth doing. A shifted CSV row lands here.
    values = ["2026-01-05T09:30:00-03:00", "2026-02-14T14:20:00-03:00", "2026-12"]

    assert detect_date_format(values) is None


def test_detect_date_format_returns_none_for_unreadable_values():
    assert detect_date_format(["Q1 2020", "Q2 2020"]) is None


def test_detect_date_format_returns_none_for_an_empty_column():
    assert detect_date_format([None, ""]) is None


def test_infer_frequency_reads_a_daily_grid():
    dates = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"])

    assert infer_frequency(dates) == "D"


def test_infer_frequency_reads_a_monthly_grid():
    dates = pd.to_datetime(["2020-01-01", "2020-02-01", "2020-03-01"])

    assert infer_frequency(dates) == "MS"


def test_infer_frequency_falls_back_to_the_most_common_gap():
    dates = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-05", "2020-01-06"])

    assert infer_frequency(dates) == pd.Timedelta(days=1)


def test_infer_frequency_gives_up_on_too_few_dates():
    assert infer_frequency(pd.to_datetime(["2020-01-01"])) is None
