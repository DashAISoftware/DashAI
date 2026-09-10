from typing import List

import numpy as np

from DashAI.back.core.schema_fields import enum_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.schema_fields.schema_field import schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.embeddings.dense_embedding import DenseEmbedding
from DashAI.back.models.RAG.exceptions import RAGEmbeddingEmptyInputError


class FastTextEmbeddingSchema(BaseSchema):
    """Configuration schema for :class:`FastTextEmbedding`.

    Attributes:
        model_name: Name of the pre-trained FastText model to use.
        pooling_strategy: Pooling strategy (``"mean"`` or ``"max"``).
    """

    model_name: schema_field(
        enum_field(["facebook/fasttext-es-vectors", "facebook/fasttext-en-vectors"]),
        "facebook/fasttext-en-vectors",
        "Name of the pre-trained model to use",
    )  # type: ignore

    pooling_strategy: schema_field(
        enum_field(["mean", "max"]),
        "mean",
        "Pooling strategy to use",
    )  # type: ignore


class FastTextEmbedding(DenseEmbedding):
    """Dense embeddings using FastText word vectors with mean or max pooling.

    Downloads the model binary from the HuggingFace Hub and aggregates
    word-level vectors into a single sentence-level embedding.
    """

    SCHEMA = FastTextEmbeddingSchema
    DISPLAY_NAME = MultilingualString(
        en="FastText Embedding",
        es="Embedding FastText",
        pt="Embedding FastText",
        de="FastText-Embedding",
        zh="FastText 嵌入",
    )
    DESCRIPTION = MultilingualString(
        en="Convert text to embeddings using FastText.",
        es="Convierte texto a embeddings usando FastText.",
        pt="Converte texto em embeddings usando FastText.",
        de="Konvertiert Text mit FastText in Embeddings.",
        zh="使用 FastText 将文本转换为嵌入。",
    )

    def __init__(self, **kwargs):
        """Initialise the embedding by validating parameters and setting up pooling.

        Args:
            **kwargs: Configuration matching :class:`FastTextEmbeddingSchema`.
        """
        self.params = self.validate_and_transform(kwargs)
        self.model_name = self.params["model_name"]
        self.pooling_strategy = self.params["pooling_strategy"]
        pooling_functions = {"mean": np.mean, "max": np.max}
        self.pooling_function = pooling_functions[self.pooling_strategy]
        self.model = None

    def load(self):
        """Download and load the FastText binary model from the HuggingFace Hub."""
        import fasttext
        from huggingface_hub import hf_hub_download

        if self.model is not None:
            return
        model_path = hf_hub_download(repo_id=self.model_name, filename="model.bin")
        self.model = fasttext.load_model(model_path)

    def save(self):
        """No-op. The model is loaded from HF Hub on demand."""

    def train(self, **kwargs):
        """No-op. Pre-trained FastText vectors are used as-is."""

    def encode(self, text: str) -> np.ndarray:
        """Encode a single text by averaging/max-pooling its word vectors.

        Args:
            text: Input string (non-empty).

        Returns:
            A 1-D float32 NumPy array of shape ``(embedding_dim,)``.

        Raises:
            RAGEmbeddingEmptyInputError: If the input text is empty or blank.
        """
        if not text or not text.strip():
            raise RAGEmbeddingEmptyInputError("Cannot encode empty text")
        token_embeddings = [self.model.get_word_vector(word) for word in text.split()]
        return self.pooling_function(np.array(token_embeddings), axis=0)

    def batch_encode(self, texts: List[str]) -> np.ndarray:
        """Encode a batch of texts by pooling their word vectors.

        Args:
            texts: List of input strings.

        Returns:
            A ``(batch, embedding_dim)`` float32 NumPy array.
        """
        all_embeddings = []
        for text in texts:
            embedding = self.encode(text)
            all_embeddings.append(embedding)
        return np.array(all_embeddings)
