"""Unit tests for the RAG query transformation module.

Pure/domain-level tests: no database, no HTTP, only stubbed LLMs and the
real prompt classes. Covers history formatting, the function-call output
parser, and the three LLM-backed transformers.
"""

from __future__ import annotations

import json

import pytest

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.core.schema_fields.defaults import resolve_component_defaults
from DashAI.back.models.hugging_face.gguf_text_generation_base import (
    GGUFTextGenerationModel,
)
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
    FunctionCallResult,
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
    FunctionCallingStubLLM.received_messages.clear()
    FunctionCallingStubLLM.received_functions.clear()
    yield
    CapturingStubLLM.received.clear()
    FunctionCallingStubLLM.received_messages.clear()
    FunctionCallingStubLLM.received_functions.clear()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

REWRITE_JSON = '{"name": "rewrite_query", "arguments": {"query": " rewritten "}}'


def _rewriter(response, history_window=2, llm_model=None):
    return LLMQueryRewriter(
        prompt=DefaultQueryRewritingPrompt(language="en"),
        llm_model=llm_model
        if llm_model is not None
        else StubTransformationLLM(response=response),
        history_window=history_window,
    )


def _expander(response, n=3, history_window=2, llm_model=None):
    return LLMQueryExpander(
        prompt=DefaultQueryExpansionPrompt(language="en"),
        llm_model=llm_model
        if llm_model is not None
        else StubTransformationLLM(response=response),
        n_queries=n,
        history_window=history_window,
    )


def _decomposer(response, cap=None, history_window=2, llm_model=None):
    return LLMQueryDecomposer(
        prompt=DefaultQueryDecompositionPrompt(language="en"),
        llm_model=llm_model
        if llm_model is not None
        else StubTransformationLLM(response=response),
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


class TestParseFunctionCallOutputDrift:
    """Real-world drift the parser must tolerate without failing the turn."""

    def test_arguments_serialized_as_json_string_wrapped(self):
        raw = (
            '{"name": "expand_query", '
            '"arguments": "{\\"queries\\": [\\"a\\", \\"b\\"]}"}'
        )
        parsed = parse_function_call_output(raw, "expand_query", "queries")
        assert parsed == {"queries": ["a", "b"]}

    def test_arguments_serialized_as_json_string_without_name(self):
        raw = '{"arguments": "{\\"query\\": \\"hi\\"}"}'
        parsed = parse_function_call_output(raw, "rewrite_query", "query")
        assert parsed == {"query": "hi"}

    def test_arguments_to_non_object_string_is_not_a_candidate(self):
        raw = 'Here: {"arguments": "nope"}\n{"queries": ["x"]}'
        parsed = parse_function_call_output(raw, "expand_query", "queries")
        assert parsed == {"queries": ["x"]}

    def test_prose_with_braces_before_object_parses(self):
        raw = (
            'The format is {"queries": [...]} as instructed.\n'
            '{"name": "expand_query", "arguments": {"queries": ["a", "b"]}}'
        )
        parsed = parse_function_call_output(raw, "expand_query", "queries")
        assert parsed == {"queries": ["a", "b"]}

    def test_prose_with_braces_before_object_parses_valid_json_example(self):
        raw = (
            'As in {"queries": []} but filled:\n'
            '{"name": "expand_query", "arguments": {"queries": ["a"]}}'
        )
        parsed = parse_function_call_output(raw, "expand_query", "queries")
        assert parsed == {"queries": ["a"]}

    def test_trailing_prose_with_brace_after_object_parses(self):
        raw = (
            '{"name": "expand_query", "arguments": {"queries": ["a", "b"]}}\n'
            "Note: queries are grouped by {topic}."
        )
        parsed = parse_function_call_output(raw, "expand_query", "queries")
        assert parsed == {"queries": ["a", "b"]}

    def test_named_wrapper_wins_over_earlier_bare_argument_object(self):
        raw = (
            '{"queries": []}\n{"name": "expand_query", "arguments": {"queries": ["a"]}}'
        )
        parsed = parse_function_call_output(raw, "expand_query", "queries")
        assert parsed == {"queries": ["a"]}

    def test_bare_array_tolerated_for_list_argument(self):
        parsed = parse_function_call_output(
            '["a", "b"]', "expand_query", "queries", list_argument_key="queries"
        )
        assert parsed == {"queries": ["a", "b"]}

    def test_bare_array_rejected_without_list_argument(self):
        with pytest.raises(RAGTransformationOutputError):
            parse_function_call_output('["a", "b"]', "expand_query", "queries")

    def test_wrong_name_among_candidates_recovered_by_later_match(self):
        raw = (
            '{"name": "other_fn", "arguments": {"queries": ["a"]}}\n'
            '{"name": "expand_query", "arguments": {"queries": ["b"]}}'
        )
        parsed = parse_function_call_output(raw, "expand_query", "queries")
        assert parsed == {"queries": ["b"]}

    def test_wrong_name_only_candidate_still_raises(self):
        raw = '{"name": "other_fn", "arguments": {"queries": ["a"]}}'
        with pytest.raises(RAGTransformationOutputError, match="instead of"):
            parse_function_call_output(raw, "expand_query", "queries")

    def test_fallback_first_resolvable_candidate_used(self):
        raw = 'Sure. Like: {"queries": ["prev"]}\n{"queries": ["real"]}'
        parsed = parse_function_call_output(raw, "expand_query", "queries")
        assert parsed == {"queries": ["prev"]}

    def test_named_wrapper_beats_nonempty_bare_example(self):
        raw = (
            'For example {"queries": ["foo", "bar"]}. The real call:\n'
            '{"name": "expand_query", "arguments": {"queries": ["real"]}}'
        )
        parsed = parse_function_call_output(raw, "expand_query", "queries")
        assert parsed == {"queries": ["real"]}

    def test_named_wrapper_beats_nonempty_bare_example_rewriting(self):
        raw = (
            'For example {"query": "widgets"} but the real call:\n'
            '{"name": "rewrite_query", "arguments": {"query": "real"}}'
        )
        parsed = parse_function_call_output(raw, "rewrite_query", "query")
        assert parsed == {"query": "real"}

    def test_object_after_leading_array_wins_for_rewriting(self):
        raw = '[1,2,3] {"name": "rewrite_query", "arguments": {"query": "real"}}'
        parsed = parse_function_call_output(raw, "rewrite_query", "query")
        assert parsed == {"query": "real"}

    def test_object_after_leading_array_wins_for_expansion(self):
        raw = '[1,2,3] {"name": "expand_query", "arguments": {"queries": ["a"]}}'
        parsed = parse_function_call_output(
            raw, "expand_query", "queries", list_argument_key="queries"
        )
        assert parsed == {"queries": ["a"]}

    def test_keyless_named_arguments_do_not_shadow_bare_arguments(self):
        raw = '{"name": "expand_query", "arguments": {"foo": 1}}\n{"queries": ["a"]}'
        parsed = parse_function_call_output(raw, "expand_query", "queries")
        assert parsed == {"queries": ["a"]}

    def test_keyless_named_arguments_alone_still_raises(self):
        raw = '{"name": "expand_query", "arguments": {"foo": 1}}'
        with pytest.raises(RAGTransformationOutputError):
            parse_function_call_output(raw, "expand_query", "queries")

    def test_string_array_with_trailing_prose_still_tolerated(self):
        parsed = parse_function_call_output(
            '["a", "b"] - hope that helps.',
            "expand_query",
            "queries",
            list_argument_key="queries",
        )
        assert parsed == {"queries": ["a", "b"]}

    def test_numeric_array_not_tolerated(self):
        with pytest.raises(RAGTransformationOutputError):
            parse_function_call_output(
                "[1, 2, 3]", "expand_query", "queries", list_argument_key="queries"
            )

    def test_array_with_braces_inside_elements_tolerated(self):
        parsed = parse_function_call_output(
            '["use {var} in python", "b"]',
            "expand_query",
            "queries",
            list_argument_key="queries",
        )
        assert parsed == {"queries": ["use {var} in python", "b"]}

    def test_array_with_json_string_element_tolerated(self):
        parsed = parse_function_call_output(
            '["{\\"a\\": 1}"]',
            "expand_query",
            "queries",
            list_argument_key="queries",
        )
        assert parsed == {"queries": ['{"a": 1}']}

    def test_array_with_braced_trailing_prose_tolerated(self):
        parsed = parse_function_call_output(
            '["a"]\nDone. Marked as {done}.',
            "expand_query",
            "queries",
            list_argument_key="queries",
        )
        assert parsed == {"queries": ["a"]}

    def test_array_with_braces_rejected_without_list_argument(self):
        with pytest.raises(RAGTransformationOutputError):
            parse_function_call_output(
                '["use {var} in python", "b"]', "expand_query", "queries"
            )

    def test_later_nonempty_bare_list_beats_earlier_empty(self):
        raw = '{"queries": []}\n{"queries": ["real"]}'
        parsed = parse_function_call_output(raw, "expand_query", "queries")
        assert parsed == {"queries": ["real"]}

    def test_named_empty_arguments_attempted_raises(self):
        raw = '{"name": "expand_query", "arguments": {}}'
        with pytest.raises(RAGTransformationOutputError):
            parse_function_call_output(raw, "expand_query", "queries")

    def test_attempted_named_call_outranks_leading_string_array(self):
        raw = '["example"] {"name": "expand_query", "arguments": {}}'
        with pytest.raises(RAGTransformationOutputError, match="Failed to parse"):
            parse_function_call_output(
                raw, "expand_query", "queries", list_argument_key="queries"
            )

    def test_array_only_when_no_braces_array_after_invalid_object(self):
        raw = '["a"] {"name": "other_fn", "arguments": {"queries": ["b"]}}'
        with pytest.raises(RAGTransformationOutputError, match="instead of"):
            parse_function_call_output(
                raw, "expand_query", "queries", list_argument_key="queries"
            )


class TestParseFunctionCallOutputPriority:
    """Named wrappers and contract objects outrank prose examples."""

    def test_expander_named_wrapper_beats_nonempty_example(self):
        raw = (
            'For example {"queries": ["foo", "bar"]}. The real call:\n'
            '{"name": "expand_query", "arguments": {"queries": ["real"]}}'
        )
        result = _expander([raw]).transform("hi", [])
        assert result.queries == ["real"]

    def test_rewriter_object_after_array_wins(self):
        raw = '[1,2,3] {"name": "rewrite_query", "arguments": {"query": "real"}}'
        result = _rewriter([raw]).transform("hi", [])
        assert result.queries == ["real"]

    def test_expander_numeric_array_not_tolerated(self):
        with pytest.raises(RAGTransformationOutputError):
            _expander(["[1, 2, 3]"]).transform("hi", [])

    def test_expander_bare_empty_list_yields_precision_error(self):
        with pytest.raises(
            RAGTransformationOutputError, match="does not contain a non-empty 'queries'"
        ):
            _expander(['{"queries": []}']).transform("hi", [])


# ===================================================================
# native function calling
# ===================================================================


class FunctionCallingStubLLM(TextToTextGenerationTaskModel):
    """Stub LLM that reports function-calling support and returns a spec call."""

    SCHEMA = _EmptySchema
    SUPPORTS_FUNCTION_CALLING = True
    received_messages: list = []
    received_functions: list = []

    def __init__(self, *, result=None, generate_error=None, **kwargs):
        self.result = result
        self.generate_error = generate_error

    @classmethod
    def spec_result(cls, arguments):
        """Build a canned expansion call result with the given arguments."""
        return FunctionCallResult(name="expand_query", arguments=arguments)

    def generate(self, prompt):
        raise AssertionError("generate() must not be called on the FC path")

    def generate_function_call(self, messages, functions):
        type(self).received_messages.append(messages)
        type(self).received_functions.append(functions)
        if self.generate_error is not None:
            raise self.generate_error
        return self.result


class _CapabilityOnlyStubLLM(TextToTextGenerationTaskModel):
    """Stub that claims function-calling support but implements no method."""

    SCHEMA = _EmptySchema

    def __init__(self, **kwargs):
        pass

    @classmethod
    def supports_function_calling(cls):
        return True

    def generate(self, prompt):
        raise AssertionError("generate() must not be called on the FC path")


class TestFunctionCallingRoute:
    """The transformation base prefers the function-calling route when available."""

    def test_function_calling_capability_flag_defaults_false(self):
        assert TextToTextGenerationTaskModel.supports_function_calling() is False
        assert StubTransformationLLM.supports_function_calling() is False
        assert GGUFTextGenerationModel.supports_function_calling() is True
        with pytest.raises(NotImplementedError):
            TextToTextGenerationTaskModel.generate_function_call(
                StubTransformationLLM(), [], []
            )

    def test_expander_uses_function_calling_route(self):
        stub = FunctionCallingStubLLM(
            result=FunctionCallingStubLLM.spec_result({"queries": ["a"]})
        )
        result = _expander(None, llm_model=stub).transform("hi", [])

        assert result.queries == ["a"]
        expected_spec = {
            "name": "expand_query",
            "description": LLMQueryExpander.FUNCTION_DESCRIPTION,
            "parameters": LLMQueryExpander.FUNCTION_PARAMETERS,
        }
        assert FunctionCallingStubLLM.received_functions == [[expected_spec]]
        messages = FunctionCallingStubLLM.received_messages[-1]
        assert "query expansion assistant" in messages[0]["content"]

    def test_expander_function_calling_arguments_as_string_resolved(self):
        stub = FunctionCallingStubLLM(
            result=FunctionCallingStubLLM.spec_result('{"queries": ["a", "b"]}')
        )
        result = _expander(None, llm_model=stub).transform("hi", [])
        assert result.queries == ["a", "b"]

    def test_expander_function_calling_wrong_name_raises(self):
        stub = FunctionCallingStubLLM(
            result=FunctionCallResult(name="other_fn", arguments={"queries": ["a"]})
        )
        with pytest.raises(RAGTransformationOutputError, match="instead of"):
            _expander(None, llm_model=stub).transform("hi", [])

    def test_expander_function_calling_unparseable_arguments_raises(self):
        stub = FunctionCallingStubLLM(
            result=FunctionCallResult(name="expand_query", arguments="not json")
        )
        with pytest.raises(RAGTransformationOutputError, match="Preview"):
            _expander(None, llm_model=stub).transform("hi", [])

    @pytest.mark.parametrize("result", [{}, None, object()])
    def test_expander_function_calling_missing_result_shape_raises(self, result):
        stub = FunctionCallingStubLLM(result=result)
        with pytest.raises(
            RAGTransformationOutputError, match="unexpected output shape"
        ):
            _expander(None, llm_model=stub).transform("hi", [])

    def test_function_calling_missing_name_raises_precise_error(self):
        stub = FunctionCallingStubLLM(
            result=FunctionCallResult(name="", arguments={"queries": ["a"]})
        )
        with pytest.raises(
            RAGTransformationOutputError,
            match="did not report a function name",
        ):
            _expander(None, llm_model=stub).transform("hi", [])

    def test_function_calling_runtime_error_wrapped_as_output_error(self):
        stub = FunctionCallingStubLLM(
            generate_error=RuntimeError(
                "The function calling model did not emit a call for 'expand_query'."
            )
        )
        with pytest.raises(
            RAGTransformationOutputError, match="Function calling failed"
        ):
            _expander(None, llm_model=stub).transform("hi", [])

    def test_function_calling_value_error_wrapped_as_output_error(self):
        stub = FunctionCallingStubLLM(generate_error=ValueError("bad function spec"))
        with pytest.raises(
            RAGTransformationOutputError, match="Function calling failed"
        ):
            _expander(None, llm_model=stub).transform("hi", [])

    def test_function_calling_type_error_wrapped_as_output_error(self):
        stub = FunctionCallingStubLLM(
            generate_error=TypeError("string indices must be integers")
        )
        with pytest.raises(
            RAGTransformationOutputError, match="Function calling failed"
        ):
            _expander(None, llm_model=stub).transform("hi", [])

    def test_decomposer_and_rewriter_function_calling_route(self):
        dec_stub = FunctionCallingStubLLM(
            result=FunctionCallResult(
                name="decompose_query", arguments={"queries": ["s1"]}
            )
        )
        decomposed = _decomposer(None, llm_model=dec_stub).transform("hi", [])
        assert decomposed.queries == ["s1"]
        dec_spec = FunctionCallingStubLLM.received_functions[-1][0]
        assert dec_spec["name"] == "decompose_query"
        properties = dec_spec["parameters"]["properties"]
        assert properties["queries"]["type"] == "array"
        assert properties["queries"]["items"] == {"type": "string"}
        assert dec_spec["parameters"]["required"] == ["queries"]

        rew_stub = FunctionCallingStubLLM(
            result=FunctionCallResult(name="rewrite_query", arguments={"query": "q"})
        )
        rewritten = _rewriter(None, llm_model=rew_stub).transform("hi", [])
        assert rewritten.queries == ["q"]
        rew_spec = FunctionCallingStubLLM.received_functions[-1][0]
        assert rew_spec["name"] == "rewrite_query"
        properties = rew_spec["parameters"]["properties"]
        assert properties["query"]["type"] == "string"
        assert rew_spec["parameters"]["required"] == ["query"]

    def test_expander_text_route_still_default_without_capability(self):
        raw = json.dumps({"name": "expand_query", "arguments": {"queries": ["a", "b"]}})
        result = _expander([raw]).transform("hi", [])
        assert result.queries == ["a", "b"]

    def test_unsupported_function_calling_method_raises_config_error(self):
        with pytest.raises(RAGTransformationConfigError, match="does not implement"):
            _expander(None, llm_model=_CapabilityOnlyStubLLM()).transform("hi", [])


class FakeLlama:
    """Captures ``create_chat_completion`` kwargs and returns a canned dict."""

    def __init__(self, result):
        self.result = result
        self.received = {}

    def create_chat_completion(self, **kwargs):
        self.received.update(kwargs)
        return self.result


class TestGGUFFunctionCalling:
    """``GGUFTextGenerationModel.generate_function_call`` envelope and params."""

    def _make_model(self, fake):
        instance = object.__new__(GGUFTextGenerationModel)
        instance.model = fake
        instance.max_tokens = 7
        instance.temperature = 0.1
        instance.frequency_penalty = 0.2
        return instance

    def _spec(self):
        return {
            "name": "expand_query",
            "description": "Expand the query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "queries": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["queries"],
            },
        }

    def test_generate_function_call_builds_tools_and_forces_choice(self):
        fake = FakeLlama(
            result={
                "choices": [
                    {
                        "message": {
                            "function_call": {
                                "name": "expand_query",
                                "arguments": '{"queries": ["x"]}',
                            }
                        }
                    }
                ]
            }
        )
        model = self._make_model(fake)
        spec = self._spec()
        returned = model.generate_function_call(
            messages=[{"role": "user", "content": "hi"}], functions=[spec]
        )

        assert returned == FunctionCallResult(
            name="expand_query", arguments='{"queries": ["x"]}'
        )
        assert fake.received["tools"] == [{"type": "function", "function": spec}]
        assert fake.received["tool_choice"] == {
            "type": "function",
            "function": {"name": "expand_query"},
        }
        assert fake.received["max_tokens"] == 7
        assert fake.received["temperature"] == 0.1
        assert fake.received["frequency_penalty"] == 0.2

    def test_generate_function_call_missing_call_raises(self):
        fake = FakeLlama(result={"choices": [{"message": {"content": "no call"}}]})
        model = self._make_model(fake)
        with pytest.raises(RuntimeError):
            model.generate_function_call(
                messages=[{"role": "user", "content": "hi"}],
                functions=[self._spec()],
            )

    def test_tool_calls_fallback_shape(self):
        fake = FakeLlama(
            result={
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "expand_query",
                                        "arguments": '{"queries": ["y"]}',
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        )
        model = self._make_model(fake)
        returned = model.generate_function_call(
            messages=[{"role": "user", "content": "hi"}],
            functions=[self._spec()],
        )
        assert returned == FunctionCallResult(
            name="expand_query", arguments='{"queries": ["y"]}'
        )

    @pytest.mark.parametrize(
        "message",
        [
            {"tool_calls": [{"id": "c_1"}]},
            {"tool_calls": [None]},
            {"tool_calls": "garbage"},
            {"tool_calls": {"function": {"name": "expand_query"}}},
            {"function_call": "garbage"},
            None,
        ],
    )
    def test_malformed_response_envelopes_normalize_to_runtime_error(self, message):
        fake = FakeLlama(result={"choices": [{"message": message}]})
        model = self._make_model(fake)
        with pytest.raises(RuntimeError, match="did not emit a call"):
            model.generate_function_call(
                messages=[{"role": "user", "content": "hi"}],
                functions=[self._spec()],
            )


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

    def test_arguments_as_string_drift_parses(self):
        raw = '{"name": "rewrite_query", "arguments": "{\\"query\\": \\"rewritten\\"}"}'
        result = _rewriter([raw]).transform("hi", [])
        assert result.queries == ["rewritten"]


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

    def test_arguments_as_string_drift_parses(self):
        raw = (
            '{"name": "expand_query", '
            '"arguments": "{\\"queries\\": [\\"a\\", \\"b\\"]}"}'
        )
        result = _expander([raw], n=3).transform("hi", [])
        assert result.queries == ["a", "b"]

    def test_bare_array_drift_parses(self):
        result = _expander(['["a", "b", "c"]'], n=3).transform("hi", [])
        assert result.queries == ["a", "b", "c"]


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

    def test_arguments_as_string_drift_parses(self):
        raw = (
            '{"name": "decompose_query", '
            '"arguments": "{\\"queries\\": [\\"s1\\", \\"s2\\"]}"}'
        )
        result = _decomposer([raw], cap=None).transform("hi", [])
        assert result.queries == ["s1", "s2"]

    def test_bare_array_drift_parses(self):
        result = _decomposer(['["s1", "s2"]'], cap=None).transform("hi", [])
        assert result.queries == ["s1", "s2"]


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

    def test_transformation_llm_defaults_to_qwen_15b(self):
        """The shared schema's model placeholder names the 1.5B Qwen."""
        expected = {"component": "Qwen25_15BInstruct", "params": {}}
        for technique in (LLMQueryRewriter, LLMQueryExpander, LLMQueryDecomposer):
            schema = technique.get_schema()
            assert schema["properties"]["llm_model"]["placeholder"] == expected

    def test_defaults_resolution_carries_the_qwen_llm(self):
        """The placeholder resolves into real defaults via the registry."""
        registry = {
            name: {"class": klass, "schema": klass.get_schema()}
            for name, klass in {
                "LLMQueryRewriter": LLMQueryRewriter,
                "Qwen25_15BInstruct": GGUFTextGenerationModel,
                "DefaultQueryRewritingPrompt": DefaultQueryRewritingPrompt,
            }.items()
        }
        resolved = resolve_component_defaults("LLMQueryRewriter", registry)
        assert resolved["llm_model"]["component"] == "Qwen25_15BInstruct"
        # The GGUF schema placeholders are inherited through the nested ref.
        assert resolved["llm_model"]["params"]["max_tokens"] == 100


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
