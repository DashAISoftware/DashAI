"""Unit that computes the metadata stored alongside a dataset."""

import logging

from DashAI.back.core.schema_fields import BaseSchema, bool_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)

#: Metadata keys produced by ``compute_metadata`` on top of the base ones.
#:
#: They are expensive (correlations and per-column statistics over the whole
#: dataset) and optional, so the unit both skips computing them and strips any it
#: finds already present when they were not asked for.
EXTENDED_METADATA_KEYS = (
    "general_info",
    "numeric_stats",
    "categorical_stats",
    "text_stats",
    "quality_info",
    "correlations",
)


class ComputeDatasetMetadataSchema(BaseSchema):
    compute_metadata: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en="Whether to compute the extended exploratory metadata "
            "(per-column statistics, quality report, correlations) on top of "
            "the base one. Disabling it makes large datasets much faster to "
            "store, at the cost of the exploration views.",
            es="Si se debe calcular la metadata exploratoria extendida "
            "(estadísticas por columna, informe de calidad, correlaciones) "
            "además de la básica. Desactivarla hace mucho más rápido el "
            "guardado de conjuntos de datos grandes, a costa de las vistas de "
            "exploración.",
            pt="Se deve calcular a metadata exploratória estendida "
            "(estatísticas por coluna, relatório de qualidade, correlações) "
            "além da básica. Desativá-la torna o armazenamento de grandes "
            "conjuntos de dados muito mais rápido, ao custo das vistas de "
            "exploração.",
            de="Ob die erweiterten explorativen Metadaten (Spaltenstatistiken, "
            "Qualitätsbericht, Korrelationen) zusätzlich zu den Basisdaten "
            "berechnet werden. Das Deaktivieren beschleunigt das Speichern "
            "großer Datensätze erheblich, auf Kosten der Explorationsansichten.",
            zh="是否在基础元数据之外计算扩展的探索性元数据（各列统计、质量报告、"
            "相关性）。禁用后可大幅加快大型数据集的存储速度，但会失去探索视图。",
        ),
        alias=MultilingualString(
            en="Compute extended metadata",
            es="Calcular metadata extendida",
            pt="Calcular metadata estendida",
            de="Erweiterte Metadaten berechnen",
            zh="计算扩展元数据",
        ),
    )  # type: ignore


class ComputeDatasetMetadataUnit(BaseUnit):
    """Fill in the metadata a dataset carries in its ``splits`` mapping.

    Two independent knobs, because "how much metadata" and "can the metadata
    already there be trusted" are different questions:

    * ``compute_metadata`` picks the depth: base only (column names, row count,
      NaN counts) or base plus the extended exploratory fields.
    * ``trust_inherited_metadata`` says the dataset arrived carrying metadata
      that still describes it — the case of a copy whose bytes never changed.
      Then the unit fills only what is missing instead of recomputing.

    Either way the requested depth is what ends up stored: asking for base only
    always strips the extended keys, even ones inherited from elsewhere, so the
    result never depends on where the dataset came from.

    Re-publishes ``dataset`` although it mutates it in place: the key is what
    makes the unit chainable, and the contract audit reads the ``ctx.put`` call.
    """

    SCHEMA = ComputeDatasetMetadataSchema

    REQUIRES = ("dataset",)
    PROVIDES = ("dataset",)
    RUNTIME_PARAMS = ("trust_inherited_metadata",)

    def execute(self, ctx: ExecutionContext) -> None:
        dataset = ctx.require("dataset")

        compute_extended = self.config.get("compute_metadata", True)
        trust_inherited = self.config.get("trust_inherited_metadata", False)

        if compute_extended:
            has_extended = any(key in dataset.splits for key in EXTENDED_METADATA_KEYS)
            if not (trust_inherited and has_extended):
                dataset.compute_metadata()
        else:
            if not (trust_inherited and "total_rows" in dataset.splits):
                dataset.compute_base_metadata()
            # Strip extended keys the dataset may have arrived with, so the
            # stored metadata matches what was asked for rather than the
            # history of the file.
            for stale_key in EXTENDED_METADATA_KEYS:
                dataset.splits.pop(stale_key, None)

        ctx.put("dataset", dataset)
