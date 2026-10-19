from DashAI.back.core.utils import MultilingualString
from DashAI.back.tasks.unsupervised_task import UnsupervisedTask
from DashAI.back.types.value_types import Float, Integer


class ClusteringTask(UnsupervisedTask):
    """Task for grouping samples into clusters without target labels.

    Clustering tasks discover groups directly from numeric input features.
    Unlike supervised tasks, they do not require output columns and are
    evaluated with internal clustering metrics computed from the feature matrix
    and the cluster labels produced by the model.
    """

    DESCRIPTION: str = MultilingualString(
        en="Group similar samples from numeric features without target labels.",
        es="Agrupa muestras similares desde variables numericas sin etiquetas.",
        pt="Agrupa amostras semelhantes a partir de variáveis numéricas sem rótulos.",
        de="Gruppiert ähnliche Stichproben anhand numerischer Merkmale ohne "
        "Zielbezeichnungen.",
        zh="根据数值特征对相似样本进行分组，无需目标标签。",
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Clustering", es="Agrupamiento", pt="Agrupamento", de="Clustering", zh="聚类"
    )

    metadata: dict = {
        "inputs_types": [Float, Integer],
        "outputs_types": [],
        "inputs_cardinality": "n",
        "outputs_cardinality": 0,
    }
