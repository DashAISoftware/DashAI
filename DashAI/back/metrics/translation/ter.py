"""TER (Translation Edit Rate) metric implementation for DashAI."""

from typing import TYPE_CHECKING

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.translation_metric import TranslationMetric, prepare_to_metric

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class Ter(TranslationMetric):
    """A class for calculating TER scores between source and target sentences.

    TER (Translation Edit Rate, also called Translation Error Rate) is a metric
    to quantify the edit operations requiered to match a reference translation.

    References
    ----------
    - [1] https://lightning.ai/docs/torchmetrics/stable/text/translation_edit_rate.html
    """

    MAXIMIZE: bool = False
    DESCRIPTION = MultilingualString(
        en=(
            "TER (Translation Edit Rate) measures the number of edits "
            "needed to change a system output into one of the references."
        ),
        es=(
            "TER (Translation Edit Rate) mide el número de ediciones "
            "necesarias para transformar la salida del sistema "
            "en una de las referencias."
        ),
        pt=(
            "TER (Translation Edit Rate) mede o número de edições "
            "necessárias para transformar a saída do sistema "
            "em uma das referências."
        ),
        de=(
            "TER (Translation Edit Rate) misst die Anzahl der Bearbeitungen, "
            "die erforderlich sind, um eine Systemausgabe in eine der Referenzen "
            "umzuwandeln."
        ),
        zh="TER（翻译编辑率）衡量将系统输出转换为参考译文之一所需的编辑次数。",
    )

    @staticmethod
    def score(
        source_sentences: "DashAIDataset",
        target_sentences: "np.ndarray",
    ) -> float:
        """Calculate the TER score between source and target sentences.

        Parameters
        ----------
        source_sentences : DashAIDataset
            Sentences in the original language.
        target_sentences : ndarray
            Sentences in the target language.

        Returns
        -------
        float
            The calculated score.
        """
        from torchmetrics.text.ter import TranslationEditRate

        ter_metric = TranslationEditRate()
        source_sentences, target_sentences = prepare_to_metric(
            source_sentences, target_sentences
        )
        return (
            ter_metric(
                target_sentences,
                source_sentences,
            )
            .numpy()
            .item()
        )
