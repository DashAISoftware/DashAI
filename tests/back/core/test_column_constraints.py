from DashAI.back.core.column_constraints import columns_satisfy_metadata

TEXT_ONLY = {
    "allowed_types": ["Text"],
    "allowed_dtypes": [],
    "non_allowed_dtypes": [],
    "input_cardinality": {"min": 1},
}
DOCUMENT_SPEC = {
    "Text": {"type": "Text", "dtype": "string"},
    "Image": {"type": "Image", "dtype": "struct"},
}


def test_a_text_tool_accepts_document_text():
    assert columns_satisfy_metadata(TEXT_ONLY, ["Text"], DOCUMENT_SPEC)


def test_a_text_tool_refuses_document_images():
    assert not columns_satisfy_metadata(TEXT_ONLY, ["Image"], DOCUMENT_SPEC)


def test_cardinality_counts_content_types():
    metadata = {**TEXT_ONLY, "allowed_types": [], "input_cardinality": {"exact": 1}}
    assert not columns_satisfy_metadata(metadata, ["Text", "Image"], DOCUMENT_SPEC)


def test_the_dtype_blacklist_applies():
    metadata = {**TEXT_ONLY, "allowed_types": [], "non_allowed_dtypes": ["struct"]}
    assert not columns_satisfy_metadata(metadata, ["Image"], DOCUMENT_SPEC)


def test_an_empty_selection_fails_the_default_minimum():
    assert not columns_satisfy_metadata(TEXT_ONLY, [], DOCUMENT_SPEC)
