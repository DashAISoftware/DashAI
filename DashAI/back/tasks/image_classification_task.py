from typing import List

from datasets import ClassLabel, DatasetDict, Image

from DashAI.back.tasks.base_task import BaseTask


class ImageClassificationTask(BaseTask):
    """Base class for image classification tasks.

    Here you can change the methods provided by class Task.
    """

    schema: dict = {
        "inputs_types": [Image],
        "outputs_types": [ClassLabel],
        "inputs_cardinality": 1,
        "outputs_cardinality": 1,
    }

    def prepare_for_task(
        self, datasetdict: DatasetDict, output_columns: List[str]
    ) -> DatasetDict:
        """Change the column types to suit the tabular classification task.

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
        types = {output_columns[0]: "Categorical"}
        for split in datasetdict:
            datasetdict[split] = datasetdict[split].change_columns_type(types)
        return datasetdict
