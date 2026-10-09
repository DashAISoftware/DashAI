"""Cross-validation: several train and validation pairs, scored per fold."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.evaluation.base_evaluation_strategy import BaseEvaluationStrategy


class FoldEvaluationStrategy(BaseEvaluationStrategy):
    """Carve the dataset into folds and score each of them.

    Each fold is split into a train and a validation partition, so the scores
    obtained by resampling are validation estimates. When the session reserved
    rows, the kept model is fitted on everything the folds could use and scored
    once against those reserved rows -- the only data no fold and no trial ever
    saw.

    A run carved this way is prepared by ``PrepareAndFoldUnit`` and fitted by
    ``FitModelOverFoldsUnit``, or by ``FitModelOverNestedFoldsUnit`` when the
    run also asks for a search inside each fold.

    The levels a fold run records, which is why the enum has more of them than
    a holdout run needs: ``FOLD`` per fold, aggregated to ``LAST`` with a
    standard deviation; ``TRIAL`` once per trial of a search, holding the mean
    over that trial's folds; and, for a nested run, ``OUTER_FOLD`` aggregated
    to ``LAST_OUTER``, kept apart because it answers a different question --
    how the procedure does rather than how this model does.
    """

    KIND: str = "cv"


class CrossValidationEvaluationStrategy(FoldEvaluationStrategy):
    """Score a model across folds, recording train and validation for each.

    The ordinary cross-validation evaluation. Not offered for
    ``ForecastingTask``, whose folds have no in-sample score to report;
    ``ForecastingCrossValidationEvaluationStrategy`` handles that.
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Cross validation cuts the dataset into folds. Each fold takes a "
            "turn as the validation set while the model trains on the rest, and "
            "the scores are averaged, so the result leans less on any single "
            "cut."
        ),
        es=(
            "La validacion cruzada corta el conjunto en pliegues. Cada pliegue "
            "actua por turno como conjunto de validacion mientras el modelo "
            "entrena con el resto, y los puntajes se promedian, asi el resultado "
            "depende menos de un solo corte."
        ),
        pt=(
            "A validacao cruzada corta o conjunto em dobras. Cada dobra serve "
            "por vez como conjunto de validacao enquanto o modelo treina no "
            "resto, e as pontuacoes sao promediadas, entao o resultado depende "
            "menos de um unico corte."
        ),
        de=(
            "Die Kreuzvalidierung teilt den Datensatz in Folds. Jeder Fold dient "
            "reihum als Validierungsmenge, waehrend das Modell auf dem Rest "
            "trainiert, und die Ergebnisse werden gemittelt, sodass das Resultat "
            "weniger von einer einzelnen Teilung abhaengt."
        ),
        zh=(
            "交叉验证把数据集切成"
            "若干折。每一折轮流作为"
            "验证集，模型在其余部分"
            "上训练，最后取平均分，"
            "因此结果不那么依赖某"
            "一次切分。"
        ),
    )

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "ImageClassificationTask",
        "TranslationTask",
        "RegressionTask",
    ]
