from sklearn.svm import SVC as _SVC

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    float_field,
    int_field,
    string_field,
)
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class SVCSchema(BaseSchema):
    """Support Vector Machine (SVM) is a machine learning algorithm that separates data
    into different classes by finding the optimal hyperplane
    """

    C: float_field(
        description="The parameter 'C' is a regularization parameter. It must be of "
        "type positive number.",
        default=1,
        gt=0,
    )
    coef0: float_field(
        description="The 'coef0' parameter is a kernel independent value. It is only "
        "significant for kernel poly and sigmoid. It must be of type number.",
        default=0,
    )
    degree: float_field(
        description="The parameter 'degree' is the degree of the polynomial for the "
        "kernel = 'poly'. It must be of type number.",
        default=3,
        ge=0,
    )
    gamma: string_field(
        description="Coefficient for 'rbf', 'poly' and 'sigmoid' kernels. Must be in "
        "string format and can be 'scale' or 'auto'.",
        default="scale",
        enum=["scale", "auto"],
    )
    kernel: string_field(
        description="The 'kernel' parameter is the kernel used in the model. It must "
        "be a string equal to 'linear', 'poly', 'rbf' or 'sigmoid'.",
        default="rbf",
        enum=["linear", "poly", "rbf", "sigmoid"],
    )
    max_iter: int_field(
        description="The 'max_iter' parameter determines the iteration limit for the "
        "solver. It must be of type positive integer or -1 to indicate no limit.",
        default=-1,
        ge=-1,
    )
    probability: bool_field(
        description="The parameter 'probability' indicates whether or not to predict "
        "with probabilities. It must be of type boolean.",
        default=True,
    )
    shrinking: bool_field(
        description="The 'shrinking' parameter determines whether a shrinking "
        "heristic is used. It must be of type boolean.",
        default=True,
    )
    tol: float_field(
        description="The parameter 'tol' determines the tolerance for the stop "
        "criterion. It must be of type positive number.",
        default=0.001,
        gt=0,
    )
    verbose: bool_field(
        description="The 'verbose' parameter allows to have a verbose output."
        "It must be of type boolean.",
        default=False,
    )


class SVC(TabularClassificationModel, SklearnLikeModel, _SVC):
    """Scikit-learn's Support Vector Machine (SVM) classifier wrapper for DashAI."""

    SCHEMA = SVCSchema

    def __init__(self, **kwargs):
        kwargs["probability"] = True
        super().__init__(**kwargs)
