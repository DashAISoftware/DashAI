import joblib
from datasets import DatasetDict

from DashAI.back.models.base_model import BaseModel


class SklearnLikeModel(BaseModel):
    """
    Abstract class to define the way to save sklearn like models.
    """

    def save(self, filename):
        """
        Method to save the model in the filename path.
        """
        joblib.dump(self, filename)

    @staticmethod
    def load(filename):
        """
        Method to load the model from the filename path.
        """
        model = joblib.load(filename)
        return model

    # --- Methods for process the data for sklearn models ---

    def format_data(self, datasetdict: DatasetDict) -> dict:
        """Load and prepare the dataset into dataframes to use in Sklearn Models.

        Parameters
        ----------
        datasetdict : DatasetDict
            Dataset to use

        Returns
        -------
        dict
            Dictionary of dataframes with the data to use in experiments.
        """
        formatted_data_to_model = {}
        for split in datasetdict:
            data_in_pandas = datasetdict[split].to_pandas()
            input_data = data_in_pandas.loc[
                :, ~data_in_pandas.columns.isin(datasetdict[split].outputs_columns)
            ]
            output_data = data_in_pandas[datasetdict[split].outputs_columns]
            formatted_data_to_model[f"{split}"] = {
                "input": input_data,
                "output": output_data,
            }

        return formatted_data_to_model

    def fit(self, x, y):
        return super().fit(x, y)

    def predict(self, x):
        return super().predict_proba(x)
