import evaluate

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.metrics.translation_metric import TranslationMetric, prepare_to_metric


class Ter(TranslationMetric):
    """
    Ter metric to translation tasks.
    """

    @staticmethod
    def score(source_sentences: DashAIDataset, target_sentences: list):
        """Calculates the ter score between sentences in their source language
         and in the target language.

        Parameters
        ----------
        source_sentences : DashAIDataset
            sentences in the original language.
        target_sentences : list
            sentences in the target language.

        Returns
        -------
        float
            Ter score between sentences in their source language
         and in the target language.
        """
        metric = evaluate.load("ter")
        source_sentences, target_sentences = prepare_to_metric(
            source_sentences, target_sentences
        )
        return metric.compute(
            references=source_sentences, predictions=target_sentences
        )["score"]
