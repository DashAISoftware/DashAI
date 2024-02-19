from typing import Tuple, Type, Union

import joblib
import pandas as pd

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.models.base_model import BaseModel


class SklearnLikeModel(BaseModel):
    """Abstract class to define the way to save sklearn like models."""

    def save(self, filename: str) -> None:
        """Save the model in the specified path."""
        joblib.dump(self, filename)

    @staticmethod
    def load(filename: str) -> None:
        """Load the model of the specified path."""
        model = joblib.load(filename)
        return model

    # --- Methods for process the data for sklearn models ---

    def format_data(self, dataset: DashAIDataset) -> Tuple[pd.DataFrame, pd.Series]:
        """Load and prepare the dataset into dataframes to use in Sklearn Models.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset to format

        Returns
        -------
        Dataframe
            Dataframe with the data to use in experiments.
        """
        data_in_pandas = dataset.to_pandas()
        x = data_in_pandas.loc[:, dataset.inputs_columns]
        y = data_in_pandas[dataset.outputs_columns]

        return x, y

    def fit(self, dataset: DashAIDataset) -> Type["SklearnLikeModel"]:
        """Fit the estimator.

        Parameters
        ----------
        dataset : DashAIDataset
            The training dataset.

        Returns
        -------
        self
            The fitted estimator object.
        """
        x, y = self.format_data(dataset)
        return super().fit(x, y)

    def predict(self, dataset: Union[DashAIDataset, pd.DataFrame]):
        # TODO: this is a momentary fix
        if isinstance(dataset, DashAIDataset):
            x, y = self.format_data(dataset)
            return super().predict_proba(x)

        return super().predict_proba(dataset)
