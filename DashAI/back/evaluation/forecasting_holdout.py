"""Holdout evaluation for models that forecast a series from its own history."""

from DashAI.back.core.enums.metrics import SplitEnum
from DashAI.back.core.utils import MultilingualString
from DashAI.back.evaluation.holdout import SinglePartitionEvaluationStrategy


class ForecastingHoldoutEvaluationStrategy(SinglePartitionEvaluationStrategy):
    """Holdout evaluation that records no in-sample metrics.

    One thing the ordinary holdout strategy assumes is wrong for a forecaster,
    and it is a decision about evaluation rather than about any model.

    **The training partition is not scored.** Scoring it would mean asking the
    model about dates it was fitted on. That is an in-sample fit statistic,
    which is a real diagnostic but is not comparable with a forecast made
    several steps out; showing the two side by side in one results table
    invites exactly that comparison. Only validation and test are recorded.

    **The kept model is fitted on the training partition alone**, like every
    other holdout run, and nothing is fed to it afterwards. Two approaches that
    would have changed that were tried and dropped, both because they hand the
    model data from a partition it was meant to be held out from:

        refitting through validation before scoring test, which overwrote the
        fit the validation metrics came from, so the saved model could not
        reproduce its own results table;

        advancing the model through the observed validation rows at predict
        time, which re-estimates nothing but still lets a held out partition
        reach the model, which no other task in DashAI does.

    So the two columns describe different horizons, and deliberately:

        validation metrics  <- forecasting 1..len(val) past the fit
        test metrics        <- forecasting len(val)+1..len(val)+len(test),
                               its own forecasts standing in for validation

    The test column is therefore the harder question, not the same one further
    along. Comparing like with like over a chosen horizon is what
    ``RollingOriginSplitter`` is for, since its ``horizon`` says outright how
    many steps ahead each refit is scored on.

    Hyperparameter search is untouched. Its trials are scored on validation, so
    they must not be fitted on it.
    """

    DESCRIPTION = MultilingualString(
        en=(
            "Cuts the series once, in time order: the model trains on the "
            "earliest rows and is scored on the ones that come after. The "
            "training partition is not scored, since a forecaster asked about "
            "dates it was fitted on reports a fit, not a forecast."
        ),
        es=(
            "Corta la serie una sola vez, en orden temporal: el modelo entrena "
            "con las filas mas antiguas y se evalua con las que vienen despues. "
            "La particion de entrenamiento no se evalua, porque preguntarle a un "
            "pronosticador por fechas con las que fue ajustado da un ajuste, no "
            "un pronostico."
        ),
        pt=(
            "Corta a serie uma unica vez, em ordem temporal: o modelo treina nas "
            "linhas mais antigas e e avaliado nas que vem depois. A particao de "
            "treino nao e avaliada, porque perguntar a um previsor sobre datas "
            "em que ele foi ajustado da um ajuste, nao uma previsao."
        ),
        de=(
            "Teilt die Zeitreihe ein einziges Mal in zeitlicher Reihenfolge: Das "
            "Modell trainiert auf den fruehesten Zeilen und wird auf den "
            "folgenden bewertet. Die Trainingspartition wird nicht bewertet, "
            "denn ein Prognosemodell, das nach Daten seiner eigenen Anpassung "
            "gefragt wird, liefert eine Anpassung und keine Prognose."
        ),
        zh=(
            "按时间顺序只切分序列"
            "一次：模型在最早的行"
            "上训练，并在其后的行"
            "上评分。训练部分不参"
            "与评分，因为让预测模"
            "型回答它自己拟合过的"
            "日期，得到的是拟合而"
            "不是预测。"
        ),
    )

    COMPATIBLE_COMPONENTS = ["ForecastingTask"]
    SCORED_SPLITS: tuple = (SplitEnum.VALIDATION, SplitEnum.TEST)
