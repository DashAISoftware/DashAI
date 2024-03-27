from typing import Tuple

import numpy as np
import pandas as pd
import plotly
import plotly.express as px
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
            Dictionary with metadata and the partial dependence of each feature
        """
        x, y = dataset

        x_test = x["test"].to_pandas()
        features = x["test"].features
        features_names = list(features)

        categorical_features = [
            1 if features[feature]._type == "ClassLabel" else 0 for feature in features
        ]

        output_column = list(y["test"].features)[0]
        target_names = y["test"].features[output_column].names

        explanation = {"metadata": {"target_names": target_names}}

        for idx in range(len(features)):
            pd = partial_dependence(
                estimator=self.model,
                X=x_test,
                features=idx,
                categorical_features=categorical_features,
                feature_names=features,
                percentiles=self.percentiles,
                grid_resolution=self.grid_resolution,
                kind="average",
            )

            explanation[features_names[idx]] = {
                "grid_values": np.round(pd["values"][0], 3).tolist(),
                "average": np.round(pd["average"], 3).tolist(),
            }

        return explanation

    def _create_plot(self, data):
        fig = px.line(
            data[0],
            x=data[0]["grid_values"],
            y=data[0].iloc[:, 0],
            labels={"grid_values": "Feature value"},
        )

        fig.update_layout(
            yaxis_title="Partial Dependence",
            updatemenus=[
                {
                    "x": 0,
                    "xanchor": "left",
                    "y": 1.2,
                    "yanchor": "top",
                    "buttons": [
                        {
                            "label": data[i].columns[0],
                            "method": "restyle",
                            "args": [
                                {
                                    "x": [data[i]["grid_values"]],
                                    "y": [data[i].iloc[:, 0]],
                                },
                            ],
                        }
                        for i in range(len(data))
                    ],
                }
            ],
        )

        plot_note = (
            "This graph shows the marginal effect of the selected feature "
            "on the <br> probability predicted by the model for the selected "
            "class"
        )

        fig.add_annotation(
            align="center",
            arrowsize=0.3,
            arrowwidth=0.1,
            borderwidth=2,
            font={"size": 12},
            showarrow=False,
            text=plot_note,
            xanchor="center",
            yanchor="bottom",
            xref="paper",
            yref="paper",
            y=-0.35,
        )

        return [plotly.io.to_json(fig)]

    def plot(self, explanation):
        explanation = explanation.copy()
        metadata = explanation.pop("metadata")
        target_names = metadata["target_names"]

        dfs = []
        for feature, data in explanation.items():
            average = data["average"]
            grid_values = data["grid_values"]

            for target, values in zip(target_names, average, strict=True):
                column_name = f"Feature: {feature} - Class: {target}"
                data = pd.DataFrame({column_name: values})
                data["grid_values"] = grid_values
                dfs.append(data)

        return self._create_plot(dfs)
