"""Smoke tests for the RAG query transformation module.

Builds a real ``ComponentRegistry`` from a test-only component list and
exercises registry resolution plus end-to-end construction through
``TransformationFactory`` with a stub LLM. The transformation components are
registered by the feature in ``initial_components``; the test still assembles
its own registry so it stays independent of that global list.
"""

from __future__ import annotations

import json

import pytest

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.prompts.transformation import (
    CustomQueryDecompositionPrompt,
    CustomQueryExpansionPrompt,
    CustomQueryRewritingPrompt,
    DefaultQueryDecompositionPrompt,
    DefaultQueryExpansionPrompt,
    DefaultQueryRewritingPrompt,
)
from DashAI.back.models.RAG.RAG_defaults import DEFAULT_FUNCTION_CALL_MAX_TRIALS
from DashAI.back.models.RAG.transformation import (
    BaseQueryTransformation,
    LLMQueryDecomposer,
    LLMQueryExpander,
    LLMQueryRewriter,
    QueryTransformationResult,
    TransformationFactory,
)
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)


class TransformationStubLLMSchema(BaseSchema):
    """Empty schema for the transformation stub LLM."""


class TransformationStubLLM(TextToTextGenerationTaskModel):
    """Stub LLM that answers according to the technique named in the prompt."""

    SCHEMA = TransformationStubLLMSchema

    def __init__(self, **kwargs):
        self.parameters = dict(kwargs)

    def generate(self, prompt):
        text = prompt[0]["content"]
        if '"rewrite_query"' in text:
            return [
                '{"name": "rewrite_query", "arguments": {"query": "rewritten query"}}'
            ]
        if '"expand_query"' in text:
            return [
                json.dumps(
                    {
                        "name": "expand_query",
                        "arguments": {"queries": ["q1", "q2"]},
                    }
                )
            ]
        if '"decompose_query"' in text:
            return [
                json.dumps(
                    {
                        "name": "decompose_query",
                        "arguments": {"queries": ["s1", "s2", "s3"]},
                    }
                )
            ]
        return ["[]"]


COMPONENTS = [
    # prompts
    DefaultQueryRewritingPrompt,
    CustomQueryRewritingPrompt,
    DefaultQueryExpansionPrompt,
    CustomQueryExpansionPrompt,
    DefaultQueryDecompositionPrompt,
    CustomQueryDecompositionPrompt,
    # transformers
    LLMQueryRewriter,
    LLMQueryExpander,
    LLMQueryDecomposer,
    # stub LLM
    TransformationStubLLM,
]

TRANSFORMER_NAMES = {"LLMQueryRewriter", "LLMQueryExpander", "LLMQueryDecomposer"}
PROMPT_NAMES = {
    "DefaultQueryRewritingPrompt",
    "CustomQueryRewritingPrompt",
    "DefaultQueryExpansionPrompt",
    "CustomQueryExpansionPrompt",
    "DefaultQueryDecompositionPrompt",
    "CustomQueryDecompositionPrompt",
}


@pytest.fixture(scope="module")
def registry() -> ComponentRegistry:
    return ComponentRegistry(COMPONENTS)


# ===================================================================
# smoke 1: registry resolution
# ===================================================================


class TestRegistryResolution:
    """Components register and resolve without violating the MRO rule."""

    def test_transformers_resolve_to_base_type(self, registry):
        for name in TRANSFORMER_NAMES:
            assert name in registry
            assert issubclass(registry[name]["class"], BaseQueryTransformation)
            assert registry[name]["type"] == "QueryTransformation"

    def test_prompts_resolve(self, registry):
        for name in PROMPT_NAMES:
            assert name in registry

    def test_transformer_children_of_base(self, registry):
        children = registry.get_child_components(
            "BaseQueryTransformation", recursive=True
        )
        assert {child["name"] for child in children} == TRANSFORMER_NAMES

    def test_rewriting_prompt_children(self, registry):
        children = registry.get_child_components(
            "QueryRewritingPrompt", recursive=False
        )
        assert {child["name"] for child in children} == {
            "DefaultQueryRewritingPrompt",
            "CustomQueryRewritingPrompt",
        }

    def test_registration_does_not_raise(self):
        ComponentRegistry([LLMQueryRewriter, LLMQueryExpander, LLMQueryDecomposer])


# ===================================================================
# smoke 4: technique metadata
# ===================================================================


class TestTechniqueMetadata:
    """Transformers and prompts expose inert technique metadata."""

    def test_transformer_metadata_pairs_technique_with_prompt_family(self, registry):
        assert registry["LLMQueryRewriter"]["metadata"] == {
            "technique": "rewriting",
            "prompt_parent": "QueryRewritingPrompt",
        }
        assert registry["LLMQueryExpander"]["metadata"] == {
            "technique": "expansion",
            "prompt_parent": "QueryExpansionPrompt",
        }
        assert registry["LLMQueryDecomposer"]["metadata"] == {
            "technique": "decomposition",
            "prompt_parent": "QueryDecompositionPrompt",
        }

    def test_prompt_metadata_carries_technique_and_variant(self, registry):
        default_metadata = registry["DefaultQueryRewritingPrompt"]["metadata"]
        assert default_metadata["technique"] == "rewriting"
        assert default_metadata["variant"] == "default"

        custom_metadata = registry["CustomQueryRewritingPrompt"]["metadata"]
        assert custom_metadata["technique"] == "rewriting"
        assert custom_metadata["variant"] == "custom"

    def test_prompt_variants_for_every_technique(self, registry):
        expected = {
            "DefaultQueryExpansionPrompt": ("expansion", "default"),
            "CustomQueryExpansionPrompt": ("expansion", "custom"),
            "DefaultQueryDecompositionPrompt": ("decomposition", "default"),
            "CustomQueryDecompositionPrompt": ("decomposition", "custom"),
        }
        for name, (technique, variant) in expected.items():
            metadata = registry[name]["metadata"]
            assert metadata["technique"] == technique
            assert metadata["variant"] == variant


# ===================================================================
# smoke 2: factory builds full transformers
# ===================================================================


class TestFactoryBuildsTransformers:
    """``TransformationFactory`` resolves nested prompt/LLM instances."""

    def test_rewriter_end_to_end(self, registry):
        params = {
            "prompt": {
                "component": "DefaultQueryRewritingPrompt",
                "params": {"language": "es"},
            },
            "llm_model": {
                "component": "TransformationStubLLM",
                "params": {"stub_marker": "rw"},
            },
            "history_window": 1,
            "function_call_max_trials": DEFAULT_FUNCTION_CALL_MAX_TRIALS,
        }
        result = TransformationFactory(registry).create("LLMQueryRewriter", params)
        model = result.model
        assert isinstance(model, LLMQueryRewriter)
        assert not isinstance(model.prompt, dict)
        assert not isinstance(model.llm_model, dict)

        output = model.transform(
            "¿Qué es DashAI?",
            [
                {"role": "user", "content": "hola"},
                {"role": "assistant", "content": "buenas"},
            ],
        )
        assert output.queries == ["rewritten query"]

    def test_expander_end_to_end(self, registry):
        params = {
            "prompt": {
                "component": "DefaultQueryExpansionPrompt",
                "params": {"language": "en"},
            },
            "llm_model": {
                "component": "TransformationStubLLM",
                "params": {"stub_marker": "exp"},
            },
            "history_window": 2,
            "n_queries": 2,
            "function_call_max_trials": DEFAULT_FUNCTION_CALL_MAX_TRIALS,
        }
        result = TransformationFactory(registry).create("LLMQueryExpander", params)
        output = result.model.transform("hello", [])
        assert output.queries == ["q1", "q2"]

    def test_decomposer_end_to_end(self, registry):
        params = {
            "prompt": {
                "component": "DefaultQueryDecompositionPrompt",
                "params": {"language": "en"},
            },
            "llm_model": {
                "component": "TransformationStubLLM",
                "params": {"stub_marker": "dec"},
            },
            "history_window": 2,
            "max_subqueries": None,
            "function_call_max_trials": DEFAULT_FUNCTION_CALL_MAX_TRIALS,
        }
        result = TransformationFactory(registry).create("LLMQueryDecomposer", params)
        output = result.model.transform("complex question", [])
        assert output.queries == ["s1", "s2", "s3"]

    def test_factory_accepts_pre_feature_params_without_trials(self, registry):
        """Persisted params from before the parameter existed still validate."""
        params = {
            "prompt": {
                "component": "DefaultQueryRewritingPrompt",
                "params": {"language": "en"},
            },
            "llm_model": {
                "component": "TransformationStubLLM",
                "params": {"stub_marker": "legacy"},
            },
            "history_window": 1,
        }

        model = TransformationFactory(registry).create("LLMQueryRewriter", params).model

        assert model.function_call_max_trials == DEFAULT_FUNCTION_CALL_MAX_TRIALS


# ===================================================================
# smoke 3: typed result
# ===================================================================


class TestQueryTransformationResult:
    """The typed result dataclass behaves as a contract."""

    def test_result_is_dataclass_with_str_queries(self):
        result = QueryTransformationResult(queries=["a", "b"])
        assert all(isinstance(query, str) for query in result.queries)
        assert result.queries == ["a", "b"]

    def test_to_list_returns_a_copy(self):
        result = QueryTransformationResult(queries=["a", "b"])
        copied = result.to_list()
        assert copied == ["a", "b"]
        assert copied is not result.queries
