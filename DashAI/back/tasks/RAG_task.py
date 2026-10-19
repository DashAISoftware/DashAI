import json
from typing import Any, List, Optional, Tuple

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import ProcessData
from DashAI.back.models.RAG.exceptions import RAGTaskInputError
from DashAI.back.models.RAG.RAG_constants import (
    RAG_OUTPUT_CHUNKS_TYPE,
    RAG_OUTPUT_MESSAGE_TYPE,
    RAG_OUTPUT_QUERIES_TYPE,
    RAG_OUTPUT_TIMINGS_TYPE,
    RAG_OUTPUT_TRACE_TYPE,
)
from DashAI.back.models.RAG.RAG_pipeline import RAGGenerationOutput
from DashAI.back.tasks.base_generative_task import BaseGenerativeTask


class RAGTask(BaseGenerativeTask):
    """Class for RAG Task.

    Here you can change the methods provided by class Task.
    """

    metadata: dict[str, Any] = {
        "inputs": {"str": {"min": 1, "max": 1}},
        "outputs": {
            RAG_OUTPUT_QUERIES_TYPE: {"min": 1, "max": 1},
            RAG_OUTPUT_CHUNKS_TYPE: {"min": 1, "max": 1},
            RAG_OUTPUT_TRACE_TYPE: {"min": 1, "max": 1},
            RAG_OUTPUT_TIMINGS_TYPE: {"min": 1, "max": 1},
            RAG_OUTPUT_MESSAGE_TYPE: {"min": 1, "max": 1},
        },
    }

    DISPLAY_NAME: str = MultilingualString(
        en="Retrieval-Augmented Generation",
        es="Generación Aumentada por Recuperación (RAG)",
        pt="Geração Aumentada por Recuperação (RAG)",
        de="Retrieval-Augmented Generation (RAG)",
        zh="检索增强生成（RAG）",
    )
    DESCRIPTION: str = MultilingualString(
        en="""
        This task generates a text response with an LLM model based on
        documents provided.
        """,
        es="""
        Esta tarea genera una respuesta de texto con un modelo LLM basado
        en los documentos proporcionados.
        """,
        pt="""
        Esta tarefa gera uma resposta de texto com um modelo LLM com base
        nos documentos fornecidos.
        """,
        de="""
        Diese Aufgabe generiert eine Textantwort mit einem LLM-Modell anhand
        der bereitgestellten Dokumente.
        """,
        zh="""
        此任务基于提供的文档，使用 LLM 模型生成文本响应。
        """,
    )

    USE_HISTORY: bool = True

    # RAG owns a dedicated entry point in the Generative module, so it is
    # not offered through the shared "create session" model gallery.
    ENTRY_POINT: str = "standalone"

    def prepare_for_task(
        self,
        input: List[ProcessData],
        history: Optional[List[Tuple[str, str]]] = None,
    ) -> list[dict[str, str]]:
        """Prepare the input by including the history.

        Parameters
        ----------
        input : str
            The current input to be processed.
            E.g.:
            ["Tell me a joke."]

        history : Optional[List[Tuple[str, str]]], optional
            The history of previous inputs and outputs, by default None. E.g.:
            [("Hello!", "Hello! How can I assist you today?")]

        Returns
        -------
        str
            The input prepared with the history to be used by the model.
            E.g.:
                [{"role": "user", "content": "Hello!"},
                 {"role": "assistant", "content": "Hello! How can I assist you today?"},
                 {"role": "user", "content": "Tell me a joke."}]
        """
        if not input:
            raise RAGTaskInputError("Task input list must not be empty")
        input = str(input[0].data)

        prepared_input = [{"role": "user", "content": input}]

        if not history:
            return prepared_input

        context = [
            (
                {"role": "user", "content": h_input},
                {"role": "assistant", "content": h_output},
            )
            for (h_input, h_output) in history
        ]
        context = [entry for input_output in context for entry in input_output]
        prepared_input = context + prepared_input
        return prepared_input

    def prepare_input_for_database(
        self,
        input: List[str],
        **kwargs: Any,
    ) -> List[Tuple[str, str]]:
        """Prepare the input for the database.

        Parameters
        ----------
        input : str
            The input to be prepared.

        Returns
        -------
        List[Tuple[str, str]]
            Input with the new types as a list of tuples containing the data
            and its type

        """
        return [(input[0], "str")]

    def process_output(
        self,
        output: RAGGenerationOutput,
        **kwargs: Any,
    ) -> List[Tuple[str, str]]:
        """Process the output of a generative model.

        Converts the generation output into the five typed output rows, in
        pipeline-chronological order: ``Queries`` (the JSON query list), then
        ``Dict`` (the JSON chunk map), then ``Trace`` (the JSON per-query
        retrieval trace), then ``Timings`` (the JSON per-stage timings), then
        ``str`` (the answer message).

        Parameters
        ----------
        output : RAGGenerationOutput
            The typed output from ``RAGPipeline.generate()``.

        Returns
        -------
        List[Tuple[str, str]]
            ``(data, type)`` rows ordered Queries, Dict, Trace, Timings, str.
        """
        queries_json = json.dumps(list(output.queries), ensure_ascii=False)
        chunks_json = json.dumps(
            {key: ref.to_dict() for key, ref in output.chunks.items()},
            ensure_ascii=False,
        )
        trace_json = json.dumps(list(output.trace), ensure_ascii=False)
        timings_json = json.dumps(output.timings.to_dict(), ensure_ascii=False)
        return [
            (queries_json, RAG_OUTPUT_QUERIES_TYPE),
            (chunks_json, RAG_OUTPUT_CHUNKS_TYPE),
            (trace_json, RAG_OUTPUT_TRACE_TYPE),
            (timings_json, RAG_OUTPUT_TIMINGS_TYPE),
            (str(output.message), RAG_OUTPUT_MESSAGE_TYPE),
        ]

    def extract_message_from_output(self, output: List[ProcessData]) -> Optional[str]:
        """Return the message ``data`` of a process output, or ``None``.

        Used by the job to build the conversation history without depending on
        row order: it returns the first row whose ``data_type`` is the message
        type, so it tolerates both the legacy layout (message first) and the
        current one (message last).

        Parameters
        ----------
        output : List[ProcessData]
            Output rows of a finished process.

        Returns
        -------
        Optional[str]
            The message text, or ``None`` when no message row is present.
        """
        for row in output:
            if row.data_type == RAG_OUTPUT_MESSAGE_TYPE:
                return row.data
        return None

    def process_output_from_database(
        self,
        output: List[ProcessData],
        **kwargs: Any,
    ) -> List[ProcessData]:
        """Process the output from the database.

        Parameters
        ----------
        output : list[str]
            The output data to be processed.

        Returns
        -------
        list[str]
            The processed output data.
        """

        return output

    def process_input_from_database(
        self,
        input: List[ProcessData],
        **kwargs: Any,
    ) -> List[ProcessData]:
        """Process the input from the database.

        Parameters
        ----------
        input : list[str]
            The input data to be processed.

        Returns
        -------
        list[str]
            The processed input data.
        """
        return input
