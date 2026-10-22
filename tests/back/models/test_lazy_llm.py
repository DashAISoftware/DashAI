"""Tests for the :class:`LazyLLM` proxy.

The proxy must defer construction of the real text-to-text model until the
first generation, answer capability queries without loading, and release the
real model on ``close`` so a later stage can reclaim its VRAM.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest

from DashAI.back.models.lazy_llm import LazyLLM
from DashAI.back.models.text_to_text_generation_model import (
    FunctionCallResult,
    TextToTextGenerationTaskModel,
)


class FakeRealLLM(TextToTextGenerationTaskModel):
    """Counting stand-in for a lazily constructed backend."""

    construction_count = 0
    close_count = 0

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        type(self).construction_count += 1
        self.parameters = {} if parameters is None else parameters
        self.closed = False

    def generate(self, prompt):
        return ["fake answer"]

    def generate_function_call(self, messages, functions):
        return FunctionCallResult(name=functions[0]["name"], arguments={"ok": True})

    @classmethod
    def supports_function_calling(cls):
        return True

    def close(self) -> None:
        type(self).close_count += 1
        self.closed = True


class FactoryError(RuntimeError):
    """Error raised by a failing factory."""


@pytest.fixture(autouse=True)
def _reset_counters():
    FakeRealLLM.construction_count = 0
    FakeRealLLM.close_count = 0


def _lazy(**kwargs: Any) -> LazyLLM:
    return LazyLLM(lambda: FakeRealLLM({"temperature": 0.2}), label="fake", **kwargs)


def test_creation_does_not_construct_the_real_model():
    """Creating the proxy must not instantiate the real backend."""
    proxy = _lazy()

    assert FakeRealLLM.construction_count == 0
    assert proxy.is_loaded is False


def test_supports_function_calling_does_not_construct_the_model():
    """Capability is answered from the captured class flag."""
    proxy = _lazy(supports_function_calling=True)

    assert proxy.supports_function_calling() is True
    assert FakeRealLLM.construction_count == 0
    assert proxy.is_loaded is False


def test_supports_function_calling_defaults_to_false():
    """The default capability flag is ``False``."""
    proxy = _lazy()

    assert proxy.supports_function_calling() is False


def test_generate_constructs_once_and_reuses_the_instance():
    """The first generation constructs; subsequent calls reuse it."""
    proxy = _lazy()
    messages = [{"role": "user", "content": "hi"}]

    assert proxy.generate(messages) == ["fake answer"]
    assert proxy.generate(messages) == ["fake answer"]

    assert FakeRealLLM.construction_count == 1
    assert proxy.is_loaded is True


def test_generate_function_call_uses_the_same_instance():
    """Function calling delegates to the instance created by ``generate``."""
    proxy = _lazy()
    messages = [{"role": "user", "content": "hi"}]
    functions = [{"name": "expand_query", "parameters": {}}]

    proxy.generate(messages)
    result = proxy.generate_function_call(messages, functions)

    assert result == FunctionCallResult(name="expand_query", arguments={"ok": True})
    assert FakeRealLLM.construction_count == 1


def test_close_releases_and_next_use_reconstructs():
    """``close`` is idempotent and a later use builds a fresh instance."""
    proxy = _lazy()
    messages = [{"role": "user", "content": "hi"}]

    proxy.generate(messages)
    proxy.close()

    assert FakeRealLLM.close_count == 1
    assert proxy.is_loaded is False

    proxy.close()
    assert FakeRealLLM.close_count == 1

    proxy.generate(messages)
    assert FakeRealLLM.construction_count == 2
    assert proxy.is_loaded is True


def test_getattr_delegates_to_the_real_model():
    """Non-underscore attributes come from the real model."""
    proxy = _lazy()

    assert proxy.parameters == {"temperature": 0.2}
    assert FakeRealLLM.construction_count == 1


def test_getattr_private_and_missing_names_raise_attribute_error():
    """Private or unknown attributes must not recurse into the proxy state."""
    proxy = _lazy()

    for name in ("_does_not_exist", "does_not_exist"):
        with pytest.raises(AttributeError):
            getattr(proxy, name)

    assert FakeRealLLM.construction_count == 1


def test_factory_error_propagates_unchanged():
    """Construction errors (for example GGUF load failures) pass through."""
    error = FactoryError("could not load GGUF")

    def _raising_factory() -> FakeRealLLM:
        raise error

    proxy = LazyLLM(_raising_factory, label="broken")

    with pytest.raises(FactoryError) as exc_info:
        proxy.generate([{"role": "user", "content": "hi"}])

    assert exc_info.value is error
    assert proxy.is_loaded is False


def test_factory_returning_non_llm_raises_type_error():
    """A factory returning the wrong type is reported clearly."""
    proxy = LazyLLM(lambda: object(), label="broken")

    with pytest.raises(TypeError, match="TextToTextGenerationTaskModel"):
        proxy.generate([{"role": "user", "content": "hi"}])


def test_failed_backend_close_is_logged_and_does_not_raise(caplog):
    """A raising backend ``close`` is logged at WARNING, never propagated."""

    class _FailingCloseLLM(FakeRealLLM):
        def close(self) -> None:
            raise RuntimeError("backend close exploded")

    proxy = LazyLLM(lambda: _FailingCloseLLM(), label="broken-close")
    proxy.generate([{"role": "user", "content": "hi"}])

    with caplog.at_level(logging.WARNING, logger="DashAI.back.models.lazy_llm"):
        proxy.close()

    assert proxy.is_loaded is False
    assert any(
        "broken-close" in record.getMessage() and record.levelno == logging.WARNING
        for record in caplog.records
    ), "Expected a warning naming the lazy LLM label."

    # The proxy stays safe and can be reused after a failed close.
    proxy.generate([{"role": "user", "content": "hi"}])
    assert proxy.is_loaded is True


def test_repr_reports_label_and_loaded_without_constructing():
    """``repr`` never triggers construction."""
    proxy = _lazy()

    assert "fake" in repr(proxy)
    assert "loaded=False" in repr(proxy)
    assert FakeRealLLM.construction_count == 0

    proxy.generate([{"role": "user", "content": "hi"}])

    assert "loaded=True" in repr(proxy)
