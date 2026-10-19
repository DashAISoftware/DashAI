"""Unit that instantiates a global explainer bound to a trained model."""

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


class BuildGlobalExplainerSchema(BaseSchema):
    explainer: schema_field(
        component_field(parent="BaseGlobalExplainer"),
        placeholder={"component": "PermutationFeatureImportance", "params": {}},
        description=MultilingualString(
            en="Explainer for the model as a whole, together with its own "
            "configuration.",
            es="Explicador para el modelo completo, junto con su propia configuración.",
            pt="Explicador para o modelo como um todo, junto com a sua própria "
            "configuração.",
            de="Erklärer für das gesamte Modell samt eigener Konfiguration.",
            zh="针对整个模型的解释器及其自身配置。",
        ),
        alias=MultilingualString(
            en="Global explainer",
            es="Explicador global",
            pt="Explicador global",
            de="Globaler Erklärer",
            zh="全局解释器",
        ),
    )  # type: ignore


class BuildGlobalExplainerUnit(BaseUnit):
    """Instantiate a global explainer over an already trained model.

    Sibling of ``BuildLocalExplainerUnit`` rather than one unit with a scope
    flag, even though the building step itself is identical — the two share it
    through a helper. Global and local explainers are separate registries with
    separate base classes, and a component field carries a single ``parent``
    hint that the front reads straight off the property to list the candidates.
    One field covering both scopes would have to be optional, and an optional
    component field is emitted as an ``anyOf``, which buries the hint where the
    front does not look and leaves the user with no picker at all.
    """

    SCHEMA = BuildGlobalExplainerSchema

    REQUIRES = ("model",)
    PROVIDES = ("explainer",)

    def execute(self, ctx: ExecutionContext) -> None:
        explainer = build_explainer(
            "global", self.config["explainer"], ctx.require("model")
        )
        ctx.put("explainer", explainer)
