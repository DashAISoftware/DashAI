from typing import TYPE_CHECKING

from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel

if TYPE_CHECKING:
    from numpy import ndarray

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class SklearnLikeClassifier(SklearnLikeModel):
    """Abstract mixin for scikit-learn style classification models.

    Extends ``SklearnLikeModel`` with a ``predict`` method that converts a
    ``DashAIDataset`` into a NumPy array, calls the wrapped sklearn estimator's
    ``predict_proba``, and returns the class probability matrix.  Concrete
    classifier wrappers (e.g. ``SVC``, ``RandomForestClassifier``) inherit
    from this class and from a ``BaseSchema`` subclass.

    Declares the model specific explainers that need sklearn classifier
    semantics (``predict_proba``); subclasses inherit them through the
    registry's MRO merge of ``COMPATIBLE_COMPONENTS``.
    """

    COMPATIBLE_COMPONENTS = ["DiceCounterfactual"]

    def predict(self, x_pred: "DashAIDataset") -> "ndarray":
        """Make a prediction with the model

        Parameters
        ----------
        x_pred : DashAIDataset
            Dataset with the input data columns.

        Returns
        -------
        np.ndarray
            Array with the predicted target values for x_pred
        """
        return self.predict_prepared(
            self.prepare_dataset(x_pred, is_fit=False).to_pandas()
        )

    def predict_prepared(self, features) -> "ndarray":
        """Predict from a feature matrix already in the model's feature space.

        DashAI classifiers return probabilities from ``predict``, so this
        delegates to ``predict_proba_prepared``.

        Parameters
        ----------
        features : pandas.DataFrame or numpy.ndarray
            Feature matrix as produced by ``prepare_dataset``.

        Returns
        -------
        np.ndarray
            Class probability matrix.
        """
        return self.predict_proba_prepared(features)

    def predict_proba_prepared(self, features) -> "ndarray":
        """Return class probabilities for an already prepared feature matrix.

        Parameters
        ----------
        features : pandas.DataFrame or numpy.ndarray
            Feature matrix as produced by ``prepare_dataset``.

        Returns
        -------
        np.ndarray
            Class probability matrix.
        """
        return super().predict_proba(features)
