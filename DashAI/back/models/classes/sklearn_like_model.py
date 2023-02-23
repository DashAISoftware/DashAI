import joblib
from datasets import load_from_disk

from DashAI.back.models.classes.model import Model


class SklearnLikeModel(Model):
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

    def load_data(self, dataset_path: str, class_column: str) -> dict:
        """Load and prepare the dataset into dataframes to use in Sklearn Models.

        Args:
            dataset_path (str): Path of the folder that contains the dataset.
            class_column (str): Name of the class column of the dataset.

        Returns:
            dict: Dictionary of dataframes with the data to use in experiments.
        """
        dataset = load_from_disk(dataset_path=dataset_path)
        train_data = dataset["train"].to_pandas()
        test_data = dataset["test"].to_pandas()
        val_data = dataset["validation"].to_pandas()
        prepared_dataset = {
            "x_train": train_data.loc[:, train_data.columns != class_column],
            "y_train": train_data[class_column],
            "x_test": test_data.loc[:, test_data.columns != class_column],
            "y_test": test_data[class_column],
            "x_val": val_data.loc[:, val_data.columns != class_column],
            "y_val": val_data[class_column],
        }
        return prepared_dataset

    def fit(self, x, y):
        return super.fit(x, y)

    def predict(self, x):
        return super.predict(x)

    def score(self, x, y):
        return super.score(x, y)
