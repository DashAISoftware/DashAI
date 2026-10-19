from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List

from DashAI.back.models.base_generative_model import BaseGenerativeModel


@dataclass(frozen=True)
class FunctionCallResult:
    """The named function call a function-calling backend produced.

    Attributes
    ----------
    name : str
        The function name the backend called.
    arguments : Any
        The raw arguments payload: typically a JSON-encoded string emitted
        under constrained sampling; already-decoded mappings are tolerated.
    """

    name: str
    arguments: Any = None


class TextToTextGenerationTaskModel(BaseGenerativeModel):
    """Base class for models that generate text from a text input.

    Concrete text-to-text models must extend this class and implement
    ``generate``. Compatible with ``TextToTextGenerationTask`` and ``RAGTask``.

    Backends that can constrain their output to a function's JSON schema
    (llama.cpp grammar-constrained sampling, the OpenAI tools API, ...) also
    implement ``generate_function_call`` and set ``SUPPORTS_FUNCTION_CALLING``
    so callers can select the structural route instead of prompt obedience.
    """

    COMPATIBLE_COMPONENTS = ["TextToTextGenerationTask", "RAGTask"]

    REQUIRED_EXTRA_KWARGS = []

    #: Whether the concrete backend can constrain its output to a function's
    #: JSON schema (llama.cpp grammar-constrained sampling, OpenAI tools API...).
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = False

    @classmethod
    def supports_function_calling(cls) -> bool:
        """Report whether instances of this class support function calling.

        Returns
        -------
        bool
            ``True`` when the concrete backend implements
            ``generate_function_call`` with schema-constrained sampling.
        """
        return bool(cls.SUPPORTS_FUNCTION_CALLING)

    def generate_function_call(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
    ) -> FunctionCallResult:
        """Produce a named function call for the given chat messages.

        Parameters
        ----------
        messages : List[Dict[str, str]]
            Chat messages (OpenAI format) as passed to ``generate``.
        functions : List[Dict[str, Any]]
            OpenAI-style function specs (``name``, ``description``,
            ``parameters`` JSON schemas). A backend MAY force a specific call
            (the GGUF backend forces ``functions[0]``); callers must not rely
            on arbitrary selection among the specs.

        Returns
        -------
        FunctionCallResult
            The called function name and its raw arguments payload. The
            ``arguments`` value is either a dict or a JSON-encoded string the
            caller is responsible for resolving.

        Raises
        ------
        NotImplementedError
            Always, unless the concrete backend overrides this method and sets
            ``SUPPORTS_FUNCTION_CALLING`` to ``True``.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support function calling. "
            "Override generate_function_call and set SUPPORTS_FUNCTION_CALLING "
            "to True in a backend that can constrain output to a JSON schema."
        )
