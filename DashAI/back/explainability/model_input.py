"""Helper to move an explainer's data into the model's feature space.

Explainers receive the model input as the task prepared it, exactly as
``predict`` receives it in the prediction job: raw columns, before any model
specific preprocessing. That is what explainers that perturb the input and
query ``model.predict`` need, since ``predict`` applies the model preparation
itself.

Explainers that instead build feature matrices (``to_pandas``) and hand them
to a third party library (SHAP, DiCE, scikit-learn inspection) must work in
the model's own feature space, because those libraries call the model with
plain frames that bypass the model preparation. Such explainers call
:func:`prepare_model_input` on both the background data and the instances so
that both live in the same space, and must query the model through
``model.predict_prepared`` / ``model.predict_proba_prepared`` (or wrap it with
:func:`as_sklearn_estimator`) instead of ``model.predict``, which would prepare
the already prepared matrix a second time.
"""

from typing import TYPE_CHECKING, Any, Callable, List, Optional

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


def as_shap_predictor(model: Any) -> Callable:
    """Wrap the model's prepared-matrix prediction so SHAP gets a plain function.

    SHAP suppresses scikit-learn's "X does not have valid feature names"
    warning by blanking ``feature_names_in_`` on whatever object the callable
    is bound to (``shap.utils._legacy.convert_to_model``). It reaches that
    object through ``__self__``, so it only does this when handed a *bound
    method*, and it assumes the attribute is writable.

    That assumption does not hold for estimators that expose
    ``feature_names_in_`` as a read-only ``property`` — a common shape among
    third party wrappers — where the assignment raises ``AttributeError:
    property 'feature_names_in_' ... has no setter`` and the explanation fails
    before it starts.

    Handing over a plain closure instead leaves ``__self__`` absent, so SHAP
    skips that step entirely — a function is SHAP's primary documented
    interface for ``model``. The only thing lost is the suppression of a
    cosmetic scikit-learn warning.

    It routes to ``predict_prepared``, not to ``predict``. Callers hand SHAP a
    background already moved into the model's feature space with
    ``prepare_model_input``, and SHAP then queries the model with perturbed
    copies of *that* matrix. Going through ``predict`` would run the model's
    input preparation a second time over an already prepared matrix — and SHAP
    passes plain arrays, which the preparation cannot consume at all.

    Parameters
    ----------
    model : Any
        The trained model being explained.

    Returns
    -------
    Callable
        A one-argument function calling ``model.predict_prepared``
        positionally, the same way SHAP calls it.
    """

    def predict(x):
        return model.predict_prepared(x)

    return predict


def prepare_model_input(model: Any, dataset: "DashAIDataset") -> "DashAIDataset":
    """Apply the model's own input preprocessing to a dataset.

    Parameters
    ----------
    model : Any
        The DashAI model being explained.
    dataset : DashAIDataset
        Input features as the task prepared them.

    Returns
    -------
    DashAIDataset
        The dataset in the model's feature space, or the dataset unchanged
        when the model does not define ``prepare_dataset``.
    """
    prepare = getattr(model, "prepare_dataset", None)
    if prepare is None:
        return dataset
    return prepare(dataset, is_fit=False)


def as_sklearn_estimator(model: Any, classes: Optional[List[Any]] = None) -> Any:
    """Wrap a model so scikit-learn inspection tools can query it.

    ``sklearn.inspection`` utilities (``partial_dependence``,
    ``permutation_importance``) call ``estimator.predict`` /
    ``estimator.predict_proba`` with plain feature matrices. Passing a DashAI
    model directly only works when the model happens to be a scikit-learn
    estimator; this adapter routes those calls to the prepared-matrix hooks
    instead, so any model family works.

    Parameters
    ----------
    model : Any
        The DashAI classification model being explained.
    classes : list, optional
        Class labels of the model, exposed as ``classes_``. Defaults to the
        model's own ``classes_`` when available.

    Returns
    -------
    Any
        A fitted-looking scikit-learn classifier delegating to ``model``.
    """
    import numpy as np
    from sklearn.base import BaseEstimator, ClassifierMixin

    class _PreparedClassifier(ClassifierMixin, BaseEstimator):
        """Scikit-learn facade over a DashAI model's prepared-matrix hooks."""

        def __init__(self, wrapped, classes_):
            self._wrapped = wrapped
            self.classes_ = classes_

        def __sklearn_is_fitted__(self) -> bool:
            """Report the estimator as fitted; the wrapped model is trained."""
            return True

        def fit(self, x, y=None):
            """No-op; the wrapped model is already trained."""
            return self

        def predict(self, x):
            """Delegate to the wrapped model's ``predict_prepared``."""
            return model.predict_prepared(x)

        def predict_proba(self, x):
            """Delegate to the wrapped model's ``predict_proba_prepared``."""
            return model.predict_proba_prepared(x)

    known_classes = classes if classes is not None else getattr(model, "classes_", None)
    if known_classes is None:
        known_classes = []
    return _PreparedClassifier(model, np.asarray(known_classes))
