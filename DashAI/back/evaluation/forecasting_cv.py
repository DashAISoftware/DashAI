"""Cross-validation for models that forecast a series from its own history."""

from DashAI.back.core.enums.metrics import SplitEnum
from DashAI.back.core.utils import MultilingualString
from DashAI.back.evaluation.cv import FoldEvaluationStrategy


class ForecastingCrossValidationEvaluationStrategy(FoldEvaluationStrategy):
    """Rolling origin cross-validation that records no in-sample metrics.

    Only one thing separates this from the ordinary cross-validation
    strategy: the training partition of a fold is not scored. Scoring it would
    mean asking the model about dates it was fitted on, which is a fit
    statistic rather than a forecast and is not comparable with the validation
    score of the same fold.

    Nothing else needs to change, and that is worth stating because it was not
    obvious. Each fold already trains on everything before its own validation
    window, and the final refit already uses the whole pool of rows outside
    the reserved tail, so this strategy never had the horizon problem that
    holdout did. Pair it with ``RollingOriginSplitter``, whose folds walk the
    origin forward through time.
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Walks the origin forward through the series. Each fold trains on "
            "everything up to a point and is scored on the rows just after it, "
            "then the origin moves on and the model is refitted with more "
            "history. Training partitions are not scored."
        ),
        es=(
            "Avanza el origen a lo largo de la serie. Cada pliegue entrena con "
            "todo lo anterior a un punto y se evalua con las filas justo "
            "posteriores; luego el origen avanza y el modelo se reajusta con mas "
            "historia. Las particiones de entrenamiento no se evaluan."
        ),
        pt=(
            "Avanca a origem ao longo da serie. Cada dobra treina com tudo o que "
            "vem antes de um ponto e e avaliada nas linhas logo depois; entao a "
            "origem avanca e o modelo e reajustado com mais historico. As "
            "particoes de treino nao sao avaliadas."
        ),
        de=(
            "Schiebt den Ursprung durch die Zeitreihe. Jeder Fold trainiert auf "
            "allem bis zu einem Punkt und wird auf den unmittelbar folgenden "
            "Zeilen bewertet, dann rueckt der Ursprung weiter und das Modell "
            "wird mit mehr Historie neu angepasst. Trainingspartitionen werden "
            "nicht bewertet."
        ),
        zh=(
            "让起点沿序列向前推进。"
            "每一折用某个时点之前的"
            "全部数据训练，并在紧随"
            "其后的行上评分；随后起"
            "点前移，模型用更多历史"
            "重新拟合。训练部分不参"
            "与评分。"
        ),
    )

    COMPATIBLE_COMPONENTS = ["ForecastingTask"]
    SCORED_SPLITS: tuple = (SplitEnum.VALIDATION, SplitEnum.TEST)
