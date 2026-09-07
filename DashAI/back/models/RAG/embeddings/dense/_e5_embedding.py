from typing import List

import numpy as np

from DashAI.back.models.RAG.embeddings.dense._overflow_handler import (
    OverflowHandler,
)

QUERY_PREFIX = "query: "
PASSAGE_PREFIX = "passage: "


class _E5Embedding(OverflowHandler):
    """Internal wrapper for E5 embedding models.

    Automatically prepends ``"passage: "`` to documents and ``"query: "``
    to queries, then applies mean pooling with L2 normalisation.
    """

    def __init__(
        self,
        model_name: str,
        device: str,
        model_max_length: int,
        overflow_strategy: str,
    ):
        """Initialise the E5 embedding wrapper.

        Args:
            model_name: HuggingFace model identifier.
            device: Target device (``"cpu"`` or ``"cuda"``).
            model_max_length: Maximum token length.
            overflow_strategy: ``"truncate"`` or ``"aggregate"``.
        """
        super().__init__(
            model_name=model_name,
            device=device,
            model_max_length=model_max_length,
            overflow_strategy=overflow_strategy,
        )

    def _pool(self, model_output, attention_mask):
        """Mean-pool token embeddings with L2 normalisation.

        Args:
            model_output: Output from ``AutoModel``.
            attention_mask: Attention mask tensor.

        Returns:
            Pooled and normalised tensor of shape ``(batch, embedding_dim)``.
        """
        import torch.nn.functional as functional

        last_hidden = model_output[0]
        mask = attention_mask[..., None].bool()
        last_hidden = last_hidden.masked_fill(~mask, 0.0)
        pooled = last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]
        return functional.normalize(pooled, p=2, dim=1)

    def batch_encode(self, texts: List[str]) -> np.ndarray:
        """Encode a batch of documents (prepends ``"passage: "``).

        Args:
            texts: List of input strings.

        Returns:
            A ``(batch, embedding_dim)`` float32 NumPy array.
        """
        prefixed = [f"{PASSAGE_PREFIX}{t}" for t in texts]
        return self._batch_encode_impl(prefixed)

    def encode(self, text: str) -> np.ndarray:
        """Encode a single query (prepends ``"query: "``).

        Args:
            text: Input string.

        Returns:
            A 1-D float32 NumPy array of shape ``(embedding_dim,)``.
        """
        result = self._batch_encode_impl([f"{QUERY_PREFIX}{text}"])
        return result.squeeze()
