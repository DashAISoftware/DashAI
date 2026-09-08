from typing import Dict, List

from DashAI.back.core.schema_fields import (
    BaseSchema,
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

LABSE_MODELS: Dict[str, dict] = {
    "sentence-transformers/LaBSE": {
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
            "gu",
            "ka",
            "ku",
            "my",
            "sq",
            "multi",
        ],
        "max_seq_length": 512,
    },
}

LABSE_MODEL_NAMES = list(LABSE_MODELS.keys())


class LaBSEmbeddingSchema(BaseSchema):
    """Configuration schema for :class:`LaBSEmbedding`.

    Attributes:
        model_name: LaBSE model for multilingual embedding generation (109 languages).
        overflow_strategy: Strategy for chunks exceeding model max sequence length.
        device: Device to run the model on.
    """

    model_name: schema_field(
        enum_field(LABSE_MODEL_NAMES),
        placeholder="sentence-transformers/LaBSE",
        description=MultilingualString(
            en="LaBSE model for multilingual embedding generation (109 languages).",
            es="Modelo LaBSE para generación de embeddings multilingües (109 idiomas).",
            pt="Modelo LaBSE para geração de embeddings multilíngues (109 idiomas).",
            de="LaBSE-Modell zur Erzeugung mehrsprachiger Embeddings (109 Sprachen).",
            zh="用于多语言嵌入生成的 LaBSE 模型（109 种语言）。",
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


class LaBSEmbedding(DenseEmbedding):
    """Dense embeddings using the LaBSE multilingual model (109 languages).

    Wraps :class:`_SentenceTransformerEmbedding` (mean pooling, L2
    normalisation forced on) and exposes it as a DashAI component with
    a configurable schema (:class:`LaBSEmbeddingSchema`).
    """

    SCHEMA = LaBSEmbeddingSchema
    DISPLAY_NAME: str = MultilingualString(
        en="LaBSE Embedding",
        es="Embedding LaBSE",
        pt="Embedding LaBSE",
        de="LaBSE-Embedding",
        zh="LaBSE 嵌入",
    )
    DESCRIPTION: str = MultilingualString(
        en="Dense embeddings using LaBSE multilingual model (109 languages).",
        es="Embeddings densos usando el modelo multilingüe LaBSE (109 idiomas).",
        pt="Embeddings densos usando o modelo multilíngue LaBSE (109 idiomas).",
        de="Dichte Embeddings mit dem mehrsprachigen LaBSE-Modell (109 Sprachen).",
        zh="使用 LaBSE 多语言模型生成稠密嵌入（109 种语言）。",
    )

    def __init__(self, **kwargs):
        """Initialise the embedding by validating parameters and creating the internal model.

        Args:
            **kwargs: Configuration matching :class:`LaBSEmbeddingSchema`.
        """  # noqa: E501
        self.params = self.validate_and_transform(kwargs)
        model_name = self.params["model_name"]
        device = self.params["device"]
        overflow_strategy = self.params.get("overflow_strategy", "truncate")
        model_info = LABSE_MODELS[model_name]
        self._embedding = _SentenceTransformerEmbedding(
            model_name=model_name,
            device=device,
            model_max_length=model_info["max_seq_length"],
            overflow_strategy=overflow_strategy,
            normalize=True,
        )

    def load(self):
        """Load the LaBSE model and tokenizer."""
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
