from typing import TYPE_CHECKING, Union

from sklearn.impute import MissingIndicator as MissingIndicatorOperation

from DashAI.back.converters.category.basic_preprocessing import (
    BasicPreprocessingConverter,
)
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Integer

if TYPE_CHECKING:
    import pandas as pd

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class MissingIndicatorSchema(BaseSchema):
    """Schema for configuring the MissingIndicator converter.

    Wraps ``sklearn.impute.MissingIndicator``. The current configuration uses
    default scikit-learn settings (all features with missing values are
    indicated, NaN is treated as the missing marker). No additional schema
    fields are exposed; the class is kept as a stub to satisfy the DashAI
    component interface.
    """


class MissingIndicator(
    BasicPreprocessingConverter, SklearnWrapper, MissingIndicatorOperation
):
    """Add binary indicator columns that flag which values were originally missing.

    For each feature that contains at least one NaN in the training data, a
    new binary column is appended to the output. The indicator column contains
    1 where the original value was missing and 0 otherwise.

    This converter is typically stacked onto an imputer (via the imputer's
    ``add_indicator=True`` option, or explicitly in a pipeline) so that the
    model can distinguish between "value was imputed" and "value was genuinely
    observed". Preserving missingness patterns can improve downstream model
    accuracy when data is not missing completely at random (MCAR). Output
    columns are typed as ``Integer`` (``int64``) in DashAI.

    Wraps ``sklearn.impute.MissingIndicator``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.impute.MissingIndicator.html
    """

    SCHEMA = MissingIndicatorSchema
    DESCRIPTION = MultilingualString(
        en="Binary indicators for missing values.",
        es="Indicadores binarios para valores faltantes.",
        pt="Indicadores binários para valores ausentes.",
        de="Binäre Indikatoren für fehlende Werte.",
        zh="缺失值的二进制指示器。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Missing Indicator",
        es="Indicador de Faltantes",
        pt="Indicador de Valores Ausentes",
        de="Fehlender-Wert-Indikator",
        zh="缺失值指示器",
    )
    IMAGE_PREVIEW = "missing_indicator.png"

    metadata = {
        "allowed_types": [],
        "allowed_dtypes": [],
    }

    def __init__(self, **kwargs):
        """Initialize the MissingIndicator converter.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments matching the converter's
            schema fields. Forwarded to the underlying scikit-learn class.
        """
        # Force indicators for all selected features so the user always sees the
        # new column, even when a feature has no missing values (all-False indicator).
        kwargs.setdefault("features", "all")
        super().__init__(**kwargs)
        # SklearnWrapper.__init__ sets set_output(transform="pandas"), which causes
        # sklearn's __init_subclass__ wrapper to intercept our custom transform and
        # attempt to rename its output using get_feature_names_out() (which returns
        # only the indicator column count, not the combined output count).
        # Reset to "default" so the wrapper returns our DashAIDataset as-is.
        if hasattr(self, "set_output"):
            self.set_output(transform="default")

    @staticmethod
    def _normalize_missing(frame: "pd.DataFrame") -> "pd.DataFrame":
        """Return a copy of *frame* where object-column missing values are float NaN.

        HuggingFace/PyArrow stores missing strings as ``None`` (Python), but
        sklearn's ``_get_mask`` uses ``x != x`` which is ``False`` for ``None``
        (only ``float('nan') != float('nan')`` is ``True``).  We also treat
        empty strings as missing to match the dataset-filter behaviour.
        """
        import numpy as np

        frame = frame.copy()
        for col in frame.select_dtypes(include="object").columns:
            frame[col] = frame[col].replace("", np.nan)
            frame[col] = frame[col].where(frame[col].notna(), np.nan)
        return frame

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "MissingIndicator":
        """Fit after normalising missing values so sklearn detects them."""
        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

        x_pandas = x.to_pandas() if hasattr(x, "to_pandas") else x
        x_clean_ds = to_dashai_dataset(self._normalize_missing(x_pandas))
        if hasattr(x, "types"):
            x_clean_ds.types = x.types.copy()
        return super().fit(x_clean_ds, y)

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Transform x by appending missing-value indicator columns.

        Keeps the original columns intact and appends one boolean indicator
        column per feature that had missing values during fit.  Indicator
        columns are named ``missingindicator_<original_col_name>`` so that
        ``_rebuild_dataset_with_transformed_columns`` treats them as *new*
        columns rather than replacements, preserving the original data.
        """
        import numpy as np
        import pandas as pd

        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

        x_pandas = x.to_pandas() if hasattr(x, "to_pandas") else x

        # Normalise missing values before sklearn sees the data (None and ""
        # are both treated as missing, matching dataset-filter behaviour).
        x_for_sklearn = self._normalize_missing(x_pandas)

        sklearn_cls = next(
            (
                cls
                for cls in type(self).__mro__
                if "sklearn" in cls.__module__
                and "DashAI" not in cls.__module__
                and "transform" in cls.__dict__
            ),
            None,
        )
        if sklearn_cls is None:
            raise RuntimeError(
                "No sklearn class with a 'transform' method found in the MRO."
            )

        indicators = sklearn_cls.__dict__["transform"](self, x_for_sklearn)

        # features_ contains the column indices for which indicators are produced.
        # With features='all' (default), this always equals all input column indices.
        if hasattr(self, "features_") and len(self.features_) > 0:
            indicator_col_names = [
                f"missingindicator_{x_pandas.columns[i]}" for i in self.features_
            ]
        else:
            indicator_col_names = [
                f"missingindicator_{col}" for col in x_pandas.columns
            ]

        if isinstance(indicators, np.ndarray):
            indicators_df = pd.DataFrame(
                indicators,
                columns=indicator_col_names,
                index=x_pandas.index,
            )
        else:
            indicators_df = indicators.copy()
            indicators_df.columns = indicator_col_names

        combined_df = pd.concat([x_pandas, indicators_df], axis=1)
        converted_dataset = to_dashai_dataset(combined_df)

        output_type = self.get_output_type()
        for col in indicator_col_names:
            if col in converted_dataset.column_names:
                converted_dataset.types[col] = output_type

        # Preserve original column types from the input dataset
        if hasattr(x, "types"):
            for col in x_pandas.columns:
                if col in x.types and col in converted_dataset.column_names:
                    converted_dataset.types[col] = x.types[col]

        return converted_dataset

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the DashAI data type produced by this converter for a column.

        Parameters
        ----------
        column_name : str, optional
            Not used; all output columns share the
            same type. Defaults to None.

        Returns
        -------
        DashAIDataType
            An Integer type backed by ``pyarrow.int64()``,
            representing binary 0/1 missingness flags.
        """
        import pyarrow as pa

        return Integer(arrow_type=pa.int64())
