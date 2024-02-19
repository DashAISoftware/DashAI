from typing import List, Union

from sklearn.inspection import partial_dependence

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.explainability.global_explainer import BaseGlobalExplainer
from DashAI.back.models import BaseModel


# Centered case
class PartialDependence(BaseGlobalExplainer):
    """PartialDependence is a model-agnostic explainability method that
    shows the average prediction of a machine learning model for each
    possible value of a feature.
    """

    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]

    def __init__(
        self,
        model: BaseModel,
        categorical_features: Union[List[str], None] = None,
        lower_percentile: float = 0.05,
        upper_percentile: float = 0.95,
        grid_resolution: int = 100,
    ):
        """Initialize a new instance of a PartialDependence explainer.

        Parameters
        ----------
            model: BaseModel
                Model to be explained.
            categorical_features: List[str]
                List with the names of the categorical features used to train the model.
            lower_percentile: int
                The lower and upper percentile used to limit the feature values.
                Defaults to 0.05
            upper_percentile: int
                The lower and upper percentile used to limit the feature values.
                Default to 0.95
            grid_resolution: int
                The number of equidistant points to split the range of the target
                feature. Defaults to 100.
        """

        assert (
            upper_percentile > lower_percentile
        ), "upper_percentile value must be greater than lower_percentile"

        super().__init__(model)

        self.percentiles = (lower_percentile, upper_percentile)
        self.grid_resolution = grid_resolution
        self.categorical_features = categorical_features
        self.explanation = None

    def explain(
        self,
        x: DashAIDataset,
    ):
        """Method to generate the explanation

        Parameters
        ----------
            X: DashAIDataset
                Data set used to evaluate the partial dependence of each feature

        Returns:
            dict
                Dictionary with the partial dependence of each feature
        """
        test_data = x["test"]
        feature_names = test_data.inputs_columns

        X, _ = self.format_tabular_data(test_data)

        self.explanation = {}

        for feature in feature_names:
            pd = partial_dependence(
                estimator=self.model,
                X=X,
                features=feature,
                categorical_features=self.categorical_features,
                feature_names=feature_names,
                percentiles=self.percentiles,
                grid_resolution=self.grid_resolution,
                kind="average",
            )

            self.explanation[feature] = {
                "grid_values": pd["values"][0].tolist(),
                "average": pd["average"].tolist(),
            }

        return self.explanation
