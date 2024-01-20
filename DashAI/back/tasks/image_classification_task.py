from typing import List

from datasets import ClassLabel, DatasetDict, Image

from DashAI.back.tasks.base_task import BaseTask


class ImageClassificationTask(BaseTask):
    """Base class for image classification tasks.

    Here you can change the methods provided by class Task.
    """

    metadata: dict = {
        "inputs_types": [Image],
        "outputs_types": [ClassLabel],
        "inputs_cardinality": 1,
        "outputs_cardinality": 1,
    }

    def prepare_for_task(
        self, datasetdict: DatasetDict, outputs_columns: List[str]
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

        types = {column: "Categorical" for column in outputs_columns}
        for split in datasetdict:
            datasetdict[split] = datasetdict[split].change_columns_type(types)
        return datasetdict
