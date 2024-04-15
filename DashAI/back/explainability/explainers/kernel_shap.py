from typing import List, Tuple, Union

import numpy as np
import pandas as pd
import plotly
import plotly.graph_objs as go
import shap
from datasets import DatasetDict

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
        background_data: np.array,
        n_background_samples: int,
        sampling_method: str = "shuffle",
        categorical_features: bool = False,
    ):
        """Method to sample the background dataset used to fit the explainer.


        Parameters
        ----------
        background_data: np.array
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
        background_dataset: Tuple[DatasetDict, DatasetDict],
        sample_background_data: bool = False,
        n_background_samples: Union[int, None] = None,
        sampling_method: Union[str, None] = None,
    ):
        """Method to train the KernelShap explainer.

        Parameters
        ----------
        background_data: Tuple[DatasetDict, DatasetDict]
            Tuple with (input_samples, targets). Input samples are used to estimate
            feature attributions and establish a baseline for the calculation of
            SHAP values.
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

        Returns
        -------
        KernelShap object
        """
        x, y = background_dataset

        background_data = x["train"].to_pandas()
        features = x["train"].features
        feature_names = list(features)

        categorical_features = False
        for feature in features:
            if features[feature]._type == "ClassLabel":
                categorical_features = True

        if sample_background_data:
            background_data = self._sample_background_data(
                background_data.to_numpy(),
                n_background_samples,
                sampling_method,
                categorical_features,
            )

        # TODO: consider the case where the predictor is not a Sklearn model
        self.explainer = shap.KernelExplainer(
            model=self.model.predict,
            data=background_data,
            feature_names=feature_names,
            link=self.link,
        )

        # Metadata
        output_column = list(y["train"].features)[0]
        target_names = y["train"].features[output_column].names
        self.metadata = {"feature_names": feature_names, "target_names": target_names}

        return self

    def explain_instance(
        self,
        instances: DatasetDict,
    ):
        """Method for explaining the model prediciton of an instance using the Kernel
        Shap method.

        Parameters
        ----------
        instances: DatasetDict
            Instances to be explained.

        Returns
        -------
        dict
            dictionary with the shap values for each instance.
        """
        X = instances["test"].to_pandas()

        predictions = self.model.predict(x_pred=X)

        # TODO: evaluate args nsamples y l1_reg
        shap_values = self.explainer.shap_values(X=X)

        # shap_values has size (n_clases, n_instances, n_features)
        # Reorder shap values: (n_instances, n_clases, n_features)
        shap_values = np.array(shap_values).swapaxes(1, 0)

        explanation = {
            "metadata": self.metadata,
            "base_values": np.round(self.explainer.expected_value, 2).tolist(),
        }

        for i, (instance, prediction, contribution_values) in enumerate(
            zip(X.to_numpy(), predictions, shap_values, strict=True)
        ):
            explanation[i] = {
                "instance_values": instance.tolist(),
                "model_prediction": prediction.tolist(),
                "shap_values": np.round(contribution_values, 2).tolist(),
            }

        return explanation

    def _create_plot(
        self, data: pd.DataFrame, base_value: float, y_pred_pbb: float, y_pred_name: str
    ):
        """Helper method to create the explanation plot using plotly.

        Parameters
        ----------
        data: pd.DataFrame
            dataframe containing the data to be plotted.
        base_value: float
            value to set where the bar base is drawn.
        y_pred_pbb: float
            predicted probability.
        y_pred_name
            name of the predicted class.

        Returns:
        JSON
            JSON containing the information of the explanation plot
            to be rendered.
        """
        x = data["shap_values"].to_numpy()
        y = data["label"].to_numpy()
        measure = np.repeat("relative", len(y))
        texts = data["shap_values"].to_numpy()

        fig = go.Figure(
            go.Waterfall(
                x=x,
                y=y,
                base=base_value,
                name="20",
                orientation="h",
                measure=measure,
                text=texts,
                textposition="auto",
                constraintext="inside",
                decreasing={"marker": {"color": "rgb(47,138,196)"}},
                increasing={"marker": {"color": "rgb(231,63,116)"}},
            )
        )

        fig.update_layout(
            margin={"pad": 20, "l": 100, "r": 130, "t": 60, "b": 10},
            xaxis={
                "tickangle": -90,
                "tickwidth": 100,
                "title_text": "",
            },
            yaxis={"showgrid": True, "tickwidth": 150},
        )

        fig.update_xaxes(
            gridcolor="#1B2631",
            gridwidth=1,
            tickmode="array",
            nticks=2,
            tickvals=[base_value, y_pred_pbb],
            ticktext=[f"E[f(x)]={base_value}", f"f(x)={y_pred_pbb}"],
            tickangle=0,
            showgrid=True,
        )

        plot_note = f"""The predicted class was {y_pred_name} with a probabiliy
                        f(x)={y_pred_pbb}."""
        fig.add_annotation(
            showarrow=False,
            text=plot_note,
            font={"size": 15},
            xanchor="left",
            xref="paper",
            yref="paper",
            x=0.2,
            y=-0.35,
        )

        return plotly.io.to_json(fig)

    def plot(self, explanation: List[dict]):
        """Method to create the explanation plot using plotly.

        Parameters
        ----------
        explanation: dict
            dictionary with the explanation generated by the explainer.

        Returns:
        List[dict]
            list of JSONs containing the information of the explanation plot
            to be rendered.
        """
        explanation = explanation.copy()

        max_features = 8
        metadata = explanation.pop("metadata")
        base_values = explanation.pop("base_values")
        feature_names = metadata["feature_names"]
        target_names = metadata["target_names"]

        plots = []
        for i in explanation:
            instance_values = explanation[i]["instance_values"]
            model_prediction = explanation[i]["model_prediction"]

            y_pred_class = np.argmax(model_prediction)
            y_pred_name = target_names[y_pred_class]
            y_pred_pbb = model_prediction[y_pred_class]

            shap_values = explanation[i]["shap_values"][y_pred_class]

            data = pd.DataFrame(
                {
                    "values": instance_values,
                    "shap_values": shap_values,
                    "features": feature_names,
                }
            )
            data["shap_values_abs"] = np.abs(data["shap_values"])
            data = data.sort_values(by="shap_values_abs", ascending=True)

            if len(data) > max_features:
                data_1 = data.iloc[-max_features:, :]
                data_2 = data.iloc[:-max_features, :]
                others = pd.DataFrame.from_dict(
                    data={
                        "values": [None],
                        "shap_values": np.round(data_2["shap_values"].sum(), 3),
                        "shap_values_abs": [None],
                        "features": ["Others"],
                    }
                )
                data = pd.concat([others, data_1])

            data["label"] = data["features"] + "=" + data["values"].map(str)
            base_value = base_values[y_pred_class]
            plot = self._create_plot(data, base_value, y_pred_pbb, y_pred_name)
            plots.append(plot)

        return plots
