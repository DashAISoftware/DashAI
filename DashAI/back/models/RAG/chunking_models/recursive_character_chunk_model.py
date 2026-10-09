from typing import List

from pydantic import field_validator

from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    list_field,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.chunking_models.base_chunking_model import (
    BaseChunkingModel,
)
from DashAI.back.models.RAG.exceptions import RAGChunkingOverlapError


class RecursiveCharacterChunkModelSchema(BaseSchema):
    """Schema for the recursive character chunking model configuration."""

    chunk_size: schema_field(
        int_field(gt=1),
        placeholder=1000,
        description=MultilingualString(
            en="Size of each chunk in characters.",
            es="Tamaño de cada fragmento en caracteres.",
            pt="Tamanho de cada fragmento em caracteres.",
            de="Größe jedes Chunks in Zeichen.",
            zh="每个块的大小（以字符为单位）。",
        ),
    )  # type: ignore

    chunk_overlap: schema_field(
        int_field(ge=0),
        placeholder=100,
        description=MultilingualString(
            en=(
                "Number of characters to overlap between chunks. "
                "Must be less than chunk_size."
            ),
            es=(
                "Número de caracteres a solapar entre fragmentos. "
                "Debe ser menor que chunk_size."
            ),
            pt=(
                "Número de caracteres a sobrepor entre fragmentos. "
                "Deve ser menor que chunk_size."
            ),
            de=(
                "Anzahl der Zeichen, die sich zwischen den Chunks überlappen. "
                "Muss kleiner als chunk_size sein."
            ),
            zh=("块之间重叠的字符数。必须小于 chunk_size。"),
        ),
    )  # type: ignore

    separators: schema_field(
        list_field(string_field(), min_items=1),
        placeholder=["\n\n", "\n", ".", " ", ""],
        description=MultilingualString(
            en="Ordered list of separators to use for splitting.",
            es="Lista ordenada de separadores a usar para dividir.",
            pt="Lista ordenada de separadores a usar para dividir.",
            de="Geordnete Liste der Trennzeichen, die zum Aufteilen verwendet werden.",
            zh="用于拆分的分隔符的有序列表。",
        ),
    )  # type: ignore

    @field_validator("chunk_overlap", mode="after")
    @classmethod
    def validate_chunk_overlap(cls, v, info):
        """Validate that chunk_overlap is less than chunk_size.

        Args:
            v: The value of chunk_overlap.
            info: Validation info containing the chunk_size field.

        Returns:
            int: The validated chunk_overlap value.

        Raises:
            ValueError: If chunk_overlap is greater than or equal to chunk_size.
        """
        chunk_size = info.data.get("chunk_size")
        if chunk_size is not None and v >= chunk_size:
            raise ValueError(
                f"chunk_overlap must be less than chunk_size. "
                f"Got chunk_overlap={v} and chunk_size={chunk_size}"
            )
        return v


class RecursiveCharacterChunkModel(BaseChunkingModel):
    """Chunking model that recursively splits text using a prioritized list
    of separators.

    Falls back to character-level splitting when no separator fits within the
    chunk size.
    """

    SCHEMA = RecursiveCharacterChunkModelSchema

    DISPLAY_NAME: str = MultilingualString(
        en="Recursive Character Chunk Model",
        es="Modelo de Fragmentación Recursiva por Caracteres",
        pt="Modelo de Fragmentação Recursiva por Caracteres",
        de="Rekursives Zeichen-Chunking-Modell",
        zh="递归字符分块模型",
    )

    def __init__(self, **kwargs):
        """Initialize the recursive character chunking model.

        Args:
            **kwargs: Must include ``chunk_size``, ``chunk_overlap``, and
                ``separators``, plus a ``documents`` mapping passed to the
                parent class.
        """
        self.chunk_size = kwargs["chunk_size"]
        self.chunk_overlap = kwargs["chunk_overlap"]
        self.separators = kwargs["separators"]
        super().__init__(**kwargs)

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks using recursive separator-based splitting.

        Args:
            text: The input text to be chunked.

        Returns:
            List[str]: A list of text chunks.

        Raises:
            RAGChunkingOverlapError: If chunk_overlap is not less than chunk_size.
        """
        if self.chunk_overlap >= self.chunk_size:
            raise RAGChunkingOverlapError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"chunk_size ({self.chunk_size})"
            )
        if len(text) <= self.chunk_size:
            return [text]
        return self._split_text(text, 0)

    def _split_text(self, text: str, separator_idx: int) -> List[str]:
        """Recursively split text using the separator at the given index,
        falling back to the next separator if needed.

        Args:
            text: The text to split.
            separator_idx: Index into the ordered separators list.

        Returns:
            List[str]: A list of text chunks.
        """
        if separator_idx >= len(self.separators):
            return self._force_split(text)

        separator = self.separators[separator_idx]

        if separator == "" or separator not in text:
            return self._split_text(text, separator_idx + 1)

        splits = text.split(separator)
        return self._recursive_split(splits, separator_idx + 1)

    def _recursive_split(self, splits: List[str], next_sep_idx: int) -> List[str]:
        """Iterate over already-split segments and further split any that exceed
        chunk_size.

        Args:
            splits: Segments from a previous split operation.
            next_sep_idx: Index of the next separator to try for oversize segments.

        Returns:
            List[str]: A flat list of chunks all within chunk_size.
        """
        result: List[str] = []
        for split in splits:
            if len(split) <= self.chunk_size:
                result.append(split)
                continue

            resolved = False
            for sep_idx in range(next_sep_idx, len(self.separators)):
                separator = self.separators[sep_idx]
                if separator == "" or separator in split:
                    result.extend(self._split_text(split, sep_idx))
                    resolved = True
                    break

            if not resolved:
                result.extend(self._force_split(split))

        return result

    def _force_split(self, text: str) -> List[str]:
        """Split text into fixed-size chunks with overlap when all separators fail.

        Args:
            text: The text to split.

        Returns:
            List[str]: A list of fixed-size character chunks.
        """
        chunks: List[str] = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunks.append(text[start:end])
            if end == text_length:
                break
            start += self.chunk_size - self.chunk_overlap

        return chunks
