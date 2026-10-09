from abc import ABC, abstractmethod
from typing import List

from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.retrievers.base_retriever import BaseRetriever


class CompositeRetriever(BaseRetriever, ABC):
    """
    Composite: abstract base for retrievers that contain child retrievers.

    Implements the Composite role in the Composite design pattern (GoF).
    """

    REQUIRED_EXTRA_KWARGS: list = []

    def __init__(self, **kwargs):
        """Initialize the composite retriever with its children.

        Pops the ``children`` key from *kwargs* and validates that it is
        a list of :class:`BaseRetriever` instances.

        Args:
            **kwargs: Must contain a ``children`` key mapping to a list
                of :class:`BaseRetriever` instances.

        Raises:
            TypeError: If ``children`` is not a list or contains
                non-retriever elements.
        """
        children_data = kwargs.pop("children")
        if not isinstance(children_data, list):
            raise TypeError(
                f"'children' must be a list, got {type(children_data).__name__}"
            )
        if children_data and not all(
            isinstance(c, BaseRetriever) for c in children_data
        ):
            raise TypeError(
                "All elements in 'children' must be BaseRetriever instances"
            )
        self._children: List[BaseRetriever] = children_data
        super().__init__(**kwargs)

    def add(self, child: BaseRetriever) -> None:
        """Add a child retriever.

        Args:
            child: The :class:`BaseRetriever` instance to add.
        """
        self._children.append(child)

    def remove(self, child: BaseRetriever) -> None:
        """Remove a child retriever.

        Args:
            child: The :class:`BaseRetriever` instance to remove.
        """
        self._children.remove(child)

    def get_children(self) -> List[BaseRetriever]:
        """Return a copy of the children list.

        Returns:
            A new list containing all child :class:`BaseRetriever`
            instances.
        """
        return list(self._children)

    @abstractmethod
    def retrieve(self, query, **kwargs) -> List[Chunk]:
        """Retrieve chunks by delegating to child retrievers.

        Args:
            query: The search query string.
            **kwargs: Additional retrieval parameters.

        Returns:
            A list of :class:`Chunk` instances.
        """
        raise NotImplementedError

    def score_chunks(self, chunk_ids: List[int], query: str) -> list:
        """Score chunks against a query.

        .. note::
           The base ``CompositeRetriever`` does not implement chunk scoring —
           each concrete composite subclass that supports scoring must
           override this method.  The ``SequentialRetriever``, for instance,
           delegates ``score_chunks`` to its leaf children.

        Args:
            chunk_ids: List of chunk IDs to score.
            query: The search query string.

        Returns:
            A list of ``(chunk_id, distance)`` tuples.

        Raises:
            NotImplementedError: Always — subclasses must override.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not implement score_chunks. "
            "Concrete composite retrievers that support re-ranking "
            "must override this method."
        )
