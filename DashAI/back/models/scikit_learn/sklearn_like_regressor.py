from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel


class SklearnLikeRegressor(SklearnLikeModel):
    """Abstract mixin for scikit-learn-style regression models.

    Inherits the prediction pipeline from ``SklearnLikeModel``: ``predict``
    prepares a ``DashAIDataset`` and forwards the resulting feature matrix to
    ``predict_prepared``, which calls the wrapped sklearn estimator's
    ``predict``.  Concrete regressor wrappers (e.g. ``LinearRegression``,
    ``RandomForestRegressor``) inherit from this class and from a
    ``BaseSchema`` subclass.
    """
