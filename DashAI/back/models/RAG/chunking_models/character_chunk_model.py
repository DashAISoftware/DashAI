from typing import List

from pydantic import field_validator

from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.chunking_models.base_chunking_model import (
    BaseChunkingModel,
)
from DashAI.back.models.RAG.exceptions import RAGChunkingOverlapError


class CharacterChunkModelSchema(BaseSchema):
    """Schema for character-based chunking model."""

    chunk_size: schema_field(
        int_field(gt=1),
        placeholder=500,
        alias=MultilingualString(
            en="Chunk size",
            es="Tamaño de fragmento",
            pt="Tamanho do fragmento",
            de="Chunk-Größe",
            zh="块大小",
        ),
        description=MultilingualString(
            en="Size of each chunk in characters.",
            es="Tamaño de cada fragmento en caracteres.",
            pt="Tamanho de cada fragmento em caracteres.",
            de="Größe jedes Chunks in Zeichen.",
            zh="每个块的字符数。",
        ),
    )  # type: ignore

    chunk_overlap: schema_field(
        int_field(gt=0),
        placeholder=50,
        alias=MultilingualString(
            en="Chunk overlap",
            es="Superposición entre fragmentos",
            pt="Sobreposição entre fragmentos",
            de="Chunk-Überlappung",
            zh="块重叠",
        ),
        description=MultilingualString(
            en=(
                "Number of characters to overlap between chunks. "
                "Must be less than the chunk size."
            ),
            es=(
                "Cantidad de caracteres que se repiten entre fragmentos "
                "consecutivos. Debe ser menor que el tamaño de fragmento."
            ),
            pt=(
                "Quantidade de caracteres repetidos entre fragmentos "
                "consecutivos. Deve ser menor que o tamanho do fragmento."
            ),
            de=(
                "Anzahl der Zeichen, die sich zwischen Chunks überlappen. "
                "Muss kleiner als die Chunk-Größe sein."
            ),
            zh="相邻块之间重叠的字符数，必须小于块大小。",
        ),
    )  # type: ignore

    @field_validator("chunk_overlap", mode="after")
    @classmethod
    def validate_chunk_overlap(cls, v, info):
        """Validate that chunk_overlap is less than chunk_size."""
        chunk_size = info.data.get("chunk_size")
        if chunk_size is not None and v >= chunk_size:
            raise ValueError(
                f"chunk_overlap must be less than chunk_size. "
                f"Got chunk_overlap={v} and chunk_size={chunk_size}"
            )
        return v


class CharacterChunkModel(BaseChunkingModel):
    """
    Chunking model that splits documents into chunks based on character count.
    This model is useful for processing large text documents into manageable pieces.
    """

    SCHEMA = CharacterChunkModelSchema
    DISPLAY_NAME = MultilingualString(
        en="Character chunking",
        es="Fragmentación por caracteres",
        pt="Fragmentação por caracteres",
        de="Zeichenbasiertes Chunking",
        zh="按字符切分",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Splits documents into fixed-size pieces counted in characters. "
            "Fast, predictable and needs no model download, which makes it a "
            "good default for most documents."
        ),
        es=(
            "Divide los documentos en fragmentos de tamaño fijo medidos en "
            "caracteres. Es rápido, predecible y no requiere descargar ningún "
            "modelo, por lo que es un buen valor por defecto."
        ),
        pt=(
            "Divide os documentos em fragmentos de tamanho fixo medidos em "
            "caracteres. É rápido, previsível e não exige baixar nenhum "
            "modelo, sendo um bom padrão."
        ),
        de=(
            "Teilt Dokumente in Stücke fester Größe, gezählt in Zeichen. "
            "Schnell, vorhersehbar und ohne Modell-Download — ein guter "
            "Standardwert."
        ),
        zh=(
            "按字符数将文档切分为固定大小的块。速度快、结果可预期，"
            "且无需下载模型，是大多数文档的良好默认选择。"
        ),
    )

    def __init__(self, **kwargs):
        """
        Initialize the character chunking model with the specified chunk size and
        overlap.

        Args:
            chunk_size (int): Size of each chunk in characters.
            chunk_overlap (int): Number of characters to overlap between chunks.
        """
        self.chunk_size = kwargs["chunk_size"]
        self.chunk_overlap = kwargs["chunk_overlap"]
        super().__init__(**kwargs)

    def chunk_text(self, text: str) -> List[str]:
        """
        Chunk the input text into smaller segments based on character count.

        Args:
            text (str): The input text to be chunked.

        Returns:
            List[str]: A list of text chunks.
        """
        if self.chunk_overlap >= self.chunk_size:
            raise RAGChunkingOverlapError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"chunk_size ({self.chunk_size})"
            )
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunk = text[start:end]
            chunks.append(chunk)
            if end == text_length:
                break
            start += self.chunk_size - self.chunk_overlap

        return chunks
