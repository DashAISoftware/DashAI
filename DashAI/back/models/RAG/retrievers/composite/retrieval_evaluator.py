"""Prompt + LLM evaluation collaborator for the LLM-evaluated retrievers.

``RetrievalEvaluator`` is the single place that turns structured retrieval data
into a prompt, chooses the function-calling or text route, and parses the
verdict. It performs no retrieval, pooling or trace work and never formats
chunk/document text: the prompt component owns all rendering.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.exceptions.retriever import (
    RAGRetrieverEvaluationError,
)
from DashAI.back.models.RAG.retrievers.composite.evaluation_output import (
    RetrievalVerdict,
    parse_evaluation_arguments,
    parse_evaluation_output,
)
from DashAI.back.models.RAG.retrievers.composite.retrieval_context import (
    RetrievalContext,
)
from DashAI.back.models.RAG.retrievers.retrieval_contracts import (
    CHUNK_DOCUMENT_ID,
    CHUNK_POSITION,
    CHUNK_TEXT,
    ChunkPayload,
    RetrieverCatalog,
)
from DashAI.back.models.text_to_text_generation_model import FunctionCallResult


class RetrievalEvaluator:
    """Owns the prompt, the LLM and the function-call verdict contract.

    Parameters
    ----------
    prompt : Any
        A retrieval-sufficiency prompt exposing ``format(**kwargs)``.
    llm_model : Any
        The text-to-text model used to judge the pool.
    expected_function : str
        The function name a function-calling model must call.
    function_description : str
        Human-readable description of that function.
    function_parameters : Dict[str, Any]
        JSON schema of the function's arguments.
    """

    def __init__(
        self,
        prompt: Any,
        llm_model: Any,
        expected_function: str,
        function_description: str,
        function_parameters: Dict[str, Any],
    ) -> None:
        self._prompt = prompt
        self._llm_model = llm_model
        self._expected_function = expected_function
        self._function_description = function_description
        self._function_parameters = function_parameters

    @staticmethod
    def _chunk_payload(chunks: Sequence[Chunk]) -> List[ChunkPayload]:
        """Return structured chunk payloads for the prompt.

        Parameters
        ----------
        chunks : Sequence[Chunk]
            Materialized pool chunks.

        Returns
        -------
        List[ChunkPayload]
            One payload per chunk with its document id, position and raw text.
        """
        payload: List[ChunkPayload] = []
        for chunk in chunks:
            payload.append(
                {
                    CHUNK_DOCUMENT_ID: chunk.document_id,
                    CHUNK_POSITION: chunk.document_position,
                    CHUNK_TEXT: chunk.text,
                }
            )
        return payload

    def _retriever_catalog(self, children: Sequence[Any]) -> RetrieverCatalog:
        """Return the 1-based retriever index -> schema summary mapping.

        Parameters
        ----------
        children : Sequence[Any]
            Direct child retrievers of the evaluated retriever.

        Returns
        -------
        RetrieverCatalog
            A mapping keyed by the 1-based index used by ``call_retrievers``.
        """
        catalog: RetrieverCatalog = {}
        index = 1
        for child in children:
            catalog[index] = child.get_schema_summary()
            index += 1
        return catalog

    def evaluate(
        self,
        *,
        query: str,
        chunks: Sequence[Chunk],
        pool_size: int,
        top_k: int,
        children: Sequence[Any],
        context: RetrievalContext,
    ) -> RetrievalVerdict:
        """Render the prompt and obtain the model's sufficiency verdict.

        Parameters
        ----------
        query : str
            The user query under evaluation.
        chunks : Sequence[Chunk]
            The currently materialized pool.
        pool_size : int
            Number of chunks in the materialized pool.
        top_k : int
            Maximum number of chunks the retriever may return.
        children : Sequence[Any]
            The retriever's direct children, catalogued by 1-based index.
        context : RetrievalContext
            Document and corpus knowledge for the prompt.

        Returns
        -------
        RetrievalVerdict
            The validated verdict.

        Raises
        ------
        RAGRetrieverEvaluationError
            If the model output is empty, not a string, malformed, or the
            function-calling route fails validation.
        """
        prompt_text = self._prompt.format(
            input=query,
            chunks=self._chunk_payload(chunks),
            pool_size=pool_size,
            top_k=top_k,
            retrievers=self._retriever_catalog(children),
            documents=context.document_payload(),
        )
        if self._llm_model.supports_function_calling():
            return self._call_function_calling(prompt_text)
        output = self._llm_model.generate([{"role": "user", "content": prompt_text}])
        raw = self._extract_raw_output(output)
        return parse_evaluation_output(raw)

    def _call_function_calling(self, prompt_text: str) -> RetrievalVerdict:
        """Call the model through its function-calling interface.

        Parameters
        ----------
        prompt_text : str
            The rendered evaluation prompt sent as the user message.

        Returns
        -------
        RetrievalVerdict
            The validated verdict carried by the function-call arguments.

        Raises
        ------
        RAGRetrieverEvaluationError
            If no function spec is declared, the backend fails, the model
            reports support without implementing it, or the returned call
            violates the contract.
        """
        if (
            not self._expected_function
            or not self._function_description
            or not self._function_parameters
        ):
            raise RAGRetrieverEvaluationError(
                "RetrievalEvaluator does not declare a function spec to use "
                "function calling; declare the expected function, its "
                "description and parameters or use a model without function "
                "calling."
            )
        spec = {
            "name": self._expected_function,
            "description": self._function_description,
            "parameters": self._function_parameters,
        }
        try:
            result = self._llm_model.generate_function_call(
                messages=[{"role": "user", "content": prompt_text}],
                functions=[spec],
            )
        except NotImplementedError as err:
            raise RAGRetrieverEvaluationError(
                f"{type(self._llm_model).__name__} reports function calling "
                "support but does not implement generate_function_call."
            ) from err
        except (ValueError, RuntimeError) as err:
            raise RAGRetrieverEvaluationError(
                f"Function calling failed: {err}"
            ) from err
        return self._validate_function_call_result(result)

    def _validate_function_call_result(self, result: Any) -> RetrievalVerdict:
        """Validate a function-call response and resolve its arguments.

        Parameters
        ----------
        result : Any
            Raw return value of ``generate_function_call``.

        Returns
        -------
        RetrievalVerdict
            The validated verdict with decoded arguments.

        Raises
        ------
        RAGRetrieverEvaluationError
            If the result is not a :class:`FunctionCallResult`, has no name,
            names a different function, or carries invalid arguments.
        """
        if not isinstance(result, FunctionCallResult):
            raise RAGRetrieverEvaluationError(
                "The function-calling model returned an unexpected output shape: "
                f"{type(result).__name__}."
            )
        if not result.name:
            raise RAGRetrieverEvaluationError(
                "The function-calling model did not report a function name."
            )
        if result.name != self._expected_function:
            raise RAGRetrieverEvaluationError(
                f"The model called '{result.name}' instead of the expected "
                f"'{self._expected_function}'."
            )
        return parse_evaluation_arguments(result.arguments)

    @staticmethod
    def _extract_raw_output(output: Any) -> str:
        """Extract the first string from the model output list.

        Parameters
        ----------
        output : Any
            Value returned by ``generate``.

        Returns
        -------
        str
            The raw output string. A plain string is returned directly; a
            non-empty sequence yields its first element.

        Raises
        ------
        RAGRetrieverEvaluationError
            If the output is empty, not a string/sequence, or its first element
            is not a string.
        """
        if isinstance(output, str):
            return output
        if not isinstance(output, (list, tuple)) or not output:
            raise RAGRetrieverEvaluationError(
                "The evaluation model returned an empty or non-sequence output."
            )
        raw = output[0]
        if not isinstance(raw, str):
            raise RAGRetrieverEvaluationError(
                f"The evaluation model output is not a string: {type(raw).__name__}."
            )
        return raw
