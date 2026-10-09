"""Unit tests for RAGTask.

Tests the prepare_for_task(), process_output(), and
prepare_input_for_database() methods of RAGTask using lightweight mocks
for ProcessData.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from DashAI.back.models.RAG.exceptions import RAGTaskInputError
from DashAI.back.models.RAG.RAG_pipeline import (
    ChunkReference,
    RAGGenerationOutput,
)
from DashAI.back.tasks.RAG_task import RAGTask

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_process_data(data: str) -> MagicMock:
    """Create a mock ProcessData with the given data attribute."""
    pd = MagicMock()
    pd.data = data
    return pd


# ===================================================================
# prepare_for_task() — input validation
# ===================================================================


class TestRAGTaskPrepareForTaskInputValidation:
    """Verify that prepare_for_task() rejects invalid inputs."""

    def test_empty_input_list_raises(self):
        """Empty input list → RAGTaskInputError."""
        task = RAGTask()
        with pytest.raises(RAGTaskInputError, match="must not be empty"):
            task.prepare_for_task([])

    def test_none_input_raises(self):
        """None input → RAGTaskInputError (empty check)."""
        task = RAGTask()
        with pytest.raises(RAGTaskInputError):
            task.prepare_for_task(None)


# ===================================================================
# prepare_for_task() — no history
# ===================================================================


class TestRAGTaskPrepareForTaskNoHistory:
    """Verify prepare_for_task() without history."""

    def test_no_history_returns_single_entry(self):
        """Without history, returns a single-entry list with the user message."""
        task = RAGTask()
        input_data = [_make_process_data("Tell me about DashAI")]
        result = task.prepare_for_task(input_data)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Tell me about DashAI"

    def test_no_history_none_explicit(self):
        """history=None explicitly → same as no history."""
        task = RAGTask()
        input_data = [_make_process_data("Hello")]
        result = task.prepare_for_task(input_data, history=None)
        assert len(result) == 1
        assert result[0]["content"] == "Hello"

    def test_no_history_empty_list(self):
        """history=[] → same as no history."""
        task = RAGTask()
        input_data = [_make_process_data("Hello")]
        result = task.prepare_for_task(input_data, history=[])
        assert len(result) == 1
        assert result[0]["content"] == "Hello"


# ===================================================================
# prepare_for_task() — with history
# ===================================================================


class TestRAGTaskPrepareForTaskWithHistory:
    """Verify prepare_for_task() correctly includes conversation history."""

    def test_single_history_entry(self):
        """One history entry → 3 messages (user, assistant, user)."""
        task = RAGTask()
        input_data = [_make_process_data("What is RAG?")]
        history = [("Hello!", "Hello! How can I assist you today?")]
        result = task.prepare_for_task(input_data, history=history)
        assert len(result) == 3
        # History user message
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello!"
        # History assistant message
        assert result[1]["role"] == "assistant"
        assert result[1]["content"] == "Hello! How can I assist you today?"
        # Current user message
        assert result[2]["role"] == "user"
        assert result[2]["content"] == "What is RAG?"

    def test_multiple_history_entries_ordering(self):
        """Multiple history entries → correct chronological ordering."""
        task = RAGTask()
        input_data = [_make_process_data("Third question")]
        history = [
            ("First question", "First answer"),
            ("Second question", "Second answer"),
        ]
        result = task.prepare_for_task(input_data, history=history)
        assert len(result) == 5  # 2*2 history + 1 current
        assert result[0]["content"] == "First question"
        assert result[1]["content"] == "First answer"
        assert result[2]["content"] == "Second question"
        assert result[3]["content"] == "Second answer"
        assert result[4]["content"] == "Third question"

    def test_history_roles_alternate(self):
        """History entries alternate user/assistant roles correctly."""
        task = RAGTask()
        input_data = [_make_process_data("Current")]
        history = [("Q1", "A1"), ("Q2", "A2"), ("Q3", "A3")]
        result = task.prepare_for_task(input_data, history=history)
        expected_roles = [
            "user",
            "assistant",
            "user",
            "assistant",
            "user",
            "assistant",
            "user",
        ]
        actual_roles = [m["role"] for m in result]
        assert actual_roles == expected_roles


# ===================================================================
# process_output() — RAGGenerationOutput
# ===================================================================


class TestRAGTaskProcessOutput:
    """Verify process_output() converts RAGGenerationOutput correctly."""

    def test_basic_output(self):
        """process_output returns list of (data, type) tuples."""
        task = RAGTask()
        chunks = {
            "1_0": ChunkReference(
                document_id=1,
                document_name="doc.txt",
                document_position=0,
                text="chunk text",
            )
        }
        output = RAGGenerationOutput(message="the answer", chunks=chunks)
        result = task.process_output(output)
        assert len(result) == 2
        # First tuple: message as str
        assert result[0] == ("the answer", "str")
        # Second tuple: chunks as Dict (JSON-encoded)
        data_str, data_type = result[1]
        assert data_type == "Dict"
        parsed = json.loads(data_str)
        assert "1_0" in parsed
        assert parsed["1_0"]["document_id"] == 1
        assert parsed["1_0"]["document_name"] == "doc.txt"
        assert parsed["1_0"]["text"] == "chunk text"

    def test_empty_chunks(self):
        """Empty chunks dict → still returns valid output."""
        task = RAGTask()
        output = RAGGenerationOutput(message="no context answer", chunks={})
        result = task.process_output(output)
        assert len(result) == 2
        assert result[0] == ("no context answer", "str")
        data_str, data_type = result[1]
        assert data_type == "Dict"
        parsed = json.loads(data_str)
        assert parsed == {}

    def test_multiple_chunks(self):
        """Multiple chunks are all serialized."""
        task = RAGTask()
        chunks = {
            "1_0": ChunkReference(1, "a.txt", 0, "text A"),
            "2_1": ChunkReference(2, "b.txt", 1, "text B"),
            "3_2": ChunkReference(3, "c.txt", 2, "text C"),
        }
        output = RAGGenerationOutput(message="multi", chunks=chunks)
        result = task.process_output(output)
        parsed = json.loads(result[1][0])
        assert len(parsed) == 3
        assert parsed["1_0"]["text"] == "text A"
        assert parsed["2_1"]["text"] == "text B"
        assert parsed["3_2"]["text"] == "text C"

    def test_message_is_string_cast(self):
        """Message is cast to str even if it's already a string."""
        task = RAGTask()
        output = RAGGenerationOutput(message=42, chunks={})  # type: ignore
        result = task.process_output(output)
        assert result[0][0] == "42"
        assert result[0][1] == "str"


# ===================================================================
# prepare_input_for_database method
# ===================================================================


class TestRAGTaskPrepareInputForDatabase:
    """Verify prepare_input_for_database() returns list of tuples."""

    def test_returns_list_of_tuples(self):
        """Returns a list with one (data, type) tuple."""
        task = RAGTask()
        result = task.prepare_input_for_database(["Tell me about ML"])
        assert len(result) == 1
        assert result[0] == ("Tell me about ML", "str")

    def test_first_element_only(self):
        """Only the first element of the input list is used."""
        task = RAGTask()
        result = task.prepare_input_for_database(["first", "second", "third"])
        assert result[0][0] == "first"

    def test_empty_string_input(self):
        """Empty string is still stored."""
        task = RAGTask()
        result = task.prepare_input_for_database([""])
        assert result[0] == ("", "str")


# ===================================================================
# RAGTask metadata
# ===================================================================


class TestRAGTaskMetadata:
    """Verify RAGTask metadata and class attributes."""

    def test_use_history_is_true(self):
        """RAGTask.USE_HISTORY must be True (conversation support)."""
        assert RAGTask.USE_HISTORY is True

    def test_metadata_inputs(self):
        """Metadata declares 1 str input."""
        task = RAGTask()
        metadata = task.get_metadata()
        assert "inputs" in metadata
        assert "str" in metadata["inputs"]
        assert metadata["inputs"]["str"]["min"] == 1
        assert metadata["inputs"]["str"]["max"] == 1

    def test_metadata_outputs(self):
        """Metadata declares str and Dict outputs."""
        task = RAGTask()
        metadata = task.get_metadata()
        assert "outputs" in metadata
        assert "str" in metadata["outputs"]
        assert "Dict" in metadata["outputs"]
