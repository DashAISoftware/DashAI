from typing import List

from datasets import ClassLabel, DatasetDict, Value

from DashAI.back.tasks.base_task import BaseTask


class TextClassificationTask(BaseTask):
    """Base class for Text Classification Task."""

    metadata: dict = {
        "inputs_types": [Value],
        "outputs_types": [ClassLabel],
        "inputs_cardinality": 1,
        "outputs_cardinality": 1,
    }

    DESCRIPTION: str = """
    Text classification is an essential Natural Language Processing (NLP) task that
    involves automatically assigning pre-defined categories or labels to text documents
    based on their content. It serves as the foundation for applications like sentiment
    analysis, spam filtering, topic classification, and document categorization.
    """

    def prepare_for_task(
        self, datasetdict: DatasetDict, output_columns: List[str]
    ) -> DatasetDict:
        """Change the column types to suit the tabular classification task.

        Note: A copy of the dataset is created.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to be configured

        Returns
        -------
        DatasetDict
            Dataset with the new types
        """
        types = {output_columns[0]: "Categorical"}
        for split in datasetdict:
            datasetdict[split] = datasetdict[split].change_columns_type(types)
        return datasetdict
