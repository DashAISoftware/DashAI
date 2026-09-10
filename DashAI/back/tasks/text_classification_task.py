from typing import TYPE_CHECKING, List, Union

from DashAI.back.core.utils import MultilingualString
from DashAI.back.tasks.classification_task import ClassificationTask
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from datasets import DatasetDict

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class TextClassificationTask(ClassificationTask):
    """Task for classifying a single text column into discrete categories.

    Text classification takes one input column of type ``Text`` and maps it to
    one categorical output column. The task covers any NLP scenario where a
    raw or pre-processed text sequence must be assigned to one of a fixed set
    of labels, such as sentiment analysis, spam detection, topic labelling, and
    intent recognition. Compatible models consume the text directly and output
    a predicted class label for each sample.
    """

    metadata: dict = {
        "inputs_types": [Text],
        "outputs_types": [Categorical],
        "inputs_cardinality": 1,
        "outputs_cardinality": 1,
    }

    DESCRIPTION: str = MultilingualString(
        en=(
            "Classify text into predefined categories. "
            "E.g.: sentiment, spam, intent detection."
        ),
        es=(
            "Clasifica textos en categorías predefinidas. "
            "Ej.: sentimiento, spam, intención."
        ),
        pt=(
            "Classifica textos em categorias predefinidas. "
            "Ex.: sentimento, spam, detecção de intenção."
        ),
        de=(
            "Text in vordefinierte Kategorien klassifizieren. "
            "Z.B.: Stimmungsanalyse, Spam, Absichtserkennung."
        ),
        zh="将文本分类到预定义类别。例如：情感分析、垃圾邮件检测、意图识别。",
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Text Classification",
        es="Clasificación de Texto",
        pt="Classificação de Texto",
        de="Textklassifikation",
        zh="文本分类",
    )

    def prepare_for_task(
        self,
        dataset: Union["DatasetDict", "DashAIDataset"],
        input_columns: List[str],
        output_columns: List[str],
    ) -> "DashAIDataset":
        """Convert the dataset to DashAIDataset and check the columns types

        A copy of the dataset is created.

        Parameters
        ----------
        dataset : Union[DatasetDict, DashAIDataset]
            Dataset to be changed

        Returns
        -------
        DashAIDataset
            Dataset with the new types
        """
        dashai_dataset = super().prepare_for_task(
            dataset, input_columns, output_columns
        )
        return dashai_dataset
