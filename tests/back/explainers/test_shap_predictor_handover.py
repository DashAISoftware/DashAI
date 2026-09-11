"""SHAP must not be handed a bound method of the model.

``shap.utils._legacy.convert_to_model`` suppresses scikit-learn's "X does not
have valid feature names" warning by blanking ``feature_names_in_`` on the
object the callable is bound to, reached through ``__self__``. It assumes that
attribute is writable, which does not hold for every estimator: those that
expose ``feature_names_in_`` as a read-only ``property`` raise instead, and the
explanation dies before it starts.

``as_shap_predictor`` hands over a plain closure, which has no ``__self__``, so
SHAP skips that step entirely. These tests pin the mechanism.
"""

import pytest

from DashAI.back.explainability.model_input import as_shap_predictor


def test_the_wrapped_predictor_forwards_to_predict_prepared_positionally():
    """SHAP calls the model with one positional argument; that must not change."""
    seen = {}

    class Model:
        def predict_prepared(self, x):
            seen["arg"] = x
            return [0]

    predictor = as_shap_predictor(Model())
    assert predictor("the frame") == [0]
    assert seen["arg"] == "the frame"


def test_the_wrapped_predictor_never_routes_through_predict():
    """The callers hand SHAP a background already in the model's feature space.

    Routing to ``predict`` would prepare an already prepared matrix a second
    time, and SHAP perturbs it into plain arrays that the preparation cannot
    consume at all — which surfaces far away, as
    ``'numpy.ndarray' object has no attribute 'types'``.
    """

    class Model:
        def predict(self, x):
            raise AssertionError("predict would prepare an already prepared matrix")

        def predict_prepared(self, x):
            return [1]

    assert as_shap_predictor(Model())("the frame") == [1]


def test_the_wrapped_predictor_hides_the_model_from_shap():
    """The whole mechanism: no ``__self__`` means SHAP never reaches the model."""

    class Model:
        def predict_prepared(self, x):
            return [0]

    model = Model()
    assert getattr(model.predict_prepared, "__self__", None) is model
    assert getattr(as_shap_predictor(model), "__self__", None) is None


def test_the_wrapped_predictor_survives_shaps_model_conversion():
    """``convert_to_model`` must accept the closure without touching a model."""
    from shap.utils._legacy import convert_to_model

    class ReadOnlyFeatureNames:
        """Stands in for an estimator whose ``feature_names_in_`` has no setter."""

        @property
        def feature_names_in_(self):
            return ["a", "b"]

        def predict_prepared(self, x):
            return [0]

    model = ReadOnlyFeatureNames()

    # The failure this exists to prevent: SHAP reaches the model through
    # ``__self__`` and tries to blank the attribute.
    with pytest.raises(AttributeError, match="feature_names_in_"):
        convert_to_model(model.predict_prepared)

    converted = convert_to_model(as_shap_predictor(model))

    assert converted.f is not None
    assert list(model.feature_names_in_) == ["a", "b"]
