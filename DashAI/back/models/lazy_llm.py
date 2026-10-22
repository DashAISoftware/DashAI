"""Lazy proxy for text-to-text generation models.

RAG stages each own a differently configured LLM, but only one of them is
needed at a time. Constructing every backend eagerly keeps all of them resident
for the whole pipeline, which can exceed the available VRAM. :class:`LazyLLM`
defers construction until the first generation and releases the real model when
its stage ends, so the next stage can load a different checkpoint.
"""

from __future__ import annotations

import gc
import logging
from collections.abc import Callable
from typing import Any

from DashAI.back.models.text_to_text_generation_model import (
    FunctionCallResult,
    TextToTextGenerationTaskModel,
)

log = logging.getLogger(__name__)


class LazyLLM(TextToTextGenerationTaskModel):
    """Text-to-text model built on first use and released on ``close``.

    Accessing any non-private attribute not defined by this proxy delegates to
    the real backend via ``__getattr__`` and therefore loads it on first access.
    Capability queries such as :meth:`supports_function_calling` are answered
    explicitly and never trigger construction.

    Parameters
    ----------
    factory : Callable[[], TextToTextGenerationTaskModel]
        Callable that constructs the real backend. It runs on the first
        generation (or first attribute access) and again after every
        :meth:`close`.
    label : str
        Human-readable label used in diagnostics and ``repr``.
    supports_function_calling : bool, optional
        Whether the real backend supports function calling. Captured at
        construction time so callers can choose a route without loading it.
    """

    def __init__(
        self,
        factory: Callable[[], TextToTextGenerationTaskModel],
        *,
        label: str,
        supports_function_calling: bool = False,
    ) -> None:
        # Deliberately skip the abstract base ``__init__``: this proxy owns no
        # backend state until the factory runs.
        self._factory = factory
        self._label = label
        self._supports_function_calling = supports_function_calling
        self._model: TextToTextGenerationTaskModel | None = None

    @property
    def is_loaded(self) -> bool:
        """Whether the real model has been constructed and not closed."""
        return self._model is not None

    def _ensure_model(self) -> TextToTextGenerationTaskModel:
        """Return the real model, constructing it on first use.

        Returns
        -------
        TextToTextGenerationTaskModel
            The cached backend instance.

        Raises
        ------
        TypeError
            If the factory returns an object that is not a text-to-text model.
        """
        model = self._model
        if model is None:
            model = self._factory()
            if not isinstance(model, TextToTextGenerationTaskModel):
                raise TypeError(
                    f"LazyLLM factory for {self._label!r} returned "
                    f"{type(model).__name__}, expected a "
                    "TextToTextGenerationTaskModel."
                )
            self._model = model
        return model

    def generate(self, prompt: list[dict[str, str]]) -> list[str]:  # type: ignore[override]
        """Generate text, constructing the real model if necessary.

        Parameters
        ----------
        prompt : list of dict
            Chat messages in OpenAI format.

        Returns
        -------
        list of str
            Generated outputs from the real backend.
        """
        return self._ensure_model().generate(prompt)

    def generate_function_call(
        self,
        messages: list[dict[str, str]],
        functions: list[dict[str, Any]],
    ) -> FunctionCallResult:
        """Produce a function call through the real model.

        Parameters
        ----------
        messages : list of dict
            Chat messages in OpenAI format.
        functions : list of dict
            OpenAI-style function specifications.

        Returns
        -------
        FunctionCallResult
            The call emitted by the real backend.
        """
        return self._ensure_model().generate_function_call(messages, functions)

    def supports_function_calling(self) -> bool:  # type: ignore[override]
        """Report the captured capability without constructing the backend.

        Returns
        -------
        bool
            The flag captured when the proxy was created.
        """
        return self._supports_function_calling

    def close(self) -> None:
        """Release the real model and reclaim its accelerator memory.

        Safe to call more than once. A failure while closing the backend is
        logged as a warning and never propagated, so cleanup cannot mask the
        error that ended the stage.
        """
        model = self._model
        self._model = None
        if model is None:
            return

        close_method = None
        try:
            close_method = getattr(model, "close", None)
            if callable(close_method):
                close_method()
        except Exception:
            log.warning("Error closing lazy LLM %s.", self._label, exc_info=True)
        finally:
            # The bound method would keep the backend alive through gc.collect().
            close_method = None
            del model
            gc.collect()

        self._clear_accelerator_cache()

    def _clear_accelerator_cache(self) -> None:
        """Ask PyTorch to release cached CUDA memory when available."""
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            log.debug(
                "Could not clear the CUDA cache while closing %s.",
                self._label,
                exc_info=True,
            )

    def __getattr__(self, name: str) -> Any:
        """Delegate non-private attribute access to the real model.

        Any public attribute this proxy does not define loads the real backend
        on first access. Private names are rejected so proxy internals cannot
        recurse into the backend.
        """
        if name.startswith("_"):
            raise AttributeError(
                f"{type(self).__name__!r} object has no attribute {name!r}"
            )
        model = self._ensure_model()
        try:
            return getattr(model, name)
        except AttributeError as error:
            raise AttributeError(
                f"{type(self).__name__!r} object has no attribute {name!r}"
            ) from error

    def __repr__(self) -> str:
        """Describe the proxy without constructing the real model."""
        return f"<LazyLLM label={self._label!r} loaded={self.is_loaded}>"
