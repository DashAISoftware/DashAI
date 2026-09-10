from abc import ABCMeta
from typing import TYPE_CHECKING, Type, Union

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.job.base_job import JobError
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.utils import save_types_in_arrow_metadata

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ImbalancedLearnWrapper(BaseConverter, metaclass=ABCMeta):
    """Abstract wrapper that adapts imbalanced-learn samplers
    to the DashAI converter API.

    Implements ``fit`` and ``transform`` by calling ``fit_resample`` from the underlying
    imbalanced-learn sampler, then wrapping the resampled data back into a
    ``DashAIDataset``. Because samplers change the number of rows, ``changes_row_count``
    returns ``True`` for all subclasses.

    All concrete imbalanced-learn converters in DashAI inherit from this class.
    """

    SUPERVISED = True
    CHANGES_ROW_COUNT = True

    def __init__(self, **kwargs):
        """Initialise the imbalanced-learn wrapper and reset internal state.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments forwarded to :class:`BaseConverter`.
        """
        super().__init__(**kwargs)
        self.fitted = False
        self._resampled_table = None
        self.original_X_column_names_: list = []
        self.original_target_column_name_: str = ""

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Not implemented; type preservation is handled in ``transform``.

        Imbalanced-learn samplers do not change column types. Types from the
        input dataset are copied directly in ``transform``.

        Parameters
        ----------
        column_name : str or None, optional
            Name of the column whose output type is queried. Ignored because
            this method always raises. Default ``None``.

        Raises
        ------
        NotImplementedError
            Always, because type determination is delegated to ``transform``.
        """
        raise NotImplementedError(
            "ImbalancedLearn samplers preserve input types. "
            "Types are handled in the transform method."
        )

    def fit(self, x: "DashAIDataset", y: "DashAIDataset") -> Type[BaseConverter]:
        """Resample the dataset by calling ``fit_resample`` and store the result.

        Converts ``x`` and ``y`` to pandas, calls the imbalanced-learn sampler's
        ``fit_resample``, then stores the combined resampled data as a PyArrow table.

        Parameters
        ----------
        x : DashAIDataset
            The input feature dataset.
        y : DashAIDataset
            The target label dataset (required; must be non-empty).

        Returns
        -------
        Type[BaseConverter]
            The fitted sampler instance (self).

        Raises
        ------
        ValueError
            If ``y`` is ``None`` or empty.
        TypeError
            If the resampled arrays from imbalanced-learn have an unexpected type.
        JobError
            If constructing the resampled PyArrow table fails.
        """
        import numpy as np
        import pandas as pd
        import pyarrow as pa

        if y is None or len(y) == 0:
            raise ValueError(
                "Imbalanced-learn samplers require a non-empty target dataset (y)."
            )

        X_df = x.to_pandas()
        y_series = y.to_pandas().iloc[:, 0]

        self.original_target_column_name_ = y.column_names[0]
        self.original_X_column_names_ = list(x.column_names)

        X_resampled_data, y_resampled_data = self.fit_resample(X_df, y_series)

        if isinstance(X_resampled_data, np.ndarray):
            X_resampled_df = pd.DataFrame(
                X_resampled_data, columns=self.original_X_column_names_
            )
        elif isinstance(X_resampled_data, pd.DataFrame):
            X_resampled_df = X_resampled_data
            X_resampled_df.columns = self.original_X_column_names_
        else:
            raise TypeError(
                (
                    "Unexpected type for X_resampled_data from imblearn: "
                    f"{type(X_resampled_data)}"
                )
            )

        if isinstance(y_resampled_data, np.ndarray):
            y_resampled_series = pd.Series(
                y_resampled_data, name=self.original_target_column_name_
            )
        elif isinstance(y_resampled_data, pd.Series):
            y_resampled_series = y_resampled_data
            y_resampled_series.name = self.original_target_column_name_
        else:
            raise TypeError(
                (
                    "Unexpected type for y_resampled_data from imblearn: "
                    f"{type(y_resampled_data)}"
                )
            )

        combined_df = pd.concat(
            [
                X_resampled_df.reset_index(drop=True),
                y_resampled_series.reset_index(drop=True),
            ],
            axis=1,
        )

        try:
            self._resampled_table = pa.Table.from_pandas(
                combined_df, preserve_index=False
            )
            combined_types = x.types.copy()
            combined_types.update(y.types)
            types_serialized = {
                col: combined_types[col].to_string() for col in combined_types
            }

            self._resampled_table = save_types_in_arrow_metadata(
                self._resampled_table, types_serialized
            )

        except Exception as e:
            raise JobError(
                f"Failed to prepare resampled data as PyArrow Table: {e}"
            ) from e

        self.fitted = True
        return self

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Return the resampled dataset stored during ``fit``.

        Parameters
        ----------
        x : DashAIDataset
            The original feature dataset (used only for type information).
        y : DashAIDataset, optional
            The original target dataset (used only for type information).
            Defaults to None.

        Returns
        -------
        DashAIDataset
            The combined resampled dataset (features + target) produced by ``fit``.

        Raises
        ------
        RuntimeError
            If ``fit`` has not been called or the resampled table is unavailable.
        JobError
            If constructing the output ``DashAIDataset`` fails.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        if not self.fitted:
            raise RuntimeError(f"{self.__class__.__name__} has not been fitted yet.")
        if self._resampled_table is None:
            raise RuntimeError("Resampled PyArrow Table not available. Call fit first.")

        ds_types = x.types.copy()
        if y is not None:
            y_types = y.types.copy()
            ds_types.update(y_types)
        try:
            dataset = DashAIDataset(self._resampled_table, types=ds_types, splits={})
            return dataset

        except Exception as e:
            raise JobError(
                f"Failed to create DashAIDataset from resampled data: {e}"
            ) from e
