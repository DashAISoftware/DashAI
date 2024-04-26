from typing import List, Tuple, Union

import numpy as np
import pandas as pd
import plotly
import plotly.express as px
from datasets import DatasetDict
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score, balanced_accuracy_score, make_scorer

from DashAI.back.explainability.global_explainer import BaseGlobalExplainer
from DashAI.back.models import BaseModel


class PermutationFeatureImportance(BaseGlobalExplainer):
    """Permutation Feature Importance is a explanation method to asses the importance
    of each feature in a model by evaluating how much the model's performance
    decreases when the values of a specific feature are randomly shuffled.
    """

    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]

    def __init__(
        self,
        model: BaseModel,
        scoring: Union[str, List[str], None] = None,
        n_repeats: int = 5,
        random_state: Union[int, None] = None,
        max_samples: int = 1,
    ):
        """Initialize a new instance of PermutationFeatureImportance explainer.

        Parameters
        ----------
        model: BaseModel
            Model to be explained
        scoring: Union[str, List[str], None]
            Scorer to evaluate how the perfomance of the model
            changes when a particular feature is shuffled
        n_repeats: int
            Numer of times to permute a feature
        random_state: Union[int, None]
            Seed for  the random number generator to control the
            permutations of each feature
        max_samples: int
            The number of samples to draw from the dataset to calculate
            feature importance at each repetition
        """

        super().__init__(model)

        metrics = {
            "accuracy": accuracy_score,
            "balanced_accuracy": balanced_accuracy_score,
        }

        self.scoring = metrics[scoring]
        self.n_repeats = n_repeats
        self.random_state = random_state
        self.max_samples = max_samples

    def explain(self, dataset: Tuple[DatasetDict, DatasetDict]):
        """Method for calculating the importance of features in the model

        Parameters
        ----------
        dataset: Tuple[DatasetDict, DatasetDict]
        Tuple with (input_samples, targets) used to generate the explanation.

        Returns
        -------
        dict
            Dictionary with the features names and the avarage importance of
            each feature
        """
        x, y = dataset

        # Select split
        x_test = x["test"]
        y_test = y["test"]

        input_columns = list(x_test.features)
        output_columns = list(y_test.features)

        input_columns = list(x_test.features)
        output_columns = list(y_test.features)

        types = {column: "Categorical" for column in output_columns}
        y_test = y_test.change_columns_type(types)

        def patched_metric(y_true, y_pred_probas):
            return self.scoring(y_true, np.argmax(y_pred_probas, axis=1))

        # TODO: binary and multi-label scorer
        pfi = permutation_importance(
            estimator=self.model,
            X=x_test.to_pandas(),
            y=y_test.to_pandas(),
            scoring=make_scorer(patched_metric),
            n_repeats=self.n_repeats,
            random_state=self.random_state,
            max_samples=self.max_samples,
        )

        return {
            "features": input_columns,
            "importances_mean": np.round(pfi["importances_mean"], 3).tolist(),
            "importances_std": np.round(pfi["importances_std"], 3).tolist(),
        }

    def _create_plot(self, data: pd.DataFrame, n_features: int):
        """Helper method to create the explanation plot using plotly.

        Parameters
        ----------
        data: pd.DataFrame
            dataframe containing the data to be plotted.
        n_features: int
            number of features to be displayed initially in the plot.

        Returns:
        List[dict]
            list of JSONs containing the information of the explanation plot
            to be rendered.
        """
        fig = px.bar(
            data.iloc[-n_features:],
            x=data.iloc[-n_features:]["importances_mean"],
            y=data.iloc[-n_features:]["features"],
            error_x=data.iloc[-n_features:]["importances_std"],
        )

        fig.update_layout(
            xaxis_title="Importance",
            yaxis_title=None,
            annotations=[
                {
                    "text": "Number of features to show: ",
                    "showarrow": False,
                    "x": 0,
                    "y": 1.15,
                    "xanchor": "left",
                    "xref": "paper",
                    "yref": "paper",
                    "yanchor": "top",
                }
            ],
            updatemenus=[
                {
                    "x": 0.25,
                    "xanchor": "left",
                    "y": 1.2,
                    "yanchor": "top",
                    "buttons": [
                        {
                            "label": len(data.iloc[-c:,]),
                            "method": "restyle",
                            "args": [
                                {
                                    "x": [data.iloc[-c:]["importances_mean"]],
                                    "y": [data.iloc[-c:]["features"]],
                                    "error_x": [data.iloc[-c:]["importances_std"]],
                                },
                            ],
                        }
                        for c in range(len(data))
                    ],
                }
            ],
        )

        return [plotly.io.to_json(fig)]

    def plot(self, explanation: dict) -> List[dict]:
        """Method to create the explanation plot.

        Parameters
        ----------
        explanation: dict
            dictionary with the explanation generated by the explainer.

        Returns:
        List[dict]
            list of JSON containing the information of the explanation plot
            to be rendered.
        """
        n_features = 10
        data = pd.DataFrame.from_dict(explanation)
        data = data.sort_values(by=["importances_mean"], ascending=True)

        if n_features > len(data):
            n_features = len(data)

        return self._create_plot(data, n_features)
