"""INSTRUCTOR embedding models, guided by a task instruction."""

from typing import Any

from DashAI.back.converters.hugging_face.text_embedding.base import (
    TextEmbeddingConverter,
    TextEmbeddingSchema,
    same_label,
)
from DashAI.back.core.schema_fields import schema_field, string_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin

DEFAULT_INSTRUCTION = "Represent the document for retrieval:"


class InstructorTextEmbeddingSchema(TextEmbeddingSchema):
    """Options of an INSTRUCTOR model."""

    instruction: schema_field(
        string_field(),
        placeholder=DEFAULT_INSTRUCTION,
        description=MultilingualString(
            en="Instruction placed before every text to describe the task.",
            es="Instrucción antepuesta a cada texto para describir la tarea.",
            pt="Instrução colocada antes de cada texto para descrever a tarefa.",
            de="Anweisung vor jedem Text, die die Aufgabe beschreibt.",
            zh="置于每段文本前、用于描述任务的指令。",
        ),
        alias=MultilingualString(
            en="Instruction",
            es="Instrucción",
            pt="Instrução",
            de="Anweisung",
            zh="指令",
        ),
    )  # type: ignore


class InstructorTextEmbedding(TextEmbeddingConverter):
    """An INSTRUCTOR model, which prepends the same instruction to every text."""

    SCHEMA = InstructorTextEmbeddingSchema

    def __init__(self, instruction: str = DEFAULT_INSTRUCTION, **kwargs: Any) -> None:
        """Store the instruction and the shared encoding options.

        Parameters
        ----------
        instruction : str, optional
            Text placed before every input.
        **kwargs
            Options of :class:`TextEmbeddingConverter`.
        """
        super().__init__(**kwargs)
        self.instruction = instruction
        self.params["instruction"] = instruction

    def prompt(self, role: str) -> str:
        """Return the instruction, whatever the role.

        Parameters
        ----------
        role : str
            ``"passage"`` or ``"query"``.

        Returns
        -------
        str
            The instruction.
        """
        return self.instruction


class InstructorLargeEmbedding(InstructorTextEmbedding):
    """INSTRUCTOR large."""

    MODEL_NAME = "hkunlp/instructor-large"
    DOWNLOAD_SIZE_BYTES = 1346259440
    HF_IGNORE_PATTERNS = list(HFDownloadableMixin.HF_IGNORE_PATTERNS)
    DISPLAY_NAME = same_label("instructor-large")
    DESCRIPTION = MultilingualString(
        en="English model steered by an instruction that describes the task.",
        es="Modelo inglés guiado por una instrucción que describe la tarea.",
        pt="Modelo inglês guiado por uma instrução que descreve a tarefa.",
        de="Englisches Modell, gesteuert durch eine Anweisung zur Aufgabe.",
        zh="由任务描述指令引导的英文模型。",
    )
