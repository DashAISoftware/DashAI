from typing import Any, List, Optional, Tuple

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import ProcessData
from DashAI.back.tasks.base_generative_task import BaseGenerativeTask


class TextToTextGenerationTask(BaseGenerativeTask):
    """Task for open-ended text generation using large language models.

    Text-to-text generation takes a natural-language prompt (user message) and
    produces a natural-language response. The task maintains a conversation
    history (``USE_HISTORY = True``) so that multi-turn chat interactions are
    supported out of the box. Input and output are both plain strings, formatted
    as OpenAI-style chat messages (``role``/``content`` dicts) before being
    passed to the underlying LLM.

    Compatible models include all DashAI LLM wrappers (Llama, Mistral, Mixtral,
    Qwen, SmolLM) which implement the ``generate`` method.
    """

    metadata: dict = {
        "inputs": {"str": {"min": 1, "max": 1}},
        "outputs": {"str": {"min": 1, "max": 1}},
    }

    DISPLAY_NAME: MultilingualString = MultilingualString(
        en="Text to Text",
        es="Texto a Texto",
        pt="Texto para Texto",
        de="Text zu Text",
        zh="文本到文本",
    )

    DESCRIPTION: MultilingualString = MultilingualString(
        en="""
        This task uses a large language model (LLM)
        to generate text from a given prompt.
        """,
        es="""
        Esta tarea utiliza un modelo de lenguaje grande (LLM)
        para generar texto a partir de un prompt dado.
        """,
        pt="""
        Esta tarefa utiliza um modelo de linguagem grande (LLM)
        para gerar texto a partir de um prompt fornecido.
        """,
        de="""
        Diese Aufgabe verwendet ein großes Sprachmodell (LLM),
        um Text aus einem gegebenen Prompt zu generieren.
        """,
        zh="""
        此任务使用大型语言模型（LLM）
        根据给定提示生成文本。
        """,
    )

    USE_HISTORY: bool = True

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
        output: List[Any],
        **kwargs: Any,
    ) -> List[Tuple[str, str]]:
        """Convert raw model output to a storable (text, type) pair.

        Parameters
        ----------
        output : list of Any
            Raw output from the generative model. The first element is cast
            to ``str`` and returned.
        **kwargs : dict
            Additional keyword arguments (e.g. ``file_name``, ``path``).
            Currently unused; present for interface compatibility.

        Returns
        -------
        list of tuple of (str, str)
            A single-element list containing ``(str(output[0]), "str")``.
        """

        return [(str(output[0]), "str")]

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
