from abc import abstractmethod
from typing import List

import numpy as np

from DashAI.back.models.RAG.embeddings.dense_embedding import DenseEmbedding


class HuggingFaceEmbedding(DenseEmbedding):
    """Abstract base for dense embeddings powered by a HuggingFace ``AutoModel``.

    Handles tokenisation, device placement and inference dispatch; subclasses
    only need to implement :meth:`_pool` to convert model outputs into a single
    vector per text.
    """

    def __init__(self, model_name: str, device: str):
        """Initialise the HuggingFace embedding wrapper.

        Args:
            model_name: Name or path of a HuggingFace ``AutoModel``.
            device: Target device (``"cpu"`` or ``"cuda"``).
        """
        self.model_name = model_name
        self.device = device
        self.params = {
            "model_name": model_name,
            "device": device,
        }
        self.model = None
        self.tokenizer = None

    def save(self):
        """No-op. Persistence is handled externally."""

    def train(self, **kwargs):
        """No-op. Pre-trained models are used as-is."""

    @abstractmethod
    def _pool(self, model_output, attention_mask):
        """Aggregate token-level hidden states into a single embedding per item.

        Args:
            model_output: Output tuple from ``AutoModel``.
            attention_mask: Attention mask tensor with shape ``(batch, seq_len)``.

        Returns:
            A torch tensor of shape ``(batch, embedding_dim)``.
        """
        raise NotImplementedError

    def load(self):
        """Download the tokenizer and model from HuggingFace Hub and move to device."""
        from transformers import AutoModel, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name).to(self.device)

    def _batch_encode_impl(self, texts: List[str]) -> np.ndarray:
        """Tokenise, forward, pool and return a NumPy array of embeddings.

        Args:
            texts: Batch of input strings.

        Returns:
            A ``(batch, embedding_dim)`` float32 NumPy array.
        """
        import torch

        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        with torch.no_grad():
            outputs = self.model(**encoded)
        embeddings = self._pool(outputs, encoded["attention_mask"])
        return embeddings.cpu().numpy()

    def batch_encode(self, texts: List[str]) -> np.ndarray:
        """Encode a batch of texts into a dense NumPy array.

        Args:
            texts: List of input strings.

        Returns:
            A ``(batch, embedding_dim)`` float32 NumPy array.
        """
        return self._batch_encode_impl(texts)

    def encode(self, text: str) -> np.ndarray:
        """Encode a single text into a 1-D embedding vector.

        Args:
            text: Input string.

        Returns:
            A 1-D float32 NumPy array of shape ``(embedding_dim,)``.
        """
        embeddings = self.batch_encode([text])
        return embeddings.squeeze()
