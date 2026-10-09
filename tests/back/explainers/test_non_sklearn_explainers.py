"""Explainer tests against models that are not scikit-learn wrappers.

Explainers that perturb the feature matrix (SHAP, partial dependence,
permutation importance) hold data that ``prepare_dataset`` already produced, so
they query the model through ``predict_prepared`` / ``predict_proba_prepared``
instead of ``predict``, which would prepare it a second time. Before that hook
existed, only the scikit-learn wrappers survived those calls, because their
``predict`` forwarded anything that was not a ``DashAIDataset`` straight to the
estimator.

The two models below implement that contract with no scikit-learn estimator
involved: a least-squares regressor and a nearest-centroid classifier, both over
plain NumPy, sharing the categorical-encoding mixin with the torch MLP models.
``UnsupportedRegressor`` implements no hook at all and must fail with a clear
error instead of an ``AttributeError`` from deep inside the preparation code.
"""

import copy
import pickle

import numpy as np
import pyarrow as pa
import pytest

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    select_columns,
    split_dataset,
    split_indexes,
)
from DashAI.back.explainability.explainers.kernel_shap import KernelShap
from DashAI.back.explainability.explainers.partial_dependence import PartialDependence
from DashAI.back.explainability.explainers.permutation_feature_importance import (
    PermutationFeatureImportance,
)
from DashAI.back.explainability.explainers.regression_kernel_shap import (
    RegressionKernelShap,
)
from DashAI.back.explainability.explainers.regression_partial_dependence import (
    RegressionPartialDependence,
)
from DashAI.back.explainability.explainers.regression_permutation_feature_importance import (  # noqa: E501
    RegressionPermutationFeatureImportance,
)
from DashAI.back.models.categorical_encoder_mixin import CategoricalEncoderMixin
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.utils import save_types_in_arrow_metadata
from DashAI.back.types.value_types import Float

INPUT_COLUMNS = [
    "SepalLengthCm",
    "SepalWidthCm",
    "PetalLengthCm",
    "Species",
]
OUTPUT_COLUMNS = ["PetalWidthCm"]
SPECIES = [
    "Iris-setosa",
    "Iris-versicolor",
    "Iris-virginica",
]


class DummyLinearRegressor(CategoricalEncoderMixin, RegressionModel):
    """Least-squares regressor implemented with NumPy only.

    Stands in for the non scikit-learn model families (torch MLP, PyMC BART,
    plugins): ``predict`` receives a ``DashAIDataset`` and runs the model
    preparation itself, without a type check.
    """

    def __init__(self):
        """Initialise the encoder state and the (unfitted) coefficients."""
        self._setup_categorical_encoders()
        self.coefficients = None
        self.intercept = 0.0

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        """Fit the coefficients by ordinary least squares.

        Parameters
        ----------
        x_train : DashAIDataset
            Input features for training.
        y_train : DashAIDataset
            Target values for training.
        x_validation : DashAIDataset, optional
            Unused. Defaults to None.
        y_validation : DashAIDataset, optional
            Unused. Defaults to None.

        Returns
        -------
        DummyLinearRegressor
            The fitted model (``self``).
        """
        x = self.prepare_dataset(x_train, is_fit=True).to_pandas().values.astype(float)
        y = (
            self.prepare_output(y_train, is_fit=True)
            .to_pandas()
            .values.astype(float)
            .ravel()
        )

        design = np.column_stack([x, np.ones(len(x))])
        solution, *_ = np.linalg.lstsq(design, y, rcond=None)
        self.coefficients = solution[:-1]
        self.intercept = float(solution[-1])
        return self

    def predict(self, x: "DashAIDataset") -> np.ndarray:
        """Predict target values for the input dataset.

        Parameters
        ----------
        x : DashAIDataset
            Input features, before the model preparation.

        Returns
        -------
        np.ndarray
            Predicted values as a 1-D array.
        """
        return self.predict_prepared(self.prepare_dataset(x, is_fit=False).to_pandas())

    def predict_prepared(self, features) -> np.ndarray:
        """Predict from a feature matrix already in the model feature space.

        Parameters
        ----------
        features : pandas.DataFrame or numpy.ndarray
            Feature matrix as produced by ``prepare_dataset``.

        Returns
        -------
        np.ndarray
            Predicted values as a 1-D array.
        """
        matrix = np.asarray(getattr(features, "values", features), dtype=float)
        return matrix @ self.coefficients + self.intercept

    def save(self, filename: str) -> None:
        """Persist the fitted state to disk.

        Parameters
        ----------
        filename : str
            Destination path.
        """
        with open(filename, "wb") as file:
            pickle.dump(
                {
                    "coefficients": self.coefficients,
                    "intercept": self.intercept,
                    "encodings": self.encodings,
                    "one_hot_encoder": self.one_hot_encoder,
                    "categorical_columns": self.categorical_columns,
                },
                file,
            )

    def load(self, filename: str):
        """Restore the fitted state from disk.

        Parameters
        ----------
        filename : str
            Path written by :meth:`save`.

        Returns
        -------
        DummyLinearRegressor
            The restored model (``self``).
        """
        with open(filename, "rb") as file:
            state = pickle.load(file)
        self.coefficients = state["coefficients"]
        self.intercept = state["intercept"]
        self.encodings = state["encodings"]
        self.one_hot_encoder = state["one_hot_encoder"]
        self.categorical_columns = state["categorical_columns"]
        return self


class DummyCentroidClassifier(CategoricalEncoderMixin, TabularClassificationModel):
    """Nearest-centroid classifier implemented with NumPy only.

    Stands in for a non scikit-learn tabular classifier: ``predict`` returns
    the class-probability matrix, as every DashAI classifier does.
    """

    def __init__(self):
        """Initialise the encoder state and the (unfitted) centroids."""
        self._setup_categorical_encoders()
        self.centroids = None
        self.classes_ = None

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        """Fit one centroid per class.

        Parameters
        ----------
        x_train : DashAIDataset
            Input features for training.
        y_train : DashAIDataset
            Target labels for training.
        x_validation : DashAIDataset, optional
            Unused. Defaults to None.
        y_validation : DashAIDataset, optional
            Unused. Defaults to None.

        Returns
        -------
        DummyCentroidClassifier
            The fitted model (``self``).
        """
        x = self.prepare_dataset(x_train, is_fit=True).to_pandas().values.astype(float)
        y = (
            self.prepare_output(y_train, is_fit=True)
            .to_pandas()
            .values.ravel()
            .astype(int)
        )

        self.classes_ = np.unique(y)
        self.centroids = np.vstack(
            [x[y == label].mean(axis=0) for label in self.classes_]
        )
        return self

    def predict(self, x_pred: "DashAIDataset") -> np.ndarray:
        """Return the class-probability matrix for the input dataset.

        Parameters
        ----------
        x_pred : DashAIDataset
            Input features, before the model preparation.

        Returns
        -------
        np.ndarray
            Array of shape ``(n_samples, n_classes)``.
        """
        return self.predict_prepared(
            self.prepare_dataset(x_pred, is_fit=False).to_pandas()
        )

    def predict_prepared(self, features) -> np.ndarray:
        """Return probabilities for an already prepared feature matrix.

        Parameters
        ----------
        features : pandas.DataFrame or numpy.ndarray
            Feature matrix as produced by ``prepare_dataset``.

        Returns
        -------
        np.ndarray
            Array of shape ``(n_samples, n_classes)``.
        """
        return self.predict_proba_prepared(features)

    def predict_proba_prepared(self, features) -> np.ndarray:
        """Softmax over the negative distance to each class centroid.

        Parameters
        ----------
        features : pandas.DataFrame or numpy.ndarray
            Feature matrix as produced by ``prepare_dataset``.

        Returns
        -------
        np.ndarray
            Array of shape ``(n_samples, n_classes)``.
        """
        matrix = np.asarray(getattr(features, "values", features), dtype=float)
        distances = np.linalg.norm(
            matrix[:, None, :] - self.centroids[None, :, :], axis=2
        )
        scores = -distances
        scores = scores - scores.max(axis=1, keepdims=True)
        exponentials = np.exp(scores)
        return exponentials / exponentials.sum(axis=1, keepdims=True)

    def save(self, filename: str) -> None:
        """Persist the fitted state to disk.

        Parameters
        ----------
        filename : str
            Destination path.
        """
        with open(filename, "wb") as file:
            pickle.dump({"centroids": self.centroids, "classes": self.classes_}, file)

    def load(self, filename: str):
        """Restore the fitted state from disk.

        Parameters
        ----------
        filename : str
            Path written by :meth:`save`.

        Returns
        -------
        DummyCentroidClassifier
            The restored model (``self``).
        """
        with open(filename, "rb") as file:
            state = pickle.load(file)
        self.centroids = state["centroids"]
        self.classes_ = state["classes"]
        return self


class UnsupportedRegressor(RegressionModel):
    """Model that does not implement the prepared-feature-matrix contract."""

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        """Pretend to train.

        Parameters
        ----------
        x_train : DashAIDataset
            Unused.
        y_train : DashAIDataset
            Unused.
        x_validation : DashAIDataset, optional
            Unused. Defaults to None.
        y_validation : DashAIDataset, optional
            Unused. Defaults to None.

        Returns
        -------
        UnsupportedRegressor
            ``self``.
        """
        return self

    def predict(self, x):
        """Predict a constant value per row.

        Parameters
        ----------
        x : DashAIDataset
            Input features.

        Returns
        -------
        np.ndarray
            Array of zeros.
        """
        return np.zeros(x.num_rows)

    def save(self, filename: str) -> None:
        """Do nothing.

        Parameters
        ----------
        filename : str
            Unused.
        """

    def load(self, filename: str):
        """Do nothing.

        Parameters
        ----------
        filename : str
            Unused.

        Returns
        -------
        UnsupportedRegressor
            ``self``.
        """
        return self


def _load_iris_dataset():
    """Load iris with DashAI types and return it as a single DashAIDataset."""
    dataloader = CSVDataLoader()
    datasetdict = dataloader.load_data(
        filepath_or_buffer="tests/back/explainers/iris.csv",
        temp_path="tests/back/explainers",
        params={
            "separator": ",",
            "schema": {
                "SepalLengthCm": {"type": "Float", "dtype": "float64"},
                "SepalWidthCm": {"type": "Float", "dtype": "float64"},
                "PetalLengthCm": {"type": "Float", "dtype": "float64"},
                "PetalWidthCm": {"type": "Float", "dtype": "float64"},
                "Species": {"type": "Categorical", "dtype": "string"},
            },
        },
    )
    datasetdict.types = {
        "SepalLengthCm": Float(arrow_type=pa.float64()),
        "SepalWidthCm": Float(arrow_type=pa.float64()),
        "PetalLengthCm": Float(arrow_type=pa.float64()),
        "PetalWidthCm": Float(arrow_type=pa.float64()),
        "Species": Categorical(values=SPECIES),
    }

    new_table = save_types_in_arrow_metadata(
        datasetdict.arrow_table,
        {col: dtype.to_string() for col, dtype in datasetdict.types.items()},
    )
    datasetdict = DashAIDataset(
        new_table, splits=datasetdict.splits, types=datasetdict.types
    )

    train_indexes, test_indexes, val_indexes = split_indexes(
        total_rows=datasetdict.num_rows, train_size=0.7, test_size=0.1, val_size=0.2
    )
    split_dataset_dict = split_dataset(
        datasetdict,
        train_indexes=train_indexes,
        test_indexes=test_indexes,
        val_indexes=val_indexes,
    )

    return split_dataset_dict


def _split_columns(split_dataset_dict, input_columns, output_columns):
    """Select the input/output columns and re-split both sides."""
    x, y = select_columns(split_dataset_dict, input_columns, output_columns)
    return split_dataset(x), split_dataset(y)


@pytest.fixture(scope="module", name="dataset")
def regression_dataset_fixture():
    """Iris as a regression dataset, with one categorical input feature."""
    return _split_columns(_load_iris_dataset(), INPUT_COLUMNS, OUTPUT_COLUMNS)


@pytest.fixture(scope="module", name="classification_dataset")
def classification_dataset_fixture():
    """Iris as a classification dataset: numeric features, Species target."""
    return _split_columns(
        _load_iris_dataset(),
        ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"],
        ["Species"],
    )


@pytest.fixture(scope="module", name="trained_model")
def trained_model_fixture(dataset):
    """Train the dummy non scikit-learn regressor."""
    x, y = dataset
    model = DummyLinearRegressor()
    model.train(x["train"], y["train"])
    return model


@pytest.fixture(scope="module", name="trained_classifier")
def trained_classifier_fixture(classification_dataset):
    """Train the dummy non scikit-learn classifier."""
    x, y = classification_dataset
    model = DummyCentroidClassifier()
    model.train(x["train"], y["train"])
    return model


def test_dummy_model_predicts_from_dashai_dataset(trained_model, dataset):
    """The model itself works through the regular DashAIDataset path."""
    x, y = dataset
    predictions = np.asarray(trained_model.predict(x["test"])).ravel()

    assert predictions.shape == (x["test"].num_rows,)
    assert np.isfinite(predictions).all()

    targets = y["test"].to_pandas().to_numpy().ravel()
    # Petal width is well explained by the other iris columns.
    assert np.corrcoef(predictions, targets)[0, 1] > 0.8


def test_regression_partial_dependence(trained_model, dataset):
    """Partial dependence perturbs the feature matrix and calls predict."""
    explainer = RegressionPartialDependence(
        trained_model, grid_resolution=5, lower_percentile=0.05, upper_percentile=0.95
    )
    explanation = explainer.explain(copy.deepcopy(dataset))

    assert explanation["metadata"]["output_column"] == OUTPUT_COLUMNS[0]

    curves = {key: value for key, value in explanation.items() if key != "metadata"}
    # The three numeric features, plus the one-hot columns of Species.
    assert set(curves) >= {"SepalLengthCm", "SepalWidthCm", "PetalLengthCm"}
    for curve in curves.values():
        assert len(curve["grid_values"]) == 5
        assert len(curve["average"]) == 5


def test_regression_permutation_feature_importance(trained_model, dataset):
    """Permutation importance calls predict with permuted frames."""
    explainer = RegressionPermutationFeatureImportance(
        trained_model,
        scoring="r2",
        n_repeats=2,
        random_state=0,
        max_samples_fraction=1.0,
    )
    explanation = explainer.explain(copy.deepcopy(dataset))

    assert len(explanation["features"]) == len(explanation["importances_mean"])
    assert len(explanation["features"]) == len(explanation["importances_std"])
    assert all(np.isfinite(explanation["importances_mean"]))
    # Petal length dominates petal width in iris.
    top_feature = explanation["features"][
        int(np.argmax(explanation["importances_mean"]))
    ]
    assert top_feature == "PetalLengthCm"


def test_regression_kernel_shap(trained_model, dataset):
    """SHAP queries the model with sampled coalitions of the feature matrix."""
    x, _ = dataset

    explainer = RegressionKernelShap(trained_model)
    explainer.fit(
        copy.deepcopy(dataset),
        sample_background_data=True,
        background_fraction=0.2,
    )

    instances = x["test"].select(range(2))
    explanation = explainer.explain_instance(instances)

    instance_keys = [
        key for key in explanation if key not in ("metadata", "base_value")
    ]
    assert len(instance_keys) == 2
    for key in instance_keys:
        instance = explanation[key]
        contributions = np.asarray(instance["shap_values"])
        assert np.isfinite(contributions).all()
        # SHAP is additive: base value plus contributions equals the prediction.
        assert np.isclose(
            explanation["base_value"] + contributions.sum(),
            instance["model_prediction"],
            atol=0.1,
        )


def test_classifier_predicts_probabilities(trained_classifier, classification_dataset):
    """The dummy classifier returns a probability matrix, as DashAI expects."""
    x, _ = classification_dataset
    probabilities = trained_classifier.predict(x["test"])

    assert probabilities.shape == (x["test"].num_rows, len(SPECIES))
    assert np.allclose(probabilities.sum(axis=1), 1.0)


def test_partial_dependence_classification(trained_classifier, classification_dataset):
    """sklearn's partial_dependence reaches the model through the adapter."""
    explainer = PartialDependence(
        trained_classifier,
        lower_percentile=0.05,
        upper_percentile=0.95,
        grid_resolution=5,
    )
    explanation = explainer.explain(copy.deepcopy(classification_dataset))

    assert set(explanation["metadata"]["target_names"]) == set(SPECIES)
    curves = {key: value for key, value in explanation.items() if key != "metadata"}
    assert set(curves) == {
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
    }
    for curve in curves.values():
        averages = np.asarray(curve["average"])
        assert len(curve["grid_values"]) > 0
        # One averaged curve per class, evaluated on the whole grid.
        assert averages.shape[-1] == len(curve["grid_values"])
        assert np.isfinite(averages).all()


def test_permutation_feature_importance_classification(
    trained_classifier, classification_dataset
):
    """sklearn's permutation_importance reaches the model through the adapter."""
    explainer = PermutationFeatureImportance(
        trained_classifier,
        scoring="accuracy",
        n_repeats=2,
        random_state=0,
        max_samples_fraction=1.0,
    )
    explanation = explainer.explain(copy.deepcopy(classification_dataset))

    assert len(explanation["features"]) == 4
    assert all(np.isfinite(explanation["importances_mean"]))
    top_feature = explanation["features"][
        int(np.argmax(explanation["importances_mean"]))
    ]
    assert top_feature in ("PetalLengthCm", "PetalWidthCm")


def test_kernel_shap_classification(trained_classifier, classification_dataset):
    """SHAP perturbs the feature matrix of a non scikit-learn classifier."""
    x, _ = classification_dataset

    explainer = KernelShap(trained_classifier)
    explainer.fit(
        copy.deepcopy(classification_dataset),
        sample_background_data=True,
        background_fraction=0.2,
        sampling_method="shuffle",
    )

    instances = x["test"].select(range(2))
    explanation = explainer.explain_instance(instances)

    instance_keys = [
        key for key in explanation if key not in ("metadata", "base_values")
    ]
    assert len(instance_keys) == 2
    for key in instance_keys:
        contributions = np.asarray(explanation[key]["shap_values"])
        assert contributions.shape[0] == len(SPECIES)
        assert np.isfinite(contributions).all()


def test_model_without_prepared_hook_reports_clearly(dataset):
    """A model that cannot take a feature matrix fails with a clear error."""
    model = UnsupportedRegressor()

    explainer = RegressionPartialDependence(model, grid_resolution=5)
    with pytest.raises(NotImplementedError, match="prepared feature matrix"):
        explainer.explain(copy.deepcopy(dataset))
