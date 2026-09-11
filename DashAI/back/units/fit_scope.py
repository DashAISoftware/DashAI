"""Shared body of the units that fit a model, with or without a search.

``FitModelUnit`` fits one set of partitions; ``FitModelOverFoldsUnit`` fits a
list of them. Everything around the fit is the same for both -- resolving the
optimizer and the goal metric, running the search, checking that the optimizer
gave back the model it was handed, recording the best parameters, and writing
the plots the search produces -- and it is exactly the sort of thing that ends
up written twice and then drifting.

What differs is only the objective the search measures and what happens once it
is over, so those stay in the units.

Named ``ModelFitScopeMixin`` rather than ``BaseSomething``: the registry derives
a component's type by walking its ``__mro__`` for a class whose name contains
"Base" and that declares ``TYPE``, and demands exactly one. A shared parent
called ``Base*`` would be a second candidate and would break the registration of
every unit that inherited it.
"""

import logging
from typing import TYPE_CHECKING, List, Tuple

from DashAI.back.core.schema_fields import (
    bool_field,
    component_field,
    enum_field,
    list_field,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.job.base_job import JobError

if TYPE_CHECKING:
    from DashAI.back.optimizers.base_optimizer import BaseOptimizer

log = logging.getLogger(__name__)

#: A trial may score the partition it fitted on and the one it is measured
#: against, and nothing else. The test partition is deliberately absent:
#: scoring it once per trial would let the search see it, and a model chosen
#: with the test set in view has no honest score left to report.
TRIAL_SPLITS = ["TRAIN", "VALIDATION"]


def optimizer_field():
    return schema_field(
        component_field(parent="BaseOptimizer"),
        placeholder={"component": "OptunaOptimizer", "params": {}},
        description=MultilingualString(
            en="Optimizer used to search for hyperparameters, along with its own "
            "configuration. Only used when the model declares optimizable "
            "parameters.",
            es="Optimizador usado para buscar hiperparámetros, junto con su propia "
            "configuración. Solo se usa cuando el modelo declara parámetros "
            "optimizables.",
            pt="Otimizador usado para procurar hiperparâmetros, junto com a sua "
            "própria configuração. Só é usado quando o modelo declara parâmetros "
            "otimizáveis.",
            de="Optimierer für die Hyperparametersuche samt seiner eigenen "
            "Konfiguration. Wird nur verwendet, wenn das Modell optimierbare "
            "Parameter deklariert.",
            zh="用于搜索超参数的优化器及其自身配置。仅当模型声明了可优化参数时使用。",
        ),
        alias=MultilingualString(
            en="Optimizer",
            es="Optimizador",
            pt="Otimizador",
            de="Optimierer",
            zh="优化器",
        ),
    )


def goal_metric_field():
    return schema_field(
        string_field(),
        placeholder="Accuracy",
        description=MultilingualString(
            en="Metric the hyperparameter search optimizes.",
            es="Métrica que optimiza la búsqueda de hiperparámetros.",
            pt="Métrica que a procura de hiperparâmetros otimiza.",
            de="Metrik, die die Hyperparametersuche optimiert.",
            zh="超参数搜索所优化的指标。",
        ),
        alias=MultilingualString(
            en="Goal metric",
            es="Métrica objetivo",
            pt="Métrica objetivo",
            de="Zielmetrik",
            zh="目标指标",
        ),
    )


def trial_splits_field():
    return schema_field(
        list_field(enum_field(enum=TRIAL_SPLITS)),
        placeholder=TRIAL_SPLITS,
        description=MultilingualString(
            en="Partitions each trial of the search records a score for. A "
            "partition the model is not meant to be judged on belongs out of "
            "this list even when metrics are configured for it.",
            es="Particiones para las que cada intento de la búsqueda registra "
            "un puntaje. Una partición sobre la que el modelo no debe juzgarse "
            "no va en esta lista aunque tenga métricas configuradas.",
            pt="Partições para as quais cada tentativa da procura regista uma "
            "pontuação. Uma partição sobre a qual o modelo não deve ser julgado "
            "fica fora desta lista mesmo que tenha métricas configuradas.",
            de="Partitionen, für die jeder Versuch der Suche einen Wert "
            "festhält. Eine Partition, nach der das Modell nicht beurteilt "
            "werden soll, gehört nicht in diese Liste, auch wenn Metriken für "
            "sie konfiguriert sind.",
            zh="搜索的每次试验为其记录分数的分区。不应据以评判模型的分区不列入此处，"
            "即使已为其配置了指标。",
        ),
        alias=MultilingualString(
            en="Trial splits",
            es="Particiones por intento",
            pt="Partições por tentativa",
            de="Versuchspartitionen",
            zh="试验分区",
        ),
    )


def validation_during_fit_field():
    return schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en="Whether the validation partition is handed to the model while "
            "fitting. Models use it to watch training and stop early. Turn it "
            "off when the same partition is what the fit will be scored on.",
            es="Si la particion de validacion se entrega al modelo durante el "
            "ajuste. Los modelos la usan para vigilar el entrenamiento y "
            "detenerse antes. Desactivar cuando esa misma particion es sobre "
            "la que se va a evaluar el ajuste.",
            pt="Se a particao de validacao e entregue ao modelo durante o "
            "ajuste. Os modelos usam-na para acompanhar o treino e parar mais "
            "cedo. Desative quando essa mesma particao for aquela sobre a qual "
            "o ajuste sera avaliado.",
            de="Ob die Validierungspartition dem Modell beim Fitten uebergeben "
            "wird. Modelle nutzen sie, um das Training zu beobachten und frueh "
            "abzubrechen. Abschalten, wenn genau diese Partition den Fit "
            "bewerten soll.",
            zh="拟合时是否将验证分区交给模型。",
        ),
        alias=MultilingualString(
            en="Validate while fitting",
            es="Validar durante el ajuste",
            pt="Validar durante o ajuste",
            de="Beim Fitten validieren",
            zh="拟合时验证",
        ),
    )


class ModelFitScopeMixin:
    """Everything around a fit that does not depend on how the data is shaped.

    Takes and returns plain values and never touches the execution context.
    That is not tidiness: the contract audit parses each unit's own source, so
    a ``ctx.require`` moved in here makes a declared key look unread and a
    ``ctx.put`` makes a broken ``PROVIDES`` pass. Reading and publishing stay
    in the units, and so does reading the runtime parameters, which the audit
    checks are used by whoever declares them.
    """

    #: Declared here so a reader can see what state an instance carries; each
    #: unit sets them in its own ``__init__``, because ``BaseUnit.__init__``
    #: comes first in the MRO and does not chain.
    _optimizer = None
    _goal_metric = None

    def _resolve_search(self):
        """Resolve the optimizer and the goal metric, memoized on this unit.

        Kept on the instance rather than in the context on purpose. These are
        this unit's own state, not something it hands to another unit: two
        fitting units sharing a context -- a graph with two training nodes --
        would otherwise overwrite each other's optimizer, and the second one
        would silently run the first one's.
        """
        if self._optimizer is not None:
            return self._optimizer, self._goal_metric

        from kink import di

        component_registry = di["component_registry"]
        goal_metric_name: str = self.config["goal_metric"]
        optimizer_name: str = self.config["optimizer"]["component"]

        try:
            # The whole registry entry, not the class: the optimizer reads
            # metadata["maximize"] from it to pick a direction.
            goal_metric = component_registry[goal_metric_name]
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Metric is not compatible with the Task. {e}",
            ) from e

        try:
            optimizer_class = component_registry[optimizer_name]["class"]
            optimizer: "BaseOptimizer" = optimizer_class(
                **self.config["optimizer"]["params"]
            )
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Error instantiating optimizer {optimizer_name}, {e}",
            ) from e

        self._goal_metric = goal_metric
        self._optimizer = optimizer
        return optimizer, goal_metric

    def _will_search(self, optimizable_parameters) -> bool:
        """Whether there is a search to run: something to tune, and a tuner.

        Both halves are needed. A run can name no optimizer at all -- the
        column is a plain string and the wizard leaves it empty when the user
        does not ask for a search -- while the model still declares a parameter
        as optimizable, and that combination has always meant "fit it once with
        the values given". Checking only the parameters turns it into a lookup
        of the empty string in the registry, which fails with a message about
        the metric being incompatible with the task.
        """
        return bool(optimizable_parameters) and bool(
            self.config["optimizer"]["component"]
        )

    def _validate_search(self, optimizable_parameters) -> None:
        """Refuse an impossible search before anything observable happens.

        Handed the value rather than the context: the caller reads it with
        ``ctx.require`` and not ``ctx.get``, because an absent key means the
        model has not been built yet -- a call-order mistake, not "there is
        nothing to optimize". A run with nothing to search skips the checks
        below, so no registry lookup is needed either.
        """
        if not self._will_search(optimizable_parameters):
            return

        self._resolve_search()

    def _fit(self, model, x, y, with_validation: bool) -> None:
        """Fit the model on the training partition of the data it was given.

        Whether the validation partition goes with it is a policy and not a
        shape: a model uses it to watch the fit and stop early, which is what
        an ordinary holdout run wants, and which is exactly wrong when that
        same partition is what the fit will be scored on -- a fold is scored on
        the rows it held back, so handing them over would be measuring the fit
        on data it was allowed to watch.

        The key may also simply not be there. The trailing entry a fold
        splitter produces holds the pooled rows and the reserved ones and has
        no validation partition at all, so there is nothing to hand over even
        where the policy would allow it.
        """
        if with_validation and "validation" in x:
            model.train(x["train"], y["train"], x["validation"], y["validation"])
        else:
            model.train(x["train"], y["train"])

    def _search(
        self,
        model,
        x,
        y,
        optimizable_parameters,
        factory,
        old_parameters,
        run_id,
        artifact_prefix,
        objective,
    ) -> Tuple[object, dict, List[str]]:
        """Run the hyperparameter search and report what it produced.

        Parameters
        ----------
        model : BaseModel
            The instance the search sets its parameters on.
        x, y : object
            Whatever the objective knows how to fit and score -- one set of
            partitions, or a list of them. The optimizer passes it through
            without looking at it, which is what lets one search serve both.
        optimizable_parameters : list
            The search space, as ModelFactory built it.
        factory : ModelFactory
            Used to write the values found back into the parameter tree.
        old_parameters : dict
            The tree they are written into. The caller is expected to hand over
            a copy it owns; this mutates nothing else.
        run_id, artifact_prefix : object
            What the plots are named after.
        objective : callable
            ``(model, x, y, metric) -> float``: what the search measures.

        Returns
        -------
        tuple
            The fitted model, the parameter tree with the best values in it,
            and the paths of the plots the search produced.
        """
        import os
        import pickle

        from kink import di

        from DashAI.back.core.artifacts import normalize_artifacts

        # Memoized: validate() resolved these already, and resolving again
        # here would be the same lookup.
        optimizer, goal_metric = self._resolve_search()

        optimizer.optimize(model, x, y, optimizable_parameters, goal_metric, objective)
        model = optimizer.get_model()
        best_params = optimizer.get_best_params()

        self._assert_model_keeps_its_runtime_state(model)

        best_parameters = factory.update_parameters(old_parameters, best_params)

        config = di["config"]
        plot_paths: List[str] = []
        trials = optimizer.get_trials_values()
        plot_filenames, plots = optimizer.create_plots(
            trials,
            run_id,
            n_params=len(optimizable_parameters),
            goal_metric=goal_metric,
            artifact_prefix=artifact_prefix,
        )
        normalized_plots = normalize_artifacts(plots)
        for filename, plot in zip(plot_filenames, normalized_plots, strict=False):
            plot_path = os.path.join(config["RUNS_PATH"], filename)
            with open(plot_path, "wb") as file:
                pickle.dump(plot, file)
                plot_paths.append(plot_path)

        return model, best_parameters, plot_paths

    @staticmethod
    def _assert_model_keeps_its_runtime_state(model) -> None:
        """Fail loudly if the optimizer returned a model that cannot be scored.

        ``ModelFactory`` attaches the metric classes to the model instance and
        whoever fits it points it at its data, and optimizers are expected to
        return that same instance. If one ever returns a fresh object instead,
        scoring it finds nothing to score and the caller ends up with no
        metrics rather than an error.

        The check is on the data, not on the run id. Keying it to ``run_id``
        made it a no-op for every caller that has no run -- a pipeline, where
        ``run_id`` is always None -- which is exactly the caller with no other
        signal that anything went wrong: it would finish with an empty metrics
        artifact. What both callers need is the same, so this asks for that
        instead.
        """
        if getattr(model, "x_data", None) is None:
            raise JobError(
                "The optimizer returned a model detached from its data: metrics "
                "could not be computed for it. Optimizers must return the same "
                "model instance they received."
            )
