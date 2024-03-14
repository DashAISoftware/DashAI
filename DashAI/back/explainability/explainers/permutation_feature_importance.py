from typing import List, Tuple, Union

import numpy as np
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

        importances_mean = pfi["importances_mean"]
        sorted_importance = sorted(
            zip(importances_mean, input_columns, strict=True), reverse=True
        )

        importances, features = zip(*sorted_importance, strict=True)

        return {
            "features": list(features),
            "importances_mean": np.round(importances, 3).tolist(),
        }
