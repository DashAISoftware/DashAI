"""Base adapter for scikit-learn clustering models."""

from typing import TYPE_CHECKING, Any

from DashAI.back.models.clustering_model import ClusteringModel

if TYPE_CHECKING:
    from numpy import ndarray

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class SklearnLikeClusterer(ClusteringModel):
    """Shared behaviour for scikit-learn-style clustering algorithms.

    Concrete subclasses also inherit from the actual sklearn estimator, for
    example ``KMeans`` or ``DBSCAN``. This adapter maps DashAI's clustering
    contract to the sklearn API: models are fitted with input features only and
    cluster assignments are exposed through ``get_cluster_labels``.

    Clustering is intentionally restricted to numeric features by
    ``ClusteringTask`` and the clustering converter. This adapter therefore
    assumes it receives a dataset that has already been validated for the
    clustering task.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the sklearn clustering adapter.

        Parameters
        ----------
        *args : tuple
            Positional arguments forwarded to the sklearn estimator.
        **kwargs : dict
            Keyword arguments forwarded to the sklearn estimator.
        """
        super().__init__(*args, **kwargs)
        self._labels: "ndarray | None" = None
        self._fitted_feature_names: list[str] = []

    def save(self, filename: str) -> None:
        """Serialise the model to disk using joblib.

        Parameters
        ----------
        filename : str
            Destination file path where the model will be written.
        """
        import joblib

        joblib.dump(self, filename)

    @staticmethod
    def load(filename: str) -> Any:
        """Deserialise a model from disk using joblib.

        Parameters
        ----------
        filename : str
            Path to the file previously written by :meth:`save`.

        Returns
        -------
        Any
            The loaded model instance.
        """
        import joblib

        model = joblib.load(filename)
        return model

    def _prepare_features(self, x: "DashAIDataset", is_fit: bool = False):
        """Return the feature matrix used by sklearn clusterers.

        During fitting, the incoming columns are remembered. During label
        assignment for new samples, the same columns are selected in the same
        order.
        """
        x_pandas = x.to_pandas()

        if is_fit:
            self._fitted_feature_names = list(x_pandas.columns)
            return x_pandas

        missing_columns = [
            name for name in self._fitted_feature_names if name not in x_pandas.columns
        ]
        if missing_columns:
            raise ValueError(
                f"Missing fitted feature columns in dataset: {missing_columns}."
            )
        return x_pandas[self._fitted_feature_names]

    def train(self, x_train: "DashAIDataset") -> "SklearnLikeClusterer":
        """Fit the clustering model using input features only.

        Parameters
        ----------
        x_train : DashAIDataset
            Dataset containing the input columns selected for clustering.

        Returns
        -------
        SklearnLikeClusterer
            The fitted clustering adapter.

        Raises
        ------
        ValueError
            If the wrapped sklearn estimator does not expose labels after
            fitting.
        """
        x_processed = self._prepare_features(x_train, is_fit=True)

        if hasattr(self, "fit_predict"):
            self._labels = self.fit_predict(x_processed)
        else:
            self.fit(x_processed)
            self._labels = getattr(self, "labels_", None)

        if self._labels is None:
            raise ValueError(
                f"{self.__class__.__name__} did not produce cluster labels."
            )

        return self

    def get_cluster_labels(self, x: "DashAIDataset | None" = None) -> "ndarray":
        """Return fitted labels or assign labels to new samples when supported.

        Some sklearn clusterers, such as K-Means, implement ``predict`` and can
        assign labels to new samples. Others, such as DBSCAN, only expose labels
        for the fitted dataset through ``labels_``. This method supports both
        cases.

        Parameters
        ----------
        x : DashAIDataset, optional
            Samples to assign to clusters. If omitted, or if the wrapped
            estimator does not support ``predict``, the labels discovered during
            fitting are returned.

        Returns
        -------
        numpy.ndarray
            Cluster label assigned to each sample.

        Raises
        ------
        ValueError
            If the model has not been fitted, or if labels are requested for
            unseen samples from an estimator that cannot predict new labels.
        """
        if x is not None and hasattr(self, "predict"):
            x_processed = self._prepare_features(x, is_fit=False)
            return self.predict(x_processed)

        if self._labels is None:
            raise ValueError(
                f"{self.__class__.__name__} must be fitted before returning labels."
            )

        if x is not None and len(x) != len(self._labels):
            raise ValueError(
                f"{self.__class__.__name__} cannot assign labels to unseen samples."
            )

        return self._labels
