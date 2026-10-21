"""Tests for the block grouping helpers shared by the PDF loaders."""

from DashAI.back.dataloaders.classes.document_blocks import (
    block_element,
    body_size,
    document_body_size,
    heading_sizes,
    name_blocks,
    representative_size,
    split_blank_line_blocks,
)


def test_blank_line_split_drops_empty_and_whitespace_only_blocks():
    text = "First line\nstill first.\n\n   \n\nSecond.\n\n"
    assert split_blank_line_blocks(text) == ["First line\nstill first.", "Second."]


def test_blank_line_split_keeps_a_text_without_blank_lines_whole():
    assert split_blank_line_blocks("One.\nTwo.") == ["One.\nTwo."]


def test_blank_line_split_of_blank_text_has_no_blocks():
    assert split_blank_line_blocks("\n  \n") == []


def test_body_size_is_the_most_common_rounded_size():
    assert body_size([12.0, 12.04, 24.0, 11.97]) == 12.0


def test_body_size_without_sizes_is_none():
    assert body_size([]) is None
    assert representative_size([0]) is None


def test_heading_sizes_are_the_standout_sizes_largest_first():
    assert heading_sizes([12.0, 24.0, 16.0, 12.0], 12.0) == [24.0, 16.0]


def test_heading_sizes_without_a_body_size_are_empty():
    assert heading_sizes([24.0], None) == []


def test_a_size_within_the_body_ratio_is_not_a_heading():
    assert heading_sizes([13.0], 12.0) == []


def test_block_element_levels_follow_the_rank_of_the_size():
    ranked = [24.0, 16.0]
    assert block_element("Title", 24.0, 12.0, ranked) == ("heading", {"level": 1})
    assert block_element("Section", 16.0, 12.0, ranked) == ("heading", {"level": 2})
    assert block_element("Body", 12.0, 12.0, ranked) == ("paragraph", {})


def test_a_long_block_is_a_paragraph_however_large_its_font():
    text = "\n".join(["line"] * 4)
    assert block_element(text, 24.0, 12.0, [24.0]) == ("paragraph", {})


def test_block_element_without_a_size_is_a_paragraph():
    assert block_element("Text", None, 12.0, [24.0]) == ("paragraph", {})


def test_name_blocks_takes_the_body_size_from_the_longest_blocks():
    blocks = [
        ("Heading", 24.0),
        ("Three\nlines\nhere.", 12.0),
        ("Another one.", 12.0),
    ]
    assert name_blocks(blocks) == [
        ("heading", {"level": 1}),
        ("paragraph", {}),
        ("paragraph", {}),
    ]


def test_name_blocks_of_a_single_size_document_finds_no_heading():
    blocks = [("One.", 12.0), ("Two.", 12.0)]
    assert name_blocks(blocks) == [("paragraph", {}), ("paragraph", {})]


def test_body_size_counts_characters_not_lines():
    blocks = [
        ("Four\nlines\nof\nbig text", 24.0),
        ("We drew 400 cases.\nEach case was weighted.\nResults follow.", 12.0),
    ]
    assert document_body_size(blocks) == 12.0


def test_body_size_of_blocks_without_a_size_is_none():
    assert document_body_size([("Text", None)]) is None


def test_a_large_title_block_does_not_pass_as_the_body_size():
    blocks = [
        ("Chapter 1", 24.0),
        ("Sampling", 16.0),
        ("We drew 400 cases.\nEach case was weighted.\nResults follow.", 12.0),
        ("Four\nlines\nof\nbig text", 24.0),
    ]
    assert [kind for kind, _ in name_blocks(blocks)] == [
        "heading",
        "heading",
        "paragraph",
        "paragraph",
    ]
    assert name_blocks(blocks)[0][1] == {"level": 1}
    assert name_blocks(blocks)[1][1] == {"level": 2}
