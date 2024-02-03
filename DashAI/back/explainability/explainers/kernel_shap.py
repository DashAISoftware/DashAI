from typing import Union

import numpy as np
import shap

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.explainability.local_explainer import BaseLocalExplainer
from DashAI.back.models import BaseModel


class KernelShap(BaseLocalExplainer):
    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]

    def __init__(
        self,
        n_background_samples: Union[int, None] = None,
        background_data_sampler: str = "shuffle",
        n_samples: Union[int, str] = "auto",
        l1_reg: Union[str, float] = "auto",
    ):
        self.n_background_samples = n_background_samples
        self.background_data_sampler = background_data_sampler
        self.n_samples = n_samples
        self.l1_reg = l1_reg

    def fit(self, model, background_data, feature_names):
        samplers = {"shuffle": shap.sample, "kmeans": shap.kmeans}

        if self.n_background_samples:
            sampler = samplers[self.background_data_sampler]
            background_data = sampler(background_data, self.n_background_samples)

        X_train, _ = self.format_tabular_data(background_data)

        kernel_explainer = shap.KernelExplainer(
            model=model.predict_proba, data=X_train, feature_names=feature_names
        )

        return kernel_explainer

    def explain_instance(
        self,
        model: BaseModel,
        background_data: DashAIDataset,
        instances: DashAIDataset,
    ):
        train_data = background_data["train"]
        feature_names = train_data.inputs_columns

        instances, _ = self.format_tabular_data(instances)
        predictions = model.predict_proba(instances)

        explainer = self.fit(model, train_data, feature_names)

        # shap_values has size (n_clases, n_instances, n_features)
        shap_values = explainer.shap_values(
            X=instances, nsamples=self.n_samples, l1_reg=self.l1_reg
        )

        # Reorder shap values: (n_instances, n_clases, n_features)
        shap_values = np.array(shap_values).swapaxes(1, 0)

        explanation = {"base_values": explainer.expected_value}

        for i, (instance, model_prediction, contribution_values) in enumerate(
            zip(instances.values, predictions, shap_values, strict=True)
        ):
            explanation[f"{i}"] = {
                "instance_values": instance,
                "model_prediction": model_prediction,
                "shap_values": contribution_values,
            }

        return explanation
