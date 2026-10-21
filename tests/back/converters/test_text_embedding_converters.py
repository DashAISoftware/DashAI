"""Text embedding converters encode text with one pretrained model each."""

import numpy as np
import pyarrow as pa
import pytest

from DashAI.back.converters.hugging_face.text_embedding import (
    TEXT_EMBEDDING_CONVERTERS,
    AllMiniLML6V2Embedding,
    InstructorLargeEmbedding,
    MultilingualE5SmallEmbedding,
    Qwen3Embedding06B,
    TextEmbeddingConverter,
)
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.dependencies.config_builder import get_initial_components
from DashAI.back.types.value_types import Float, Text
from tests.back.converters.text_embedding_stub import with_fake_model


def _dataset(values):
    return DashAIDataset(
        pa.table({"review": pa.array(values, type=pa.string())}),
        types={"review": Text(arrow_type=pa.string())},
    )


def test_e5_prefixes_queries_and_passages():
    converter = MultilingualE5SmallEmbedding()
    model = with_fake_model(converter)

    converter.encode(["hola"], role="query")
    converter.encode(["hola"], role="passage")

    assert [call["prompt"] for call in model.calls] == ["query: ", "passage: "]


def test_qwen3_prompts_only_queries():
    converter = Qwen3Embedding06B()
    model = with_fake_model(converter)

    converter.encode(["x"], role="query")
    converter.encode(["x"], role="passage")

    assert model.calls[0]["prompt"].startswith("Instruct: Given a web search query")
    assert model.calls[1]["prompt"] is None


def test_plain_models_never_prompt():
    converter = AllMiniLML6V2Embedding()
    model = with_fake_model(converter)

    converter.encode(["x"], role="query")
    converter.encode(["x"], role="passage")

    assert [call["prompt"] for call in model.calls] == [None, None]


def test_instructor_uses_its_instruction_for_both_roles():
    converter = InstructorLargeEmbedding(instruction="Represent the law:")
    model = with_fake_model(converter)

    converter.encode(["x"], role="query")
    converter.encode(["x"], role="passage")

    assert [call["prompt"] for call in model.calls] == [
        "Represent the law:",
        "Represent the law:",
    ]
    assert converter.params["instruction"] == "Represent the law:"


def test_an_unknown_role_is_rejected():
    converter = AllMiniLML6V2Embedding()
    with_fake_model(converter)

    with pytest.raises(ValueError, match="role"):
        converter.encode(["x"], role="document")


def test_normalize_controls_the_vector_length():
    normalized = AllMiniLML6V2Embedding(normalize=True)
    with_fake_model(normalized)
    raw = AllMiniLML6V2Embedding(normalize=False)
    with_fake_model(raw)

    lengths = np.linalg.norm(normalized.encode(["a", "b"]), axis=1)
    raw_lengths = np.linalg.norm(raw.encode(["a", "b"]), axis=1)

    assert np.allclose(lengths, 1.0)
    assert not np.allclose(raw_lengths, 1.0)


def test_aggregate_encodes_long_text_in_windows_and_averages():
    converter = AllMiniLML6V2Embedding(overflow_strategy="aggregate")
    model = with_fake_model(converter, max_seq_length=6)
    text = " ".join(f"w{index}" for index in range(10))

    vectors = converter.encode([text, "short text"])

    assert model.calls[0]["sentences"] == [
        "w0 w1 w2 w3",
        "w4 w5 w6 w7",
        "w8 w9",
        "short text",
    ]
    assert vectors.shape == (2, 8)
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0)


def test_truncate_encodes_each_text_once():
    converter = AllMiniLML6V2Embedding(overflow_strategy="truncate")
    model = with_fake_model(converter, max_seq_length=6)
    text = " ".join(f"w{index}" for index in range(10))

    converter.encode([text])

    assert model.calls[0]["sentences"] == [text]


def test_empty_input_gives_an_empty_matrix():
    converter = AllMiniLML6V2Embedding()
    with_fake_model(converter)

    assert converter.encode([]).shape == (0, 8)


def test_transform_replaces_text_columns_with_float_columns():
    converter = AllMiniLML6V2Embedding()
    with_fake_model(converter)
    data = _dataset(["good movie", None, ""])

    result = converter.fit(data).transform(data)

    assert result.column_names == [f"emb_review_{index}" for index in range(8)]
    assert len(result) == 3
    assert all(isinstance(result.types[name], Float) for name in result.column_names)
    assert result.arrow_table.column("emb_review_0").type == pa.float32()


def test_fit_rejects_non_text_columns():
    converter = AllMiniLML6V2Embedding()
    data = DashAIDataset(
        pa.table({"n": pa.array([1.0, 2.0], type=pa.float64())}),
        types={"n": Float(arrow_type=pa.float64())},
    )

    with pytest.raises(ValueError, match="text"):
        converter.fit(data)


def test_the_fourteen_models_are_registered_dataset_only():
    registered = [
        component
        for component in get_initial_components()
        if isinstance(component, type) and issubclass(component, TextEmbeddingConverter)
    ]

    assert sorted(c.__name__ for c in registered) == sorted(
        c.__name__ for c in TEXT_EMBEDDING_CONVERTERS
    )
    assert len(TEXT_EMBEDDING_CONVERTERS) == 14
    assert len({c.MODEL_NAME for c in TEXT_EMBEDDING_CONVERTERS}) == 14
    for component in TEXT_EMBEDDING_CONVERTERS:
        assert component.REQUIRES_DOWNLOAD
        assert component.DOWNLOAD_SIZE_BYTES > 0
        assert component.get_metadata()["data_kinds"] == ["dataset"]
