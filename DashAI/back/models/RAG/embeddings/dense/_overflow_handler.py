from abc import abstractmethod
from typing import List

import numpy as np

from DashAI.back.models.RAG.embeddings.dense.huggingface_embedding import (
    HuggingFaceEmbedding,
)

TRUNCATE = "truncate"
AGGREGATE = "aggregate"


class OverflowHandler(HuggingFaceEmbedding):
    """Extends :class:`HuggingFaceEmbedding` with overflow handling strategies.

    When text exceeds ``model_max_length``, the tokeniser either truncates
    (``"truncate"``) or splits into segments and pools their embeddings
    together (``"aggregate"``).
    """

    def __init__(
        self,
        model_name: str,
        device: str,
        model_max_length: int,
        overflow_strategy: str,
    ):
        """Initialise the overflow handler.

        Args:
            model_name: HuggingFace model identifier.
            device: Target device (``"cpu"`` or ``"cuda"``).
            model_max_length: Maximum token length before overflow logic kicks in.
            overflow_strategy: ``"truncate"`` or ``"aggregate"``.
        """
        super().__init__(model_name=model_name, device=device)
        self.model_max_length = model_max_length
        self.overflow_strategy = overflow_strategy
        self.params["model_max_length"] = model_max_length
        self.params["overflow_strategy"] = overflow_strategy

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

    def _batch_encode_impl(self, texts: List[str]) -> np.ndarray:
        """Tokenise and encode, applying the configured overflow strategy.

        Args:
            texts: Batch of input strings.

        Returns:
            A ``(batch, embedding_dim)`` float32 NumPy array.

        Raises:
            ValueError: If ``overflow_strategy`` is not supported.
        """
        import torch

        if self.overflow_strategy not in [TRUNCATE, AGGREGATE]:
            raise ValueError(
                f"Invalid overflow strategy: {self.overflow_strategy}. "
                f"Supported strategies are: {TRUNCATE}, {AGGREGATE}."
            )
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.model_max_length,
            return_tensors="pt",
            return_overflowing_tokens=self.overflow_strategy == AGGREGATE,
            stride=0,
        )
        num_texts = len(texts)
        if (
            self.overflow_strategy == AGGREGATE
            and "overflow_to_sample_mapping" in encoded
        ):
            mapping = encoded.pop("overflow_to_sample_mapping")
            encoded = {k: v.to(self.device) for k, v in encoded.items()}
            with torch.no_grad():
                outputs = self.model(**encoded)
            segment_embeddings = self._pool(outputs, encoded["attention_mask"]).cpu()
            result = []
            for i in range(num_texts):
                segment_indices = (mapping == i).nonzero(as_tuple=True)[0]
                if len(segment_indices) == 1:
                    result.append(segment_embeddings[segment_indices[0]])
                else:
                    result.append(
                        torch.mean(segment_embeddings[segment_indices], dim=0)
                    )
            return torch.stack(result).numpy()
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        with torch.no_grad():
            outputs = self.model(**encoded)
        embeddings = self._pool(outputs, encoded["attention_mask"])
        return embeddings.cpu().numpy()
