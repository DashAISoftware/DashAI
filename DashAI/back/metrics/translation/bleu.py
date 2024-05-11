"""BLEU (bilingual evaluation understudy) metric implementation for DashAI."""

import evaluate
import numpy as np

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.metrics.translation_metric import TranslationMetric, prepare_to_metric


class Bleu(TranslationMetric):
    """A class for calculating BLEU scores between source and target sentences.

    BLEU (bilingual evaluation understudy) is an algorithm for evaluating the quality
    of text which has been machine-translated from one natural language to another.

    References
    ----------
    [1] https://en.wikipedia.org/wiki/BLEU
    """

    @staticmethod
    def score(source_sentences: DashAIDataset, target_sentences: np.ndarray):
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
        metric = evaluate.load("bleu")
        source_sentences, target_sentences = prepare_to_metric(
            source_sentences, target_sentences
        )
        return metric.compute(
            references=source_sentences, predictions=target_sentences
        )["bleu"]
