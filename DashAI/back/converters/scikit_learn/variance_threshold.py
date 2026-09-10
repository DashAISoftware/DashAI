from typing import TYPE_CHECKING, Union

from sklearn.feature_selection import VarianceThreshold as VarianceThresholdOperation

from DashAI.back.converters.category.dimensionality_reduction import (
    DimensionalityReductionConverter,
)
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import float_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class VarianceThresholdSchema(BaseSchema):
    """Schema for VarianceThreshold hyperparameters.

    Configures the variance cutoff used to remove low-information features
    for sklearn's ``VarianceThreshold``. Features whose variance across the
    training set falls strictly below ``threshold`` are dropped. Setting
    ``threshold`` to 0.0 (the default) removes only features that are
    constant across all samples.
    """

    threshold: schema_field(
        float_field(ge=0.0),
        0.0,
        description=MultilingualString(
            en=("Features with a variance lower than this threshold will be removed."),
            es=(
                "Se eliminarán las características con una varianza inferior "
                "a este umbral."
            ),
            pt=(
                "Características com variância inferior a este limiar serão removidas."
            ),
            de=(
                "Merkmale mit einer Varianz unterhalb dieses Schwellenwerts werden "
                "entfernt."
            ),
            zh="方差低于此阈值的特征将被删除。",
        ),
    )  # type: ignore


class VarianceThreshold(
    DimensionalityReductionConverter, SklearnWrapper, VarianceThresholdOperation
):
    """Remove features whose variance across the training set is below a threshold.

    For each feature column the sample variance is computed during fitting::

        Var(x) = E[x^2] - (E[x])^2

    Feature columns for which ``Var(x) < threshold`` are removed. Because
    the criterion is purely based on the marginal variance of each feature,
    this selector requires no class labels and runs in O(n * p) time.

    Common use cases include:

    * **Constant-feature removal**: with the default ``threshold=0.0`` any
      feature that takes the same value in every training sample is dropped.
    * **Near-constant-feature removal**: for binary features, a threshold
      of ``p * (1 - p)`` drops features that are ``True`` in fewer than a
      fraction ``p`` of samples (e.g. ``threshold=0.8 * 0.2 = 0.16``
      removes features that are ``True`` in less than 20 % of samples).
    * **Pre-filtering before expensive selectors**: quickly reducing
      dimensionality before applying supervised selection methods such as
      ``SelectKBest`` or ``RFECV``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.VarianceThreshold.html
    """

    SCHEMA = VarianceThresholdSchema
    DESCRIPTION = MultilingualString(
        en="Feature selector that removes all low variance features.",
        es="Selector de características que elimina todas las de baja varianza.",
        pt="Seletor de características que remove todas as de baixa variância.",
        de="Merkmalsselektor, der alle Merkmale mit niedriger Varianz entfernt.",
        zh="删除所有低方差特征的特征选择器。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Variance Threshold",
        es="Umbral de Varianza",
        pt="Limiar de Variância",
        de="Varianz-Schwellenwert",
        zh="方差阈值",
    )

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "VarianceThreshold":
        """Fit the selector, remembering input types and tolerating empty output.

        VarianceThreshold only drops low-variance columns without modifying the
        retained columns' values, so their original types are captured here to be
        returned later by ``get_output_type`` instead of coercing to float. Types
        are recorded during ``fit`` (rather than ``transform``) because
        scikit-learn auto-wraps ``transform`` on subclasses and would coerce its
        output back to a pandas DataFrame.

        Additionally, sklearn raises a ValueError when no feature meets the
        threshold; we catch it and return self instead so that ``transform`` can
        legitimately return a dataset with zero columns. ``self.variances_`` is
        already populated by sklearn before it raises, so the internal state is
        correct.

        Parameters
        ----------
        x : DashAIDataset
            The input dataset to fit the selector on.
        y : DashAIDataset, optional
            Ignored; present for API consistency.

        Returns
        -------
        VarianceThreshold
            The fitted selector instance (self).
        """
        if hasattr(x, "types") and x.types is not None:
            self._input_types = dict(x.types)
        try:
            return super().fit(x, y)
        except ValueError as e:
            if "meets the variance threshold" not in str(e):
                raise
            # self.variances_ is already set by sklearn before it raises,
            # so transform will correctly produce a zero-column result.
            return self

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the original DashAI data type of a retained column.

        Since the selection leaves the retained columns' values unchanged, the
        output type matches the input type of that column.

        Parameters
        ----------
        column_name : str, optional
            The name of the retained column. Defaults to None.

        Returns
        -------
        DashAIDataType
            The original type of the column. Falls back to ``float64`` when the
            input type is unknown (the selector only operates on numbers).
        """
        input_types = getattr(self, "_input_types", None)
        if input_types is not None and column_name in input_types:
            return input_types[column_name]

        import pyarrow as pa

        return Float(arrow_type=pa.float64())

    IMAGE_PREVIEW = "variance_threshold.png"

    metadata = {
        "allowed_types": [Float, Integer],
        "allowed_dtypes": [],
    }
