"""Reusable `infer_output_columns` overrides shared by several converters."""

from typing import List, Optional

from DashAI.back.preprocessing.structure_types import StateItem, StructureDelta


class ComponentsOutputMixin:
    """Structure of a converter that outputs `n_components` new columns.

    Covers projections and kernel approximations (PCA, TruncatedSVD,
    Nystroem, RBFSampler...), which consume their scope and output one
    column per component. The count is known whenever `n_components` is an
    integer. None, a float (explained-variance ratio) or "mle" only resolve
    on fit: None means min(n_samples, n_features) for the PCA family. List
    this mixin before the converter's category base so its override wins.
    """

    def _components_count(self, inputs: List[StateItem]) -> Optional[int]:
        n_components = getattr(self, "n_components", None)
        if isinstance(n_components, int) and not isinstance(n_components, bool):
            return n_components
        return None

    def infer_output_columns(self, inputs: List[StateItem]) -> StructureDelta:
        return StructureDelta(
            added=self._default_blocks(count=self._components_count(inputs))
        )
