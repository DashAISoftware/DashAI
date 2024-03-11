from sklearn.dummy import DummyClassifier as _DummyClassifier

from DashAI.back.core.schema_fields import BaseSchema, schema_field, string_field
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class DummyClassifierSchema(BaseSchema):
    "DummyClassifier makes predictions that ignore the input features."
    strategy: schema_field(
        string_field(enum=["most_frequent", "prior", "stratified", "uniform"]),
        placeholder="prior",
        description="Strategy to use to generate predictions.",
    )  # type: ignore


class DummyClassifier(TabularClassificationModel, SklearnLikeModel, _DummyClassifier):
    """Scikit-learn's DummyClassifier wrapper for DashAI."""

    SCHEMA = DummyClassifierSchema
