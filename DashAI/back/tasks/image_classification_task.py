from typing import TYPE_CHECKING, List, Union

from DashAI.back.core.utils import MultilingualString
from DashAI.back.tasks.classification_task import ClassificationTask
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.dashai_image import DashAIImage

if TYPE_CHECKING:
    from datasets import DatasetDict

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ImageClassificationTask(ClassificationTask):
    """Task for classifying images into discrete categories.

    Image classification predicts categorical labels from image inputs.
    It accepts image columns as inputs, requires a single categorical
    output column, and is compatible with image classifier models.
    """

    DESCRIPTION: str = MultilingualString(
        en=(
            "Predict categorical labels from image data by learning visual "
            "patterns and features."
        ),
        es=(
            "Predice etiquetas categóricas para imágenes aprendiendo patrones "
            "y características visuales."
        ),
        pt=(
            "Prevê rótulos categóricos para imagens aprendendo padrões "
            "e características visuais."
        ),
        de=(
            "Sagt kategoriale Zielgrößen für Bilddaten vorher, indem visuelle "
            "Muster erlernt werden."
        ),
        zh=(
            "机器学习中的图像分类涉及预测图像数据的分类标签。"
            "模型被训练以学习图像中的视觉模式和特征，"
            "从而实现对新实例的精确分类。"
        ),
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Image Classification",
        es="Clasificación de Imágenes",
        pt="Classificação de Imagens",
        de="Bildklassifikation",
        zh="图像分类",
    )
    metadata: dict = {
        "inputs_types": [DashAIImage],
        "outputs_types": [Categorical],
        "inputs_cardinality": 1,
        "outputs_cardinality": 1,
    }

    def prepare_for_task(
        self,
        dataset: Union["DatasetDict", "DashAIDataset"],
        input_columns: List[str],
        output_columns: List[str],
    ) -> "DashAIDataset":
        """Prepare a dataset for an image classification task.

        Parameters
        ----------
        dataset : Union[DatasetDict, DashAIDataset]
            Dataset to be prepared.
        input_columns : List[str]
            Names of the image input columns.
        output_columns : List[str]
            Names of the categorical output columns.

        Returns
        -------
        DashAIDataset
            The validated dataset, ready for training or inference.
        """
        dashai_dataset = super().prepare_for_task(
            dataset, input_columns, output_columns
        )
        return dashai_dataset
