from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Sequence, Type

from DashAI.back.models.base_model import BaseModel

if TYPE_CHECKING:
    from numpy import ndarray

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ClusteringModel(BaseModel):
    """Base contract for models that perform clustering tasks.

    Concrete clustering models receive input features and produce discovered
    cluster assignments. They are evaluated by clustering executors with
    metrics that use ``X`` and labels, not ``y_true`` and ``y_pred``. Backend
    adapters such as sklearn or FAISS should implement this contract once so
    concrete clustering algorithms can remain small.
    """

    COMPATIBLE_COMPONENTS = ["ClusteringTask"]

    @classmethod
    def get_registry(cls) -> Dict[str, Type["ClusteringModel"]]:
        """Return concrete clustering algorithm classes keyed by class name.

        Any subclass that declares its own ``SCHEMA`` is treated as a concrete
        algorithm and included automatically.  New algorithms become available
        to the ``Clustering`` converter as soon as their module is imported —
        no manual registration step is required.
        """
        result: Dict[str, Type["ClusteringModel"]] = {}

        def _collect(base: Type["ClusteringModel"]) -> None:
            for sub in base.__subclasses__():
                if "SCHEMA" in sub.__dict__:
                    result[sub.__name__] = sub
                _collect(sub)

        _collect(cls)
        return result

    def get_fit_attributes(self) -> Dict[str, Any]:
        """Return algorithm-specific post-fit attributes for the converter report.

        Override in concrete subclasses to expose attributes that are
        specific to the clustering algorithm (e.g. cluster centres for K-Means,
        linkage data for Agglomerative). The converter calls this after ``train``
        and includes the result in the execution report consumed by explorers.

        Returns
        -------
        Dict[str, Any]
            JSON-serializable dict of algorithm-specific attributes.
        """
        return {}

    @abstractmethod
    def train(self, x: "DashAIDataset") -> "ClusteringModel":
        """Fit the clustering model using input features only.

        Clustering models do not receive target columns. Implementations should
        store the labels discovered during fitting when the backend exposes
        them only for the training data.

        Parameters
        ----------
        x : DashAIDataset
            Input feature matrix used to fit the clustering model.

        Returns
        -------
        ClusteringModel
            The fitted clustering model instance.
        """
        raise NotImplementedError

    @abstractmethod
    def get_cluster_labels(
        self, x: "DashAIDataset" = None
    ) -> "ndarray | Sequence[int]":
        """Return cluster labels for fitted data or provided samples.

        Algorithms that support assigning labels to new samples may use ``x``.
        Algorithms that only expose labels for the fitted dataset should return
        those stored labels when ``x`` is omitted.

        Parameters
        ----------
        x : DashAIDataset, optional
            Input samples to assign to clusters. If omitted, the method should
            return labels discovered during fitting when the backend supports
            only fitted-data labels.

        Returns
        -------
        array-like
            Cluster label assigned to each sample. Noise points may be encoded
            with backend-specific labels such as ``-1``.
        """
        raise NotImplementedError
