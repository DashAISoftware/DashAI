"""TER (Translation Edit Rate) metric implementation for DashAI."""
import evaluate

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.metrics.translation_metric import TranslationMetric, prepare_to_metric


class Ter(TranslationMetric):
    """A class for calculating TER scores between source and target sentences.

    TER (Translation Edit Rate, also called Translation Error Rate) is a metric
    to quantify the edit operations requiered to match a reference translation.

    References
    ----------
    [1] https://huggingface.co/spaces/evaluate-metric/ter
    """

    @staticmethod
    def score(source_sentences: DashAIDataset, target_sentences: list):
        """Calculate the TER score between source and target sentences.

        Parameters
        ----------
        source_sentences : DashAIDataset
            Sentences in the original language.
        target_sentences : list
            Sentences in the target language.

        Returns
        -------
        float
            The calculated score.
        """
        metric = evaluate.load("ter")
        source_sentences, target_sentences = prepare_to_metric(
            source_sentences, target_sentences
        )
        return metric.compute(
            references=source_sentences, predictions=target_sentences
        )["score"]
