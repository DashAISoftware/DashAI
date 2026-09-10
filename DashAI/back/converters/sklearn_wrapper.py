import contextlib
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Union

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.dashai_data_type import DashAIDataType

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


def _normalize_missing(df: object) -> object:
    """Normalize missing-value sentinels to ``np.nan`` before handing off to sklearn.

    ``DashAIDataset.to_pandas()`` converts Arrow nulls in string/Categorical
    columns to Python ``None``, while numeric columns get actual float
    ``nan``. Several sklearn transformers (notably ``SimpleImputer``, whose
    default ``missing_values=np.nan`` masks via a ``value != value`` check)
    only recognize float ``nan`` as missing: ``None != None`` is ``False``,
    so ``None`` entries are silently treated as real values and never
    imputed, even though ``pandas``/Arrow both consider them missing.
    ``DataFrame.notna()`` correctly flags both, so this unifies the
    representation without altering any non-missing value or dtype.

    Parameters
    ----------
    df : object
        The value returned by ``DashAIDataset.to_pandas()``. Only
        ``pandas.DataFrame`` instances are normalized; anything else is
        returned unchanged.

    Returns
    -------
    object
        The normalized DataFrame, or ``df`` unchanged if it isn't one.
    """
    import numpy as np
    import pandas as pd

    if not isinstance(df, pd.DataFrame):
        return df
    return df.where(df.notna(), np.nan)


class SklearnWrapper(BaseConverter, metaclass=ABCMeta):
    """Abstract mixin that adapts scikit-learn transformers to the DashAI converter API.

    This wrapper bridges scikit-learn's `fit` / `transform` interface with
    DashAI's `DashAIDataset`. It converts datasets to pandas DataFrames before
    calling the underlying scikit-learn methods, then converts the output back to
    `DashAIDataset` with proper DashAI types set via `get_output_type`.

    All concrete scikit-learn converters in DashAI inherit from this class.
    """

    def __init__(self, **kwargs):
        """Initialize the sklearn wrapper and configure pandas output format.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments forwarded to the
            parent scikit-learn transformer and ConfigObject.
        """
        super().__init__(**kwargs)

        if hasattr(self, "set_output"):
            self.set_output(transform="pandas")

    @abstractmethod
    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the DashAI data type produced by this transformer for a column.

        Each concrete sklearn converter must implement this to declare its
        output column type after transformation.

        Parameters
        ----------
        column_name : str, optional
            The name of the column. Defaults to None.

        Returns
        -------
        DashAIDataType
            The DashAI data type for the output column.
        """
        raise NotImplementedError

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> BaseConverter:
        """Fit the scikit-learn transformer to the data.

        Converts `x` (and optionally `y`) to pandas DataFrames, then delegates
        to the underlying scikit-learn class's `fit` method found in the MRO.

        Parameters
        ----------
        x : DashAIDataset
            The input dataset to fit the transformer on.
        y : DashAIDataset, optional
            Target values for supervised transformers.
            Defaults to None.

        Returns
        -------
        BaseConverter
            The fitted transformer instance (self).

        Raises
        ------
        ValueError
            If the transformer requires ``y`` but none is provided
            (only applies to legacy sklearn estimators that define
            ``_get_tags()`` with ``requires_y=True``).
        RuntimeError
            If no scikit-learn class with a `fit` method is found
            in the MRO.
        """
        try:
            if hasattr(x, "to_pandas"):
                x_pandas = _normalize_missing(x.to_pandas())
                self._fit_input_cache = (x, x_pandas)
            else:
                x_pandas = x
                self._fit_input_cache = None
            y_pandas = (
                _normalize_missing(y.to_pandas())
                if y is not None and hasattr(y, "to_pandas")
                else y
            )

            requires_y = False
            if hasattr(self, "__sklearn_tags__"):
                try:
                    tags = self.__sklearn_tags__()
                    target_tags = getattr(tags, "target_tags", None)
                    if target_tags is not None:
                        requires_y = bool(getattr(target_tags, "required", False))
                except Exception:
                    requires_y = False
            if not requires_y and hasattr(self, "_get_tags"):
                with contextlib.suppress(Exception):
                    requires_y = bool(self._get_tags().get("requires_y", False))

            if requires_y and y is None:
                raise ValueError("This transformer requires y for fitting")

            sklearn_cls = next(
                (
                    cls
                    for cls in type(self).__mro__
                    if "sklearn" in cls.__module__
                    and "DashAI" not in cls.__module__
                    and "fit" in cls.__dict__
                ),
                None,
            )

            if sklearn_cls is None:
                raise RuntimeError(
                    "No sklearn class with a 'fit' method found in the MRO. "
                    "Ensure that your transformer inherits from a valid sklearn "
                    "class."
                )
            fit_method = sklearn_cls.__dict__["fit"]
            if requires_y or y_pandas is not None:
                fit_method(self, x_pandas, y_pandas)
            else:
                fit_method(self, x_pandas)
        except Exception:
            self._fit_input_cache = None
            raise

        return self

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Transform the data using the fitted scikit-learn transformer.

        Converts `x` to a pandas DataFrame, applies the underlying scikit-learn
        transformer's `transform` method, then converts the result back to a
        `DashAIDataset` with column types set via `get_output_type`.

        Parameters
        ----------
        x : DashAIDataset
            The input dataset to transform.
        y : DashAIDataset, optional
            Not used. Present for API consistency.
            Defaults to None.

        Returns
        -------
        DashAIDataset
            The transformed dataset with updated DashAI column types.

        Raises
        ------
        RuntimeError
            If no scikit-learn class with a `transform` method is
            found in the MRO.
        """
        import numpy as np
        import pandas as pd
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

        cached = getattr(self, "_fit_input_cache", None)
        if cached is not None and cached[0] is x:
            x_pandas = cached[1]
        elif hasattr(x, "to_pandas"):
            x_pandas = _normalize_missing(x.to_pandas())
        else:
            x_pandas = x
        # Drop the reference now that it's been consumed (or wasn't a hit),
        # so the cached DataFrame doesn't outlive this transform call.
        self._fit_input_cache = None

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
                "No sklearn class with a 'transform' method found in the "
                "inheritance hierarchy. Transformation cannot be performed."
            )
        x_new = sklearn_cls.__dict__["transform"](self, x_pandas)

        if isinstance(x_new, np.ndarray):
            columns = x_pandas.columns if hasattr(x_pandas, "columns") else None
            x_new = pd.DataFrame(x_new, columns=columns)

        converted_dataset = to_dashai_dataset(x_new)

        for col in converted_dataset.column_names:
            try:
                output_type = self.get_output_type(col)

                if isinstance(output_type, Categorical) and hasattr(self, "classes_"):
                    values = pa.array(self.classes_.tolist())
                    encoding = {v: i for i, v in enumerate(self.classes_)}
                    converted_dataset.types[col] = Categorical(
                        values=values, encoding=encoding, converted=True
                    )
                else:
                    converted_dataset.types[col] = output_type
            except NotImplementedError:
                pass

        return converted_dataset
