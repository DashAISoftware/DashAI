from typing import TYPE_CHECKING

from DashAI.back.models.categorical_encoder_mixin import CategoricalEncoderMixin
from DashAI.back.models.supervised_model import SupervisedModel

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class SklearnLikeModel(CategoricalEncoderMixin, SupervisedModel):
    """Abstract base class for scikit-learn-compatible DashAI models.

    Provides ``save`` / ``load`` via joblib and inherits the categorical
    encoding helpers and ``prepare_dataset`` / ``prepare_output`` pipeline from
    ``CategoricalEncoderMixin``. Concrete subclasses (classifiers and
    regressors) supply ``train`` and ``predict`` implementations backed by
    scikit-learn estimators.

    Inherits directly from ``SupervisedModel`` rather than ``BaseModel``.
    Its ``train`` signature requires labeled data (``y_train``), which is
    the defining property of supervised learning, so every model built on
    this class is supervised by construction.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the SklearnLikeModel."""
        super().__init__(*args, **kwargs)
        self._setup_categorical_encoders()

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
    def load(filename: str) -> None:
        """Deserialise a model from disk using joblib.

        Parameters
        ----------
        filename : str
            Path to the file previously written by :meth:`save`.

        Returns
        -------
        SklearnLikeModel
            The loaded model instance.
        """
        import joblib

        model = joblib.load(filename)
        return model

    # --- Methods for process the data for sklearn models ---

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        """Train the sklearn model on the provided dataset.

        Applies ``prepare_dataset`` and ``prepare_output`` to encode categorical
        features and targets before delegating to the scikit-learn ``fit`` method.

        Parameters
        ----------
        x_train : DashAIDataset
            The input features for training.
        y_train : DashAIDataset
            The target labels for training.
        x_validation : DashAIDataset, optional
            Validation input features (unused in sklearn models). Defaults to None.
        y_validation : DashAIDataset, optional
            Validation target labels (unused in sklearn models). Defaults to None.

        Returns
        -------
        BaseModel
            The fitted scikit-learn estimator (self).
        """
        x_processed = self.prepare_dataset(x_train, is_fit=True).to_pandas()
        y_processed = self.prepare_output(y_train, is_fit=True).to_pandas()
        # Every task using this base class has outputs_cardinality 1, so this
        # is always a single column. Passed as a DataFrame, some estimators
        # (e.g. LinearRegression) keep predictions 2D to match; squeezing to a
        # Series here keeps fit/predict shapes 1D for every estimator alike.
        if y_processed.shape[1] == 1:
            y_processed = y_processed.iloc[:, 0]
        return super().fit(x_processed, y_processed)

    def predict(self, x: "DashAIDataset"):
        """Predict using the trained model.

        Parameters
        ----------
        x : DashAIDataset
            Dataset with the input data.

        Returns
        -------
        np.ndarray
            Predicted values.
        """
        return self.predict_prepared(self.prepare_dataset(x, is_fit=False).to_pandas())

    def predict_prepared(self, features):
        """Predict from a feature matrix already in the model's feature space.

        Parameters
        ----------
        features : pandas.DataFrame or numpy.ndarray
            Feature matrix as produced by ``prepare_dataset``.

        Returns
        -------
        np.ndarray
            Predicted values.
        """
        return super().predict(features)
