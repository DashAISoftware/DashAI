from typing import Tuple

from sklearn.inspection import partial_dependence

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.explainability.global_explainer import BaseGlobalExplainer
from DashAI.back.models import BaseModel


# Centered case
class PartialDependence(BaseGlobalExplainer):
    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]

    def __init__(
        self,
        percentiles: Tuple[float] = (0.05, 0.95),
        grid_resolution: int = 100,
    ):
        self.percentiles = percentiles
        self.grid_resolution = grid_resolution

    def explain(
        self,
        model: BaseModel,
        x: DashAIDataset,
        categorical_features,
    ):
        # DashAIDAtaset debe venir con prepared_for_task

        test_data = x["test"]
        feature_names = test_data.inputs_columns

        X, _ = self.format_tabular_data(test_data)

        explanation = {}

        for feature in feature_names:
            pd = partial_dependence(
                estimator=model,
                X=X,
                features=feature,
                categorical_features=categorical_features,
                feature_names=feature_names,
                percentiles=self.percentiles,
                grid_resolution=self.grid_resolution,
                kind="average",
            )

            explanation[feature] = {
                "grid_values": pd["values"][0],
                "average": pd["average"],
            }

        return explanation
