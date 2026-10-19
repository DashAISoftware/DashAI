"""Abstract adapter combining FAISS infrastructure with the clustering contract.

This module sits between the generic FAISS mixin (FaissBaseModel) and concrete
clustering algorithms. It does not implement train() or get_cluster_labels() —
those are deliberately left abstract so each algorithm can use the FAISS API
that best fits its needs (index.search for K-Means, range_search for DBSCAN,
etc.).

Inheritance hierarchy for FAISS clustering models:

    FaissBaseModel          ← infrastructure mixin (not tied to clustering)
         ↓
    FaissLikeClusterer      ← this class: FAISS infra + clustering contract
         ↓             ↓
    FaissKMeans    FaissDBSCAN   ← concrete algorithms
"""

from DashAI.back.models.clustering_model import ClusteringModel
from DashAI.back.models.faiss.faiss_base_model import FaissBaseModel


class FaissLikeClusterer(FaissBaseModel, ClusteringModel):
    """Abstract base for FAISS-backed clustering algorithms.

    Combines the FAISS infrastructure mixin (``FaissBaseModel``) with DashAI's
    clustering contract (``ClusteringModel``). Subclasses receive float32
    conversion, save/load, and FAISS index pickle support for free, and only
    need to implement the two abstract methods from ``ClusteringModel``:

    - ``train(x_train)`` — fit the FAISS index and store cluster labels.
    - ``get_cluster_labels(x=None)`` — return stored or predicted labels.

    Every FAISS clustering model stores its FAISS index in ``self._index`` so
    that the inherited ``__getstate__`` / ``__setstate__`` serialises it
    correctly.
    """

    def __init__(self, **kwargs) -> None:
        """Initialise shared FAISS clustering state.

        Parameters
        ----------
        **kwargs : dict
            Forwarded to parent classes via cooperative multiple inheritance.
        """
        super().__init__(**kwargs)
        self._labels = None
        self._index = None
