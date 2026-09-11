"""Unit that restores a run's model the way the explanation flow expects."""

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


class LoadRunModelSchema(BaseSchema):
    run_id: schema_field(
        int_field(gt=0),
        placeholder=1,
        description=MultilingualString(
            en="Identifier of the run whose trained model is restored. The "
            "model component, its parameters and the artifact path all come "
            "from that row.",
            es="Identificador de la ejecución cuyo modelo entrenado se "
            "restaura. El componente del modelo, sus parámetros y la ruta del "
            "artefacto salen de esa fila.",
            pt="Identificador da execução cujo modelo treinado é restaurado. O "
            "componente do modelo, os seus parâmetros e o caminho do artefacto "
            "vêm todos dessa linha.",
            de="Kennung des Laufs, dessen trainiertes Modell wiederhergestellt "
            "wird. Modellkomponente, Parameter und Artefaktpfad stammen alle "
            "aus dieser Zeile.",
            zh="要恢复其已训练模型的运行标识符。模型组件、参数和产物路径都来自该行。",
        ),
        alias=MultilingualString(
            en="Run", es="Ejecución", pt="Execução", de="Lauf", zh="运行"
        ),
    )  # type: ignore


class LoadRunModelUnit(BaseUnit):
    """Restore a run's trained model for an explanation.

    Deliberately **not** ``LoadTrainedModelUnit``, and the difference is not
    cosmetic to preserve even though it is very likely accidental:

    * this unit builds an instance with ``model_class(**run.parameters)`` and
      only then calls ``load`` on it, the way the explanation flow always has;
    * ``LoadTrainedModelUnit`` calls ``load`` straight on the class.

    Every concrete model in this codebase declares ``load`` as a
    ``staticmethod`` or a ``classmethod`` that rebuilds the object from the
    file, so the instance built here is thrown away and the extra step changes
    nothing — and no explainer reads anything that ``__init__`` sets: the only
    model attributes any of them touch (``one_hot_encoder``,
    ``categorical_columns``, ``label_encoder``) are set during training and
    restored from the artifact.

    The two units are kept apart because merging them would have to unify their
    error messages, which are user-visible and differ word for word. Do not
    collapse them into one with a flag without deciding that first.
    """

    SCHEMA = LoadRunModelSchema

    PROVIDES = ("model",)

    def __init__(self, **config) -> None:
        super().__init__(**config)
        self._model_class = None

    def _resolve_model_class(self, model_name: str) -> type:
        """Resolve the model class from the registry, memoized on this unit."""
        if self._model_class is not None:
            return self._model_class

        from kink import di

        component_registry = di["component_registry"]

        try:
            model_class = component_registry[model_name]["class"]
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Unable to find Model with name {model_name} in registry.",
            ) from e

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
            parameters = dict(run.parameters or {})

        run_model_class = self._resolve_model_class(model_name)

        try:
            model = run_model_class(**parameters)
        except Exception as e:
            log.exception(e)
            raise JobError("Unable to instantiate model") from e

        try:
            trained_model = model.load(run_path)
        except Exception as e:
            log.exception(e)
            raise JobError(f"Can not load model from path {run_path}") from e

        ctx.put("model", trained_model)
