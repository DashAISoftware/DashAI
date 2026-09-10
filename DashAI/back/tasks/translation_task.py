"""DashAI Translation Task."""

from typing import TYPE_CHECKING, List, Union

from DashAI.back.core.utils import MultilingualString
from DashAI.back.tasks.base_task import BaseTask
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from datasets import DatasetDict
    from numpy import ndarray

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class TranslationTask(BaseTask):
    """Task for sequence-to-sequence machine translation between languages.

    Translation tasks take a single ``Text`` input column (source language) and
    produce a single ``Text`` output column (target language). The compatible
    metrics are BLEU, CHRF, and TER, which measure n-gram overlap, character-level
    F-score, and translation edit rate against reference translations respectively.
    """

    COMPATIBLE_COMPONENTS = ["Bleu", "Chrf", "Ter"]

    metadata: dict = {
        "inputs_types": [Text],
        "outputs_types": [Text],
        "inputs_cardinality": 1,
        "outputs_cardinality": 1,
    }
    DESCRIPTION: str = MultilingualString(
        en="Convert text from one language to another preserving meaning.",
        es="Convierte texto de un idioma a otro preservando el significado.",
        pt="Converte texto de um idioma para outro preservando o significado.",
        de=(
            "Text von einer Sprache in eine andere übersetzen, wobei die Bedeutung "
            "erhalten bleibt."
        ),
        zh="在保留原义的前提下，将文本从一种语言转换为另一种语言。",
    )

    DISPLAY_NAME: str = MultilingualString(
        en="Translation", es="Traducción", pt="Tradução", de="Übersetzung", zh="翻译"
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

    def process_predictions(
        self, dataset: "DashAIDataset", predictions: "ndarray", output_column: str
    ):
        """Process the predictions

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset used for training
        predictions : np.ndarray
            Predictions from the model
        output_column : str
            Output column

        Returns
        -------
        Processed predictions
        """
        return predictions

    def num_labels(self, dataset: "DashAIDataset", output_column: str) -> int | None:
        """Get the number of unique labels in the output column.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset used for training
        output_column : str
            Output column

        Returns
        -------
        int | None
            Number of unique labels or None if not applicable
        """
        return None
