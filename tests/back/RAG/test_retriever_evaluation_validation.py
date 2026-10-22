"""Unit tests for the LLM-evaluated retriever validation service.

Covers the nested ``llm_model`` and ``prompt`` references of the two
LLM-evaluated composite retrievers: missing/invalid refs, wrong prompt
family, unregistered LLM, wrong param container types, blank custom
templates and the schema-driven default resolution.

The retriever component names are the fixed cross-workstream contract
strings; the outer classes are lightweight stubs, since the service only
inspects their ``EVALUATION_PROMPT_BASE`` marker.
"""

from __future__ import annotations

import pytest

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.models.RAG.prompts.evaluation import (
    CustomRetrievalSufficiencyPrompt,
    DefaultRetrievalSufficiencyPrompt,
    RetrievalSufficiencyPrompt,
)
from DashAI.back.models.RAG.prompts.transformation import DefaultQueryRewritingPrompt
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from DashAI.back.services.RAG.retriever_evaluation_validation import (
    DEFAULT_SUFFICIENCY_PROMPT_NAMES,
    LLM_EVALUATED_RETRIEVER_NAMES,
    RetrieverEvaluationValidationService,
)

# ===================================================================
# stubs / registry
# ===================================================================


class _EmptySchema(BaseSchema):
    """Empty schema for the stub LLM."""


class StubEvaluationLLM(TextToTextGenerationTaskModel):
    """Minimal registered LLM used in the fake registry."""

    SCHEMA = _EmptySchema

    def __init__(self, **kwargs):
        self.parameters = {}

    def generate(self, prompt):
        return ["stub"]


class StubDepthRetriever:
    """Stand-in for ``LLMEvaluatedDepthRetriever`` (owned by workstream B)."""


class StubEnsembleRetriever:
    """Stand-in for ``LLMEvaluatedEnsembleRetriever`` (owned by workstream B)."""


_RETRIEVER_SCHEMA = {
    "properties": {
        "llm_model": {
            "placeholder": {"component": "StubEvaluationLLM", "params": {}},
        },
        "prompt": {
            "placeholder": {
                "component": "DefaultRetrievalSufficiencyPrompt",
                "params": {},
            },
        },
        "top_k": {"placeholder": 5},
        "function_call_max_trials": {"placeholder": 3},
    }
}

_LLM_SCHEMA = {
    "properties": {
        "max_tokens": {"placeholder": 100},
        "temperature": {"placeholder": 0.7},
    }
}

_DEFAULT_PROMPT_SCHEMA = {
    "properties": {
        "language": {"placeholder": "en"},
        "template": {"placeholder": ""},
    }
}

_CUSTOM_PROMPT_SCHEMA = {
    "properties": {
        "template": {"placeholder": ""},
    }
}


class _FakeRegistry(dict):
    """Minimal registry mapping names to ``{"class", "schema"}`` dicts."""

    def __init__(self):
        super().__init__(
            {
                "LLMEvaluatedDepthRetriever": {
                    "class": StubDepthRetriever,
                    "schema": _RETRIEVER_SCHEMA,
                },
                "LLMEvaluatedEnsembleRetriever": {
                    "class": StubEnsembleRetriever,
                    "schema": _RETRIEVER_SCHEMA,
                },
                "StubEvaluationLLM": {
                    "class": StubEvaluationLLM,
                    "schema": _LLM_SCHEMA,
                },
                "DefaultRetrievalSufficiencyPrompt": {
                    "class": DefaultRetrievalSufficiencyPrompt,
                    "schema": _DEFAULT_PROMPT_SCHEMA,
                },
                "CustomRetrievalSufficiencyPrompt": {
                    "class": CustomRetrievalSufficiencyPrompt,
                    "schema": _CUSTOM_PROMPT_SCHEMA,
                },
                "DefaultQueryRewritingPrompt": {
                    "class": DefaultQueryRewritingPrompt,
                    "schema": {"properties": {"template": {"placeholder": ""}}},
                },
            }
        )


def _service() -> RetrieverEvaluationValidationService:
    """Build a validation service over the fake registry with a no-op validator."""
    return RetrieverEvaluationValidationService(
        _FakeRegistry(), lambda name, template: None
    )


def _ref(
    retriever: str = "LLMEvaluatedDepthRetriever",
    prompt_component: str = "DefaultRetrievalSufficiencyPrompt",
    prompt_params: dict | None = None,
    llm_component: str = "StubEvaluationLLM",
    llm_params: object = None,
) -> dict:
    """Build a retriever reference with the fixed shape."""
    return {
        "component": retriever,
        "params": {
            "prompt": {
                "component": prompt_component,
                "params": {} if prompt_params is None else prompt_params,
            },
            "llm_model": {
                "component": llm_component,
                "params": {} if llm_params is None else llm_params,
            },
        },
    }


# ===================================================================
# constants
# ===================================================================


class TestConstants:
    """The fixed cross-workstream name sets are exposed."""

    def test_retriever_names(self):
        assert (
            frozenset({"LLMEvaluatedDepthRetriever", "LLMEvaluatedEnsembleRetriever"})
            == LLM_EVALUATED_RETRIEVER_NAMES
        )

    def test_default_prompt_names(self):
        assert (
            frozenset({"DefaultRetrievalSufficiencyPrompt"})
            == DEFAULT_SUFFICIENCY_PROMPT_NAMES
        )

    def test_anchor_is_subclass_target(self):
        assert issubclass(DefaultRetrievalSufficiencyPrompt, RetrievalSufficiencyPrompt)


# ===================================================================
# validate
# ===================================================================


class TestValidate:
    """``validate`` accepts well-formed refs and rejects malformed ones."""

    @pytest.mark.parametrize(
        "retriever",
        ["LLMEvaluatedDepthRetriever", "LLMEvaluatedEnsembleRetriever"],
    )
    def test_valid_ref_accepted(self, retriever):
        _service().validate(_ref(retriever=retriever))

    def test_non_dict_ref_rejected(self):
        with pytest.raises(ValueError, match="must be a dict"):
            _service().validate("not a dict")

    def test_missing_component_rejected(self):
        with pytest.raises(ValueError, match="component"):
            _service().validate({"params": {}})

    def test_missing_params_rejected(self):
        with pytest.raises(ValueError, match="params"):
            _service().validate({"component": "LLMEvaluatedDepthRetriever"})

    def test_unregistered_retriever_rejected(self):
        with pytest.raises(ValueError, match="not registered"):
            _service().validate(_ref(retriever="NotARetriever"))

    @pytest.mark.parametrize(
        "retriever",
        ["LLMEvaluatedDepthRetriever", "LLMEvaluatedEnsembleRetriever"],
    )
    def test_missing_prompt_rejected(self, retriever):
        ref = _ref(retriever=retriever)
        del ref["params"]["prompt"]
        with pytest.raises(ValueError, match="prompt"):
            _service().validate(ref)

    def test_invalid_prompt_ref_rejected(self):
        ref = _ref()
        ref["params"]["prompt"] = "not a ref"
        with pytest.raises(ValueError, match="prompt"):
            _service().validate(ref)

    def test_wrong_prompt_family_rejected(self):
        with pytest.raises(ValueError, match="RetrievalSufficiencyPrompt"):
            _service().validate(_ref(prompt_component="DefaultQueryRewritingPrompt"))

    def test_prompt_params_wrong_type_rejected(self):
        ref = _ref()
        ref["params"]["prompt"]["params"] = "not a dict"
        with pytest.raises(ValueError, match="must be a dict"):
            _service().validate(ref)

    @pytest.mark.parametrize(
        "retriever",
        ["LLMEvaluatedDepthRetriever", "LLMEvaluatedEnsembleRetriever"],
    )
    def test_missing_llm_rejected(self, retriever):
        ref = _ref(retriever=retriever)
        del ref["params"]["llm_model"]
        with pytest.raises(ValueError, match="llm_model"):
            _service().validate(ref)

    def test_unregistered_llm_rejected(self):
        with pytest.raises(ValueError, match="not registered"):
            _service().validate(_ref(llm_component="NonexistentLLM"))

    def test_llm_params_wrong_type_rejected(self):
        ref = _ref()
        ref["params"]["llm_model"]["params"] = "not a dict"
        with pytest.raises(ValueError, match="must be a dict"):
            _service().validate(ref)

    def test_blank_custom_template_rejected(self):
        with pytest.raises(ValueError, match="blank"):
            _service().validate(
                _ref(
                    prompt_component="CustomRetrievalSufficiencyPrompt",
                    prompt_params={"template": "   "},
                )
            )

    def test_missing_custom_template_rejected(self):
        with pytest.raises(ValueError, match="blank"):
            _service().validate(
                _ref(prompt_component="CustomRetrievalSufficiencyPrompt")
            )

    def test_default_prompt_blank_template_allowed(self):
        _service().validate(
            _ref(
                prompt_component="DefaultRetrievalSufficiencyPrompt",
                prompt_params={"template": ""},
            )
        )


# ===================================================================
# apply defaults
# ===================================================================


class TestApplyDefaults:
    """``apply_defaults`` resolves nested schema defaults without clobbering."""

    def test_fills_nested_defaults(self):
        ref = _ref()
        _service().apply_defaults(ref)
        params = ref["params"]
        assert params["top_k"] == 5
        assert params["llm_model"]["params"]["max_tokens"] == 100
        assert params["llm_model"]["params"]["temperature"] == 0.7
        assert params["prompt"]["params"]["language"] == "en"

    def test_preserves_user_values(self):
        ref = _ref(
            prompt_component="CustomRetrievalSufficiencyPrompt",
            prompt_params={"template": "Q:{input} C:{chunks}"},
            llm_params={"temperature": 0.1},
        )
        _service().apply_defaults(ref)
        params = ref["params"]
        assert params["llm_model"]["params"]["temperature"] == 0.1
        assert params["llm_model"]["params"]["max_tokens"] == 100
        assert params["prompt"]["params"]["template"] == "Q:{input} C:{chunks}"

    def test_absent_ref_is_noop(self):
        _service().apply_defaults({})

    @pytest.mark.parametrize(
        "retriever",
        ["LLMEvaluatedDepthRetriever", "LLMEvaluatedEnsembleRetriever"],
    )
    def test_applies_for_both_retrievers(self, retriever):
        ref = _ref(retriever=retriever)
        _service().apply_defaults(ref)
        assert ref["params"]["top_k"] == 5
        assert ref["params"]["function_call_max_trials"] == 3

    def test_recursive_defaults_fill_nested_llm_evaluated_children(self):
        nested = _ref()
        parent = {
            "component": "ParallelRetriever",
            "params": {"merge_strategy": "round_robin", "children": [nested]},
        }

        _service().apply_defaults_recursive(parent)

        assert nested["params"]["function_call_max_trials"] == 3
        assert nested["params"]["top_k"] == 5
        assert nested["params"]["llm_model"]["params"]["max_tokens"] == 100
