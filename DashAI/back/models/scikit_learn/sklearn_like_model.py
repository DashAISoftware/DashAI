import joblib
from datasets import Dataset, DatasetDict

from DashAI.back.models.base_model import BaseModel


class SklearnLikeModel(BaseModel):
    """Abstract class to define the way to save sklearn like models."""

    def save(self, filename):
        """Save the model in the specified path."""
        joblib.dump(self, filename)

    @staticmethod
    def load(filename):
        """Load the model of the specified path."""
        model = joblib.load(filename)
        return model

    # --- Methods for process the data for sklearn models ---

    def format_data(self, dataset: Dataset) -> tuple:
        """Load and prepare the dataset into dataframes to use in Sklearn Models.

        Parameters
        ----------
        datasetdict : Dataset
            Dataset to format

        Returns
        -------
        Dataframe
            Dataframe with the data to use in experiments.
        """
        data_in_pandas = dataset.to_pandas()
        x = data_in_pandas.loc[:, ~data_in_pandas.columns.isin(dataset.outputs_columns)]
        y = data_in_pandas[dataset.outputs_columns]

        return x, y

    def fit(self, dataset: DatasetDict):
        x, y = self.format_data(dataset["train"])
        return super().fit(x, y)

    def predict(self, dataset: DatasetDict, validation=False):
        if validation:
            x, y = self.format_data(dataset["validation"])
        else:
            x, y = self.format_data(dataset["test"])
        return super().predict_proba(x)
