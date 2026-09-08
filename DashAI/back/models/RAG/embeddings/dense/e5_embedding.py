from typing import Dict, List

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.embeddings.dense._e5_embedding import _E5Embedding
from DashAI.back.models.RAG.embeddings.dense._overflow_handler import (
    AGGREGATE,
    TRUNCATE,
)
from DashAI.back.models.RAG.embeddings.dense_embedding import DenseEmbedding

E5_MODELS: Dict[str, dict] = {
    "intfloat/e5-small-v2": {
        "languages": ["en"],
        "max_seq_length": 512,
    },
    "intfloat/e5-large-v2": {
        "languages": ["en"],
        "max_seq_length": 512,
    },
    "intfloat/multilingual-e5-large": {
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
    "intfloat/multilingual-e5-base": {
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
    "intfloat/multilingual-e5-small": {
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
    "intfloat/e5-mistral-7b-instruct": {
        "languages": ["en"],
        "max_seq_length": 4096,
    },
}

E5_MODEL_NAMES = list(E5_MODELS.keys())


class E5EmbeddingSchema(BaseSchema):
    """Configuration schema for :class:`E5Embedding`.

    Attributes:
        model_name: E5 model for embedding generation (uses query/passage prefixes).
        overflow_strategy: Strategy for chunks exceeding model max sequence length.
        device: Device to run the model on.
    """

    model_name: schema_field(
        enum_field(E5_MODEL_NAMES),
        placeholder="intfloat/e5-small-v2",
        description=MultilingualString(
            en="E5 model for embedding generation (uses query/passage prefixes).",
            es="Modelo E5 para generación de embeddings (usa prefijos query/passage).",
            pt="Modelo E5 para geração de embeddings (usa prefixos query/passage).",
            de=(
                "E5-Modell zur Erzeugung von Embeddings (verwendet"
                " query/passage-Präfixe)."
            ),
            zh="用于生成嵌入的 E5 模型（使用 query/passage 前缀）。",
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


class E5Embedding(DenseEmbedding):
    """Dense embeddings using E5 models with average pooling + L2 normalization.

    Automatically prepends ``"query: "`` or ``"passage: "`` prefixes to
    input text (see :class:`_E5Embedding`).

    Wraps :class:`_E5Embedding` and exposes it as a DashAI component with
    a configurable schema (:class:`E5EmbeddingSchema`).
    """

    SCHEMA = E5EmbeddingSchema
    DISPLAY_NAME: str = MultilingualString(
        en="E5 Embedding",
        es="Embedding E5",
        pt="Embedding E5",
        de="E5-Embedding",
        zh="E5 嵌入",
    )
    DESCRIPTION: str = MultilingualString(
        en="Dense embeddings using E5 models with average pooling + L2"
        " normalization + query/passage prefixes.",
        es="Embeddings densos usando modelos E5 con average pooling +"
        " normalización L2 + prefijos query/passage.",
        pt="Embeddings densos usando modelos E5 com average pooling +"
        " normalização L2 + prefixos query/passage.",
        de="Dichte Embeddings mit E5-Modellen, Average Pooling +"
        " L2-Normalisierung + query/passage-Präfixen.",
        zh="使用 E5 模型生成稠密嵌入，结合平均池化 + L2 归一化 + query/passage 前缀。",
    )

    def __init__(self, **kwargs):
        """Initialise the embedding by validating parameters and creating the internal model.

        Args:
            **kwargs: Configuration matching :class:`E5EmbeddingSchema`.
        """  # noqa: E501
        self.params = self.validate_and_transform(kwargs)
        model_name = self.params["model_name"]
        device = self.params["device"]
        overflow_strategy = self.params.get("overflow_strategy", "truncate")
        model_info = E5_MODELS[model_name]
        self._embedding = _E5Embedding(
            model_name=model_name,
            device=device,
            model_max_length=model_info["max_seq_length"],
            overflow_strategy=overflow_strategy,
        )

    def load(self):
        """Load the E5 model and tokenizer."""
        self._embedding.load()

    def encode(self, text: str):
        """Encode a single text into a dense embedding (prepends ``"query: "``).

        Args:
            text: Input string.

        Returns:
            A 1-D NumPy array of shape ``(embedding_dim,)``.
        """
        return self._embedding.encode(text)

    def batch_encode(self, texts: List[str]):
        """Encode a batch of texts into dense embeddings (prepends ``"passage: "``).

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
