import logging
from typing import TYPE_CHECKING

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.optimizers.base_optimizer import BaseOptimizer

if TYPE_CHECKING:
    import optuna

logger = logging.getLogger(__name__)

UNFITTABLE_TRIAL_ERRORS = (ValueError, ArithmeticError)


class OptunaSchema(BaseSchema):
    n_trials: schema_field(
        int_field(gt=0),
        placeholder=10,
        description=MultilingualString(
            en=(
                "The quantity of trials per study. It must be of type positive integer."
            ),
            es=("La cantidad de pruebas por estudio. Debe ser un entero positivo."),
            pt=("A quantidade de tentativas por estudo. Deve ser um inteiro positivo."),
            de=(
                "Die Anzahl der Versuche pro Studie. Muss eine positive ganze Zahl "
                "sein."
            ),
            zh="每次研究的试验次数，必须为正整数。",
        ),
        alias=MultilingualString(
            en="N trials",
            es="N pruebas",
            pt="N tentativas",
            de="N Versuche",
            zh="试验次数",
        ),
    )  # type: ignore
    sampler: schema_field(
        enum_field(
            enum=[
                "TPESampler",
                "CmaEsSampler",
                "GPSampler",
                "NSGAIISampler",
                "QMCSampler",
                "RandomSampler",
            ]
        ),
        placeholder="TPESampler",
        description=MultilingualString(
            en=(
                "The sampler algorithm to use for hyperparameter optimization. "
                "Different samplers use different strategies for exploring the "
                "hyperparameter space."
            ),
            es=(
                "El algoritmo de muestreo a usar para la optimización de "
                "hiperparámetros. Diferentes muestreadores usan diferentes "
                "estrategias para explorar el espacio de hiperparámetros."
            ),
            pt=(
                "O algoritmo de amostragem a usar para a otimização de "
                "hiperparâmetros. Diferentes amostradores usam diferentes "
                "estratégias para explorar o espaço de hiperparâmetros."
            ),
            de=(
                "Der Abtastalgorithmus für die Hyperparameter-Optimierung. "
                "Verschiedene Abtaster verwenden unterschiedliche Strategien "
                "zur Erkundung des Hyperparameter-Raums."
            ),
            zh=(
                "用于超参数优化的采样算法。不同的采样器使用不同的策略来探索超参数空间。"
            ),
        ),
        alias=MultilingualString(
            en="Sampler",
            es="Muestreador",
            pt="Amostrador",
            de="Abtaster",
            zh="采样器",
        ),
    )  # type: ignore
    pruner: schema_field(
        enum_field(enum=["MedianPruner", "None"]),
        placeholder="None",
        description=MultilingualString(
            en=(
                "The pruner to use for early stopping of unpromising trials. "
                "'MedianPruner' stops trials below the median. 'None' disables pruning."
            ),
            es=(
                "El podador a usar para detener tempranamente pruebas poco "
                "prometedoras. 'MedianPruner' detiene pruebas bajo la mediana. "
                "'None' desactiva la poda."
            ),
            pt=(
                "O podador a usar para parada antecipada de tentativas pouco "
                "promissoras. 'MedianPruner' para tentativas abaixo da mediana. "
                "'None' desativa a poda."
            ),
            de=(
                "Der Pruner für den vorzeitigen Abbruch aussichtsloser Versuche. "
                "'MedianPruner' stoppt Versuche unterhalb des Mittelwerts. "
                "'None' deaktiviert das Pruning."
            ),
            zh=(
                "用于提前停止无希望试验的剪枝器。"
                "'MedianPruner' 停止低于中位数的试验。'None' 禁用剪枝。"
            ),
        ),
        alias=MultilingualString(
            en="Pruner",
            es="Podador",
            pt="Podador",
            de="Pruner",
            zh="剪枝器",
        ),
    )  # type: ignore


def _build_pruner(name: "str | None") -> "optuna.pruners.BasePruner":
    """Resolve a pruner name from the schema into an Optuna pruner instance.

    ``create_study`` accepts any object for ``pruner`` without validating it, so
    passing the raw schema string silently produces a study whose pruner is a
    ``str``. The failure only surfaces later, as
    ``AttributeError: 'str' object has no attribute 'prune'``.

    ``"None"`` (the string the schema sends when pruning is disabled) maps to
    ``NopPruner``, Optuna's explicit no-op.

    Only pruners that Optuna can build with default arguments are supported.
    ``PatientPruner``, ``PercentilePruner`` and ``ThresholdPruner`` need
    configuration (a wrapped pruner, a percentile, a threshold), so exposing them
    means adding those fields to the schema first.
    """
    import optuna

    if name in (None, "", "None"):
        return optuna.pruners.NopPruner()

    pruner_class = getattr(optuna.pruners, name, None)
    if pruner_class is None:
        raise ValueError(f"Unknown pruner '{name}'. Available: {_no_arg_pruners()}")
    try:
        return pruner_class()
    except TypeError as exc:
        raise ValueError(
            f"Pruner '{name}' requires configuration and cannot be built from its "
            f"name alone. Available: {_no_arg_pruners()}"
        ) from exc


def _no_arg_pruners() -> "list[str]":
    """Pruner names Optuna can instantiate with no arguments."""
    import optuna

    names = []
    for name in dir(optuna.pruners):
        if not name.endswith("Pruner") or name == "BasePruner":
            continue
        try:
            getattr(optuna.pruners, name)()
        except TypeError:
            continue
        names.append(name)
    return sorted(names)


def _report_epoch(trial, metric):
    """Build the per-epoch callback handed to the model during a trial.

    Optuna prunes by being told how a trial is doing while it still runs:
    `trial.report(value, step)` feeds the pruner, `trial.should_prune()` asks it
    for a verdict, and raising `TrialPruned` is how a trial is abandoned.

    Nothing between here and `study.optimize` catches that exception, so it
    reaches Optuna and the trial is recorded as pruned rather than failed.

    A missing metric is not an error: `calculate_metrics` skips any metric that
    returns a non-finite value, so a given epoch may legitimately have nothing to
    report. The trial simply continues unpruned.
    """
    import optuna

    def report(results, step):
        value = results.get(metric.__name__)
        if value is None:
            return
        trial.report(value, step)
        if trial.should_prune():
            raise optuna.TrialPruned

    return report


class OptunaOptimizer(BaseOptimizer):
    DISPLAY_NAME: str = MultilingualString(
        en="Optuna Optimizer",
        es="Optimizador Optuna",
        pt="Otimizador Optuna",
        de="Optuna-Optimierer",
        zh="Optuna 优化器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Hyperparameter optimization using Optuna library.",
        es="Optimización de hiperparámetros usando la librería Optuna.",
        pt="Otimização de hiperparâmetros usando a biblioteca Optuna.",
        de="Hyperparameter-Optimierung mit der Optuna-Bibliothek.",
        zh="使用 Optuna 库进行超参数优化。",
    )
    COLOR: str = "#E91E63"
    SCHEMA = OptunaSchema

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "TranslationTask",
        "RegressionTask",
        "ForecastingTask",
    ]

    def __init__(self, n_trials=None, sampler=None, pruner=None):
        self.n_trials = n_trials
        self.sampler = sampler
        self.pruner = pruner

    def optimize(
        self, model, input_dataset, output_dataset, parameters, metric, strategy
    ):
        """
        Run hyperparameter optimization.

        Parameters
        ----------
        model : object
            Model instance to optimize.
        input_dataset : dict
            Dataset splits keyed by "train" and "validation".
        output_dataset : dict
            Label splits keyed by "train" and "validation".
        parameters : list
            Tuples of (obj, key, bounds, dtype) for each hyperparameter.
        metric : dict
            Dict with keys "class" (metric instance) and "metadata".
        strategy : callable
            Function that trains the model and returns a score based on the metric.
            Depends on the specific evaluation strategy used.
        """
        import optuna

        sampler = getattr(optuna.samplers, self.sampler)
        pruner = _build_pruner(self.pruner)

        self.model = model
        self.input_dataset = input_dataset
        self.output_dataset = output_dataset
        self.parameters = parameters
        direction = "maximize" if metric["metadata"]["maximize"] else "minimize"
        study = optuna.create_study(
            direction=direction, sampler=sampler(), pruner=pruner
        )

        self.metric = metric["class"]

        failures = []

        def objective(trial):
            # Set value for each hyperparameter and for each model
            # (either self or submodels nested inside)
            for obj, key, bounds, dtype in self.parameters:
                if dtype == "number":
                    value = trial.suggest_float(key, bounds[0], bounds[1], log=False)
                elif dtype == "integer":
                    value = trial.suggest_int(key, bounds[0], bounds[1], log=False)
                else:
                    raise ValueError(f"Unsupported parameter type for {key} : {dtype}")
                setattr(obj, key, value)

            # The reporter is installed around the whole strategy call: any
            # epoch-level validation metric computed while the strategy trains
            # feeds the pruner, and `TrialPruned` raised from inside it reaches
            # `study.optimize` untouched, so the trial is recorded as pruned.
            #
            # Whether it ever fires depends on the strategy. It does when the
            # model is trained with validation data — the epoch loops guard
            # `calculate_metrics(split=VALIDATION, level=EPOCH)` behind
            # `if x_validation is not None` — and a strategy that trains
            # without validation data never triggers it, so that trial simply
            # runs to completion unpruned.
            self.model._epoch_reporter = _report_epoch(trial, self.metric)
            try:
                # Train the model and get the score from the strategy
                score = strategy(
                    self.model, self.input_dataset, self.output_dataset, self.metric
                )
            except UNFITTABLE_TRIAL_ERRORS as e:
                failures.append(e)
                raise
            finally:
                # Cleared even when the trial is pruned: the model instance is
                # reused across trials and by the final refit afterwards.
                self.model._epoch_reporter = None

            return score

        study.optimize(objective, n_trials=self.n_trials, catch=UNFITTABLE_TRIAL_ERRORS)

        completed = study.get_trials(
            deepcopy=False, states=(optuna.trial.TrialState.COMPLETE,)
        )
        if not completed:
            raise ValueError(
                f"Every one of the {len(study.trials)} trials failed: the model "
                f"could not be fitted with any combination the search drew from "
                f"the ranges given. Narrow them and try again. The last trial "
                f"failed with: {failures[-1]}"
                if failures
                else (
                    f"Every one of the {len(study.trials)} trials failed and none "
                    f"produced a score."
                )
            )
        if failures:
            logger.warning(
                "%d of %d hyperparameter trials could not be fitted and were "
                "skipped. The last one failed with: %s",
                len(failures),
                len(study.trials),
                failures[-1],
            )

        # Write the best values back onto the objects that actually declare them.
        # `self.parameters` holds (owner, key, bounds, dtype) tuples built by
        # ModelFactory, where `owner` may be a nested sub-component rather than the
        # top-level model. Assigning to the wrapper instead leaves the sub-component
        # holding whatever the last trial set, so the model that gets retrained and
        # serialized is the last one tried, not the best one. This mirrors what
        # `objective` already does above.
        best_params = study.best_params
        for obj, key, _bounds, _dtype in self.parameters:
            if key in best_params:
                setattr(obj, key, best_params[key])

        self.study = study

    def get_model(self):
        return self.model

    def get_trials_values(self):
        import optuna

        trials = []
        for trial in self.study.trials:
            if trial.state == optuna.trial.TrialState.COMPLETE:
                trials.append({"params": trial.params, "value": trial.value})
        return trials

    def get_best_params(self):
        """Return the best parameters found during optimization."""
        return self.study.best_params
