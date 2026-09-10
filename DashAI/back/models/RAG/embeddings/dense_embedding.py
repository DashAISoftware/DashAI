from abc import abstractmethod
from typing import Any, List

import numpy as np

from DashAI.back.models.base_model import BaseModel


class DenseEmbedding(BaseModel):
    """Base class for all dense encoding (embedding) models.

    Subclasses must override :meth:`encode`, :meth:`batch_encode`, and
    :meth:`train`, and set :attr:`embedding_dim` during initialisation.
    """

    embedding_dim: int

    def __init__(self, **kwargs: Any):
        """Initialise the embedding model with arbitrary keyword parameters.

        Args:
            **kwargs: Model configuration parameters forwarded to subclasses.
        """
        self.params = kwargs

    def encode(self, text: str) -> List[float] | np.ndarray:
        """Generate an embedding vector for a single text string.

        Args:
            text: The input text to encode.

        Returns:
            A 1-D vector (list or ndarray) representing the embedding.

        Raises:
            NotImplementedError: Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def batch_encode(self, texts: List[str]) -> List[List[float]] | np.ndarray:
        """Generate embedding vectors for a batch of texts.

        Args:
            texts: A list of input texts to encode.

        Returns:
            A 2-D array (list of lists or ndarray) of embeddings, one per input.

        Raises:
            NotImplementedError: Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def train(self, **kwargs):
        """Train the embedding model on the provided data.

        Args:
            **kwargs: Training configuration (data, hyperparameters, etc.).
        """
        return
