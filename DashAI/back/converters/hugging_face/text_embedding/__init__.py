"""Converters that turn text into dense vectors, one per pretrained model."""

from DashAI.back.converters.hugging_face.text_embedding.base import (
    TextEmbeddingConverter,
)
from DashAI.back.converters.hugging_face.text_embedding.e5 import (
    E5TextEmbedding,
    MultilingualE5BaseEmbedding,
    MultilingualE5LargeEmbedding,
    MultilingualE5SmallEmbedding,
)
from DashAI.back.converters.hugging_face.text_embedding.instructor import (
    InstructorLargeEmbedding,
    InstructorTextEmbedding,
)
from DashAI.back.converters.hugging_face.text_embedding.sentence_transformer import (
    AllMiniLML6V2Embedding,
    AllMpnetBaseV2Embedding,
    HarrierOSS06BEmbedding,
    HarrierOSS270MEmbedding,
    LaBSEEmbedding,
    MultiQAMiniLML6CosV1Embedding,
    MultiQAMpnetBaseCosV1Embedding,
    ParaphraseMultilingualMiniLML12V2Embedding,
    ParaphraseMultilingualMpnetBaseV2Embedding,
    Qwen3Embedding06B,
    SentenceTransformerTextEmbedding,
)

TEXT_EMBEDDING_CONVERTERS = [
    AllMiniLML6V2Embedding,
    AllMpnetBaseV2Embedding,
    MultiQAMiniLML6CosV1Embedding,
    MultiQAMpnetBaseCosV1Embedding,
    ParaphraseMultilingualMiniLML12V2Embedding,
    ParaphraseMultilingualMpnetBaseV2Embedding,
    LaBSEEmbedding,
    MultilingualE5SmallEmbedding,
    MultilingualE5BaseEmbedding,
    MultilingualE5LargeEmbedding,
    Qwen3Embedding06B,
    HarrierOSS270MEmbedding,
    HarrierOSS06BEmbedding,
    InstructorLargeEmbedding,
]

__all__ = [
    "TEXT_EMBEDDING_CONVERTERS",
    "TextEmbeddingConverter",
    "SentenceTransformerTextEmbedding",
    "E5TextEmbedding",
    "InstructorTextEmbedding",
    *[component.__name__ for component in TEXT_EMBEDDING_CONVERTERS],
]
