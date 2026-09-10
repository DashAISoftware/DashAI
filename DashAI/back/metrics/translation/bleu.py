"""BLEU (bilingual evaluation understudy) metric implementation for DashAI."""

from typing import TYPE_CHECKING

from DashAI.back.core.utils import MultilingualString
from DashAI.back.metrics.translation_metric import TranslationMetric, prepare_to_metric

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class Bleu(TranslationMetric):
    """A class for calculating BLEU scores between source and target sentences.

    BLEU (bilingual evaluation understudy) is an algorithm for evaluating the quality
    of text which has been machine-translated from one natural language to another.

    References
    ----------
    - [1] https://en.wikipedia.org/wiki/BLEU
    - [2] https://lightning.ai/docs/torchmetrics/stable/text/bleu_score.html
    """

    MAXIMIZE: bool = True
    DESCRIPTION = MultilingualString(
        en=(
            "BLEU (bilingual evaluation understudy) "
            "measures similarity between generated and reference text "
            "based on n-gram overlap."
        ),
        es=(
            "BLEU (bilingual evaluation understudy) "
            "mide la similitud entre el texto generado y el de referencia "
            "basándose en la superposición de n-gramas."
        ),
        pt=(
            "BLEU (bilingual evaluation understudy) "
            "mede a similaridade entre o texto gerado e o de referência "
            "com base na sobreposição de n-gramas."
        ),
        de=(
            "BLEU (bilingual evaluation understudy) "
            "misst die Ähnlichkeit zwischen generiertem und Referenztext "
            "basierend auf N-Gramm-Überlappung."
        ),
        zh="BLEU（双语评估替代）基于 n-gram 重叠度衡量生成文本与参考文本的相似度。",
    )

    @staticmethod
    def score(
        source_sentences: "DashAIDataset",
        target_sentences: "np.ndarray",
    ) -> float:
        """Calculate the BLEU score between source and target sentences.

        Parameters
        ----------
        source_sentences : DashAIDataset
            Sentences in the original language.
        target_sentences : ndarray
            Sentences in the target language.

        Returns
        -------
        float
            The calculated BLEU score ranging between 0 and 1.
        """
        from torchmetrics.text.bleu import BLEUScore

        bleu_metric = BLEUScore()
        source_sentences, target_sentences = prepare_to_metric(
            source_sentences, target_sentences
        )
        return (
            bleu_metric(
                target_sentences,
                [[reference] for reference in source_sentences],
            )
            .numpy()
            .item()
        )
