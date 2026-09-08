"""Per family implementations of the model artifact hook.

Each mixin here supplies ``get_model_artifacts`` for one family of estimators
and is mixed into the concrete DashAI models as their first base class, so its
implementation wins method resolution over the empty default on ``BaseModel``.

Every mixin guards on the attribute a fitted estimator would expose and returns
an empty list when it is absent, so calling the hook on an unfitted model is a
no-op rather than an error.
"""

from typing import TYPE_CHECKING, Any, List, Union

from DashAI.back.core.artifacts import (
    Artifact,
    ArtifactGroup,
    GroupedArtifacts,
    TextArtifact,
)
from DashAI.back.models.model_artifact_plots import (
    plot_feature_importances,
    plot_sklearn_tree,
    plot_weight_heatmap,
)

if TYPE_CHECKING:
    from DashAI.back.models.model_artifact_context import ModelArtifactContext

#: Upper bound on how many trees of an ensemble are rendered. A forest can hold
#: hundreds of trees; past this many the payload stops being useful and starts
#: being a burden on the browser. Truncation is always stated in the output.
MAX_PLOTTED_TREES = 20

ArtifactList = List[Union[Artifact, GroupedArtifacts]]


def _importances_artifact(
    model: Any, context: "ModelArtifactContext"
) -> List[Artifact]:
    """Build the feature importance bar for an estimator that exposes them.

    Parameters
    ----------
    model : Any
        A fitted estimator, possibly without importances.
    context : ModelArtifactContext
        Training data and naming.

    Returns
    -------
    List[Artifact]
        A single element list, or empty when the estimator has no importances.
    """
    importances = getattr(model, "feature_importances_", None)
    if importances is None:
        return []
    return [
        plot_feature_importances(
            context.feature_names, importances, title="Feature importances"
        )
    ]


def _truncation_notice(total: int, shown: int) -> List[Artifact]:
    """State that only part of an ensemble is rendered.

    Parameters
    ----------
    total : int
        How many trees the ensemble holds.
    shown : int
        How many of them are rendered.

    Returns
    -------
    List[Artifact]
        A single text artifact, or empty when nothing was dropped.
    """
    if total <= shown:
        return []
    return [
        TextArtifact(
            payload=(
                f"Showing the first {shown} of {total} trees. "
                "The remaining trees are not rendered."
            ),
            title="Truncated",
        )
    ]


class TreeArtifactsMixin:
    """Render a single fitted decision tree and its feature importances."""

    def get_model_artifacts(self, context: "ModelArtifactContext") -> ArtifactList:
        """Build the tree diagram and importance bar of a fitted tree.

        Parameters
        ----------
        context : ModelArtifactContext
            Training data and naming.

        Returns
        -------
        ArtifactList
            The tree diagram followed by the feature importances, or an empty
            list when the model has not been fitted.
        """
        tree = getattr(self, "tree_", None)
        if tree is None:
            return []
        return [
            plot_sklearn_tree(
                tree,
                context.feature_names,
                context.class_names if hasattr(self, "classes_") else None,
                title="Tree structure",
            ),
            *_importances_artifact(self, context),
        ]


class TreeEnsembleArtifactsMixin:
    """Render the trees of a fitted ensemble as a selector."""

    def get_model_artifacts(self, context: "ModelArtifactContext") -> ArtifactList:
        """Build the importance bar and a per tree selector.

        Gradient boosting nests its estimators in a two dimensional array, so
        the collection is flattened before the trees are read.

        Parameters
        ----------
        context : ModelArtifactContext
            Training data and naming.

        Returns
        -------
        ArtifactList
            The importances, a grouped artifact holding one entry per rendered
            tree, and a truncation notice when the ensemble is larger than the
            render cap. Empty when the model has not been fitted.
        """
        import numpy as np

        estimators = getattr(self, "estimators_", None)
        if estimators is None or len(estimators) == 0:
            return []

        flattened = [
            estimator
            for estimator in np.asarray(estimators, dtype=object).ravel().tolist()
            if getattr(estimator, "tree_", None) is not None
        ]
        if not flattened:
            return []

        shown = flattened[:MAX_PLOTTED_TREES]
        groups = [
            ArtifactGroup(
                title=f"Tree {index + 1}",
                artifacts=[
                    plot_sklearn_tree(
                        estimator.tree_,
                        context.feature_names,
                        (
                            context.class_names
                            if hasattr(estimator, "classes_")
                            else None
                        ),
                        title=f"Tree {index + 1}",
                    )
                ],
            )
            for index, estimator in enumerate(shown)
        ]

        return [
            *_importances_artifact(self, context),
            GroupedArtifacts(title="Trees", groups=groups),
            *_truncation_notice(len(flattened), len(shown)),
        ]


class MLPArtifactsMixin:
    """Render the learned weight matrices of a fitted perceptron."""

    def _weight_matrices(self) -> List[Any]:
        """Collect the per layer weight matrices of the fitted network.

        Supports both backends DashAI ships: scikit-learn's ``MLPClassifier``,
        which exposes ``coefs_``, and the PyTorch regressor, whose linear
        layers live in a ``nn.Sequential``.

        Returns
        -------
        List[Any]
            One ``(inputs, outputs)`` shaped array per layer, empty when the
            network has not been fitted.
        """
        coefficients = getattr(self, "coefs_", None)
        if coefficients is not None:
            return list(coefficients)

        module = getattr(self, "model", None)
        inner = getattr(module, "model", None)
        if inner is None:
            return []
        return [
            layer.weight.detach().cpu().numpy().T
            for layer in inner
            if hasattr(layer, "weight") and layer.weight.dim() == 2
        ]

    def get_model_artifacts(self, context: "ModelArtifactContext") -> ArtifactList:
        """Build a per layer weight heatmap selector.

        The training loss curve is deliberately absent: it is a scalar per
        epoch, which the metrics system already models as a ``STEP`` level
        metric, so it belongs on the live metrics chart rather than here.

        Parameters
        ----------
        context : ModelArtifactContext
            Feature and class naming for the fitted model.

        Returns
        -------
        ArtifactList
            A grouped artifact with one heatmap per layer, empty when the
            network has not been fitted.
        """
        matrices = self._weight_matrices()
        if not matrices:
            return []

        groups = [
            ArtifactGroup(
                title=f"Layer {index + 1}",
                artifacts=[
                    plot_weight_heatmap(
                        matrix,
                        title=f"Layer {index + 1} weights",
                        x_title="Output unit",
                        y_title="Input unit" if index else "Input feature",
                        row_labels=context.feature_names if index == 0 else None,
                    )
                ],
            )
            for index, matrix in enumerate(matrices)
        ]
        return [GroupedArtifacts(title="Weights", groups=groups)]


__all__ = [
    "MAX_PLOTTED_TREES",
    "MLPArtifactsMixin",
    "TreeArtifactsMixin",
    "TreeEnsembleArtifactsMixin",
]
