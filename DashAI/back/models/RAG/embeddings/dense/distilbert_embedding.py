from typing import Dict, List

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.embeddings.dense._bert_embedding import (
    CLS,
    CONCAT_2,
    CONCAT_3,
    CONCAT_4,
    MAX,
    MEAN,
    _BERTEmbedding,
)
from DashAI.back.models.RAG.embeddings.dense._overflow_handler import (
    AGGREGATE,
    TRUNCATE,
)
from DashAI.back.models.RAG.embeddings.dense_embedding import DenseEmbedding

DISTILBERT_POOLING_STRATEGIES = [CLS, MEAN, MAX, CONCAT_2, CONCAT_3, CONCAT_4]

DISTILBERT_MODELS: Dict[str, dict] = {
    "distilbert/distilbert-base-cased": {
        "languages": ["en"],
        "max_seq_length": 512,
    },
    "distilbert/distilbert-base-uncased": {
        "languages": ["en"],
        "max_seq_length": 512,
    },
    "distilbert/distilbert-base-multilingual-cased": {
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
    },
    "distilbert/distilbert-roberta-base": {
        "languages": ["en"],
        "max_seq_length": 512,
    },
}

DISTILBERT_MODEL_NAMES = list(DISTILBERT_MODELS.keys())


class DistilBERTEmbeddingSchema(BaseSchema):
    """Configuration schema for :class:`DistilBERTEmbedding`.

    Attributes:
        model_name: DistilBERT model for embedding generation.
        overflow_strategy: Strategy for chunks exceeding model max sequence length.
        device: Device to run the model on.
        pooling_strategy: Pooling strategy to aggregate token embeddings.
    """

    model_name: schema_field(
        enum_field(DISTILBERT_MODEL_NAMES),
        placeholder="distilbert/distilbert-base-cased",
        description=MultilingualString(
            en="DistilBERT model for embedding generation.",
            es="Modelo DistilBERT para generación de embeddings.",
            pt="Modelo DistilBERT para geração de embeddings.",
            de="DistilBERT-Modell zur Erzeugung von Embeddings.",
            zh="用于生成嵌入的 DistilBERT 模型。",
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

    pooling_strategy: schema_field(
        enum_field(DISTILBERT_POOLING_STRATEGIES),
        placeholder=MEAN,
        description=MultilingualString(
            en="Pooling strategy to aggregate token embeddings.",
            es="Estrategia de pooling para agregar embeddings de tokens.",
            pt="Estratégia de pooling para agregar embeddings de tokens.",
            de="Pooling-Strategie zur Aggregation von Token-Embeddings.",
            zh="聚合 token 嵌入的池化策略。",
        ),
    )  # type: ignore


class DistilBERTEmbedding(DenseEmbedding):
    """Dense embeddings using DistilBERT models with configurable pooling.

    Wraps :class:`_BERTEmbedding` (reusing BERT pooling logic) and exposes
    it as a DashAI component with a configurable schema
    (:class:`DistilBERTEmbeddingSchema`).
    """

    SCHEMA = DistilBERTEmbeddingSchema
    DISPLAY_NAME: str = MultilingualString(
        en="DistilBERT Embedding",
        es="Embedding DistilBERT",
        pt="Embedding DistilBERT",
        de="DistilBERT-Embedding",
        zh="DistilBERT 嵌入",
    )
    DESCRIPTION: str = MultilingualString(
        en="Dense embeddings using DistilBERT models with configurable pooling.",
        es="Embeddings densos usando modelos DistilBERT con pooling configurable.",
        pt="Embeddings densos usando modelos DistilBERT com pooling configurável.",
        de="Dichte Embeddings mit DistilBERT-Modellen und konfigurierbarem Pooling.",
        zh="使用 DistilBERT 模型生成稠密嵌入，支持可配置的池化。",
    )

    def __init__(self, **kwargs):
        """Initialise the embedding by validating parameters and creating the internal model.

        Args:
            **kwargs: Configuration matching :class:`DistilBERTEmbeddingSchema`.
        """  # noqa: E501
        self.params = self.validate_and_transform(kwargs)
        model_name = self.params["model_name"]
        device = self.params["device"]
        overflow_strategy = self.params.get("overflow_strategy", "truncate")
        pooling_strategy = self.params["pooling_strategy"]
        model_info = DISTILBERT_MODELS[model_name]
        self._embedding = _BERTEmbedding(
            model_name=model_name,
            device=device,
            model_max_length=model_info["max_seq_length"],
            overflow_strategy=overflow_strategy,
            pooling_strategy=pooling_strategy,
        )

    def load(self):
        """Load the DistilBERT model and tokenizer."""
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
