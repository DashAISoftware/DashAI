from typing import List

import numpy as np

from DashAI.back.models.RAG.embeddings.dense.huggingface_embedding import (
    HuggingFaceEmbedding,
)
from DashAI.back.models.RAG.exceptions import RAGEmbeddingError


class _InstructorEmbedding(HuggingFaceEmbedding):
    """Internal wrapper around INSTRUCTOR models via ``SentenceTransformer``.

    Prepends a fixed instruction string to every input text and delegates
    encoding to the ``SentenceTransformer`` API (which handles INSTRUCTOR's
    prompt-based pooling).
    """

    def __init__(
        self,
        model_name: str,
        device: str,
        instruction: str,
    ):
        """Initialise the INSTRUCTOR embedding wrapper.

        Args:
            model_name: HuggingFace model identifier for the INSTRUCTOR model.
            device: Target device (``"cpu"`` or ``"cuda"``).
            instruction: Instruction text prepended to every query / document.
        """
        super().__init__(model_name=model_name, device=device)
        self.instruction = instruction
        self.params["instruction"] = instruction

    def _pool(self, model_output, attention_mask):
        """Not implemented — INSTRUCTOR uses its own encoding API."""
        raise NotImplementedError(
            "INSTRUCTOR uses SentenceTransformer API, _pool is unused."
        )

    def load(self):
        """Instantiate the INSTRUCTOR model via ``SentenceTransformer``."""
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(self.model_name, device=self.device)

    def batch_encode(self, texts: List[str]) -> np.ndarray:
        """Encode a batch of texts with the fixed instruction prefix.

        Args:
            texts: List of input strings.

        Returns:
            A ``(batch, embedding_dim)`` float32 NumPy array.

        Raises:
            RAGEmbeddingError: If the model has not been loaded yet.
        """
        if self.model is None:
            raise RAGEmbeddingError(
                "Model not loaded. Call load() before batch_encode()."
            )
        return self.model.encode(
            texts,
            prompt=self.instruction,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    def encode(self, text: str) -> np.ndarray:
        """Encode a single text with the fixed instruction prefix.

        Args:
            text: Input string.

        Returns:
            A 1-D float32 NumPy array of shape ``(embedding_dim,)``.

        Raises:
            RAGEmbeddingError: If the model has not been loaded yet.
        """
        if self.model is None:
            raise RAGEmbeddingError("Model not loaded. Call load() before encode().")
        result = self.model.encode(
            [text],
            prompt=self.instruction,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return result.squeeze()
