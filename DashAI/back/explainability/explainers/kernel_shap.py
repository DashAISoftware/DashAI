from typing import Union

import numpy as np
import shap

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.explainability.local_explainer import BaseLocalExplainer
from DashAI.back.models import BaseModel


class KernelShap(BaseLocalExplainer):
    """Kernel SHAP is a model-agnostic explainability method for approximating SHAP
    values to explain the output of machine learning model by attributing contributions
    of each feature to the model's prediction.
    """

    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]

    def __init__(
        self,
        model: BaseModel,
        link: str = "identity",
    ):
        """Initialize a new instance of a KernelShap explainer.

        Parameters
        ----------
            model: BaseModel
                    Model to be explained.
            link: str
                String indicating the link function to connect the feature importance
                values to the model's outputs. Options are 'identity' to use identity
                function or 'logit'to use log-odds function.
        """
        super().__init__(model)
        self.link = link

    def _sample_background_data(
        self,
        background_data: DashAIDataset,
        n_background_samples: int,
        sampling_method: str = "shuffle",
        categorical_features: bool = False,
    ):
        """Method to sample the background dataset used to fit the explainer.


        Parameters
        ----------
            background_data: DashAIDataset
                Data used to estimate feature attributions and establish a baseline for
                the calculation of SHAP values.
            n_background_samples: int
                Number of background data samples used to estimate of SHAP values. By
                default, the entire train dataset is used, but this option limits the
                samples to reduce run times.
            sampling_method: str
                Sampling method used to select the background samples. Options are
                'shuffle' to select random samples or 'kmeans' to summarise the data
                set. 'kmeans' option can only be used if there are no categorical
                features.
            categorical_features: bool
                Bool indicating whether some features are categorical.

        Returns
        -------
            pd.DataFrame
                pandas DataFrame with the background data used to fit the
                explainer.
        """

        samplers = {"shuffle": shap.sample, "kmeans": shap.kmeans}

        if categorical_features:
            data = samplers["shuffle"](background_data, n_background_samples)
        else:
            data = samplers[sampling_method](background_data, n_background_samples)

        return data

    def fit(
        self,
        background_data: DashAIDataset,
        sample_background_data: bool = False,
        n_background_samples: Union[int, None] = None,
        sampling_method: Union[str, None] = None,
        categorical_features: bool = False,
    ):
        """Method to train the KernelShap explainer.

        Parameters
        ----------
            background_data: DashAIDataset
                Data used to estimate feature attributions and establish a baseline for
                the calculation of SHAP values.
            sample_background_data: bool
                True if the background data must be sampled. Smaller data sets speed up
                the algorithm run time. False by default.
            n_background_samples: int
                Number of background data samples used to estimate of SHAP values if
                ``sample_background_data=True``.
            sampling_method: str
                Sampling method used to select the background samples if
                ``sample_background_data=True``. Options are 'shuffle' to select random
                samples or 'kmeans' to summarise the data set. 'kmeans' option can only
                be used if there are no categorical features.
            categorical_features: bool
                Bool indicating whether some features are categorical. False by deault.

        Returns
        -------
            KernelShap object
        """

        background_data = background_data["train"]
        feature_names = background_data.inputs_columns
        background_data, _ = self.format_tabular_data(background_data)

        if sample_background_data:
            background_data = self._sample_background_data(
                background_data,
                n_background_samples,
                sampling_method,
                categorical_features,
            )

        # TODO: consider the case where the predictor is not a Sklearn model
        self.explainer = shap.KernelExplainer(
            model=self.model.predict_proba,
            data=background_data,
            feature_names=feature_names,
            link=self.link,
        )

        return self

    def explain_instance(
        self,
        instances: DashAIDataset,
    ):
        """Method to

        Parameters
        ----------
            instances: DashAIDataset
                Instances to be explained.

        Returns
        -------
            dict
                dictionary with the shap values for each instance.
        """
        instances, _ = self.format_tabular_data(instances)
        predictions = self.model.predict_proba(instances)

        # TODO: evaluate args nsamples y l1_reg
        shap_values = self.explainer.shap_values(X=instances)

        # shap_values has size (n_clases, n_instances, n_features)
        # Reorder shap values: (n_instances, n_clases, n_features)
        shap_values = np.array(shap_values).swapaxes(1, 0)

        self.explanation = {"base_values": self.explainer.expected_value.tolist()}

        for i, (instance, model_prediction, contribution_values) in enumerate(
            zip(instances.values, predictions, shap_values)
        ):
            self.explanation[f"{i}"] = {
                "instance_values": instance.tolist(),
                "model_prediction": model_prediction.tolist(),
                "shap_values": contribution_values.tolist(),
            }

        return self.explanation
