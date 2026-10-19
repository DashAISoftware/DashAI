from typing import TYPE_CHECKING, Dict, Type

from DashAI.back.metrics.base_metric import BaseMetric

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ClusteringMetric(BaseMetric):
    """Base class for all clustering evaluation metrics.

    Clustering metrics evaluate the quality of groups discovered by an
    unsupervised model. Unlike supervised metrics, they do not receive
    ground-truth targets. Concrete metrics operate on the input feature
    matrix and the labels assigned by the clustering model.

    This base class does not define a shared optimization direction because
    clustering validity indices differ: some metrics are maximized
    (Silhouette, Calinski-Harabasz), while others are minimized
    (Davies-Bouldin). Concrete metric classes must set ``MAXIMIZE`` according
    to their mathematical interpretation.
    """

    COMPATIBLE_COMPONENTS = ["ClusteringTask"]

    @classmethod
    def get_registry(cls) -> Dict[str, Type["ClusteringMetric"]]:
        """Return concrete clustering metric classes keyed by class name.

        Any subclass that defines its own ``score`` method is treated as a
        concrete metric and included automatically. New metrics are picked up
        as soon as their module is imported — no manual registration needed.
        """
        result: Dict[str, Type["ClusteringMetric"]] = {}

        def _collect(base: Type["ClusteringMetric"]) -> None:
            for sub in base.__subclasses__():
                if "score" in sub.__dict__:
                    result[sub.__name__] = sub
                _collect(sub)

        _collect(cls)
        return result


def validate_inputs(
    x_values: "pd.DataFrame",
    label_values: "np.ndarray",
) -> None:
    """Validate feature rows and cluster labels before scoring.

    Parameters
    ----------
    x_values : pandas.DataFrame
        Feature matrix used to fit or evaluate the clustering model.
    label_values : np.ndarray
        Cluster assignment for each row in ``x_values``.

    Raises
    ------
    ValueError
        If the number of samples and labels is different.
    """
    if len(x_values) != len(label_values):
        raise ValueError("Feature rows and cluster labels must have the same length.")


def prepare_to_metric(
    x: "DashAIDataset | pd.DataFrame",
    labels: "np.ndarray | list",
) -> tuple["pd.DataFrame | None", "np.ndarray | None"]:
    """Prepare feature data and labels for internal clustering metrics.

    Converts DashAI datasets or pandas data frames into the numeric feature
    matrix accepted by sklearn clustering metrics. Noise labels (``-1``), used
    by density-based algorithms such as DBSCAN, are excluded because internal
    validity indices are defined over clusters.

    Parameters
    ----------
    x : DashAIDataset or pandas.DataFrame
        Feature data selected.
    labels : np.ndarray or list
        Cluster labels produced by the model.

    Returns
    -------
    tuple[pandas.DataFrame | None, np.ndarray | None]
        Prepared feature matrix and labels. Returns ``(None, None)`` when the
        score is not mathematically defined, for example when fewer than two
        clusters remain after filtering noise.

    Raises
    ------
    ValueError
        If there are no numeric feature columns or the number of rows and labels
        does not match.
    """
    import numpy as np
    import pandas as pd

    x_values = x.to_pandas() if hasattr(x, "to_pandas") else x
    if isinstance(x_values, pd.DataFrame):
        x_values = x_values.select_dtypes(include=["number"])
        if x_values.shape[1] == 0:
            raise ValueError("Clustering metrics require at least one numeric column.")
    else:
        raise TypeError(
            "Clustering metrics expect a DashAIDataset or pandas DataFrame."
        )

    label_values = np.asarray(labels)
    validate_inputs(x_values, label_values)

    valid_mask = label_values != -1
    if hasattr(x_values, "iloc"):
        x_values = x_values.iloc[valid_mask]
    else:
        x_values = x_values[valid_mask]
    label_values = label_values[valid_mask]

    unique_labels = np.unique(label_values)
    if len(unique_labels) < 2 or len(unique_labels) >= len(label_values):
        return None, None

    return x_values, label_values
