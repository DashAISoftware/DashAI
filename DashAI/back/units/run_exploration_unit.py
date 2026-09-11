"""Unit that runs one exploration over the dataset in the context."""

import logging
from typing import TYPE_CHECKING, Type

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

if TYPE_CHECKING:
    from DashAI.back.exploration.base_explorer import BaseExplorer

log = logging.getLogger(__name__)


class RunExplorationSchema(BaseSchema):
    explorer_id: schema_field(
        int_field(gt=0),
        placeholder=1,
        description=MultilingualString(
            en="Identifier of the exploration whose selected columns and "
            "display name the explorer component reads.",
            es="Identificador de la exploración cuyas columnas seleccionadas y "
            "nombre para mostrar lee el componente de exploración.",
            pt="Identificador da exploração cujas colunas selecionadas e nome "
            "de exibição o componente de exploração lê.",
            de="Kennung der Exploration, deren ausgewählte Spalten und "
            "Anzeigename die Explorer-Komponente liest.",
            zh="探索的标识符，探索组件从中读取所选列和显示名称。",
        ),
        alias=MultilingualString(
            en="Exploration",
            es="Exploración",
            pt="Exploração",
            de="Exploration",
            zh="探索",
        ),
    )  # type: ignore
    explorer: schema_field(
        component_field(parent="BaseExplorer"),
        placeholder={
            "component": "DescribeExplorer",
            "params": {"percentiles": "25, 50, 75", "include": "all", "exclude": None},
        },
        description=MultilingualString(
            en="Exploration to run, together with its own configuration.",
            es="Exploración a ejecutar, junto con su propia configuración.",
            pt="Exploração a executar, junto com a sua própria configuração.",
            de="Auszuführende Exploration samt ihrer eigenen Konfiguration.",
            zh="要运行的探索及其自身配置。",
        ),
        alias=MultilingualString(
            en="Explorer",
            es="Explorador",
            pt="Explorador",
            de="Explorer",
            zh="探索器",
        ),
    )  # type: ignore


class RunExplorationUnit(BaseUnit):
    """Instantiate an explorer component and run it over the dataset.

    Preparing the dataset and launching the exploration are one unit, not two:
    ``prepare_dataset`` is a hook on the explorer component itself
    (``BaseExplorer.prepare_dataset``), so it does not exist without an
    instantiated explorer. Splitting them would force the live explorer
    instance through the context, which is instance state wearing a context
    key's clothes.

    The unit re-reads the ``Explorer`` row because the component API takes it:
    ``prepare_dataset`` needs its ``columns`` and ``launch_exploration``
    receives the row itself. The read is strictly read-only — the row's status
    belongs to the job.

    The explorer instance is published alongside the result because saving is
    also a method on it (``save_notebook``). Handing over the same object,
    rather than letting the save unit build its own from the same
    configuration, is what keeps a stateful explorer working: ``CorrMatrix``
    and ``CovMatrix`` read ``self.plot`` while saving. Same shape as
    ``BuildModelUnit`` publishing ``model`` for ``SaveModelUnit``.
    """

    SCHEMA = RunExplorationSchema

    PROVIDES = ("exploration_result", "explorer")
    REQUIRES = ("dataset",)

    def __init__(self, **config) -> None:
        super().__init__(**config)
        self._explorer_class = None

    @property
    def exploration_type(self) -> str:
        return self.config["explorer"]["component"]

    @property
    def parameters(self) -> dict:
        return self.config["explorer"]["params"]

    def _resolve_explorer_class(self) -> Type["BaseExplorer"]:
        """Resolve the explorer class from the registry, memoized on this unit.

        Memoized on the instance rather than in the shared context: a context
        can hold more than one exploration node, and a context-global cache key
        would make the second one silently reuse the first one's class.
        """
        if self._explorer_class is not None:
            return self._explorer_class

        from kink import di

        component_registry = di["component_registry"]
        exploration_type = self.exploration_type

        try:
            explorer_class = component_registry[exploration_type]["class"]
        except KeyError as e:
            log.exception(e)
            raise JobError(
                (f"Explorer {exploration_type} not found in the registry.")
            ) from e

        self._explorer_class = explorer_class
        return explorer_class

    def execute(self, ctx: ExecutionContext) -> None:
        from kink import di

        from DashAI.back.exploration.base_explorer import BaseExplorer

        session_factory = di["session_factory"]

        explorer_id = self.config["explorer_id"]
        exploration_type = self.exploration_type
        loaded_dataset = ctx.require("dataset")

        explorer_component_class = self._resolve_explorer_class()

        with session_factory() as db:
            explorer_info: Explorer = db.get(Explorer, explorer_id)
            if explorer_info is None:
                raise JobError(f"Explorer with id {explorer_id} not found.")

            try:
                explorer_instance = explorer_component_class(**self.parameters)
                assert isinstance(explorer_instance, BaseExplorer)
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Error instancing the explorer {exploration_type}."
                ) from e

            try:
                prepared_dataset = explorer_instance.prepare_dataset(
                    loaded_dataset, explorer_info.columns
                )
            except Exception as e:
                log.exception(e)
                raise JobError(
                    (
                        "Error preparing the dataset for the exploration "
                        f"{exploration_type}."
                    )
                ) from e

            try:
                result = explorer_instance.launch_exploration(
                    prepared_dataset, explorer_info
                )
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Error launching the exploration {exploration_type}."
                ) from e

        ctx.put("exploration_result", result)
        ctx.put("explorer", explorer_instance)
