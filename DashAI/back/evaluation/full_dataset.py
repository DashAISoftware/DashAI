"""Full dataset evaluation: no partitions, fitted and scored once on every row."""

from DashAI.back.core.enums.metrics import SplitEnum
from DashAI.back.core.utils import MultilingualString
from DashAI.back.evaluation.base_evaluation_strategy import BaseEvaluationStrategy


class FullDatasetEvaluationStrategy(BaseEvaluationStrategy):
    """Fit the model once on every row and score it on those same rows.

    For a task with no target, such as clustering, nothing can be held out:
    there is no y_true to compare a prediction against, and the metrics are
    internal ones computed from the features and the labels the model assigned
    them. So the dataset is not carved at all, and the run records a single
    ``FULL`` score per metric.

    A run carved this way is prepared by ``PrepareWithoutTargetUnit``, fitted
    by ``FitWithoutTargetUnit`` and scored by ``ScoreClustersUnit``. It takes no
    splitter and no hyperparameter search, since a search needs a held-out
    partition to be measured on.

    Only offered for tasks without a target. The session API enforces the
    pairing, which is what lets a run of this kind assume there is no target.
    """

    KIND: str = "full"
    SCORED_SPLITS: tuple = (SplitEnum.FULL,)

    DESCRIPTION = MultilingualString(
        en=(
            "The model is fitted once on the whole dataset and scored on those "
            "same rows. Nothing is held out, because a task without a target "
            "has nothing to compare predictions against."
        ),
        es=(
            "El modelo se ajusta una vez con el conjunto completo y se evalua "
            "con esas mismas filas. No se reserva nada, porque una tarea sin "
            "objetivo no tiene con que comparar las predicciones."
        ),
        pt=(
            "O modelo e ajustado uma vez com o conjunto completo e avaliado "
            "nessas mesmas linhas. Nada e reservado, porque uma tarefa sem alvo "
            "nao tem com o que comparar as previsoes."
        ),
        de=(
            "Das Modell wird einmal auf dem gesamten Datensatz angepasst und auf "
            "denselben Zeilen bewertet. Nichts wird zurueckgehalten, denn eine "
            "Aufgabe ohne Zielspalte hat nichts, womit Vorhersagen verglichen "
            "werden koennten."
        ),
        zh=(
            "模型在整个数据集上拟合一次，"
            "并在同样的行上评分。"
            "不保留任何数据，因为没有目标列的任务"
            "没有可与预测比较的对象。"
        ),
    )

    COMPATIBLE_COMPONENTS = ["ClusteringTask"]
