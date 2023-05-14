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

    def format_data(self, datasetdict_dashai: DatasetDict) -> dict:
        """Load and prepare the dataset into dataframes to use in Sklearn Models.

        Args:
            dataset_path (str): Path of the folder that contains the dataset.
            class_column (str): Name of the class column of the dataset.

        Returns:
            dict: Dictionary of dataframes with the data to use in experiments.
        """
        train_data = datasetdict_dashai["train"].to_pandas()
        test_data = datasetdict_dashai["test"].to_pandas()
        val_data = datasetdict_dashai["validation"].to_pandas()
        prepared_dataset = {
            "x_train": train_data.loc[
                :, ~train_data.columns.isin(datasetdict_dashai["train"].outputs_columns)
            ],
            "y_train": train_data[datasetdict_dashai["train"].outputs_columns],
            "x_test": test_data.loc[
                :, ~test_data.columns.isin(datasetdict_dashai["test"].outputs_columns)
            ],
            "y_test": test_data[datasetdict_dashai["test"].outputs_columns],
            "x_val": val_data.loc[
                :,
                ~val_data.columns.isin(
                    datasetdict_dashai["validation"].outputs_columns
                ),
            ],
            "y_val": val_data[datasetdict_dashai["validation"].outputs_columns],
        }
        return prepared_dataset

    def fit(self, x, y):
        return super().fit(x, y)

    def predict(self, x):
        return super().predict_proba(x)
