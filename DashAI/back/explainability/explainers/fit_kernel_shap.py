from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.explainability.local_explainer import BaseLocalExplainer


class FitKernelShapSchema(BaseSchema):
    """Kernel SHAP is a model-agnostic explainability method for approximating SHAP
    values to explain the output of machine learning model by attributing contributions
    of each feature to the model's prediction.
    """

    sample_background_data: schema_field(
        bool_field(),
        placeholder=False,
        description="'true' if the background data must be sampled, otherwise "
        "the entire train data set is used. Smaller datasets speed up the "
        "algorithm run time.",
    )  # type: ignore

    n_background_samples: schema_field(
        int_field(ge=1),
        placeholder=1,
        description="If the parameter 'sample_background_data' is 'true', the "
        "number of background data samples to be drawn.",
    )  # type: ignore

    sampling_method: schema_field(
        enum_field(enum=["shuffle", "kmeans"]),
        placeholder="shuffle",
        description="If the parameter 'sample_background_data' is 'true', whether "
        "to sample random samples with 'shuffle' option or summarize the data set "
        "with 'kmeans' option. If 'categorical_features' is 'true', 'shuffle' "
        "options used by default.",
    )  # type: ignore


class FitKernelShap(BaseLocalExplainer):
    SCHEMA = FitKernelShapSchema
