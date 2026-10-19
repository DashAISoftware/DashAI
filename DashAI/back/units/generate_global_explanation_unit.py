"""Unit that explains a model as a whole and stores the result."""

import logging

from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.explanation_artifacts import dump_explanation

log = logging.getLogger(__name__)


class GenerateGlobalExplanationSchema(BaseSchema):
    explainer_id: schema_field(
        int_field(gt=0),
        placeholder=1,
        description=MultilingualString(
            en="Identifier of the global explanation being produced. It names "
            "the files on disk, so a re-run overwrites its own artifacts and "
            "never another explanation's.",
            es="Identificador de la explicación global que se produce. Da "
            "nombre a los archivos en disco, de modo que volver a ejecutarla "
            "sobrescribe sus propios artefactos y nunca los de otra.",
            pt="Identificador da explicação global a ser produzida. Dá nome aos "
            "ficheiros em disco, pelo que uma nova execução substitui os seus "
            "próprios artefactos e nunca os de outra.",
            de="Kennung der erzeugten globalen Erklärung. Sie benennt die "
            "Dateien auf der Festplatte, sodass ein erneuter Lauf nur die "
            "eigenen Artefakte überschreibt.",
            zh="所生成全局解释的标识符。它命名磁盘上的文件，因此重新运行只会覆盖自身产物。",
        ),
        alias=MultilingualString(
            en="Explanation",
            es="Explicación",
            pt="Explicação",
            de="Erklärung",
            zh="解释",
        ),
    )  # type: ignore


class GenerateGlobalExplanationUnit(BaseUnit):
    """Explain the model over the whole dataset and pickle the result.

    Sibling of ``GenerateLocalExplanationUnit`` rather than one unit with a
    branch, for three reasons that all point the same way: the two produce
    different outputs (a single plot here, a set of plots plus the explained
    instances there), which a single ``PROVIDES`` could not describe since it
    is checked unconditionally; the local path has steps this one does not
    (fitting, selecting instances); and their configurations point at two
    different component registries.

    The unit never touches the explanation row: it publishes where it wrote,
    and the job owns the columns.
    """

    SCHEMA = GenerateGlobalExplanationSchema

    REQUIRES = ("explainer", "data_x", "data_y")
    PROVIDES = ("explanation_path", "plot_path")

    def execute(self, ctx: ExecutionContext) -> None:
        from DashAI.back.core.artifacts import normalize_artifacts

        explainer = ctx.require("explainer")
        dataset = (ctx.require("data_x"), ctx.require("data_y"))

        try:
            explanation = explainer.explain(dataset)
            plot = normalize_artifacts(explainer.plot(explanation))
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Failed to generate the explanation",
            ) from e

        explanation_path, plot_path = dump_explanation(
            explanation, plot, "global", self.config["explainer_id"]
        )

        ctx.put_ref("explanation_path", explanation_path)
        ctx.put_ref("plot_path", plot_path)
