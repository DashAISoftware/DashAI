import pyarrow as pa
import pytest

from DashAI.back.converters.hugging_face.translation import (
    TRANSLATION_CONVERTERS,
    OpusMtEnEsTranslator,
    OpusMtEnRoaTranslator,
    OpusMtEnZhTranslator,
)
from DashAI.back.converters.hugging_face.translation.base import (
    LINE_BREAK,
    SENTENCE_BREAK,
    split_keeping_separators,
)
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.dataloaders.classes.document_items import (
    ItemFilter,
    apply_converter_to_document,
)
from DashAI.back.types.value_types import Text
from tests.back.document_fixtures import build_document, image, text


class FakeTranslator(OpusMtEnEsTranslator):
    """Counts words as tokens and upper cases each piece it translates."""

    def __init__(self, limit=128, identity=False, **kwargs):
        super().__init__(**kwargs)
        self.MAX_INPUT_TOKENS = limit
        self.identity = identity
        self.pieces = []

    def count_tokens(self, value):
        return len(value.split())

    def translate_pieces(self, pieces):
        self.pieces.extend(pieces)
        return list(pieces) if self.identity else [p.upper() for p in pieces]


def _texts(values):
    table = pa.table({"text": pa.array(values, type=pa.string())})
    return DashAIDataset(table, types={"text": Text(arrow_type=pa.string())})


MESSY = (
    "  Title line  \n"
    "-----\n"
    "\n"
    "First sentence here. Second one!  Third?\n"
    "\r\n"
    "中文第一句。中文第二句！\n"
    "tail"
)


@pytest.mark.parametrize("split_by", ["whole", "paragraphs", "lines", "sentences"])
@pytest.mark.parametrize("limit", [128, 3, 1])
def test_putting_the_pieces_back_rebuilds_the_text(split_by, limit):
    translator = FakeTranslator(limit=limit, identity=True, split_by=split_by)
    assert translator.convert_text(MESSY) == MESSY


def test_missing_and_letterless_values_never_reach_the_model():
    translator = FakeTranslator()
    data = _texts(["hello there", None, "", "   ", "42 - 7", "ok"])
    result = translator.fit(data).transform(data)
    assert result.arrow_table.column("text").to_pylist() == [
        "HELLO THERE",
        None,
        "",
        "   ",
        "42 - 7",
        "OK",
    ]
    assert translator.pieces == ["hello there", "ok"]
    assert isinstance(result.types["text"], Text)


def test_a_whole_value_is_one_piece_and_keeps_its_edge_spacing():
    translator = FakeTranslator()
    assert translator.convert_text("  one line\nand another  \n") == (
        "  ONE LINE\nAND ANOTHER  \n"
    )
    assert translator.pieces == ["one line\nand another"]


def test_lines_are_translated_one_by_one_and_letterless_lines_kept():
    translator = FakeTranslator(split_by="lines")
    result = translator.convert_text("Heading\n=====\n  body text  \r\nend")
    assert result == "HEADING\n=====\n  BODY TEXT  \r\nEND"
    assert translator.pieces == ["Heading", "body text", "end"]


def test_paragraphs_keep_their_inner_line_breaks_in_one_piece():
    translator = FakeTranslator(split_by="paragraphs")
    translator.convert_text("a b\nc d\n\n  \ne f")
    assert translator.pieces == ["a b\nc d", "e f"]


def test_sentences_split_after_latin_and_chinese_punctuation():
    translator = FakeTranslator(split_by="sentences")
    translator.convert_text("One. Two! Three?\n第一句。第二句！")
    assert translator.pieces == ["One.", "Two!", "Three?", "第一句。", "第二句！"]


def test_a_value_too_long_for_the_model_is_cut_by_lines_then_sentences():
    translator = FakeTranslator(limit=4)
    translator.convert_text("short line\na b c. d e f. g h\nlast")
    assert translator.pieces == ["short line", "a b c.", "d e f.", "g h", "last"]


def test_a_sentence_too_long_for_the_model_is_packed_by_words():
    translator = FakeTranslator(limit=3)
    result = translator.convert_text("a b c d e f g")
    assert translator.pieces == ["a b c", "d e f", "g"]
    assert result == "A B C D E F G"


def test_a_word_too_long_for_the_model_is_cut_into_slices():
    class CharTokens(FakeTranslator):
        def count_tokens(self, value):
            return len(value)

    translator = CharTokens(limit=4, identity=True)
    assert translator.convert_text("abcdefghij xy") == "abcdefghij xy"
    assert translator.pieces == ["abcd", "efgh", "ij", "xy"]


def test_splitting_keeps_separators_at_odd_positions():
    parts = split_keeping_separators("A. B\nC", [LINE_BREAK, SENTENCE_BREAK])
    assert parts == ["A.", " ", "B", "\n", "C"]


def test_document_items_are_translated_in_place_with_a_table_cell_by_cell():
    document = build_document(
        [
            text("Title", kind="heading", level=1),
            text("line one\nline two"),
            image(),
            text("a | b", kind="table", rows=[["a", "b"]], header=False),
        ]
    )
    converted = apply_converter_to_document(
        document,
        lambda: FakeTranslator(split_by="lines"),
        {"Text": ItemFilter()},
    )
    items = [item for item in converted.items() if item.type is Text]
    assert [item.content for item in items[:2]] == ["TITLE", "LINE ONE\nLINE TWO"]
    assert items[2].attrs["rows"] == [["A", "B"]]
    assert [item.kind for item in items] == ["heading", "paragraph", "table"]
    assert len(converted.items()) == 4


def test_an_unknown_split_option_is_refused():
    with pytest.raises(ValueError, match="split_by"):
        OpusMtEnEsTranslator(split_by="words")


def test_multi_target_opus_models_put_the_language_token_first():
    assert OpusMtEnRoaTranslator().source_prefix() == ">>por<< "
    assert OpusMtEnRoaTranslator(target_language="ita").source_prefix() == (">>ita<< ")
    assert OpusMtEnZhTranslator().source_prefix() == ">>cmn_Hans<< "
    with pytest.raises(ValueError, match="cannot translate into"):
        OpusMtEnRoaTranslator(target_language="deu")


def test_every_translator_downloads_its_own_model_and_works_on_both_kinds():
    repos = set()
    for component in TRANSLATION_CONVERTERS:
        metadata = component.get_metadata()
        assert metadata["requires_download"] is True, component.__name__
        assert metadata["download_size_bytes"] > 100_000_000, component.__name__
        assert metadata["data_kinds"] == ["dataset", "document"], component.__name__
        assert component.hf_repos() == [(component.MODEL_NAME, "model")]
        repos.add(component.MODEL_NAME)
    assert len(repos) == len(TRANSLATION_CONVERTERS)


def test_the_target_language_comes_before_the_shared_options():
    assert list(OpusMtEnRoaTranslator.get_schema()["properties"]) == [
        "target_language",
        "split_by",
        "batch_size",
        "device",
    ]
