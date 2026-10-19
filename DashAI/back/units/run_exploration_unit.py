"""Unit that runs one exploration over the dataset in the context."""

import logging
from typing import TYPE_CHECKING, Type

from DashAI.back.converters.converter_report import load_converter_report
from DashAI.back.core.enums.status import ConverterStatus
from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Converter, Explorer
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

if TYPE_CHECKING:
    from DashAI.back.exploration.base_explorer import BaseExplorer

log = logging.getLogger(__name__)


def _build_explorer_context(
    db,
    notebook_id: int,
    explorer_instance: "BaseExplorer",
) -> dict:
    """Build optional runtime context for explorers.

    Moved here from ``ExplorerJob`` when the job was merged with its unit
    version: it has to run between instantiating the explorer and preparing
    its dataset, and both happen inside ``RunExplorationUnit``. It reads the
    database and the disk and never sees the execution context.

    Explorers keep receiving the current notebook dataset as their main input.
    A converter report is loaded only when the explorer explicitly requires it
    via ``metadata["requires_converter_report"] = True``.

    When the explorer also declares ``metadata["requires_converter_class"]``,
    the most recently finished converter of any type in the notebook must be
    of that class. This guarantees the referenced report describes exactly
    the current dataset state: nothing could have run afterwards to alter the
    columns the report depends on. If a different converter ran more recently,
    the explorer is refused instead of silently reusing a report that may no
    longer match the live dataset.
    """
    explorer_metadata = explorer_instance.get_metadata()
    if not explorer_metadata.get("requires_converter_report", False):
        return {}

    required_class = explorer_metadata.get("requires_converter_class")
    latest_converter = (
        db.query(Converter)
        .filter(Converter.notebook_id == notebook_id)
        .filter(Converter.status == ConverterStatus.FINISHED)
        .order_by(Converter.created.desc())
        .first()
    )

    if latest_converter is None:
        class_hint = f" of type '{required_class}'" if required_class else ""
        raise JobError(
            f"This explorer requires a converter report, but the notebook has "
            f"no finished converters{class_hint}."
        )

    if required_class and latest_converter.converter != required_class:
        raise JobError(
            f"This explorer requires a report from the most recently finished "
            f"converter in the notebook, but the last converter was "
            f"'{latest_converter.converter}', not '{required_class}'. Re-run "
            f"the '{required_class}' converter before creating this explorer "
            f"so its report reflects the current dataset."
        )

    # Read only here: an explorer that needs no report needs no paths either.
    from kink import di

    notebook_output_path = di["config"]["NOTEBOOK_PATH"] / str(notebook_id)
    converter_report = load_converter_report(
        notebook_output_path,
        latest_converter.id,
    )

    if converter_report is None:
        class_hint = f" '{required_class}'" if required_class else ""
        raise JobError(
            f"This explorer requires a converter report, but the latest "
            f"finished{class_hint} converter did not produce one."
        )

    required_algorithm = explorer_metadata.get("requires_algorithm")
    if required_algorithm:
        used_algorithm = converter_report.get("algorithm_key", "").lower()
        if used_algorithm != required_algorithm.lower():
            raise JobError(
                f"This explorer requires the '{required_algorithm}' clustering "
                f"algorithm, but the last Clustering converter ran '{used_algorithm}'"
                f". Re-run the Clustering converter selecting the "
                f"'{required_algorithm}' algorithm."
            )

    return {
        "converter_report": converter_report,
        "converter_report_source": {
            "converter_id": latest_converter.id,
            "converter": latest_converter.converter,
        },
    }


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

            # An explorer that draws from a converter's report gets it here,
            # before it prepares its dataset. Its own refusals are JobErrors
            # and reach the user verbatim; anything else is reported as a
            # failure to load the context.
            try:
                explorer_instance.set_context(
                    _build_explorer_context(
                        db,
                        explorer_info.notebook_id,
                        explorer_instance,
                    )
                )
            except JobError:
                raise
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Error loading context for explorer {exploration_type}."
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
            except (JobError, ValueError) as e:
                # The explorer's own complaint about the data it was given is
                # already written for the user. That holds for every explorer,
                # not only the clustering ones that brought the rule in: several
                # older ones raise ValueError from here too. The traceback still
                # goes to the log, as it does for the wrapped failures below.
                log.exception(e)
                raise JobError(str(e)) from e
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Error launching the exploration {exploration_type}."
                ) from e

        ctx.put("exploration_result", result)
        ctx.put("explorer", explorer_instance)
