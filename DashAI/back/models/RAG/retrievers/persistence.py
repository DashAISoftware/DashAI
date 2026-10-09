from dataclasses import dataclass


@dataclass
class SparsePersistence:
    """Reference to a sparse retriever's on-disk dump.

    Attributes:
        model_dir: Absolute path to the directory containing ``.pkl``
            files. If ``None``, no previous dump exists and the retriever
            must train from scratch.
    """

    model_dir: str | None


@dataclass
class DensePersistence:
    """References to embedding matrices for a dense retriever.

    Attributes:
        matrix_dirs: Maps ``document_id`` to the absolute path of the
            directory containing ``embeddings.npy`` for that document.
        embedding_model_id: Identifier of the embedding model that
            produced the vectors.
    """

    matrix_dirs: dict[int, str]
    embedding_model_id: int | None
