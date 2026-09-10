"""Unit tests for RAGPipeline and RAGPipelineConfig.

Tests the configuration parsing (RAGPipelineConfig.from_kwargs) and the
pipeline's generate() method using mocks for retriever, prompt, and LLM.

These tests do NOT require a database connection for the config tests.
The generate() tests use MagicMock for all dependencies.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from DashAI.back.models.RAG.documents.chunk import Chunk
from DashAI.back.models.RAG.exceptions import (
    RAGPipelineConfigError,
    RAGPipelineInputError,
    RAGPipelineRuntimeError,
)
from DashAI.back.models.RAG.RAG_constants import RAG_INFRA_KEYS
from DashAI.back.models.RAG.RAG_pipeline import (
    ChunkReference,
    ModelRef,
    RAGGenerationOutput,
    RAGPipeline,
    RAGPipelineConfig,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _valid_kwargs(**overrides) -> dict:
    """Build a minimal valid kwargs dict for RAGPipelineConfig.from_kwargs()."""
    base = {
        "session_id": 1,
        "db": MagicMock(),
        "component_registry": MagicMock(),
        "env_RAG_path": "/tmp/rag",
        "documents": [10, 20],
        "prompt": {
            "component": "DefaultRAGGenerationPrompt",
            "params": {"language": "en"},
        },
        "chunking_model": {
            "component": "CharacterChunkModel",
            "params": {"chunk_size": 200},
        },
        "retriever_model": {"component": "BM25Retriever", "params": {"top_k": 5}},
        "generation_model": {"component": "StubLLM", "params": {}},
    }
    base.update(overrides)
    return base


def _make_pipeline(
    documents=None,
    retriever=None,
    prompt_model=None,
    llm_model=None,
    chunks=None,
) -> RAGPipeline:
    """Build a RAGPipeline with mock dependencies for generate() tests."""
    config = MagicMock(spec=RAGPipelineConfig)
    config.session_id = 1
    config.documents = [1, 2]

    if documents is None:
        doc1 = MagicMock()
        doc1.file_name = "doc1.txt"
        doc2 = MagicMock()
        doc2.file_name = "doc2.txt"
        documents = {1: doc1, 2: doc2}

    if retriever is None:
        retriever = MagicMock()
        retriever.retrieve.return_value = []

    if prompt_model is None:
        prompt_model = MagicMock()
        prompt_model.format.return_value = "formatted prompt"

    if llm_model is None:
        llm_model = MagicMock()
        llm_model.generate.return_value = ["stub answer"]

    if chunks is None:
        chunks = {}

    return RAGPipeline(
        config=config,
        pipeline_id=100,
        chunking_model_id=200,
        documents=documents,
        chunks=chunks,
        prompt_model=prompt_model,
        chunking_model=MagicMock(),
        retriever=retriever,
        llm_model=llm_model,
    )


# ===================================================================
# RAGPipelineConfig.from_kwargs() — missing infrastructure keys
# ===================================================================


class TestRAGPipelineConfigMissingInfraKeys:
    """Verify that missing infrastructure keys raise RAGPipelineConfigError."""

    def test_missing_session_id(self):
        """Missing 'session_id' → RAGPipelineConfigError."""
        kwargs = _valid_kwargs()
        del kwargs["session_id"]
        with pytest.raises(RAGPipelineConfigError, match="Missing required parameters"):
            RAGPipelineConfig.from_kwargs(**kwargs)

    def test_missing_db(self):
        """Missing 'db' → RAGPipelineConfigError."""
        kwargs = _valid_kwargs()
        del kwargs["db"]
        with pytest.raises(RAGPipelineConfigError, match="Missing required parameters"):
            RAGPipelineConfig.from_kwargs(**kwargs)

    def test_missing_component_registry(self):
        """Missing 'component_registry' → RAGPipelineConfigError."""
        kwargs = _valid_kwargs()
        del kwargs["component_registry"]
        with pytest.raises(RAGPipelineConfigError, match="Missing required parameters"):
            RAGPipelineConfig.from_kwargs(**kwargs)

    def test_missing_env_rag_path(self):
        """Missing 'env_RAG_path' → RAGPipelineConfigError."""
        kwargs = _valid_kwargs()
        del kwargs["env_RAG_path"]
        with pytest.raises(RAGPipelineConfigError, match="Missing required parameters"):
            RAGPipelineConfig.from_kwargs(**kwargs)

    def test_missing_all_infra_keys(self):
        """Missing all infra keys → RAGPipelineConfigError listing all of them."""
        kwargs = _valid_kwargs()
        for key in RAG_INFRA_KEYS:
            del kwargs[key]
        with pytest.raises(RAGPipelineConfigError, match="Missing required parameters"):
            RAGPipelineConfig.from_kwargs(**kwargs)


# ===================================================================
# RAGPipelineConfig.from_kwargs() — missing model keys
# ===================================================================


class TestRAGPipelineConfigMissingModelKeys:
    """Verify that missing model keys raise RAGPipelineConfigError."""

    def test_missing_prompt(self):
        """Missing 'prompt' → RAGPipelineConfigError."""
        kwargs = _valid_kwargs()
        del kwargs["prompt"]
        with pytest.raises(RAGPipelineConfigError, match="Missing required parameters"):
            RAGPipelineConfig.from_kwargs(**kwargs)

    def test_missing_chunking_model(self):
        """Missing 'chunking_model' → RAGPipelineConfigError."""
        kwargs = _valid_kwargs()
        del kwargs["chunking_model"]
        with pytest.raises(RAGPipelineConfigError, match="Missing required parameters"):
            RAGPipelineConfig.from_kwargs(**kwargs)

    def test_missing_retriever_model(self):
        """Missing 'retriever_model' → RAGPipelineConfigError."""
        kwargs = _valid_kwargs()
        del kwargs["retriever_model"]
        with pytest.raises(RAGPipelineConfigError, match="Missing required parameters"):
            RAGPipelineConfig.from_kwargs(**kwargs)

    def test_missing_generation_model(self):
        """Missing 'generation_model' → RAGPipelineConfigError."""
        kwargs = _valid_kwargs()
        del kwargs["generation_model"]
        with pytest.raises(RAGPipelineConfigError, match="Missing required parameters"):
            RAGPipelineConfig.from_kwargs(**kwargs)


# ===================================================================
# RAGPipelineConfig.from_kwargs() — malformed model refs
# ===================================================================


class TestRAGPipelineConfigMalformedModelRefs:
    """Verify that malformed model references raise RAGPipelineConfigError."""

    def test_model_ref_not_a_dict(self):
        """Model ref that is a string (not dict) → RAGPipelineConfigError."""
        kwargs = _valid_kwargs(prompt="not_a_dict")
        with pytest.raises(RAGPipelineConfigError, match="must be a dict"):
            RAGPipelineConfig.from_kwargs(**kwargs)

    def test_model_ref_is_list(self):
        """Model ref that is a list → RAGPipelineConfigError."""
        kwargs = _valid_kwargs(retriever_model=[1, 2, 3])
        with pytest.raises(RAGPipelineConfigError, match="must be a dict"):
            RAGPipelineConfig.from_kwargs(**kwargs)

    def test_model_ref_missing_component_key(self):
        """Model ref dict without 'component' → RAGPipelineConfigError."""
        kwargs = _valid_kwargs(prompt={"params": {"language": "en"}})
        with pytest.raises(RAGPipelineConfigError, match="Missing 'component'"):
            RAGPipelineConfig.from_kwargs(**kwargs)

    def test_model_ref_missing_params_key(self):
        """Model ref dict without 'params' → RAGPipelineConfigError."""
        kwargs = _valid_kwargs(chunking_model={"component": "CharacterChunkModel"})
        with pytest.raises(RAGPipelineConfigError, match="Missing 'params'"):
            RAGPipelineConfig.from_kwargs(**kwargs)


# ===================================================================
# RAGPipelineConfig.from_kwargs() — unknown/extra parameters
# ===================================================================


class TestRAGPipelineConfigExtraKeys:
    """Verify that extra/unknown keys raise RAGPipelineConfigError."""

    def test_extra_key_raises(self):
        """An unknown key in kwargs → RAGPipelineConfigError."""
        kwargs = _valid_kwargs(prompt_id=42)
        with pytest.raises(RAGPipelineConfigError, match="Unknown parameters"):
            RAGPipelineConfig.from_kwargs(**kwargs)

    def test_multiple_extra_keys(self):
        """Multiple unknown keys → RAGPipelineConfigError listing them."""
        kwargs = _valid_kwargs(foo="bar", baz=123)
        with pytest.raises(RAGPipelineConfigError, match="Unknown parameters"):
            RAGPipelineConfig.from_kwargs(**kwargs)


# ===================================================================
# RAGPipelineConfig.from_kwargs() — valid kwargs
# ===================================================================


class TestRAGPipelineConfigValid:
    """Verify that valid kwargs produce a correct RAGPipelineConfig."""

    def test_valid_kwargs_returns_config(self):
        """All required keys present → returns RAGPipelineConfig."""
        kwargs = _valid_kwargs()
        config = RAGPipelineConfig.from_kwargs(**kwargs)
        assert isinstance(config, RAGPipelineConfig)
        assert config.session_id == 1
        assert config.documents == [10, 20]
        assert config.env_RAG_path == "/tmp/rag"

    def test_model_refs_parsed_correctly(self):
        """Model refs are parsed into ModelRef dataclass instances."""
        kwargs = _valid_kwargs()
        config = RAGPipelineConfig.from_kwargs(**kwargs)
        assert isinstance(config.prompt, ModelRef)
        assert config.prompt.component == "DefaultRAGGenerationPrompt"
        assert config.prompt.params == {"language": "en"}
        assert isinstance(config.chunking_model, ModelRef)
        assert config.chunking_model.component == "CharacterChunkModel"
        assert isinstance(config.retriever_model, ModelRef)
        assert config.retriever_model.component == "BM25Retriever"
        assert isinstance(config.generation_model, ModelRef)
        assert config.generation_model.component == "StubLLM"


# ===================================================================
# RAGPipeline.generate() — input validation
# ===================================================================


class TestRAGPipelineGenerateInputValidation:
    """Verify that generate() rejects invalid inputs."""

    def test_empty_input_data(self):
        """Empty tuple → RAGPipelineInputError."""
        pipeline = _make_pipeline()
        with pytest.raises(RAGPipelineInputError, match="must not be empty"):
            pipeline.generate(())

    def test_empty_list_input(self):
        """Empty list → RAGPipelineInputError."""
        pipeline = _make_pipeline()
        with pytest.raises(RAGPipelineInputError, match="must not be empty"):
            pipeline.generate([])

    def test_malformed_input_missing_content_key(self):
        """Dict without 'content' key → RAGPipelineInputError."""
        pipeline = _make_pipeline()
        with pytest.raises(RAGPipelineInputError, match="Malformed input_data"):
            pipeline.generate(({"role": "user", "text": "hello"},))

    def test_input_data_none(self):
        """None input → RAGPipelineInputError (TypeError caught)."""
        pipeline = _make_pipeline()
        with pytest.raises(RAGPipelineInputError):
            pipeline.generate(None)

    def test_input_data_wrong_type(self):
        """String input (not tuple of dicts) → RAGPipelineInputError."""
        pipeline = _make_pipeline()
        with pytest.raises(RAGPipelineInputError):
            pipeline.generate("not a tuple")


# ===================================================================
# RAGPipeline.generate() — runtime errors
# ===================================================================


class TestRAGPipelineGenerateRuntimeErrors:
    """Verify that generate() wraps runtime failures correctly."""

    def test_retriever_raises_exception(self):
        """Retriever failure → RAGPipelineRuntimeError."""
        retriever = MagicMock()
        retriever.retrieve.side_effect = RuntimeError("index corrupted")
        pipeline = _make_pipeline(retriever=retriever)
        with pytest.raises(RAGPipelineRuntimeError, match="retrieval"):
            pipeline.generate(({"role": "user", "content": "hello"},))

    def test_document_id_not_in_pipeline_documents(self):
        """Retrieved chunk references unknown document → RAGPipelineRuntimeError."""
        chunk = Chunk(id=1, document_id=999, document_position=0, text="orphan")
        retriever = MagicMock()
        retriever.retrieve.return_value = [chunk]
        pipeline = _make_pipeline(retriever=retriever)
        with pytest.raises(RAGPipelineRuntimeError, match="not found"):
            pipeline.generate(({"role": "user", "content": "hello"},))

    def test_prompt_format_raises_exception(self):
        """Prompt formatting failure → RAGPipelineRuntimeError."""
        chunk = Chunk(id=1, document_id=1, document_position=0, text="text")
        retriever = MagicMock()
        retriever.retrieve.return_value = [chunk]
        prompt_model = MagicMock()
        prompt_model.format.side_effect = ValueError("bad template")
        pipeline = _make_pipeline(retriever=retriever, prompt_model=prompt_model)
        with pytest.raises(RAGPipelineRuntimeError, match="prompt formatting"):
            pipeline.generate(({"role": "user", "content": "hello"},))

    def test_llm_returns_empty_output(self):
        """LLM returns empty list → RAGPipelineRuntimeError."""
        retriever = MagicMock()
        retriever.retrieve.return_value = []
        llm = MagicMock()
        llm.generate.return_value = []
        pipeline = _make_pipeline(retriever=retriever, llm_model=llm)
        with pytest.raises(RAGPipelineRuntimeError, match="empty output"):
            pipeline.generate(({"role": "user", "content": "hello"},))

    def test_llm_returns_non_string_output(self):
        """LLM returns non-string → RAGPipelineRuntimeError."""
        retriever = MagicMock()
        retriever.retrieve.return_value = []
        llm = MagicMock()
        llm.generate.return_value = [42]  # int, not str
        pipeline = _make_pipeline(retriever=retriever, llm_model=llm)
        with pytest.raises(RAGPipelineRuntimeError, match="not a string"):
            pipeline.generate(({"role": "user", "content": "hello"},))

    def test_llm_raises_exception(self):
        """LLM raises exception → RAGPipelineRuntimeError."""
        retriever = MagicMock()
        retriever.retrieve.return_value = []
        llm = MagicMock()
        llm.generate.side_effect = RuntimeError("OOM")
        pipeline = _make_pipeline(retriever=retriever, llm_model=llm)
        with pytest.raises(RAGPipelineRuntimeError, match="LLM generation"):
            pipeline.generate(({"role": "user", "content": "hello"},))


# ===================================================================
# RAGPipeline.generate() — happy path
# ===================================================================


class TestRAGPipelineGenerateHappyPath:
    """Verify the happy path of generate()."""

    def test_returns_correct_output(self):
        """Happy path: returns RAGGenerationOutput with message and chunks."""
        chunk = Chunk(id=1, document_id=1, document_position=0, text="hello world")
        retriever = MagicMock()
        retriever.retrieve.return_value = [chunk]
        prompt_model = MagicMock()
        prompt_model.format.return_value = "formatted"
        llm = MagicMock()
        llm.generate.return_value = ["the answer"]
        pipeline = _make_pipeline(
            retriever=retriever,
            prompt_model=prompt_model,
            llm_model=llm,
        )
        result = pipeline.generate(({"role": "user", "content": "what is DashAI?"},))
        assert isinstance(result, RAGGenerationOutput)
        assert result.message == "the answer"
        assert "1_0" in result.chunks
        ref = result.chunks["1_0"]
        assert isinstance(ref, ChunkReference)
        assert ref.document_id == 1
        assert ref.document_name == "doc1.txt"
        assert ref.document_position == 0
        assert ref.text == "hello world"

    def test_history_passed_to_llm(self):
        """History (input_data[:-1]) is forwarded to the LLM as prior messages."""
        retriever = MagicMock()
        retriever.retrieve.return_value = []
        prompt_model = MagicMock()
        prompt_model.format.return_value = "formatted prompt"
        llm = MagicMock()
        llm.generate.return_value = ["answer"]
        pipeline = _make_pipeline(
            retriever=retriever,
            prompt_model=prompt_model,
            llm_model=llm,
        )
        input_data = (
            {"role": "user", "content": "first question"},
            {"role": "assistant", "content": "first answer"},
            {"role": "user", "content": "follow-up question"},
        )
        pipeline.generate(input_data)
        # The LLM should receive history + formatted user message
        call_args = llm.generate.call_args[0][0]
        assert len(call_args) == 3  # 2 history + 1 current
        assert call_args[0] == {"role": "user", "content": "first question"}
        assert call_args[1] == {"role": "assistant", "content": "first answer"}
        assert call_args[2]["role"] == "user"
        assert call_args[2]["content"] == "formatted prompt"

    def test_empty_chunks_returns_empty_dict(self):
        """When retriever returns no chunks, chunks dict is empty."""
        retriever = MagicMock()
        retriever.retrieve.return_value = []
        llm = MagicMock()
        llm.generate.return_value = ["answer with no context"]
        pipeline = _make_pipeline(retriever=retriever, llm_model=llm)
        result = pipeline.generate(({"role": "user", "content": "hello"},))
        assert result.chunks == {}
        assert result.message == "answer with no context"

    def test_multiple_chunks_from_different_documents(self):
        """Multiple chunks from different documents are correctly referenced."""
        chunk1 = Chunk(id=1, document_id=1, document_position=0, text="chunk A")
        chunk2 = Chunk(id=2, document_id=2, document_position=1, text="chunk B")
        retriever = MagicMock()
        retriever.retrieve.return_value = [chunk1, chunk2]
        llm = MagicMock()
        llm.generate.return_value = ["multi-doc answer"]
        pipeline = _make_pipeline(retriever=retriever, llm_model=llm)
        result = pipeline.generate(({"role": "user", "content": "compare docs"},))
        assert len(result.chunks) == 2
        assert "1_0" in result.chunks
        assert "2_1" in result.chunks
        assert result.chunks["1_0"].document_name == "doc1.txt"
        assert result.chunks["2_1"].document_name == "doc2.txt"


# ===================================================================
# ChunkReference to_dict
# ===================================================================


class TestChunkReferenceToDict:
    """Verify ChunkReference serialization."""

    def test_to_dict_returns_all_fields(self):
        """to_dict() returns all four fields."""
        ref = ChunkReference(
            document_id=5,
            document_name="test.pdf",
            document_position=3,
            text="some text",
        )
        d = ref.to_dict()
        assert d == {
            "document_id": 5,
            "document_name": "test.pdf",
            "document_position": 3,
            "text": "some text",
        }
