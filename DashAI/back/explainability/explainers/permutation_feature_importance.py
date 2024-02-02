from typing import List, Union

from sklearn.inspection import permutation_importance

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.explainability.global_explainer import BaseGlobalExplainer
from DashAI.back.models import BaseModel


class PermutationFeatureImportance(BaseGlobalExplainer):
    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]

    def __init__(
        self,
        scoring: Union[str, List[str], None] = None,
        n_repeats: int = 5,
        random_state: Union[int, None] = None,
        max_samples: int = 1,
    ):
        self.scoring = scoring
        self.n_repeats = n_repeats
        self.random_state = random_state
        self.max_samples = max_samples

    def explain(
        self,
        model: BaseModel,
        x: DashAIDataset,
    ):
        test_data = x["test"]
        feature_names = test_data.inputs_columns

        X, y = self.format_tabular_data(test_data)

        pfi = permutation_importance(
            estimator=model,
            X=X,
            y=y,
            scoring=self.scoring,
            n_repeats=self.n_repeats,
            random_state=self.random_state,
            max_samples=self.max_samples,
        )

        importances_mean = pfi["importances_mean"]
        sorted_importance = sorted(
            zip(importances_mean, feature_names, strict=True), reverse=True
        )

        importances, features = zip(*sorted_importance, strict=True)

        explanation = {
            "features": list(features),
            "importances_mean": list(importances),
        }

        return explanation
