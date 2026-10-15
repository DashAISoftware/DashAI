"""Unit tests for the RAG query transformation module.

Pure/domain-level tests: no database, no HTTP, only stubbed LLMs and the
real prompt classes. Covers history formatting, the function-call output
parser, and the three LLM-backed transformers.
"""

from __future__ import annotations

import json

import pytest

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.models.RAG.exceptions import (
    RAGTransformationConfigError,
    RAGTransformationOutputError,
)
from DashAI.back.models.RAG.prompts.transformation import (
    DefaultQueryDecompositionPrompt,
    DefaultQueryExpansionPrompt,
    DefaultQueryRewritingPrompt,
    QueryDecompositionPrompt,
    QueryExpansionPrompt,
    QueryRewritingPrompt,
)
from DashAI.back.models.RAG.transformation import (
    BaseQueryTransformation,
    LLMQueryDecomposer,
    LLMQueryExpander,
    LLMQueryRewriter,
    QueryTransformationResult,
)
from DashAI.back.models.RAG.transformation.llm_output_parser import (
    parse_function_call_output,
)
from DashAI.back.models.RAG.transformation.llm_query_transformation import (
    format_history,
)
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from DashAI.back.services.RAG.query_transformation_validation import (
    QueryTransformationValidationService,
)

# ---------------------------------------------------------------------------
# stubs
# ---------------------------------------------------------------------------


class _EmptySchema(BaseSchema):
    """Empty schema for the stub models."""


class StubTransformationLLM(TextToTextGenerationTaskModel):
    """Deterministic stub that returns a canned response list."""

    SCHEMA = _EmptySchema

    def __init__(self, response=None, **kwargs):
        self.response = ["{}"] if response is None else response

    def generate(self, prompt):
        return self.response


class CapturingStubLLM(TextToTextGenerationTaskModel):
    """Stub that records every prompt list passed to ``generate``."""

    SCHEMA = _EmptySchema
    received: list = []

    def __init__(self, response=None, **kwargs):
        self.response = ["{}"] if response is None else response

    def generate(self, prompt):
        CapturingStubLLM.received.append(prompt)
        return self.response


@pytest.fixture(autouse=True)
def _reset_captures():
    CapturingStubLLM.received.clear()
    yield
    CapturingStubLLM.received.clear()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

REWRITE_JSON = '{"name": "rewrite_query", "arguments": {"query": " rewritten "}}'


def _rewriter(response, history_window=2):
    return LLMQueryRewriter(
        prompt=DefaultQueryRewritingPrompt(language="en"),
        llm_model=StubTransformationLLM(response=response),
        history_window=history_window,
    )


def _expander(response, n=3, history_window=2):
    return LLMQueryExpander(
        prompt=DefaultQueryExpansionPrompt(language="en"),
        llm_model=StubTransformationLLM(response=response),
        n_queries=n,
        history_window=history_window,
    )


def _decomposer(response, cap=None, history_window=2):
    return LLMQueryDecomposer(
        prompt=DefaultQueryDecompositionPrompt(language="en"),
        llm_model=StubTransformationLLM(response=response),
        max_subqueries=cap,
        history_window=history_window,
    )


def _captured_content(llm_instances):
    return CapturingStubLLM.received[-1][0]["content"]


# ===================================================================
# history formatting
# ===================================================================


class TestFormatHistory:
    """``format_history`` windowing and tolerance."""

    def test_window_slicing_takes_last_entries(self):
        history = [{"role": "user", "content": f"m{i}"} for i in range(5)]
        assert format_history(history, 2) == "user: m3\nuser: m4"

    def test_window_zero_is_empty(self):
        history = [{"role": "user", "content": "m0"}]
        assert format_history(history, 0) == ""

    def test_short_history_uses_all(self):
        history = [{"role": "user", "content": "only"}]
        assert format_history(history, 5) == "user: only"

    def test_missing_role_raises_with_index(self):
        with pytest.raises(RAGTransformationConfigError, match="index 0"):
            format_history([{"content": "a"}], 2)

    def test_missing_content_raises_with_index(self):
        with pytest.raises(RAGTransformationConfigError, match="index 0"):
            format_history([{"role": "assistant"}], 2)

    def test_non_string_content_raises_with_index(self):
        with pytest.raises(RAGTransformationConfigError, match="index 0"):
            format_history([{"role": "user", "content": 3}], 2)

    def test_empty_role_raises_with_index(self):
        with pytest.raises(RAGTransformationConfigError, match="index 0"):
            format_history([{"role": "", "content": "a"}], 2)

    def test_non_mapping_entry_raises_with_index(self):
        with pytest.raises(RAGTransformationConfigError, match="index 0"):
            format_history(["not a mapping"], 2)

    def test_malformed_index_reflects_the_window(self):
        history = [{"role": "user", "content": "ok"}] * 3 + [{"content": "bad"}]
        with pytest.raises(RAGTransformationConfigError, match="index 3"):
            format_history(history, 2)

    def test_role_content_formatting(self):
        history = [
            {"role": "user", "content": "x"},
            {"role": "assistant", "content": "y"},
        ]
        assert format_history(history, 2) == "user: x\nassistant: y"

    def test_empty_history_is_empty(self):
        assert format_history([], 3) == ""


# ===================================================================
# function-call parser
# ===================================================================


class TestParseFunctionCallOutput:
    """``parse_function_call_output`` robustness."""

    def test_valid_wrapped_object(self):
        raw = '{"name": "rewrite_query", "arguments": {"query": "hello"}}'
        parsed = parse_function_call_output(raw, "rewrite_query", "query")
        assert parsed == {"query": "hello"}

    def test_valid_without_arguments_wrapper(self):
        raw = '{"query": "hello"}'
        parsed = parse_function_call_output(raw, "rewrite_query", "query")
        assert parsed == {"query": "hello"}

    def test_markdown_fenced(self):
        raw = '```json\n{"name": "rewrite_query", "arguments": {"query": "hi"}}\n```'
        parsed = parse_function_call_output(raw, "rewrite_query", "query")
        assert parsed == {"query": "hi"}

    def test_text_surrounding_the_object(self):
        raw = (
            "Sure! Here is the call:\n"
            '{"name": "rewrite_query", "arguments": {"query": "hi"}}\n'
            "Hope it helps."
        )
        parsed = parse_function_call_output(raw, "rewrite_query", "query")
        assert parsed == {"query": "hi"}

    def test_invalid_json_includes_truncated_preview(self):
        raw = '{"name": "rewrite_query", "arguments": {' + ("x" * 500) + "}}"
        with pytest.raises(RAGTransformationOutputError) as exc_info:
            parse_function_call_output(raw, "rewrite_query", "query")
        message = str(exc_info.value)
        assert "..." in message
        assert message.count("x") <= 200

    def test_missing_braces_raises(self):
        with pytest.raises(RAGTransformationOutputError):
            parse_function_call_output(
                "there is no json here", "rewrite_query", "query"
            )

    def test_non_dict_json_raises(self):
        with pytest.raises(RAGTransformationOutputError):
            parse_function_call_output("[1, 2, 3]", "rewrite_query", "query")

    def test_wrong_name_wrapper_raises(self):
        raw = '{"name": "expand_query", "arguments": {"query": "hi"}}'
        with pytest.raises(RAGTransformationOutputError, match="instead of"):
            parse_function_call_output(raw, "rewrite_query", "query")

    def test_right_name_wrapper_ok(self):
        raw = '{"name": "rewrite_query", "arguments": {"query": "hi"}}'
        assert parse_function_call_output(raw, "rewrite_query", "query") == {
            "query": "hi"
        }

    def test_arguments_only_without_name_ok(self):
        raw = '{"arguments": {"query": "hi"}}'
        assert parse_function_call_output(raw, "rewrite_query", "query") == {
            "query": "hi"
        }

    def test_bare_arguments_without_name_ok(self):
        raw = '{"query": "hi"}'
        assert parse_function_call_output(raw, "rewrite_query", "query") == {
            "query": "hi"
        }


# ===================================================================
# rewriting (1 -> 1)
# ===================================================================


class TestLLMQueryRewriter:
    """Rewriting transformer contract."""

    def test_returns_single_clean_query(self):
        result = _rewriter([REWRITE_JSON]).transform("hi", [])
        assert isinstance(result, QueryTransformationResult)
        assert result.queries == ["rewritten"]

    def test_result_subclasses_base_contract(self):
        assert isinstance(_rewriter([REWRITE_JSON]), BaseQueryTransformation)

    def test_missing_query_key_raises(self):
        raw = '{"name": "rewrite_query", "arguments": {"other": "x"}}'
        with pytest.raises(RAGTransformationOutputError):
            _rewriter([raw]).transform("hi", [])

    def test_empty_query_string_raises(self):
        raw = '{"name": "rewrite_query", "arguments": {"query": "   "}}'
        with pytest.raises(RAGTransformationOutputError):
            _rewriter([raw]).transform("hi", [])

    def test_returns_exactly_one_query(self):
        result = _rewriter([REWRITE_JSON]).transform("hi", [])
        assert len(result.queries) == 1


# ===================================================================
# expansion (1 -> n)
# ===================================================================


class TestLLMQueryExpander:
    """Expansion transformer contract."""

    def test_truncates_to_n(self):
        raw = json.dumps(
            {
                "name": "expand_query",
                "arguments": {"queries": ["a", "b", "c", "d", "e"]},
            }
        )
        result = _expander([raw], n=3).transform("hi", [])
        assert result.queries == ["a", "b", "c"]

    def test_dedupes_preserving_order(self):
        raw = json.dumps(
            {"name": "expand_query", "arguments": {"queries": ["a", "b", "a", "c"]}}
        )
        result = _expander([raw], n=5).transform("hi", [])
        assert result.queries == ["a", "b", "c"]

    def test_fewer_than_n_kept(self):
        raw = json.dumps({"name": "expand_query", "arguments": {"queries": ["a", "b"]}})
        result = _expander([raw], n=5).transform("hi", [])
        assert result.queries == ["a", "b"]

    def test_empty_list_raises(self):
        raw = json.dumps({"name": "expand_query", "arguments": {"queries": []}})
        with pytest.raises(RAGTransformationOutputError):
            _expander([raw]).transform("hi", [])


# ===================================================================
# decomposition (1 -> n, LLM decides)
# ===================================================================


class TestLLMQueryDecomposer:
    """Decomposition transformer contract."""

    def test_llm_decided_count(self):
        raw = json.dumps(
            {
                "name": "decompose_query",
                "arguments": {"queries": ["s1", "s2", "s3", "s4"]},
            }
        )
        result = _decomposer([raw], cap=None).transform("hi", [])
        assert result.queries == ["s1", "s2", "s3", "s4"]

    def test_cap_truncates(self):
        raw = json.dumps(
            {
                "name": "decompose_query",
                "arguments": {"queries": ["s1", "s2", "s3", "s4"]},
            }
        )
        result = _decomposer([raw], cap=2).transform("hi", [])
        assert result.queries == ["s1", "s2"]

    def test_none_cap_keeps_all(self):
        raw = json.dumps(
            {"name": "decompose_query", "arguments": {"queries": ["s1", "s2", "s3"]}}
        )
        result = _decomposer([raw], cap=None).transform("hi", [])
        assert len(result.queries) == 3

    def test_empty_queries_raises(self):
        raw = json.dumps({"name": "decompose_query", "arguments": {"queries": []}})
        with pytest.raises(RAGTransformationOutputError):
            _decomposer([raw]).transform("hi", [])


# ===================================================================
# prompt rendering / plumbing
# ===================================================================


class TestPromptRendering:
    """The rendered chat message reaches the LLM with the right values."""

    def test_rewriter_message_contains_input_history_and_contract(self):
        llm = CapturingStubLLM(response=[REWRITE_JSON])
        rewriter = LLMQueryRewriter(
            prompt=DefaultQueryRewritingPrompt(language="en"),
            llm_model=llm,
            history_window=2,
        )
        rewriter.transform(
            "What is DashAI?", [{"role": "user", "content": "earlier message"}]
        )
        sent = _captured_content(CapturingStubLLM.received)
        assert "What is DashAI?" in sent
        assert "user: earlier message" in sent
        assert "rewrite_query" in sent

    def test_expander_placeholder_n_replaced(self):
        raw = json.dumps({"name": "expand_query", "arguments": {"queries": ["a", "b"]}})
        llm = CapturingStubLLM(response=[raw])
        expander = LLMQueryExpander(
            prompt=DefaultQueryExpansionPrompt(language="en"),
            llm_model=llm,
            n_queries=4,
            history_window=2,
        )
        expander.transform("hi", [])
        sent = _captured_content(CapturingStubLLM.received)
        assert "{n}" not in sent
        assert "exactly 4 concise" in sent

    def test_decomposer_cap_line_present_when_set(self):
        raw = json.dumps(
            {"name": "decompose_query", "arguments": {"queries": ["s1", "s2"]}}
        )
        llm = CapturingStubLLM(response=[raw])
        decomposer = LLMQueryDecomposer(
            prompt=DefaultQueryDecompositionPrompt(language="en"),
            llm_model=llm,
            max_subqueries=2,
            history_window=2,
        )
        decomposer.transform("hi", [])
        sent = _captured_content(CapturingStubLLM.received)
        assert "more than 2 sub-queries" in sent
        assert "{n_max}" not in sent

    def test_decomposer_cap_line_absent_when_none(self):
        raw = json.dumps(
            {"name": "decompose_query", "arguments": {"queries": ["s1", "s2"]}}
        )
        llm = CapturingStubLLM(response=[raw])
        decomposer = LLMQueryDecomposer(
            prompt=DefaultQueryDecompositionPrompt(language="en"),
            llm_model=llm,
            max_subqueries=None,
            history_window=2,
        )
        decomposer.transform("hi", [])
        sent = _captured_content(CapturingStubLLM.received)
        assert "Do not produce more than" not in sent
        assert "{n_max}" not in sent

    def test_history_window_limits_context(self):
        history = [
            {"role": "user", "content": "h1"},
            {"role": "assistant", "content": "h2"},
            {"role": "user", "content": "h3"},
            {"role": "assistant", "content": "h4"},
        ]
        llm = CapturingStubLLM(response=[REWRITE_JSON])
        rewriter = LLMQueryRewriter(
            prompt=DefaultQueryRewritingPrompt(language="en"),
            llm_model=llm,
            history_window=2,
        )
        rewriter.transform("current message", history)
        sent = _captured_content(CapturingStubLLM.received)
        assert "h3" in sent
        assert "h4" in sent
        assert "h1" not in sent
        assert "h2" not in sent


# ===================================================================
# configuration and output errors
# ===================================================================


class TestConfigurationErrors:
    """Missing required parameters raise config errors."""

    def test_missing_prompt_raises(self):
        with pytest.raises(RAGTransformationConfigError):
            LLMQueryRewriter(llm_model=StubTransformationLLM(response=[REWRITE_JSON]))

    def test_missing_llm_raises(self):
        with pytest.raises(RAGTransformationConfigError):
            LLMQueryRewriter(prompt=DefaultQueryRewritingPrompt(language="en"))


class TestOutputErrors:
    """Bad LLM output shapes raise output errors."""

    def test_empty_output_list_raises(self):
        with pytest.raises(RAGTransformationOutputError):
            _rewriter([]).transform("hi", [])

    def test_non_string_first_element_raises(self):
        with pytest.raises(RAGTransformationOutputError):
            _rewriter([42]).transform("hi", [])


# ===================================================================
# placeholder ordering and single-pass substitution
# ===================================================================


class TestPromptPlaceholderOrdering:
    """Optionals resolve before required tokens; substitution is single-pass."""

    def test_decomposition_message_with_nmax_survives_when_cap_absent(self):
        prompt = DefaultQueryDecompositionPrompt(language="en")
        rendered = prompt.format(input="keep {n_max} verbatim", history="", n_max=None)
        assert "keep {n_max} verbatim" in rendered
        assert "Do not produce more than" not in rendered

    def test_decomposition_message_with_input_token_not_re_expanded(self):
        prompt = DefaultQueryDecompositionPrompt(language="en")
        rendered = prompt.format(input="literal {input} token", history="", n_max=2)
        assert "literal {input} token" in rendered
        assert "more than 2 sub-queries" in rendered

    def test_expansion_message_with_n_token_not_double_substituted(self):
        prompt = DefaultQueryExpansionPrompt(language="en")
        rendered = prompt.format(input="give me {n} things", history="", n=4)
        assert "give me {n} things" in rendered
        assert "exactly 4 concise" in rendered

    def test_rewriting_message_tokens_not_re_expanded(self):
        prompt = DefaultQueryRewritingPrompt(language="en")
        rendered = prompt.format(input="literal {input}", history="ctx {history}")
        assert "literal {input}" in rendered
        assert "ctx {history}" in rendered


# ===================================================================
# per-technique default prompt placeholders
# ===================================================================


class TestTechniqueDefaultPromptPlaceholders:
    """Each technique's schema defaults to its own prompt component."""

    def test_rewriter_defaults_to_rewriting_prompt(self):
        schema = LLMQueryRewriter.get_schema()
        assert schema["properties"]["prompt"]["placeholder"] == {
            "component": "DefaultQueryRewritingPrompt",
            "params": {},
        }

    def test_expander_defaults_to_expansion_prompt(self):
        schema = LLMQueryExpander.get_schema()
        assert schema["properties"]["prompt"]["placeholder"] == {
            "component": "DefaultQueryExpansionPrompt",
            "params": {},
        }

    def test_decomposer_defaults_to_decomposition_prompt(self):
        schema = LLMQueryDecomposer.get_schema()
        assert schema["properties"]["prompt"]["placeholder"] == {
            "component": "DefaultQueryDecompositionPrompt",
            "params": {},
        }


# ===================================================================
# validator: technique/prompt-family matching
# ===================================================================


class _FakeRegistry(dict):
    """Minimal registry mapping component names to ``{"class": ...}``."""

    def __init__(self, classes):
        super().__init__({name: {"class": klass} for name, klass in classes.items()})


def _validator_registry() -> _FakeRegistry:
    return _FakeRegistry(
        {
            "LLMQueryRewriter": LLMQueryRewriter,
            "LLMQueryExpander": LLMQueryExpander,
            "LLMQueryDecomposer": LLMQueryDecomposer,
            "DefaultQueryRewritingPrompt": DefaultQueryRewritingPrompt,
            "DefaultQueryExpansionPrompt": DefaultQueryExpansionPrompt,
            "DefaultQueryDecompositionPrompt": DefaultQueryDecompositionPrompt,
            "StubTransformationLLM": StubTransformationLLM,
        }
    )


def _validate_transformation(ref: dict) -> None:
    service = QueryTransformationValidationService(
        _validator_registry(), lambda name, template: None
    )
    service.validate({"query_transformation": ref})


def _transformation_ref(component: str, prompt_component: str) -> dict:
    return {
        "component": component,
        "params": {
            "prompt": {"component": prompt_component, "params": {}},
            "llm_model": {"component": "StubTransformationLLM", "params": {}},
        },
    }


class TestTransformationPromptFamily:
    """Each technique anchors a prompt family; mismatches are rejected."""

    def test_rewriter_prompt_base(self):
        assert LLMQueryRewriter.TRANSFORMATION_PROMPT_BASE is QueryRewritingPrompt

    def test_expander_prompt_base(self):
        assert LLMQueryExpander.TRANSFORMATION_PROMPT_BASE is QueryExpansionPrompt

    def test_decomposer_prompt_base(self):
        assert LLMQueryDecomposer.TRANSFORMATION_PROMPT_BASE is QueryDecompositionPrompt

    def test_valid_pairing_accepted(self):
        _validate_transformation(
            _transformation_ref("LLMQueryRewriter", "DefaultQueryRewritingPrompt")
        )

    def test_rewriter_with_expansion_prompt_rejected(self):
        with pytest.raises(ValueError, match="family") as exc_info:
            _validate_transformation(
                _transformation_ref("LLMQueryRewriter", "DefaultQueryExpansionPrompt")
            )
        message = str(exc_info.value)
        assert "LLMQueryRewriter" in message
        assert "DefaultQueryExpansionPrompt" in message

    def test_expander_with_rewriting_prompt_rejected(self):
        with pytest.raises(ValueError, match="family") as exc_info:
            _validate_transformation(
                _transformation_ref("LLMQueryExpander", "DefaultQueryRewritingPrompt")
            )
        message = str(exc_info.value)
        assert "LLMQueryExpander" in message
        assert "DefaultQueryRewritingPrompt" in message
