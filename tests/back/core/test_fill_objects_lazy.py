"""Tests for the optional lazy resolution in ``fill_objects``.

``fill_objects`` keeps instantiating component references eagerly by default,
which every existing caller relies on. RAG passes ``lazy_model_classes`` so a
nested text-to-text model becomes a :class:`LazyLLM` proxy instead of being
constructed during configuration assembly.
"""

from __future__ import annotations

from typing import Any, Dict

import pytest
from pydantic import ValidationError

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    int_field,
    schema_field,
)
from DashAI.back.core.schema_fields.utils import fill_objects
from DashAI.back.models.lazy_llm import LazyLLM
from DashAI.back.models.RAG.transformation import (
    BaseQueryTransformation,
    TransformationFactory,
)
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)


class _EmptySchema(BaseSchema):
    """Empty schema shared by the test components."""


class _EagerComponent:
    """Counting component that must be constructed eagerly."""

    construction_count = 0

    def __init__(self, **kwargs: Any) -> None:
        type(self).construction_count += 1
        self.kwargs = kwargs


class _LazyComponent(TextToTextGenerationTaskModel):
    """Counting text-to-text component that must be constructed on first use."""

    SCHEMA = _EmptySchema
    SUPPORTS_FUNCTION_CALLING = True
    construction_count = 0
    close_count = 0

    def __init__(self, **kwargs: Any) -> None:
        type(self).construction_count += 1
        self.kwargs = kwargs

    def generate(self, prompt):
        return ["lazy answer"]

    def close(self) -> None:
        type(self).close_count += 1


class _ValidatingLLMSchema(BaseSchema):
    """Schema with a required parameter that rejects malformed input."""

    context_window: schema_field(
        int_field(gt=0),
        placeholder=2048,
        description="Context window used by the stub LLM.",
    )  # type: ignore


class _ValidatingLazyComponent(TextToTextGenerationTaskModel):
    """Lazy stub whose schema must be validated during assembly."""

    SCHEMA = _ValidatingLLMSchema
    SUPPORTS_FUNCTION_CALLING = True
    construction_count = 0

    def __init__(self, **kwargs: Any) -> None:
        type(self).construction_count += 1
        self.kwargs = kwargs

    def generate(self, prompt):
        return ["validated answer"]


class _TransformerSchema(BaseSchema):
    """Schema with one nested LLM reference for the transformer stub."""

    llm_model: schema_field(
        component_field(parent="TextToTextGenerationTaskModel"),
        placeholder={
            "component": "_ValidatingLazyComponent",
            "params": {"context_window": 2048},
        },
        description="Nested evaluation LLM.",
    )  # type: ignore


class _StubTransformer(BaseQueryTransformation):
    """Counting transformer that accepts a lazily resolved nested LLM."""

    SCHEMA = _TransformerSchema
    construction_count = 0

    def __init__(self, **kwargs: Any) -> None:
        type(self).construction_count += 1
        self.kwargs = kwargs

    def transform(self, message, history):
        return None


class _OuterSchema(BaseSchema):
    """Schema with one nested component reference."""

    nested: schema_field(
        component_field(parent="TextToTextGenerationTaskModel"),
        placeholder={"component": "_EagerComponent", "params": {}},
        description="Nested component under test.",
    )  # type: ignore


def _registry() -> Dict[str, Any]:
    """Minimal registry mapping names to the classes under test."""
    return {
        "_EagerComponent": {"class": _EagerComponent},
        "_LazyComponent": {"class": _LazyComponent},
        "_ValidatingLazyComponent": {"class": _ValidatingLazyComponent},
        "_StubTransformer": {"class": _StubTransformer},
    }


def _instance(component: str, params: Dict[str, Any] | None = None) -> _OuterSchema:
    """Build a validated outer schema with one component reference."""
    return _OuterSchema.model_validate(
        {
            "nested": {
                "component": component,
                "params": {} if params is None else params,
            }
        }
    )


def test_fill_objects_constructs_eagerly_by_default() -> None:
    """Without ``lazy_model_classes`` every component is instantiated."""
    _EagerComponent.construction_count = 0

    resolved = fill_objects(_instance("_EagerComponent", {"x": 1}), _registry())

    assert isinstance(resolved["nested"], _EagerComponent)
    assert resolved["nested"].kwargs == {"x": 1}
    assert _EagerComponent.construction_count == 1


def test_fill_objects_empty_lazy_tuple_keeps_eager_behavior() -> None:
    """An explicitly empty tuple is the same as the default."""
    _EagerComponent.construction_count = 0

    resolved = fill_objects(
        _instance("_EagerComponent"), _registry(), lazy_model_classes=()
    )

    assert isinstance(resolved["nested"], _EagerComponent)
    assert _EagerComponent.construction_count == 1


def test_fill_objects_wraps_matching_components_lazily() -> None:
    """A matching class becomes a ``LazyLLM`` and is not constructed."""
    _LazyComponent.construction_count = 0
    _LazyComponent.close_count = 0

    resolved = fill_objects(
        _instance("_LazyComponent", {"temperature": 0.2}),
        _registry(),
        lazy_model_classes=(TextToTextGenerationTaskModel,),
    )
    lazy_model = resolved["nested"]

    assert isinstance(lazy_model, LazyLLM)
    assert lazy_model.is_loaded is False
    assert _LazyComponent.construction_count == 0
    assert lazy_model.supports_function_calling() is True
    assert _LazyComponent.construction_count == 0

    assert lazy_model.generate([]) == ["lazy answer"]
    assert _LazyComponent.construction_count == 1
    assert lazy_model.is_loaded is True
    assert lazy_model.kwargs == {"temperature": 0.2}

    lazy_model.close()
    assert lazy_model.is_loaded is False
    assert _LazyComponent.close_count == 1

    # The proxy stays reusable after its real model is released.
    assert lazy_model.generate([]) == ["lazy answer"]
    assert _LazyComponent.construction_count == 2


def test_fill_objects_leaves_non_matching_components_eager() -> None:
    """A lazy tuple only affects subclasses of its entries."""
    _EagerComponent.construction_count = 0

    resolved = fill_objects(
        _instance("_EagerComponent"),
        _registry(),
        lazy_model_classes=(TextToTextGenerationTaskModel,),
    )

    assert isinstance(resolved["nested"], _EagerComponent)
    assert _EagerComponent.construction_count == 1


def test_fill_objects_rejects_invalid_lazy_params_without_constructing() -> None:
    """Invalid nested LLM parameters fail during assembly, not on first use."""
    _ValidatingLazyComponent.construction_count = 0

    with pytest.raises(ValidationError):
        fill_objects(
            _instance("_ValidatingLazyComponent", {"context_window": "not-a-number"}),
            _registry(),
            lazy_model_classes=(TextToTextGenerationTaskModel,),
        )

    assert _ValidatingLazyComponent.construction_count == 0


def test_fill_objects_accepts_valid_lazy_params_without_constructing() -> None:
    """Valid nested LLM parameters still yield a proxy and build nothing."""
    _ValidatingLazyComponent.construction_count = 0

    resolved = fill_objects(
        _instance("_ValidatingLazyComponent", {"context_window": 2048}),
        _registry(),
        lazy_model_classes=(TextToTextGenerationTaskModel,),
    )

    lazy_model = resolved["nested"]
    assert isinstance(lazy_model, LazyLLM)
    assert lazy_model.is_loaded is False
    assert _ValidatingLazyComponent.construction_count == 0


def test_transformation_factory_rejects_invalid_nested_llm_params() -> None:
    """The factory validates a nested LLM during assembly without building it."""
    _ValidatingLazyComponent.construction_count = 0
    _StubTransformer.construction_count = 0

    factory = TransformationFactory(_registry())

    with pytest.raises(ValidationError):
        factory.create(
            "_StubTransformer",
            {
                "llm_model": {
                    "component": "_ValidatingLazyComponent",
                    "params": {"context_window": "not-a-number"},
                }
            },
        )

    assert _ValidatingLazyComponent.construction_count == 0
    assert _StubTransformer.construction_count == 0


def test_transformation_factory_keeps_valid_nested_llm_lazy() -> None:
    """A valid nested LLM becomes a proxy that is not constructed at assembly."""
    _ValidatingLazyComponent.construction_count = 0
    _StubTransformer.construction_count = 0

    factory = TransformationFactory(_registry())
    result = factory.create(
        "_StubTransformer",
        {
            "llm_model": {
                "component": "_ValidatingLazyComponent",
                "params": {"context_window": 2048},
            }
        },
    )

    assert _StubTransformer.construction_count == 1
    assert isinstance(result.model.kwargs["llm_model"], LazyLLM)
    assert result.model.kwargs["llm_model"].is_loaded is False
    assert _ValidatingLazyComponent.construction_count == 0
