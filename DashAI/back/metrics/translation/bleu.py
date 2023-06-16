import evaluate

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.metrics.translation_metric import TranslationMetric


class Bleu(TranslationMetric):
    """
    Bleu metric to translation tasks
    """

    @staticmethod
    def score(source_sentences: DashAIDataset, target_sentences: list):
        """Calculates the Bleu score between sentences in their source language
         and in the target language

        Parameters
        ----------
        source_sentences : DashAIDataset
            sentences in the original language
        target_sentences : list
            sentences in the target language

        Returns
        -------
        float
            Bleu score between sentences in their source language
         and in the target language
        """
        metric = evaluate.load("bleu")
        output_column = source_sentences.outputs_columns[0]
        refs = [[example[output_column]] for example in source_sentences]
        return metric.compute(predictions=target_sentences, references=refs)["bleu"]
