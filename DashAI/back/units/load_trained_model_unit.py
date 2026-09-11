"""Unit that restores a trained model from the artifact a run left on disk."""

import logging

from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Run
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)


class LoadTrainedModelSchema(BaseSchema):
    run_id: schema_field(
        int_field(gt=0),
        placeholder=1,
        description=MultilingualString(
            en="Identifier of the run whose trained model is restored. Both "
            "the model component and the artifact path come from that row.",
            es="Identificador de la ejecución cuyo modelo entrenado se "
            "restaura. Tanto el componente del modelo como la ruta del "
            "artefacto salen de esa fila.",
            pt="Identificador da execução cujo modelo treinado é restaurado. "
            "Tanto o componente do modelo como o caminho do artefacto vêm "
            "dessa linha.",
            de="Kennung des Laufs, dessen trainiertes Modell wiederhergestellt "
            "wird. Sowohl die Modellkomponente als auch der Artefaktpfad "
            "stammen aus dieser Zeile.",
            zh="要恢复其已训练模型的运行标识符。模型组件和产物路径都来自该行。",
        ),
        alias=MultilingualString(
            en="Run", es="Ejecución", pt="Execução", de="Lauf", zh="运行"
        ),
    )  # type: ignore


class LoadTrainedModelUnit(BaseUnit):
    """Rebuild a trained model from the run that produced it.

    Reads the model component name and the artifact path off the ``Run`` row
    rather than taking them as configuration, so the model that is restored is
    always the one that run actually saved.

    ``load`` is invoked on the model *class*, not on an instance, which is what
    every concrete model in this codebase expects: they all declare it as a
    ``staticmethod`` or a ``classmethod`` that rebuilds the object from the
    file. ``ExplainerJob`` instead instantiates the class before calling
    ``load``; that extra step has no effect for those models, and preserving
    the difference is why ``LoadRunModelUnit`` exists separately instead of
    this unit growing a flag.
    """

    SCHEMA = LoadTrainedModelSchema

    PROVIDES = ("model",)

    def __init__(self, **config) -> None:
        super().__init__(**config)
        self._model_class = None

    def _resolve_model_class(self, model_name: str) -> type:
        """Resolve the model class from the registry, memoized on this unit.

        Memoized on the instance, not in the shared context: a context can hold
        more than one model-loading node, and a context-global cache key would
        make the second one silently reuse the first one's class.
        """
        if self._model_class is not None:
            return self._model_class

        from kink import di

        component_registry = di["component_registry"]

        try:
            model_class = component_registry[model_name]["class"]
        except KeyError as e:
            log.exception(e)
            raise JobError(f"Model {model_name} not found in the registry") from e

        self._model_class = model_class
        return model_class

    def execute(self, ctx: ExecutionContext) -> None:
        from kink import di

        session_factory = di["session_factory"]

        run_id = self.config["run_id"]

        with session_factory() as db:
            run: Run = db.get(Run, run_id)
            if not run:
                raise JobError(f"Run {run_id} does not exist in DB.")
            model_name = run.model_name
            run_path = run.run_path

        model_class = self._resolve_model_class(model_name)

        try:
            trained_model = model_class.load(run_path)
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Failed to load model {model_name} from path {run_path}"
            ) from e

        ctx.put("model", trained_model)
