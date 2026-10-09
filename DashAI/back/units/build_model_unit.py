"""Unit that instantiates a model with its parameters, data and metrics."""

import logging
from typing import TYPE_CHECKING, List

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    list_field,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.nested import missing_downloads
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

if TYPE_CHECKING:
    from DashAI.back.metrics.base_metric import BaseMetric
    from DashAI.back.models.base_model import BaseModel

log = logging.getLogger(__name__)


def _metrics_field(alias: MultilingualString, description: MultilingualString):
    return schema_field(
        list_field(string_field()),
        placeholder=[],
        description=description,
        alias=alias,
    )


class BuildModelSchema(BaseSchema):
    model: schema_field(
        component_field(parent="BaseModel"),
        placeholder={"component": "SVC", "params": {}},
        description=MultilingualString(
            en="Model to instantiate, along with its own configuration.",
            es="Modelo a instanciar, junto con su propia configuración.",
            pt="Modelo a instanciar, junto com a sua própria configuração.",
            de="Zu instanziierendes Modell samt seiner eigenen Konfiguration.",
            zh="要实例化的模型及其自身配置。",
        ),
        alias=MultilingualString(
            en="Model", es="Modelo", pt="Modelo", de="Modell", zh="模型"
        ),
    )  # type: ignore
    train_metrics: _metrics_field(
        alias=MultilingualString(
            en="Train metrics",
            es="Métricas de entrenamiento",
            pt="Métricas de treino",
            de="Trainingsmetriken",
            zh="训练指标",
        ),
        description=MultilingualString(
            en="Metrics evaluated on the train split.",
            es="Métricas evaluadas sobre la partición de entrenamiento.",
            pt="Métricas avaliadas na partição de treino.",
            de="Auf der Trainingsteilmenge ausgewertete Metriken.",
            zh="在训练集上评估的指标。",
        ),
    )  # type: ignore
    validation_metrics: _metrics_field(
        alias=MultilingualString(
            en="Validation metrics",
            es="Métricas de validación",
            pt="Métricas de validação",
            de="Validierungsmetriken",
            zh="验证指标",
        ),
        description=MultilingualString(
            en="Metrics evaluated on the validation split.",
            es="Métricas evaluadas sobre la partición de validación.",
            pt="Métricas avaliadas na partição de validação.",
            de="Auf der Validierungsteilmenge ausgewertete Metriken.",
            zh="在验证集上评估的指标。",
        ),
    )  # type: ignore
    test_metrics: _metrics_field(
        alias=MultilingualString(
            en="Test metrics",
            es="Métricas de prueba",
            pt="Métricas de teste",
            de="Testmetriken",
            zh="测试指标",
        ),
        description=MultilingualString(
            en="Metrics evaluated on the test split.",
            es="Métricas evaluadas sobre la partición de prueba.",
            pt="Métricas avaliadas na partição de teste.",
            de="Auf der Testteilmenge ausgewertete Metriken.",
            zh="在测试集上评估的指标。",
        ),
    )  # type: ignore


class BuildModelUnit(BaseUnit):
    """Instantiate an untrained model bound to its data and metrics.

    ``ModelFactory`` attaches the run id and the metric classes to the model
    instance, which is what later lets the model log metrics on its own during
    and after training. The metrics are configured here rather than in the
    evaluation unit because models use them *while* training to log at the step
    and epoch levels.

    **The data is not attached here.** It used to be, and that only worked
    because a model was fitted once on one split. A model fitted over folds
    sees different data on every iteration, so binding one partition at
    construction would leave the metrics describing whichever fold happened to
    be built with. Whoever fits the model points it at the data it is being
    fitted on, and this unit no longer needs ``x`` or ``y`` at all -- only the
    label count, which is a property of the dataset rather than of a split.

    ``validate`` checks that the model and every component nested in its
    parameters have been downloaded, so an impossible run is rejected before
    anything observable happens.

    The model is configured as a component field, the same way a model picks
    its own sub-components: the value is ``{"component": <name>, "params":
    {...}}``. The parameter tree stays an opaque ``dict`` in the schema and the
    front resolves it recursively, fetching the chosen component's schema to
    render the nested form. ``ModelFactory`` walks the same shape to build the
    object graph.
    """

    SCHEMA = BuildModelSchema

    # task_name only appears in the ModelFactory call and in error messages,
    # but it is declared all the same: a key read without being declared is
    # invisible to any caller — and to the DAG validator — that inspects
    # REQUIRES instead of running the unit.
    #
    # run_id is configuration, not context: no unit publishes it, so nothing
    # upstream could ever satisfy it. It is read without a default on purpose
    # — a run_id nobody passed would read as "this model has no run", and a
    # model with no run logs no metrics at all (see BaseModel).
    REQUIRES = ("n_labels", "task_name")
    PROVIDES = ("model", "factory", "optimizable_parameters", "model_parameters")
    RUNTIME_PARAMS = ("run_id",)

    def __init__(self, **config) -> None:
        super().__init__(**config)
        self._model_class = None

    @property
    def model_name(self) -> str:
        return self.config["model"]["component"]

    @property
    def model_parameters(self) -> dict:
        return self.config["model"]["params"]

    def _resolve_model_class(self) -> type:
        """Resolve the model class from the registry, memoized on this unit.

        Memoized on the unit instance, not in the shared context: a context
        can outlive a single ``BuildModelUnit`` (a future DAG could have more
        than one build-model node feeding the same run), and a context-global
        cache key would make the second instance silently reuse the first
        one's model class.
        """
        if self._model_class is not None:
            return self._model_class

        from kink import di

        component_registry = di["component_registry"]
        model_name: str = self.model_name

        try:
            model_class = component_registry[model_name]["class"]
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Unable to find Model with name {model_name} in registry.",
            ) from e

        self._model_class = model_class
        return model_class

    def validate(self, ctx: ExecutionContext) -> None:
        from kink import di

        component_registry = di["component_registry"]
        model_name: str = self.model_name
        parameters = self.model_parameters

        model_class = self._resolve_model_class()

        if getattr(model_class, "REQUIRES_DOWNLOAD", False) and not (
            model_class.is_downloaded()
        ):
            raise JobError(
                f"Model {model_name} is not downloaded. Download it before training."
            )

        nested_missing = missing_downloads(parameters, component_registry)
        if nested_missing:
            names = ", ".join(m["name"] for m in nested_missing)
            raise JobError(
                "These components are not downloaded. "
                f"Download them before training: {names}."
            )

    def execute(self, ctx: ExecutionContext) -> None:
        from kink import di

        from DashAI.back.models.model_factory import ModelFactory

        component_registry = di["component_registry"]

        parameters = self.model_parameters
        run_id = self.config["run_id"]
        task_name = ctx.require("task_name")

        model_class = self._resolve_model_class()

        try:
            train_metrics: List["BaseMetric"] = [
                component_registry[m]["class"] for m in self.config["train_metrics"]
            ]
            validation_metrics: List["BaseMetric"] = [
                component_registry[m]["class"]
                for m in self.config["validation_metrics"]
            ]
            test_metrics: List["BaseMetric"] = [
                component_registry[m]["class"] for m in self.config["test_metrics"]
            ]
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Unable to find metrics associated with Task {task_name} in registry",
            ) from e

        try:
            factory = ModelFactory(
                model_class,
                parameters,
                run_id,
                train_metrics=train_metrics,
                validation_metrics=validation_metrics,
                test_metrics=test_metrics,
                n_labels=ctx.require("n_labels"),
            )
            model: "BaseModel" = factory.model
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Unable to instantiate model using run {run_id}",
            ) from e

        # The original tree is what the search unit rewrites with the best
        # values found, so it travels as a reference instead of being read
        # from this unit's configuration again.
        ctx.put_ref("model_parameters", parameters)
        ctx.put("factory", factory)
        ctx.put("model", model)
        ctx.put("optimizable_parameters", factory.optimizable_parameters)
