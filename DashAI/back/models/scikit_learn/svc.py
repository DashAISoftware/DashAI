from sklearn.svm import SVC as _SVC

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    float_field,
    optimizer_float_field,
    optimizer_int_field,
    int_field,
    schema_field,
)
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class SVCSchema(BaseSchema):
    """Support Vector Machine (SVM) is a machine learning algorithm that separates data
    into different classes by finding the optimal hyperplane
    """

    C: schema_field(
        optimizer_float_field(gt=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1.0,
            "lower_bound": 1.0,
            "upper_bound": 10.0},
        description="The parameter 'C' is a regularization parameter. It must be of "
        "type positive number.",
    )  # type: ignore
    coef0: schema_field(
        optimizer_float_field(),
        placeholder={
            "optimize": False,
            "fixed_value": 1.0,
            "lower_bound": 1.0,
            "upper_bound": 10.0},
        description="The 'coef0' parameter is a kernel independent value. It is only "
        "significant for kernel poly and sigmoid. It must be of type number.",
    )  # type: ignore
    degree: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1.0,
            "lower_bound": 1.0,
            "upper_bound": 10.0},
        description="The parameter 'degree' is the degree of the polynomial for the "
        "kernel = 'poly'. It must be of type number.",
    )  # type: ignore
    gamma: schema_field(
        enum_field(enum=["scale", "auto"]),
        placeholder="scale",
        description="Coefficient for 'rbf', 'poly' and 'sigmoid' kernels. Must be in "
        "string format and can be 'scale' or 'auto'.",
    )  # type: ignore
    kernel: schema_field(
        enum_field(enum=["linear", "poly", "rbf", "sigmoid"]),
        placeholder="rbf",
        description="The 'kernel' parameter is the kernel used in the model. It must "
        "be a string equal to 'linear', 'poly', 'rbf' or 'sigmoid'.",
    )  # type: ignore
    max_iter: schema_field(
        optimizer_int_field(ge=-1),
        placeholder={
            "optimize": False,
            "fixed_value": -1,
            "lower_bound": 1,
            "upper_bound": 10},
        description="The 'max_iter' parameter determines the iteration limit for the "
        "solver. It must be of type positive integer or -1 to indicate no limit.",
    )  # type: ignore
    probability: schema_field(
        bool_field(),
        placeholder=True,
        description="The parameter 'probability' indicates whether or not to predict "
        "with probabilities. It must be of type boolean.",
    )  # type: ignore
    shrinking: schema_field(
        bool_field(),
        placeholder=True,
        description="The 'shrinking' parameter determines whether a shrinking "
        "heristic is used. It must be of type boolean.",
    )  # type: ignore
    tol: schema_field(
        optimizer_float_field(gt=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1.0,
            "lower_bound": 1.0,
            "upper_bound": 10.0},
        description="The parameter 'tol' determines the tolerance for the stop "
        "criterion. It must be of type positive number.",
    )  # type: ignore
    verbose: schema_field(
        bool_field(),
        placeholder=False,
        description="The 'verbose' parameter allows to have a verbose output."
        "It must be of type boolean.",
    )  # type: ignore


class SVC(TabularClassificationModel, SklearnLikeModel, _SVC):
    """Scikit-learn's Support Vector Machine (SVM) classifier wrapper for DashAI."""

    SCHEMA = SVCSchema

    def __init__(self, **kwargs):
        kwargs = self.validate_and_transform(kwargs)
        kwargs["probability"] = True
        super().__init__(**kwargs)
