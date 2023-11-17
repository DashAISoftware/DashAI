from typing import Tuple
from sklearn.inspection import partial_dependence

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.explainability.global_explainer import GlobalExplainer
from DashAI.back.models import BaseModel


# Centered case
class PartialDependence(GlobalExplainer):
    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]

    def __init__(
        self,
        percentiles: Tuple[float, float] = (0.05, 0.95),
        grid_resolution: int = 100,
    ):
        self.percentiles = percentiles
        self.grid_resolution = grid_resolution

    def explain(
        self,
        model: BaseModel,
        X: DashAIDataset,
        categorical_features,
    ):
        """_summary_

        Args:
            model (BaseModel): _description_
            X (DashAIDataset): _description_
            categorical_features (_type_): _description_
        """

        """Assumptions:
        1. En la interfaz se podrán seleccionar los features categóricos
        2. Se calculará para todos los features bajo los mismos parámetros 
        configurables

        Cosas a considerar:
        1. Interacting features: only continuos pairs
        2.Centered case"""

        X_test = X["test"]
        feature_names = X_test.column_names
        df = X_test.to_pandas()

        explanation = {}

        for feature in feature_names:
            pd = partial_dependence(
                estimator=model,
                X=df,
                features=feature,
                categorical_features=categorical_features,
                feature_names=feature_names,
                percentiles=self.percentiles,
                grid_resolution=self.grid_resolution,
                kind="both",
            )

            explanation["feature"] = pd

        return explanation
