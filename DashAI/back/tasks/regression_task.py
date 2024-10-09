from typing import List

from datasets import DatasetDict, Value

from DashAI.back.tasks.base_task import BaseTask


class RegressionTask(BaseTask):
    """Base class for regression tasks.

    Here you can change the methods provided by class Task.
    """

    DESCRIPTION: str = """
    Regression in machine learning involves predicting continuous values for
    structured data organized in tabular form (rows and columns).
    Models are trained to learn patterns and relationships in the data,
    enabling accurate prediction of new instances."""
    metadata: dict = {
        "inputs_types": [Value],
        "outputs_types": [Value],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }

    def prepare_for_task(
        self, datasetdict: DatasetDict, outputs_columns: List[str]
    ) -> DatasetDict:
        """Change the column types to suit the regression task.

        A copy of the dataset is created.

        Parameters
        ----------
        datasetdict : DatasetDict
            Dataset to be changed

        Returns
        -------
        DatasetDict
            Dataset with the new types
        """
        return datasetdict
