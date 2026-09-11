"""Unit that instantiates a local explainer bound to a trained model."""

import logging

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.explanation_artifacts import build_explainer

log = logging.getLogger(__name__)


class BuildLocalExplainerSchema(BaseSchema):
    explainer: schema_field(
        component_field(parent="BaseLocalExplainer"),
        placeholder={"component": "KernelShap", "params": {}},
        description=MultilingualString(
            en="Explainer for individual instances, together with its own "
            "configuration.",
            es="Explicador para instancias individuales, junto con su propia "
            "configuración.",
            pt="Explicador para instâncias individuais, junto com a sua própria "
            "configuração.",
            de="Erklärer für einzelne Instanzen samt eigener Konfiguration.",
            zh="针对单个实例的解释器及其自身配置。",
        ),
        alias=MultilingualString(
            en="Local explainer",
            es="Explicador local",
            pt="Explicador local",
            de="Lokaler Erklärer",
            zh="局部解释器",
        ),
    )  # type: ignore


class BuildLocalExplainerUnit(BaseUnit):
    """Instantiate a local explainer over an already trained model.

    See ``BuildGlobalExplainerUnit`` for why the two scopes are two units even
    though they share their whole implementation.
    """

    SCHEMA = BuildLocalExplainerSchema

    REQUIRES = ("model",)
    PROVIDES = ("explainer",)

    def execute(self, ctx: ExecutionContext) -> None:
        explainer = build_explainer(
            "local", self.config["explainer"], ctx.require("model")
        )
        ctx.put("explainer", explainer)
