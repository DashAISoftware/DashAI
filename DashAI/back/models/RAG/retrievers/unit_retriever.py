from abc import ABC
from typing import Any, Dict, Final, List

from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.retrievers.persistence import (
    DensePersistence,
    SparsePersistence,
)
from DashAI.back.models.RAG.retrievers.retriever_model import RetrieverModel


class UnitRetriever(RetrieverModel, ABC):
    """Leaf: abstract base for unit retrievers.

    A unit retriever cannot contain children — it is the leaf node in the
    Composite design pattern.  Concrete subclasses must be either sparse
    or dense retrievers.
    """

    TYPE: Final[str] = "RetrieverModel"

    def __init__(self, **kwargs):
        """Initialize the unit retriever.

        Args:
            **kwargs: Keyword arguments forwarded to the parent
                :class:`RetrieverModel`.
        """
        super().__init__(**kwargs)

    def inject_infra(
        self,
        env_RAG_path: str,  # noqa: N803
        chunks: Dict[int, Dict[int, Chunk]],
        persistence: Any,
    ) -> None:
        """Inject runtime infrastructure with type-checked persistence.

        Args:
            env_RAG_path: Root directory path for RAG data.
            chunks: Nested dictionary mapping document IDs to chunk IDs
                to :class:`Chunk` instances.
            persistence: A :class:`SparsePersistence` or
                :class:`DensePersistence` instance.

        Raises:
            TypeError: If *persistence* is not a supported persistence type.
        """
        if not isinstance(persistence, (SparsePersistence, DensePersistence)):
            raise TypeError(
                f"Expected SparsePersistence or DensePersistence, "
                f"got {type(persistence).__name__}"
            )
        super().inject_infra(env_RAG_path, chunks, persistence)

    def _check_infra(self) -> None:
        """Raise if infrastructure has not been injected.

        Raises:
            RuntimeError: If ``inject_infra()`` has not been called yet.
        """
        if self._persistence is None:
            raise RuntimeError(
                f"{self.__class__.__name__}: infrastructure not injected. "
                "Call inject_infra() before retrieve()."
            )

    def add(self, child: RetrieverModel) -> None:
        """Add a child retriever (not supported for unit retrievers).

        Args:
            child: The child retriever to add.

        Raises:
            TypeError: Always — unit retrievers cannot contain children.
        """
        raise TypeError(
            f"{self.__class__.__name__} is a unit retriever and"
            " cannot contain children."
        )

    def remove(self, child: RetrieverModel) -> None:
        """Remove a child retriever (not supported for unit retrievers).

        Args:
            child: The child retriever to remove.

        Raises:
            TypeError: Always — unit retrievers cannot contain children.
        """
        raise TypeError(
            f"{self.__class__.__name__} is a unit retriever and"
            " cannot contain children."
        )

    def get_children(self) -> List[RetrieverModel]:
        """Return the (empty) list of child retrievers.

        Returns:
            An empty list — unit retrievers have no children.
        """
        return []
