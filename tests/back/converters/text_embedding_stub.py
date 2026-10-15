"""A stand-in for a SentenceTransformer model, so tests download nothing."""

import zlib
from typing import Any, Dict, List, Optional

import numpy as np


class FakeTokenizer:
    """Tokenize on whitespace, one token per word."""

    def __call__(self, text: str, add_special_tokens: bool = False) -> Dict[str, Any]:
        """Return the words of a text as token ids.

        Parameters
        ----------
        text : str
            The text.
        add_special_tokens : bool
            Ignored.

        Returns
        -------
        dict
            ``{"input_ids": <list of words>}``.
        """
        return {"input_ids": text.split()}

    def decode(self, ids: List[str], **kwargs: Any) -> str:
        """Join words back into a text.

        Parameters
        ----------
        ids : list of str
            Words.
        **kwargs
            Ignored.

        Returns
        -------
        str
            The words joined by spaces.
        """
        return " ".join(ids)


class FakeSentenceModel:
    """Deterministic vectors keyed on the prompted text, with a call log.

    Parameters
    ----------
    dim : int
        Embedding size.
    max_seq_length : int or None
        Token limit used by the aggregate overflow strategy.
    """

    def __init__(self, dim: int = 8, max_seq_length: Optional[int] = 16):
        self.dim = dim
        self.max_seq_length = max_seq_length
        self.tokenizer = FakeTokenizer()
        self.calls: List[Dict[str, Any]] = []

    def get_sentence_embedding_dimension(self) -> int:
        """Return the embedding size.

        Returns
        -------
        int
            ``dim``.
        """
        return self.dim

    def encode(
        self,
        sentences: List[str],
        batch_size: int = 32,
        prompt: Optional[str] = None,
        normalize_embeddings: bool = False,
        convert_to_numpy: bool = True,
        show_progress_bar: bool = False,
    ) -> np.ndarray:
        """Return one vector per sentence and record the call.

        Parameters
        ----------
        sentences : list of str
            Texts to encode.
        batch_size : int
            Recorded only.
        prompt : str, optional
            Prepended to every sentence before hashing.
        normalize_embeddings : bool
            Whether rows are scaled to unit length.
        convert_to_numpy : bool
            Ignored.
        show_progress_bar : bool
            Ignored.

        Returns
        -------
        np.ndarray
            ``(len(sentences), dim)`` float32 array.
        """
        self.calls.append(
            {
                "sentences": list(sentences),
                "prompt": prompt,
                "normalize": normalize_embeddings,
                "batch_size": batch_size,
            }
        )
        rows = []
        for sentence in sentences:
            seed = zlib.crc32(((prompt or "") + sentence).encode("utf-8"))
            rows.append(np.random.RandomState(seed).rand(self.dim) + 0.5)
        vectors = np.asarray(rows, dtype=np.float32).reshape(len(sentences), self.dim)
        if normalize_embeddings and len(sentences):
            vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors


def with_fake_model(converter: Any, **kwargs: Any) -> FakeSentenceModel:
    """Make a converter use a fake model instead of loading one.

    Parameters
    ----------
    converter : TextEmbeddingConverter
        The converter to patch.
    **kwargs
        Passed to :class:`FakeSentenceModel`.

    Returns
    -------
    FakeSentenceModel
        The model the converter now uses.
    """
    model = FakeSentenceModel(**kwargs)
    converter._pretrained = model
    return model
