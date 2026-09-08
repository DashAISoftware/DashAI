from typing import Dict, List

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.embeddings.dense._overflow_handler import (
    AGGREGATE,
    TRUNCATE,
)
from DashAI.back.models.RAG.embeddings.dense._sentence_transformer_embedding import (
    _SentenceTransformerEmbedding,
)
from DashAI.back.models.RAG.embeddings.dense_embedding import DenseEmbedding

ST_MODELS: Dict[str, dict] = {
    "microsoft/harrier-oss-v1-270m": {
        "languages": ["multi"],
        "max_seq_length": 32768,
        "pooling": "last_token",
    },
    "microsoft/harrier-oss-v1-0.6b": {
        "languages": ["multi"],
        "max_seq_length": 32768,
        "pooling": "last_token",
    },
    "microsoft/harrier-oss-v1-27b": {
        "languages": ["multi"],
        "max_seq_length": 32768,
        "pooling": "last_token",
    },
    "Qwen/Qwen3-Embedding-0.6B": {
        "languages": ["multi"],
        "max_seq_length": 32768,
        "pooling": "mean",
    },
    "Qwen/Qwen3-Embedding-4B": {
        "languages": ["multi"],
        "max_seq_length": 32768,
        "pooling": "mean",
    },
    "Qwen/Qwen3-Embedding-8B": {
        "languages": ["multi"],
        "max_seq_length": 32768,
        "pooling": "mean",
    },
    "sentence-transformers/all-MiniLM-L6-v2": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/all-MiniLM-L12-v2": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/all-mpnet-base-v2": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/all-distilroberta-v1": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/multi-qa-mpnet-base-dot-v1": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
        "normalize_default": False,
    },
    "sentence-transformers/multi-qa-mpnet-base-cos-v1": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/multi-qa-distilbert-dot-v1": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
        "normalize_default": False,
    },
    "sentence-transformers/multi-qa-distilbert-cos-v1": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/multi-qa-MiniLM-L6-dot-v1": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
        "normalize_default": False,
    },
    "sentence-transformers/multi-qa-MiniLM-L6-cos-v1": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/msmarco-bert-base-dot-v5": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
        "normalize_default": False,
    },
    "sentence-transformers/msmarco-distilbert-dot-v5": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
        "normalize_default": False,
    },
    "sentence-transformers/msmarco-distilbert-base-tas-b": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/msmarco-distilbert-cos-v5": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/msmarco-MiniLM-L12-cos-v5": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/msmarco-MiniLM-L6-cos-v5": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": {
        "languages": [
            "en",
            "es",
            "fr",
            "de",
            "it",
            "pt",
            "nl",
            "pl",
            "ca",
            "fi",
            "ar",
            "zh",
            "ja",
            "ko",
            "ru",
            "tr",
            "hi",
            "sv",
            "da",
            "no",
            "cs",
            "ro",
            "el",
            "he",
            "hu",
            "th",
            "vi",
            "id",
            "ms",
            "bg",
            "hr",
            "sk",
            "sl",
            "sr",
            "uk",
            "et",
            "lv",
            "lt",
            "fa",
            "ur",
            "mk",
            "af",
            "bn",
            "multi",
        ],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": {
        "languages": [
            "en",
            "es",
            "fr",
            "de",
            "it",
            "pt",
            "nl",
            "pl",
            "ca",
            "fi",
            "ar",
            "zh",
            "ja",
            "ko",
            "ru",
            "tr",
            "hi",
            "sv",
            "da",
            "no",
            "cs",
            "ro",
            "el",
            "he",
            "hu",
            "th",
            "vi",
            "id",
            "ms",
            "bg",
            "hr",
            "sk",
            "sl",
            "sr",
            "uk",
            "et",
            "lv",
            "lt",
            "fa",
            "ur",
            "mk",
            "af",
            "bn",
            "multi",
        ],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/distiluse-base-multilingual-cased-v2": {
        "languages": [
            "en",
            "es",
            "fr",
            "de",
            "it",
            "pt",
            "nl",
            "pl",
            "ca",
            "fi",
            "ar",
            "zh",
            "ja",
            "ko",
            "ru",
            "tr",
            "hi",
            "sv",
            "da",
            "no",
            "cs",
            "ro",
            "el",
            "he",
            "hu",
            "th",
            "vi",
            "id",
            "ms",
            "bg",
            "hr",
            "sk",
            "sl",
            "sr",
            "uk",
            "et",
            "lv",
            "lt",
            "fa",
            "ur",
            "mk",
            "af",
            "bn",
            "multi",
        ],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/distiluse-base-multilingual-cased-v1": {
        "languages": [
            "en",
            "es",
            "fr",
            "de",
            "it",
            "nl",
            "pt",
            "ar",
            "zh",
            "ja",
            "ko",
            "pl",
            "ru",
            "tr",
            "multi",
        ],
        "max_seq_length": 512,
        "pooling": "mean",
    },
    "sentence-transformers/allenai-specter": {
        "languages": ["en"],
        "max_seq_length": 512,
        "pooling": "mean",
    },
}

ST_MODEL_NAMES = list(ST_MODELS.keys())


class SentenceTransformerEmbeddingSchema(BaseSchema):
    """Configuration schema for :class:`SentenceTransformerEmbedding`.

    Attributes:
        model_name: Sentence Transformer model for embedding generation.
        overflow_strategy: Strategy for chunks exceeding model max sequence length.
        normalize: Whether to L2-normalize the output embeddings.
        device: Device to run the model on.
    """

    model_name: schema_field(
        enum_field(ST_MODEL_NAMES),
        placeholder="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        description=MultilingualString(
            en="Sentence Transformer model for embedding generation.",
            es="Modelo Sentence Transformer para generación de embeddings.",
            pt="Modelo Sentence Transformer para geração de embeddings.",
            de="Sentence-Transformer-Modell zur Erzeugung von Embeddings.",
            zh="用于生成嵌入的 Sentence Transformer 模型。",
        ),
    )  # type: ignore

    overflow_strategy: schema_field(
        enum_field([TRUNCATE, AGGREGATE]),
        placeholder=TRUNCATE,
        description=MultilingualString(
            en="Strategy for chunks exceeding model max sequence length.",
            es="Estrategia para fragmentos que exceden la longitud máxima del modelo.",
            pt=(
                "Estratégia para fragmentos que excedem o comprimento máximo"
                " de sequência do modelo."
            ),
            de=(
                "Strategie für Chunks, die die maximale Sequenzlänge des"
                " Modells überschreiten."
            ),
            zh="对于超过模型最大序列长度的块的策略。",
        ),
    )  # type: ignore

    normalize: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en="Whether to L2-normalize the output embeddings.",
            es="Si normalizar con L2 los embeddings de salida.",
            pt="Se deve normalizar com L2 os embeddings de saída.",
            de="Ob die Ausgabe-Embeddings L2-normalisiert werden sollen.",
            zh="是否对输出的嵌入进行 L2 归一化。",
        ),
    )  # type: ignore

    device: schema_field(
        enum_field(["cpu", "cuda"]),
        placeholder="cpu",
        description=MultilingualString(
            en="Device to run the model on.",
            es="Dispositivo para ejecutar el modelo.",
            pt="Dispositivo para executar o modelo.",
            de="Gerät, auf dem das Modell ausgeführt wird.",
            zh="运行模型的设备。",
        ),
    )  # type: ignore


class SentenceTransformerEmbedding(DenseEmbedding):
    """Dense embeddings using Sentence Transformer models.

    Wraps :class:`_SentenceTransformerEmbedding` and exposes it as a
    DashAI component with a configurable schema
    (:class:`SentenceTransformerEmbeddingSchema`).

    Supports mean / last-token pooling, L2 normalisation, and overflow
    strategies (truncate / aggregate).
    """

    SCHEMA = SentenceTransformerEmbeddingSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Sentence Transformer Embedding",
        es="Embedding Sentence Transformer",
        pt="Embedding Sentence Transformer",
        de="Sentence-Transformer-Embedding",
        zh="Sentence Transformer 嵌入",
    )
    DESCRIPTION: str = MultilingualString(
        en="Dense embeddings using Sentence Transformer models with mean"
        " pooling and L2 normalization.",
        es="Embeddings densos usando modelos Sentence Transformer con mean"
        " pooling y normalización L2.",
        pt="Embeddings densos usando modelos Sentence Transformer com mean"
        " pooling e normalização L2.",
        de="Dichte Embeddings mit Sentence-Transformer-Modellen mit"
        " Mean-Pooling und L2-Normalisierung.",
        zh="使用 Sentence Transformer 模型生成稠密嵌入，结合 mean 池化和 L2 归一化。",
    )

    def __init__(self, **kwargs):
        """Initialise the embedding by validating parameters and creating the internal model.

        Args:
            **kwargs: Configuration matching :class:`SentenceTransformerEmbeddingSchema`.  # noqa: E501
        """  # noqa: E501
        self.params = self.validate_and_transform(kwargs)
        model_name = self.params["model_name"]
        device = self.params["device"]
        normalize = self.params["normalize"]
        overflow_strategy = self.params.get("overflow_strategy", "truncate")
        model_info = ST_MODELS[model_name]
        pooling = model_info.get("pooling", "mean")
        self._embedding = _SentenceTransformerEmbedding(
            model_name=model_name,
            device=device,
            model_max_length=model_info["max_seq_length"],
            overflow_strategy=overflow_strategy,
            normalize=normalize
            if model_info.get("normalize_default", True)
            else normalize,
            pooling=pooling,
        )

    def load(self):
        """Load the Sentence Transformer model and tokenizer."""
        self._embedding.load()

    def encode(self, text: str):
        """Encode a single text into a dense embedding.

        Args:
            text: Input string.

        Returns:
            A 1-D NumPy array of shape ``(embedding_dim,)``.
        """
        return self._embedding.encode(text)

    def batch_encode(self, texts: List[str]):
        """Encode a batch of texts into dense embeddings.

        Args:
            texts: List of input strings.

        Returns:
            A ``(batch, embedding_dim)`` float32 NumPy array.
        """
        return self._embedding.batch_encode(texts)

    def save(self):
        """No-op. Persistence is handled externally."""

    def train(self, **kwargs):
        """No-op. Pre-trained models are used as-is."""
