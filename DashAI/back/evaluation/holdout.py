"""Holdout evaluation: one split into three partitions, scored once."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.evaluation.base_evaluation_strategy import BaseEvaluationStrategy


class SinglePartitionEvaluationStrategy(BaseEvaluationStrategy):
    """Split once into train, validation and test.

    The training set fits the model, the validation set is what a
    hyperparameter search is measured on, and the test set is scored once at
    the end. A run carved this way is prepared by ``PrepareAndSplitUnit`` and
    fitted by ``FitModelUnit``.
    """

    KIND: str = "holdout"


class HoldoutEvaluationStrategy(SinglePartitionEvaluationStrategy):
    """Split once into train, validation and test, and score all three.

    The ordinary holdout evaluation. Not offered for ``ForecastingTask``:
    scoring the training partition of a forecaster means predicting on dates
    it was fitted on, which is a fit statistic rather than a forecast and does
    not belong in the same results table as one.
    ``ForecastingHoldoutEvaluationStrategy`` records validation and test only.

    The kept model is fitted on the training partition alone in both, so it is
    the model the recorded metrics describe. The validation partition is handed
    to the fit, which models use to watch training and stop early -- being
    given it to watch is not the same as being fitted on it.
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Holdout cuts the dataset once. The model trains on one part and is "
            "scored on rows it never saw. Fast, but the score depends on which "
            "rows happened to land where."
        ),
        es=(
            "Holdout corta el conjunto una sola vez. El modelo entrena con una "
            "parte y se evalua con filas que nunca vio. Es rapido, pero el "
            "resultado depende de que filas cayeron en cada parte."
        ),
        pt=(
            "O holdout corta o conjunto uma unica vez. O modelo treina em uma "
            "parte e e avaliado em linhas que nunca viu. E rapido, mas o "
            "resultado depende de quais linhas cairam em cada parte."
        ),
        de=(
            "Holdout teilt den Datensatz ein einziges Mal. Das Modell trainiert "
            "auf einem Teil und wird auf Zeilen bewertet, die es nie gesehen "
            "hat. Schnell, aber das Ergebnis haengt davon ab, welche Zeilen wo "
            "gelandet sind."
        ),
        zh=(
            "留出法只切分数据集一次。"
            "模型在一部分上训练，"
            "并在从未见过的行上评分。"
            "速度快，但结果取决于"
            "哪些行落在了哪一部分。"
        ),
    )

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "ImageClassificationTask",
        "TranslationTask",
        "RegressionTask",
    ]
