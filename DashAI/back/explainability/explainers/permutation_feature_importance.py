from typing import List, Union

from sklearn.inspection import permutation_importance

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
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

        self.scoring = scoring
        self.n_repeats = n_repeats
        self.random_state = random_state
        self.max_samples = max_samples

    def explain(
        self,
        x: DashAIDataset,
    ):
        """Method for calculating the importance of features in the model

        Parameters
        ----------
            X: DashAIDataset
                Data set used to calculate feature importances.

        Returns
        -------
            dict
                Dictionary with the features names and the avarage importance of
                each feature
        """
        test_data = x["test"]
        feature_names = test_data.inputs_columns

        X, y = self.format_tabular_data(test_data, one_hot_encoding=True)

        print(f"y: {y}")

        # TODO: binary and multi-label scorer
        pfi = permutation_importance(
            estimator=self.model,
            X=X,
            y=y,
            scoring=self.scoring,
            n_repeats=self.n_repeats,
            random_state=self.random_state,
            max_samples=self.max_samples,
        )

        importances_mean = pfi["importances_mean"]
        sorted_importance = sorted(zip(importances_mean, feature_names), reverse=True)

        importances, features = zip(*sorted_importance)

        self.explanation = {
            "features": list(features),
            "importances_mean": list(importances),
        }

        return self.explanation
