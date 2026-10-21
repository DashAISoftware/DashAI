import pyarrow as pa
import pytest

from DashAI.back.converters.simple_converters.regex_replacer import RegexReplacer
from DashAI.back.converters.simple_converters.text_cleaner import TextCleaner
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.dataloaders.classes.document_items import (
    ItemFilter,
    apply_converter_to_document,
)
from DashAI.back.types.value_types import Integer, Text
from tests.back.document_fixtures import build_document, text


def _dataset(values, extra=None):
    columns = {"text": pa.array(values, type=pa.string())}
    types = {"text": Text(arrow_type=pa.string())}
    if extra is not None:
        columns["number"] = pa.array(extra, type=pa.int64())
        types["number"] = Integer(arrow_type=pa.int64())
    return DashAIDataset(pa.table(columns), types=types)


def _run(converter, values):
    data = _dataset(values)
    return converter.fit(data).transform(data).arrow_table.column("text").to_pylist()


def test_the_cleaner_runs_every_step_by_default():
    raw = "  The ﬁrst exam-\nple​  has   spaces \n\n\n\nEnd\x07.  "
    assert _run(TextCleaner(), [raw]) == ["The first example has spaces\n\nEnd."]


def test_each_cleaning_step_can_be_turned_off():
    cleaner = TextCleaner(
        normalize_unicode=False,
        join_hyphenated=False,
        remove_control_characters=False,
        collapse_whitespace=False,
    )
    raw = " ﬁ exam-\nple​  "
    assert _run(cleaner, [raw]) == [raw]


def test_the_cleaner_keeps_line_breaks_and_tabs_inside_lines():
    assert _run(TextCleaner(), ["a\tb\nc"]) == ["a b\nc"]
    assert _run(TextCleaner(collapse_whitespace=False), ["a\tb\nc"]) == ["a\tb\nc"]


def test_missing_values_and_other_columns_are_left_alone():
    data = _dataset([" a ", None], extra=[1, 2])
    result = TextCleaner().fit(data).transform(data)
    assert result.arrow_table.column("text").to_pylist() == ["a", None]
    assert result.arrow_table.column("number").to_pylist() == [1, 2]
    assert isinstance(result.types["number"], Integer)
    assert isinstance(result.types["text"], Text)


def test_the_cleaner_rewrites_document_table_cells():
    table = text(" a  b\t\x07c", kind="table", rows=[[" a  b", "\x07c"]])
    converted = apply_converter_to_document(
        build_document([table]), TextCleaner, {"Text": ItemFilter()}
    )
    item = converted.items()[0]
    assert item.attrs["rows"] == [["a b", "c"]]
    assert item.content == "a b\tc"


@pytest.mark.parametrize(
    ("preset", "raw", "expected"),
    [
        ("Email addresses", "mail ana.b+x@uc.cl now", "mail [X] now"),
        ("URLs", "see https://dash.ai/docs?a=1 and www.x.org.", "see [X] and [X]"),
        ("Phone numbers", "call +56 9 1234 5678 today", "call [X] today"),
        ("Numbers", "page 12 of 3.5 and v2", "page [X] of [X] and v2"),
    ],
)
def test_presets_redact_their_matches(preset, raw, expected):
    assert _run(RegexReplacer(preset=preset, replacement="[X]"), [raw]) == [expected]


def test_a_custom_pattern_can_use_groups_and_ignore_case():
    converter = RegexReplacer(
        pattern=r"(\w+)@example\.com", replacement=r"\1@hidden", ignore_case=True
    )
    assert _run(converter, ["Ana@EXAMPLE.com"]) == ["Ana@hidden"]


def test_an_empty_replacement_removes_the_matches():
    assert _run(RegexReplacer(pattern=r"\s*\[\d+\]"), ["text [1] more [22]"]) == [
        "text more"
    ]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"pattern": None}, "Write a pattern"),
        ({"pattern": "("}, "not valid"),
        ({"pattern": "a*"}, "matches empty text"),
        ({"pattern": r"\b"}, "matches empty text"),
        ({"preset": "Planets"}, "Unknown preset"),
    ],
)
def test_bad_patterns_are_refused(kwargs, message):
    with pytest.raises(ValueError, match=message):
        RegexReplacer(**kwargs)


def test_a_replacement_with_a_missing_group_is_refused_when_used():
    converter = RegexReplacer(pattern="a", replacement=r"\2")
    with pytest.raises(ValueError, match="replacement"):
        _run(converter, ["a"])


def test_both_converters_run_on_datasets_and_documents():
    for converter in (TextCleaner, RegexReplacer):
        metadata = converter.get_metadata()
        assert metadata["data_kinds"] == ["dataset", "document"]
        assert metadata["allowed_types"] == ["Text"]
        assert metadata["learns_from_data"] is False
