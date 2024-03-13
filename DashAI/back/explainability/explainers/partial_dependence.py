from typing import Tuple

import numpy as np
from datasets import DatasetDict
from sklearn.inspection import partial_dependence

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
        lower_percentile: float = 0.05,
        upper_percentile: float = 0.95,
        grid_resolution: int = 100,
    ):
        """Initialize a new instance of a PartialDependence explainer.

        Parameters
        ----------
        model: BaseModel
            Model to be explained.
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
        self.explanation = None

    def explain(self, dataset: Tuple[DatasetDict, DatasetDict]):
        """Method to generate the explanation

        Parameters
        ----------
        X: Tuple[DatasetDict, DatasetDict]
            Tuple with (input_samples, targets). Input samples are used to evaluate
            the partial dependence of each feature

        Returns:
        dict
            Dictionary with the partial dependence of each feature
        """
        x, _ = dataset

        # Select split
        test_data = x["test"]
        features = test_data.features
        features_names = list(features)
        n_features = len(features)

        categorical_features = [0] * n_features
        for i, feature in enumerate(features):
            if features[feature]._type == "ClassLabel":
                categorical_features[i] = 1

        X = [list(row.values()) for row in test_data]
        self.explanation = {}

        for idx in range(n_features):
            pd = partial_dependence(
                estimator=self.model,
                X=np.array(X),
                features=idx,
                categorical_features=categorical_features,
                feature_names=features,
                percentiles=self.percentiles,
                grid_resolution=self.grid_resolution,
                kind="average",
            )

            self.explanation[features_names[idx]] = {
                "grid_values": np.round(pd["values"][0], 2).tolist(),
                "average": np.round(pd["average"], 2).tolist(),
            }

        return self.explanation
