import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Final, List, Tuple

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.base_model import BaseModel
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.exceptions import RAGWorkflowError


class RetrieverModel(BaseModel, ABC):
    """
    Component: abstract base class for all retriever models.

    Implements the Component role in the Composite design pattern (GoF).
    """

    TYPE: Final[str] = "RetrieverModel"
    DISPLAY_NAME: str = MultilingualString(
        en="Retriever",
        es="Recuperador",
        pt="Recuperador",
        de="Retriever",
        zh="检索器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Document retrieval component.",
        es="Componente de recuperación de documentos.",
        pt="Componente de recuperação de documentos.",
        de="Komponente zur Dokumentabfrage.",
        zh="文档检索组件。",
    )
    COLOR: str = "#9C27B0"
    ICON: str = "Search"

    env_RAG_path: str | os.PathLike | None  # noqa: N815
    chunks: Dict[int, Dict[int, Chunk]]
    params: Dict[str, Any]

    def __init__(self, **kwargs):
        """Initialize the retriever model.

        Stores keyword arguments as ``self.params`` and initialises the
        database ID to ``None``.

        Args:
            **kwargs: Configuration parameters for the retriever.
        """
        self._db_id: int | None = None
        self.params = kwargs

    def get_id(self) -> int | None:
        """Return the database ID of this retriever, or ``None``.

        Returns:
            The database ID if already persisted, otherwise ``None``.
        """
        return self._db_id

    def set_id(self, id: int) -> None:
        """Assign a database ID to this retriever.

        The ID can only be set once; subsequent calls raise an error.

        Args:
            id: The database ID to assign.

        Raises:
            RAGWorkflowError: If an ID has already been assigned.
        """
        if self._db_id is not None:
            raise RAGWorkflowError(
                f"ID is already set to {self._db_id}, cannot reassign to {id}."
            )
        self._db_id = id

    def _validate_chunks_dict(self) -> None:
        """Validate the structure of the ``chunks`` attribute.

        Ensures it is a nested dictionary of the form
        ``{doc_id: {chunk_id: Chunk}}`` and that each chunk's
        ``document_id`` matches its parent key.

        Raises:
            ValueError: If the structure is invalid.
        """
        if not isinstance(self.chunks, dict):
            raise ValueError("Chunks must be a dictionary.")
        for doc_id, doc_chunks in self.chunks.items():
            if not isinstance(doc_id, int):
                raise ValueError(f"Document ID {doc_id} must be an integer.")
            if not isinstance(doc_chunks, dict):
                raise ValueError(
                    f"Chunks for document ID {doc_id} must be a dictionary."
                )
            for chunk_id, chunk in doc_chunks.items():
                if not isinstance(chunk_id, int):
                    raise ValueError(
                        f"Chunk ID {chunk_id} in document ID {doc_id}"
                        f" must be an integer."
                    )
                if not isinstance(chunk, Chunk):
                    raise ValueError(
                        f"Chunk {chunk_id} in document ID {doc_id}"
                        f" must be an instance of Chunk."
                    )
                if chunk.document_id != doc_id:
                    raise ValueError(
                        f"Chunk {chunk_id} document_id {chunk.document_id}"
                        f" != doc ID {doc_id}."
                    )

    def inject_infra(
        self,
        env_RAG_path: str | os.PathLike,  # noqa: N803
        chunks: Dict[int, Dict[int, Chunk]],
        persistence: Any,
    ) -> None:
        """Inject runtime infrastructure *after* schema validation.

        Subclasses **must** store the three arguments as instance
        attributes.  Raises ``TypeError`` if any argument has an
        unexpected type.

        Subclasses define required params in their ``__init__`` and
        pop them from ``self.params``.

        Args:
            env_RAG_path: Root directory path for RAG data.
            chunks: Nested dictionary mapping document IDs to chunk IDs
                to :class:`Chunk` instances.
            persistence: Persistence object for saving/loading state.
        """
        self.env_RAG_path = env_RAG_path
        self.chunks = chunks
        self._persistence = persistence
        self._validate_chunks_dict()

    @property
    def persistence(self):
        """Get the persistence object."""
        return self._persistence

    @persistence.setter
    def persistence(self, value):
        """Set the persistence object.

        Args:
            value: The new persistence object.
        """
        self._persistence = value

    def init_model(self) -> None:
        """Called by the factory **after** ``inject_infra()``.

        Subclasses restore saved state (``load()``) or compute initial
        state (``_fit()``, ``_init_embedding()``).  Default is a no-op.
        """

    @abstractmethod
    def retrieve(self, query, **kwargs) -> List[Chunk]:
        """Retrieve the top-k chunks most relevant to the query.

        Args:
            query: The search query string.
            **kwargs: Additional retrieval parameters (e.g. ``top_k``).

        Returns:
            A list of :class:`Chunk` instances ordered by relevance.
        """
        raise NotImplementedError

    @abstractmethod
    def score_chunks(self, chunk_ids: List[int], query: str) -> List[Tuple[int, float]]:
        """Score a set of chunks against a query.

        Args:
            chunk_ids: List of chunk IDs to score.
            query: The search query string.

        Returns:
            A list of ``(chunk_id, distance)`` tuples sorted by distance
            (ascending — lower is more relevant).
        """
        raise NotImplementedError

    @property
    def retrieval_top_k(self) -> int:
        """Return the maximum number of chunks this retriever returns.

        Returns:
            The top-k value.
        """
        raise NotImplementedError

    # ── Child management (Composite pattern) ────────────────────────

    def add(self, child: "RetrieverModel") -> None:
        """Add a child retriever (Composite pattern).

        Args:
            child: The child retriever to add.

        Raises:
            NotImplementedError: If the subclass does not support children.
        """
        raise NotImplementedError

    def remove(self, child: "RetrieverModel") -> None:
        """Remove a child retriever (Composite pattern).

        Args:
            child: The child retriever to remove.

        Raises:
            NotImplementedError: If the subclass does not support children.
        """
        raise NotImplementedError

    def get_children(self) -> List["RetrieverModel"]:
        """Return the list of child retrievers (Composite pattern).

        Returns:
            A list of :class:`RetrieverModel` children.

        Raises:
            NotImplementedError: If the subclass does not support children.
        """
        raise NotImplementedError

    def save(self, filename: str = "") -> None:
        """Persist the retriever's state to disk.

        Args:
            filename: Optional filename override. Defaults to an empty
                string (subclasses determine their own default path).
        """

    def load(self, filename: str = "") -> None:
        """Restore the retriever's state from disk.

        Args:
            filename: Optional filename override. Defaults to an empty
                string (subclasses determine their own default path).
        """

    def train(self, **kwargs):
        """Train the retriever on the injected chunks.

        Args:
            **kwargs: Training parameters. Default is a no-op.
        """
        return
