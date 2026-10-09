"""Structure estimates of converters that download pretrained models.

They cannot join the estimate-vs-runtime test (fitting loads the model), but
building them is cheap because the model is only loaded on fit, so their
`infer_output_columns` overrides are checked directly.
"""

import pytest

from DashAI.back.converters.hugging_face.embedding import Embedding
from DashAI.back.converters.hugging_face.image_embedding import (
    ImageEmbeddingConverter,
)
from DashAI.back.converters.hugging_face.tokenizer import TokenizerConverter
from DashAI.back.converters.segmentation.sam3_segment_converter import (
    SAM3SegmentConverter,
)
from DashAI.back.preprocessing.structure_types import BlockItem, ColumnItem
from DashAI.back.splitters.splits_payload import schema_placeholder_defaults


def _build(cls, **params):
    return cls(**{**schema_placeholder_defaults(cls), **params})


@pytest.mark.parametrize(
    ("cls", "type_name"),
    [(Embedding, "Float"), (TokenizerConverter, "Integer")],
)
def test_text_encoders_replace_the_text_with_one_block(cls, type_name):
    inputs = [ColumnItem(name="review", type="Text", dtype="string")]

    delta = _build(cls).infer_output_columns(inputs)

    assert delta.kept == []
    (block,) = delta.added
    assert isinstance(block, BlockItem)
    assert (block.type, block.count) == (type_name, None)


@pytest.mark.parametrize("keep_source", [True, False])
def test_image_embedding_keeps_the_source_only_when_asked(keep_source):
    inputs = [ColumnItem(name="photo", type="Image")]
    converter = _build(ImageEmbeddingConverter, keep_source_column=keep_source)

    delta = converter.infer_output_columns(inputs)

    assert delta.kept == (inputs if keep_source else [])
    (block,) = delta.added
    assert (block.type, block.count) == ("Float", None)


@pytest.mark.parametrize(
    ("keep_mask", "expected"),
    [
        (False, ["segment_1", "seg_score_1", "segment_2", "seg_score_2"]),
        (
            True,
            [
                "segment_1",
                "seg_score_1",
                "segment_2",
                "seg_score_2",
                "mask_1",
                "mask_2",
            ],
        ),
    ],
)
def test_sam3_names_one_column_set_per_rank(keep_mask, expected):
    inputs = [ColumnItem(name="photo", type="Image")]
    converter = _build(SAM3SegmentConverter, max_masks=2, keep_binary_mask=keep_mask)

    delta = converter.infer_output_columns(inputs)

    assert delta.kept == inputs
    assert [item.name for item in delta.added] == expected
    types = {item.name: item.type for item in delta.added}
    assert types["segment_1"] == "Image"
    assert types["seg_score_1"] == "Float"
