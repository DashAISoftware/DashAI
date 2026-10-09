"""DashAI Dataset implementation."""

import logging
import os

from beartype import beartype
from beartype.typing import Dict, List, Literal, Optional, Tuple, Union
from datasets import Dataset

from DashAI.back.types.categorical import Categorical
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.utils import (
    arrow_to_dashai_types,
    comma_float_to_float,
    get_types_from_arrow_metadata,
    save_types_in_arrow_metadata,
    to_arrow_types,
)
from DashAI.back.types.value_types import Decimal, Float, Integer, Text

log = logging.getLogger(__name__)


def get_arrow_table(ds: Dataset) -> object:
    """Retrieve the underlying PyArrow table from a HuggingFace Dataset.

    Abstracts away version-dependent private attribute access by trying
    ``arrow_table`` first and then ``data.table``.

    Parameters
    ----------
    ds : Dataset
        A HuggingFace ``Dataset`` or ``DashAIDataset`` instance.

    Returns
    -------
    object
        The underlying PyArrow ``Table``.

    Raises
    ------
    ValueError
        If neither ``arrow_table`` nor ``data.table`` is available on ``ds``.
    """
    if hasattr(ds, "arrow_table"):
        return ds.arrow_table
    elif hasattr(ds, "data") and hasattr(ds.data, "table"):
        return ds.data.table
    else:
        raise ValueError("Unable to retrieve underlying arrow table from the dataset.")


class DashAIDataset(Dataset):
    """DashAI dataset wrapper for Huggingface datasets with extra metadata."""

    @beartype
    def __init__(
        self,
        table: object,
        splits: dict = None,
        types: Optional[Dict[str, DashAIDataType]] = None,
        *args,
        **kwargs,
    ):
        """Initialize a new instance of a DashAI dataset.

        Parameters
        ----------
        table : Table
            Arrow table from which the dataset will be created
        """
        super().__init__(table, *args, **kwargs)
        self.splits = splits or {}
        self._table = table
        self._types = (
            get_types_from_arrow_metadata(self._table) if types is None else types
        )

    @property
    def types(self):
        """Get the types of the dataset."""
        return self._types

    @types.setter
    def types(self, value):
        """Set the column type mapping for this dataset.

        Parameters
        ----------
        value : dict of {str: DashAIDataType}
            New mapping from column name to DashAI data type.
        """
        self._types = value

    @beartype
    def cast(self, *args, **kwargs) -> "DashAIDataset":
        """Override of the cast method to leave it in DashAI dataset format.

        Returns
        -------
        DatasetDashAI
            Dataset after cast
        """
        ds = super().cast(*args, **kwargs)
        arrow_tbl = get_arrow_table(ds)
        return DashAIDataset(arrow_tbl, splits=self.splits, types=self._types)

    @property
    def arrow_table(self) -> object:
        """
        Provides a clean way to access the underlying PyArrow table.

        Returns:
            object: The underlying PyArrow table.
        """
        try:
            # Now we reference  the pa.table from here (DashAIDataset)
            # and not the huggingface dataset, so we preserve the metadata
            return self._table
        except AttributeError:
            raise ValueError("Unable to retrieve the underlying Arrow table.") from None

    def keys(self) -> List[str]:
        """Return the available splits in the dataset.

        Returns
        -------
        List[str]
            List of split names (e.g., ['train', 'test', 'validation'])
        """
        if "split_indices" in self.splits:
            return list(self.splits["split_indices"].keys())
        return []

    def compute_base_metadata(self) -> "DashAIDataset":
        """Compute basic metadata for the dataset and store it in self.splits.

        Includes column names, total rows, and NaN counts.

        Returns
        -------
        DashAIDataset
            The dataset with updated basic metadata in self.splits.
        """

        dataset_df = self.to_pandas()

        self.splits["column_names"] = dataset_df.columns.tolist()
        self.splits["total_rows"] = len(dataset_df)
        self.splits["nan"] = dataset_df.isna().sum().to_dict()

        return self

    def compute_metadata(self) -> "DashAIDataset":
        """Compute extended metadata for the dataset and store it in self.splits.

        Includes NaN counts, column types, numeric and categorical summaries,
        quality indicators, sample data, and correlations
        useful for frontend visualization.

        Returns
        -------
        DashAIDataset
            The dataset with updated metadata in self.splits.
        """

        dataset_df = self.to_pandas()

        if self.types is None:
            raise ValueError("Dataset types are not defined.")

        # --- Base ---
        self.compute_base_metadata()

        # --- Compute all metadata components ---
        self.splits["general_info"] = self._compute_general_info(dataset_df)
        self.splits["numeric_stats"] = self._compute_numeric_metadata(dataset_df)
        self.splits["categorical_stats"] = self._compute_categorical_metadata(
            dataset_df
        )
        self.splits["text_stats"] = self._compute_text_metadata(dataset_df)
        self.splits["quality_info"] = self._compute_quality_metadata(dataset_df)
        self.splits["correlations"] = self._compute_correlations(dataset_df)

        return self

    def _compute_general_info(self, dataset_df) -> dict:
        """Compute general dataset information.

        Parameters
        ----------
        dataset_df : pd.DataFrame
            The dataset as a pandas DataFrame.

        Returns
        -------
        dict
            General information including rows, columns, memory usage, and dtypes.
        """
        hashable_cols = [
            c
            for c in dataset_df.columns
            if not isinstance(self.types.get(c), DashAIImage)
        ]
        all_categorical = hashable_cols and all(
            isinstance(self.types.get(c), Categorical) for c in hashable_cols
        )
        if hashable_cols and not all_categorical:
            duplicate_rows = int(dataset_df[hashable_cols].duplicated().sum())
        else:
            duplicate_rows = 0

        return {
            "n_rows": len(dataset_df),
            "n_columns": len(dataset_df.columns),
            "memory_usage_mb": float(self.arrow_table.nbytes / 1e6),
            "duplicate_rows": duplicate_rows,
            "dtypes": {k: v.to_string().get("type") for k, v in self.types.items()},
        }

    def _get_numeric_columns(self) -> list:
        """Get list of numeric column names based on DashAI types.

        Returns
        -------
        list
            List of numeric column names.
        """
        return [
            k for k, v in self.types.items() if isinstance(v, (Integer, Float, Decimal))
        ]

    def _get_categorical_columns(self) -> list:
        """Get list of categorical column names based on DashAI types.

        Returns
        -------
        list
            List of categorical column names.
        """
        return [k for k, v in self.types.items() if isinstance(v, Categorical)]

    def _get_text_columns(self) -> list:
        """Get list of text column names based on DashAI types.

        Returns
        -------
        list
            List of text column names.
        """
        return [k for k, v in self.types.items() if isinstance(v, Text)]

    def _compute_numeric_metadata(self, dataset_df) -> dict:
        """Compute statistics for numeric columns.

        Parameters
        ----------
        dataset_df : pd.DataFrame
            The dataset as a pandas DataFrame.

        Returns
        -------
        dict
            Dictionary with statistics for each numeric column.
        """
        numeric_keys = [
            k for k in self._get_numeric_columns() if k in dataset_df.columns
        ]
        numeric_cols = dataset_df[numeric_keys]
        numeric_stats = {}

        for col in numeric_cols.columns:
            series = numeric_cols[col].dropna()
            if series.empty:
                continue

            # Calculate quartiles
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1

            # Detect outliers using IQR method
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers_count = int(
                ((series < lower_bound) | (series > upper_bound)).sum()
            )

            numeric_stats[col] = {
                "mean": float(series.mean()),
                "std": float(series.std()),
                "min": float(series.min()),
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "max": float(series.max()),
                "median": float(series.median()),
                "q1": q1,
                "q3": q3,
                "n_unique": int(series.nunique()),
                "skew": float(series.skew()),
                "kurtosis": float(series.kurtosis()),
                "outliers_count": outliers_count,
            }

        return numeric_stats

    def _compute_categorical_metadata(self, dataset_df) -> dict:
        """Compute statistics for categorical columns.

        Parameters
        ----------
        dataset_df : pd.DataFrame
            The dataset as a pandas DataFrame.

        Returns
        -------
        dict
            Dictionary with statistics for each categorical column.
        """
        categorical_keys = [
            k for k in self._get_categorical_columns() if k in dataset_df.columns
        ]
        categorical_cols = dataset_df[categorical_keys]
        categorical_stats = {}

        for col in categorical_cols.columns:
            series = categorical_cols[col].dropna()
            if series.empty:
                continue
            counts = series.value_counts()

            # Get top 5 categories for visualization
            top_5 = [
                {"value": str(val), "count": int(count)}
                for val, count in counts.head(5).items()
            ]

            categorical_stats[col] = {
                "n_unique": int(counts.size),
                "most_frequent": str(counts.index[0]),
                "most_frequent_count": int(counts.iloc[0]),
                "top_5": top_5,
            }

        return categorical_stats

    def _compute_text_metadata(self, dataset_df) -> dict:
        """Compute statistics for text columns.

        Parameters
        ----------
        dataset_df : pd.DataFrame
            The dataset as a pandas DataFrame.

        Returns
        -------
        dict
            Dictionary with statistics for each text column.
        """
        text_keys = self._get_text_columns()
        text_stats = {}

        for col in text_keys:
            if col not in dataset_df.columns:
                continue
            series = dataset_df[col].astype(str)
            lengths = series.str.len()
            text_stats[col] = {
                "avg_length": float(lengths.mean()),
                "median_length": float(lengths.median()),
                "min_length": int(lengths.min()),
                "max_length": int(lengths.max()),
                "unique_count": int(series.nunique()),
                "unique_ratio": float(series.nunique() / len(series)),
                "avg_word_count": float(series.str.split().str.len().mean()),
            }

        return text_stats

    def _compute_quality_metadata(self, dataset_df) -> dict:
        """Compute data quality indicators.

        Parameters
        ----------
        dataset_df : pd.DataFrame
            The dataset as a pandas DataFrame.

        Returns
        -------
        dict
            Dictionary with quality indicators including completeness,
            constant columns, high cardinality columns, and quality score.
        """
        if dataset_df.empty:
            return {}

        # Count rows with missing values
        rows_with_any_nan = int(dataset_df.isna().any(axis=1).sum())
        rows_with_multiple_nan = int((dataset_df.isna().sum(axis=1) > 1).sum())

        # Calculate overall data quality score
        # by combining completeness and uniqueness
        completeness = 1 - (
            dataset_df.isna().sum().sum() / (len(dataset_df) * len(dataset_df.columns))
        )

        hashable_cols = [
            c
            for c in dataset_df.columns
            if not isinstance(self.types.get(c), DashAIImage)
        ]
        all_categorical = hashable_cols and all(
            isinstance(self.types.get(c), Categorical) for c in hashable_cols
        )
        if hashable_cols and not all_categorical:
            duplicate_rows = int(dataset_df[hashable_cols].duplicated().sum())
        else:
            duplicate_rows = 0
        uniqueness = 1 - (duplicate_rows / len(dataset_df))
        data_quality_score = float((completeness * 0.7 + uniqueness * 0.3) * 100)

        # Compute unique counts (excluding image columns which are unhashable)
        nunique_series = (
            dataset_df[hashable_cols].nunique(dropna=False) if hashable_cols else {}
        )

        categorical_keys = self._get_categorical_columns()
        # Filter categorical columns to only hashable ones
        hashable_categorical_keys = [k for k in categorical_keys if k in hashable_cols]
        categorical_cols = (
            dataset_df[hashable_categorical_keys]
            if hashable_categorical_keys
            else dataset_df[[]]
        )
        nunique_categorical = (
            categorical_cols.nunique(dropna=False) if hashable_categorical_keys else {}
        )

        return {
            "constant_columns": [
                c
                for c in hashable_cols
                if c in nunique_series and int(nunique_series[c]) == 1
            ],
            "high_cardinality_columns": [
                c
                for c in hashable_categorical_keys
                if c in nunique_categorical and int(nunique_categorical[c]) > 100
            ],
            "possible_id_columns": [
                c for c in hashable_cols if dataset_df[c].is_unique
            ],
            "nan_ratio_per_column": {
                c: float(dataset_df[c].isna().mean()) for c in dataset_df.columns
            },
            "rows_with_any_nan": rows_with_any_nan,
            "rows_with_multiple_nan": rows_with_multiple_nan,
            "data_quality_score": data_quality_score,
        }

    def _compute_correlations(self, dataset_df) -> dict:
        """Compute correlation matrix for numeric columns.

        Parameters
        ----------
        dataset_df : pd.DataFrame
            The dataset as a pandas DataFrame.

        Returns
        -------
        dict
            Nested dictionary representing the correlation matrix.
        """
        numeric_keys = [
            k for k in self._get_numeric_columns() if k in dataset_df.columns
        ]
        numeric_cols = dataset_df[numeric_keys]

        if numeric_cols.empty:
            return {}

        corr_matrix = numeric_cols.corr(numeric_only=True)
        # Drop columns and rows from correlation matrix that are all NaN
        corr_matrix = corr_matrix.dropna(axis=0, how="all").dropna(axis=1, how="all")

        correlations = {}
        for col1 in corr_matrix.columns:
            col_corrs = {}
            for col2 in corr_matrix.columns:
                corr_val = float(corr_matrix.loc[col1, col2])
                col_corrs[col2] = round(corr_val, 4)
            if col_corrs:
                correlations[col1] = col_corrs

        return correlations

    @beartype
    def remove_columns(self, column_names: Union[str, List[str]]) -> "DashAIDataset":
        """Remove one or several column(s) in the dataset and the features
        associated to them.

        Parameters
        ----------
        column_names : Union[str, List[str]]
            Name, or list of names of columns to be removed.

        Returns
        -------
        DashAIDataset
            The dataset after columns removal.
        """
        if isinstance(column_names, str):
            column_names = [column_names]

        # Remove column from features
        modified_dataset = super().remove_columns(column_names)
        # Update self with modified dataset attributes
        self.__dict__.update(modified_dataset.__dict__)

        # Keep self.types in sync so Arrow metadata stays consistent
        if self.types is not None:
            for col in column_names:
                self.types.pop(col, None)

        return self

    @beartype
    def sample(
        self,
        n: int = 1,
        method: Literal["head", "tail", "random"] = "head",  # noqa
        seed: Union[int, None] = None,
    ) -> Dict[str, List]:
        """Return sample rows from dataset.

        Parameters
        ----------
        n : int
            number of samples to return.
        method: Literal[str]
            method for selecting samples. Possible values are: 'head' to
            select the first n samples, 'tail' to select the last n samples
            and 'random' to select n random samples.
        seed : int, optional
            seed for random number generator when using 'random' method.

        Returns
        -------
        Dict
            A dictionary with selected samples.
        """
        import numpy as np

        if n > len(self):
            raise ValueError(
                "Number of samples must be less than or equal to the length "
                f"of the dataset. Number of samples: {n}, "
                f"dataset length: {len(self)}"
            )

        if method == "random":
            rng = np.random.default_rng(seed=seed)
            indexes = rng.integers(low=0, high=(len(self) - 1), size=n)
            sample = self.select(indexes).to_dict()

        elif method == "head":
            sample = self[:n]

        elif method == "tail":
            sample = self[-n:]

        return sample

    @beartype
    def get_split(self, split_name: str) -> "DashAIDataset":
        """Return a new dataset containing only the rows of the requested split.

        Uses the ``"split_indices"`` metadata stored in :attr:`splits` to
        select the correct rows.

        Parameters
        ----------
        split_name : str
            Name of the split to extract (e.g. ``"train"``, ``"test"``,
            ``"validation"``).

        Returns
        -------
        DashAIDataset
            A new ``DashAIDataset`` containing only the rows of
            ``split_name``.

        Raises
        ------
        ValueError
            If ``split_name`` is not found in :attr:`splits`.
        """
        splits = self.splits.get("split_indices", {})
        if split_name not in splits:
            raise ValueError(f"Split '{split_name}' not found in dataset splits.")

        indices = splits[split_name]
        subset = self.select(indices)

        new_splits = {"split_indices": {split_name: indices}}
        arrow_table = subset.arrow_table  # with_format("arrow")[:] ####Check
        subset = DashAIDataset(arrow_table, splits=new_splits, types=self._types)
        return subset

    @beartype
    def select_columns(self, column_names: Union[str, List[str]]) -> "DashAIDataset":
        """Return a new dataset with only the specified columns.

        Parameters
        ----------
        column_names : str or list of str
            Name(s) of the column(s) to keep.

        Returns
        -------
        DashAIDataset
            A new ``DashAIDataset`` containing only the requested columns,
            with the corresponding types from the original dataset.
        """
        if isinstance(column_names, str):
            column_names = [column_names]

        subset_table = self.arrow_table.select(column_names)
        subset_types = {
            col: self._types[col] for col in column_names if col in self._types
        }

        return DashAIDataset(table=subset_table, splits=self.splits, types=subset_types)

    def __getitem__(self, key):
        result = super().__getitem__(key)
        if not isinstance(result, dict):
            return result

        image_cols = [
            c
            for c, t in self._types.items()
            if isinstance(t, DashAIImage) and c in result
        ]
        if not image_cols:
            return result

        if isinstance(key, int):
            for col in image_cols:
                if isinstance(result[col], dict):
                    result[col] = DashAIImage(
                        bytes=result[col].get("bytes"), path=result[col].get("path")
                    )
        elif isinstance(key, slice):
            for col in image_cols:
                result[col] = [
                    DashAIImage(bytes=v.get("bytes"), path=v.get("path"))
                    if isinstance(v, dict)
                    else v
                    for v in result[col]
                ]
        return result

    @beartype
    def select(self, *args, **kwargs) -> "DashAIDataset":
        """
        Selects rows from the dataset based on the provided indices or boolean mask.

        Parameters:
            *args: Positional arguments for selection.
            **kwargs: Keyword arguments for selection.

        Returns:
            DashAIDataset: A new DashAIDataset instance containing the selected rows.
        """
        selected_dataset = super().select(*args, **kwargs)
        if isinstance(selected_dataset, DashAIDataset):
            return selected_dataset
        else:
            # If the selected dataset is a Dataset, convert it to DashAIDataset
            arrow_tbl = selected_dataset.with_format("arrow")[:]
            arrow_tblx = save_types_in_arrow_metadata(
                arrow_tbl, {col: self._types[col].to_string() for col in self._types}
            )
            return DashAIDataset(arrow_tblx, types=self._types)


@beartype
def merge_splits_with_metadata(dataset_dict: object) -> DashAIDataset:
    """Merge all splits of a DatasetDict into a single DashAIDataset.

    Concatenates the splits in sorted key order and records the row-index
    range for each split in the ``splits`` metadata so they can later be
    recovered with :meth:`DashAIDataset.get_split`.

    Parameters
    ----------
    dataset_dict : DatasetDict
        A HuggingFace ``DatasetDict`` containing one or more named splits.

    Returns
    -------
    DashAIDataset
        A unified ``DashAIDataset`` whose :attr:`splits` metadata maps each
        split name to its original row indices.
    """

    from datasets import concatenate_datasets  # local import

    concatenated_datasets = []
    split_index = {}
    current_index = 0

    if len(dataset_dict.keys()) == 1:
        arrow_tbl = get_arrow_table(dataset_dict["train"])
        return DashAIDataset(arrow_tbl)

    for split in sorted(dataset_dict.keys()):
        ds = dataset_dict[split]
        n_rows = len(ds)
        split_index[split] = list(range(current_index, current_index + n_rows))
        current_index += n_rows
        concatenated_datasets.append(ds)
    merged_dataset = concatenate_datasets(concatenated_datasets)
    arrow_tbl = get_arrow_table(merged_dataset)

    dashai_metadata = get_arrow_table(dataset_dict["train"]).schema.metadata.get(
        b"dashai_types", None
    )
    # We overwrite the metadata with the original DashAI types
    # because concatenate_datasets resets it to the huggingface default
    if dashai_metadata is not None:
        new_metadata = dict(arrow_tbl.schema.metadata)
        new_metadata[b"dashai_types"] = dashai_metadata
        arrow_tbl = arrow_tbl.replace_schema_metadata(new_metadata)

    dashai_dataset = DashAIDataset(arrow_tbl, splits={"split_indices": split_index})

    return dashai_dataset


@beartype
def transform_dataset_with_schema(
    dataset: DashAIDataset, schema: Dict[str, Dict]
) -> DashAIDataset:
    """
    Transform dataset columns according to the specified schema.

    This function processes each column in the dataset according to the type information
    provided in the schema, converting data types as needed and updating the dataset's
    type metadata.

    Parameters
    ----------
    dataset : DashAIDataset
        The dataset to transform
    schema : Dict[str, Dict]
        Dictionary mapping column names to type information

    Returns
    -------
    DashAIDataset
        - The updated dataset with new type information
    """
    import pyarrow as pa  # local import

    table = get_arrow_table(dataset)
    dai_table = {}
    my_schema = pa.schema([])
    dashai_types = {}

    # First, include all columns from the dataset in the order they appear
    for column_name in dataset.column_names:
        if column_name not in schema:
            # Column not in schema - preserve it as-is with inferred type
            col_data = table.column(column_name)
            dai_table[column_name] = col_data
            pa_type = table.schema.field(column_name).type
            my_schema = my_schema.append(pa.field(column_name, pa_type))

            # Infer the DashAI type from Arrow type
            dashai_types[column_name] = arrow_to_dashai_types(pa_type)
        else:
            # Column is in schema - process according to schema definition
            info = schema[column_name]
            _type = info.get("type")
            dtype = info.get("dtype")
            pa_type = to_arrow_types(dtype)
            if _type == "Categorical":
                base_col = table.column(column_name)
                converted = info.get("converted", False)

                # Always infer categories from actual data to ensure all values are
                # included. Type inference (ptype) excludes anomalous values from
                # its suggested categories, which causes KeyErrors during training
                # when those "anomalous" values appear in the data.
                col_list = base_col.to_pylist()
                categories = sorted({v for v in col_list if v is not None})

                encoder = info.get("encoder", "one_hot")
                dashai_types[column_name] = Categorical(
                    values=categories, converted=converted, dtype=dtype, encoder=encoder
                )
                # Keep the column data as-is without converting to string
                dai_table[column_name] = base_col
                # Use the dtype from schema for pa_type
                pa_type = to_arrow_types(dtype)
            elif _type == "Image":
                dashai_types[column_name] = DashAIImage(dtype=dtype)
                dai_table[column_name] = table.column(column_name)
                pa_type = table.schema.field(column_name).type
            else:
                if _type in ["Date", "Time", "Timestamp"]:
                    # Since DashAI is not using date, time or timestamp types for its
                    # models
                    # we are saving them as strings to preserve the original format.
                    # Can modify classes in value_types.py
                    # if want to use PyArrow date, time or timestamp types.
                    #
                    # Two dict shapes reach this function. The one built by
                    # type inference and by get_columns_spec carries the
                    # strptime format in "dtype"; the one a column emits
                    # through to_string() carries it in "format" and leaves
                    # "dtype" as the arrow type. Reading only "dtype" turned
                    # the second shape's format into the literal "string".
                    _format = info.get("format") or dtype
                    if not _format:
                        raise ValueError(
                            f"Column '{column_name}' is typed as {_type} but "
                            "carries no format. A date, time or timestamp "
                            "column is stored as text plus a strptime format, "
                            "so the format has to be resolved before saving."
                        )
                    dashai_types[column_name] = arrow_to_dashai_types(
                        arrow_type=_type, format=_format
                    )
                    pa_type = to_arrow_types("string")
                    dai_table[column_name] = table.column(column_name)

                elif _type == "Float":
                    dashai_types[column_name] = arrow_to_dashai_types(pa_type)
                    dai_table[column_name] = comma_float_to_float(
                        table.column(column_name)
                    )

                else:
                    dashai_types[column_name] = arrow_to_dashai_types(pa_type)
                    dai_table[column_name] = table.column(column_name)

            my_schema = my_schema.append(pa.field(column_name, pa_type))

    # Create the transformed table with the new schema
    transformed_table = pa.table(dai_table)
    transformed_table = transformed_table.cast(target_schema=my_schema)

    # Update dataset types
    dataset._types = dashai_types

    # Save types in arrow metadata
    types = {col: dashai_types[col].to_string() for col in dashai_types}
    transformed_table = save_types_in_arrow_metadata(transformed_table, types)

    return DashAIDataset(transformed_table, splits=dataset.splits, types=dashai_types)


@beartype
def save_dataset(
    dataset: DashAIDataset, path: Union[str, os.PathLike], schema=None
) -> None:
    """Save a DashAIDataset to disk in DashAI's two-file format.

    Creates the directory at ``path`` if needed, then writes:

    * ``data.arrow``: the PyArrow IPC file containing the table.
    * ``splits.json``: JSON file with split indices and row counts.

    Parameters
    ----------
    dataset : DashAIDataset
        The dataset to persist.
    path : str or os.PathLike
        Directory path where the two output files will be written.
    schema : object or None, optional
        If provided, the dataset is transformed with ``transform_dataset_with_schema``
        before saving. Default ``None``.
    """

    import json
    from pathlib import Path as _Path

    import pyarrow as pa  # local import

    from DashAI.back.core.atomic import atomic_directory

    if schema is not None:
        dataset = transform_dataset_with_schema(dataset, schema)

    table = get_arrow_table(dataset)

    with atomic_directory(_Path(path)) as tmp_dir:
        data_filepath = tmp_dir / "data.arrow"
        with pa.OSFile(str(data_filepath), "wb") as sink:
            writer = pa.ipc.new_file(sink, table.schema)
            writer.write_table(table)
            writer.close()

        metadata = dataset.splits
        metadata.update(
            {
                "total_rows": dataset.shape[0],
                "column_names": dataset.column_names,
            }
        )

        if "general_info" in metadata:
            metadata["general_info"]["memory_usage_mb"] = (
                os.path.getsize(data_filepath) / 1e6
            )

        metadata_filepath = tmp_dir / "splits.json"
        with open(metadata_filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, sort_keys=True, ensure_ascii=False)


@beartype
def load_dataset(dataset_path: Union[str, os.PathLike]) -> DashAIDataset:
    """Load a DashAIDataset previously saved with :func:`save_dataset`.

    Expects the directory at ``dataset_path`` to contain:

    * ``data.arrow``: the PyArrow IPC file.
    * ``splits.json``: JSON file with split indices (optional).

    Parameters
    ----------
    dataset_path : str or os.PathLike
        Directory path where the dataset files are stored.

    Returns
    -------
    DashAIDataset
        The restored dataset with data and split metadata.
    """

    import json

    import pyarrow as pa  # local import

    data_filepath = os.path.join(dataset_path, "data.arrow")
    with pa.OSFile(data_filepath, "rb") as source:
        reader = pa.ipc.open_file(source)
        data = reader.read_all()
    metadata_filepath = os.path.join(dataset_path, "splits.json")
    if os.path.exists(metadata_filepath):
        with open(metadata_filepath, "r", encoding="utf-8") as f:
            splits = json.load(f)
    else:
        splits = {}
    return DashAIDataset(data, splits=splits)


@beartype
def check_split_values(
    train_size: float,
    test_size: float,
    val_size: float,
) -> None:
    """Validate that each split proportion is in the open interval (0, 1).

    Parameters
    ----------
    train_size : float
        Proportion of samples assigned to the training split.
    test_size : float
        Proportion of samples assigned to the test split.
    val_size : float
        Proportion of samples assigned to the validation split.

    Raises
    ------
    ValueError
        If any of the proportions is less than 0 or greater than 1.
    """
    if train_size < 0 or train_size > 1:
        raise ValueError(
            "train_size should be in the (0, 1) range "
            f"(0 and 1 not included), got {val_size}"
        )
    if test_size < 0 or test_size > 1:
        raise ValueError(
            "test_size should be in the (0, 1) range "
            f"(0 and 1 not included), got {val_size}"
        )
    if val_size < 0 or val_size > 1:
        raise ValueError(
            "val_size should be in the (0, 1) range "
            f"(0 and 1 not included), got {val_size}"
        )


@beartype
def split_indexes(
    total_rows: int,
    train_size: float,
    test_size: float,
    val_size: float,
    seed: Union[int, None] = None,
    shuffle: bool = True,
    stratify: bool = False,
    labels: Union[List, None] = None,
) -> Tuple[List, List, List]:
    """Generate lists with train, test and validation indexes.

    The algorithm for splitting the dataset is as follows:

    1. The dataset is divided into a training and a test-validation split
        (sum of test_size and val_size).
    2. The test and validation set is generated from the test-validation set,
        where the size of the test-validation set is now considered to be 100%.
        Therefore, the sizes of the test and validation sets will now be
        calculated as 100%, i.e. as val_size/(test_size+val_size) and
        test_size/(test_size+val_size) respectively.

    Example:

    If we split a dataset into 0.8 training, a 0.1 test, and a 0.1 validation,
    in the first process we split the training data with 80% of the data, and
    the test-validation data with the remaining 20%; and then in the second
    process we split this 20% into 50% test and 50% validation.

    Parameters
    ----------
    total_rows : int
        Size of the Dataset.
    train_size : float
        Proportion of the dataset for train split (in 0-1).
    test_size : float
        Proportion of the dataset for test split (in 0-1).
    val_size : float
        Proportion of the dataset for validation split (in 0-1).
    seed : Union[int, None], optional
        Set seed to control to enable replicability, by default None
    shuffle : bool, optional
        If True, the data will be shuffled when splitting the dataset,
        by default True.
    stratify : bool, optional
        If True, the data will be stratified when splitting the dataset,
        by default False.

    Returns
    -------
    Tuple[List, List, List]
        Train, Test and Validation indexes.
    """

    # Generate shuffled indexes
    if seed is None:
        seed = 42
    import numpy as np
    from sklearn.model_selection import train_test_split

    indexes = np.arange(total_rows)
    stratify_labels = np.array(labels) if stratify else None

    if test_size == 0 and val_size == 0:
        return indexes.tolist(), [], []

    if test_size == 0:
        train_indexes, val_indexes = train_test_split(
            indexes,
            train_size=train_size,
            random_state=seed,
            shuffle=shuffle,
            stratify=stratify_labels,
        )
        return train_indexes.tolist(), [], val_indexes.tolist()

    if val_size == 0:
        train_indexes, test_indexes = train_test_split(
            indexes,
            train_size=train_size,
            random_state=seed,
            shuffle=shuffle,
            stratify=stratify_labels,
        )
        return train_indexes.tolist(), test_indexes.tolist(), []

    test_val = test_size + val_size
    val_proportion = test_size / test_val

    train_indexes, test_val_indexes = train_test_split(
        indexes,
        train_size=train_size,
        random_state=seed,
        shuffle=shuffle,
        stratify=stratify_labels,
    )

    stratify_labels_test_val = stratify_labels[test_val_indexes] if stratify else None

    test_indexes, val_indexes = train_test_split(
        test_val_indexes,
        train_size=val_proportion,
        random_state=seed,
        shuffle=shuffle,
        stratify=stratify_labels_test_val,
    )
    return train_indexes.tolist(), test_indexes.tolist(), val_indexes.tolist()


@beartype
def split_dataset(
    dataset: DashAIDataset,
    train_indexes: List = None,
    test_indexes: List = None,
    val_indexes: List = None,
) -> object:
    """
    Split the dataset in train, test and validation subsets.
    If indexes are not provided, it will use the split indices
    from the dataset's splits.

    Parameters
    ----------
    dataset : DashAIDataset
        A HuggingFace DashAIDataset containing the dataset to be split.
    train_indexes : List, optional
        Train split indexes. If None, uses indices from splits.
    test_indexes : List, optional
        Test split indexes. If None, uses indices from splits.
    val_indexes : List, optional
        Validation split indexes. If None, uses indices from splits.

    Returns
    -------
    DatasetDict
        The split dataset.

    Raises
    -------
    ValueError
        Must provide all indexes or none.
    """
    import numpy as np

    if all(idx is None for idx in [train_indexes, test_indexes, val_indexes]):
        from datasets import DatasetDict

        train_dataset = dataset.get_split("train")
        test_dataset = dataset.get_split("test")
        val_dataset = dataset.get_split("validation")
        return DatasetDict(
            {
                "train": train_dataset,
                "test": test_dataset,
                "validation": val_dataset,
            }
        )
    elif any(idx is None for idx in [train_indexes, test_indexes, val_indexes]):
        raise ValueError("Must provide all indexes or none.")

    # Get the number of records
    n = len(dataset)

    # Convert the indexes into boolean masks
    train_mask = np.isin(np.arange(n), train_indexes)
    test_mask = np.isin(np.arange(n), test_indexes)
    val_mask = np.isin(np.arange(n), val_indexes)

    # Get the underlying table
    import pyarrow as pa  # local import

    table = dataset.arrow_table

    dataset.splits["split_indices"] = {
        "train": train_indexes,
        "test": test_indexes,
        "validation": val_indexes,
    }

    # Create separate tables for each split
    train_table = table.filter(pa.array(train_mask))
    test_table = table.filter(pa.array(test_mask))
    val_table = table.filter(pa.array(val_mask))

    # Preserve types from the original dataset to maintain categorical mappings
    from datasets import DatasetDict  # local import

    separate_dataset_dict = DatasetDict(
        {
            "train": DashAIDataset(train_table, types=dataset.types),
            "test": DashAIDataset(test_table, types=dataset.types),
            "validation": DashAIDataset(val_table, types=dataset.types),
        }
    )

    return separate_dataset_dict


def split_dataset_cv(
    dataset: DashAIDataset,
    train_indexes: List = None,
    test_indexes: List = None,
    second_split_name: str = "test",
) -> object:
    """
    Split a dataset into two subsets for cross-validation.

    Parameters
    ----------
    dataset : DashAIDataset
        A HuggingFace DashAIDataset containing the data to be partitioned.
    train_indexes : List, optional
        Indices of the rows assigned to the training subset.
    test_indexes : List, optional
        Indices of the rows assigned to the second subset.
    second_split_name : str, optional
        Name the second subset takes in the returned dictionary. Folds are
        scored on their ``"validation"`` partition; the trailing entry that
        fits the final model keeps the default ``"test"`` for the reserved
        rows it is measured on.

    Returns
    -------
    DatasetDict
        A dataset dictionary containing the train split and the second split.
    """
    import numpy as np

    # Get the number of records
    n = len(dataset)

    # Convert the indexes into boolean masks
    train_mask = np.isin(np.arange(n), train_indexes)
    test_mask = np.isin(np.arange(n), test_indexes)

    # Get the underlying table
    import pyarrow as pa  # local import

    table = dataset.arrow_table

    # Create separate tables for each split
    train_table = table.filter(pa.array(train_mask))
    test_table = table.filter(pa.array(test_mask))

    # Preserve types from the original dataset to maintain categorical mappings
    from datasets import DatasetDict  # local import

    separate_dataset_dict = DatasetDict(
        {
            "train": DashAIDataset(train_table, types=dataset.types),
            second_split_name: DashAIDataset(test_table, types=dataset.types),
        }
    )

    return separate_dataset_dict


def to_dashai_dataset(
    dataset: object,
    types: Optional[Dict[str, DashAIDataType]] = None,
) -> DashAIDataset:
    """Convert various dataset formats into a unified ``DashAIDataset``.

    Accepts ``DashAIDataset`` (pass through), HuggingFace ``Dataset``,
    HuggingFace ``DatasetDict`` (merged via
    :func:`merge_splits_with_metadata`), and ``pandas.DataFrame``.

    Parameters
    ----------
    dataset : DashAIDataset, Dataset, DatasetDict, or pd.DataFrame
        The source dataset to convert.
    types : dict of {str: DashAIDataType} or None, optional
        Column-type mapping to embed in the Arrow metadata. If ``None``,
        types are inferred from the Arrow schema. Default ``None``.

    Returns
    -------
    DashAIDataset
        A unified ``DashAIDataset`` containing all rows from ``dataset``.
    """

    if isinstance(dataset, DashAIDataset):
        return dataset

    from datasets import Dataset as HFDataset  # local import

    if isinstance(dataset, HFDataset):
        arrow_tbl = get_arrow_table(dataset)
        if types:
            types_serialized = {col: types[col].to_string() for col in types}
            arrow_tbl = save_types_in_arrow_metadata(arrow_tbl, types_serialized)
        return DashAIDataset(arrow_tbl, types=types)
    try:
        from pandas import DataFrame as PDDataFrame  # local import
    except Exception:
        PDDataFrame = None
    if PDDataFrame is not None and isinstance(dataset, PDDataFrame):
        hf_dataset = HFDataset.from_pandas(dataset, preserve_index=False)
        arrow_tbl = get_arrow_table(hf_dataset)
        if types:
            types_serialized = {col: types[col].to_string() for col in types}
            arrow_tbl = save_types_in_arrow_metadata(arrow_tbl, types_serialized)
        return DashAIDataset(arrow_tbl, types=types)
    from datasets import DatasetDict  # local import

    if isinstance(dataset, DatasetDict) and len(dataset) == 1:
        key = list(dataset.keys())[0]
        ds = dataset[key]
        arrow_tbl = get_arrow_table(ds)
        if types:
            types_serialized = {col: types[col].to_string() for col in types}
            arrow_tbl = save_types_in_arrow_metadata(arrow_tbl, types_serialized)
        return DashAIDataset(arrow_tbl, types=types)
    if isinstance(dataset, DatasetDict):
        return merge_splits_with_metadata(dataset)
    else:
        raise TypeError(f"Unsupported dataset type: {type(dataset)}")


@beartype
def validate_inputs_outputs(
    datasetdict: object,
    inputs: List[str],
    outputs: List[str],
) -> None:
    """Validate the columns to be chosen as input and output.
    The algorithm considers those that already exist in the dataset.

    Parameters
    ----------
    names : List[str]
        Dataset column names.
    inputs : List[str]
        List of input column names.
    outputs : List[str]
        List of output column names.
    """
    datasetdict = to_dashai_dataset(datasetdict)
    dataset_features = list((datasetdict.features).keys())
    if len(inputs) == 0 or len(outputs) == 0:
        raise ValueError(
            "Inputs and outputs columns lists to validate must not be empty"
        )
    if len(inputs) + len(outputs) > len(dataset_features):
        raise ValueError(
            "Inputs and outputs cannot have more elements than names. "
            f"Number of inputs: {len(inputs)}, "
            f"number of outputs: {len(outputs)}, "
            f"number of names: {len(dataset_features)}. "
        )
        # Validate that inputs and outputs only contain elements that exist in names
    if not set(dataset_features).issuperset(set(inputs + outputs)):
        raise ValueError(
            f"Inputs and outputs can only contain elements that exist in names. "
            f"Extra elements: "
            f"{', '.join(set(inputs + outputs).difference(set(dataset_features)))}"
        )


@beartype
def get_column_names_from_indexes(dataset: object, indexes: List[int]) -> List[str]:
    """Obtain the column labels that correspond to the provided indexes.

    Note: indexing starts from 1.

    Parameters
    ----------
    datasetdict : DatasetDict
        Path where the dataset is stored.
    indices : List[int]
        List with the indices of the columns.

    Returns
    -------
    List[str]
        List with the labels of the columns
    """
    dataset = to_dashai_dataset(dataset)

    dataset_features = list((dataset.features).keys())
    col_names = []
    for index in indexes:
        if index > len(dataset_features):
            raise ValueError(
                f"The list of indices can only contain elements within"
                f" the amount of columns. "
                f"Index {index} is greater than the total of columns."
            )
        col_names.append(dataset_features[index - 1])
    return col_names


@beartype
def select_columns(
    dataset: object,
    input_columns: List[str],
    output_columns: List[str],
) -> Tuple[DashAIDataset, DashAIDataset]:
    """Divide the dataset into a dataset with only the input columns in it
    and other dataset only with the output columns

    Parameters
    ----------
    dataset : Union[DatasetDict, DashAIDataset]
        Dataset to divide
    input_columns : List[str]
        List with the input columns labels
    output_columns : List[str]
        List with the output columns labels

    Returns
    -------
    DashAIDataset
        Tuple with the separated datasets x and y
    """
    dataset = to_dashai_dataset(dataset)
    input_columns_dataset = dataset.select_columns(input_columns)
    output_columns_dataset = dataset.select_columns(output_columns)
    return (input_columns_dataset, output_columns_dataset)


@beartype
def get_columns_spec(dataset_path: str) -> Dict[str, Dict]:
    """Return the column with their respective types.

    This function reads only the schema metadata from the Arrow file without
    loading the entire dataset into memory, making it much more efficient.

    Parameters
    ----------
    dataset_path : str
        Path where the dataset is stored.

    Returns
    -------
    Dict
        Dict with the columns and types
    """
    data_filepath = os.path.join(dataset_path, "data.arrow")

    import pyarrow as pa  # local import

    with pa.OSFile(data_filepath, "rb") as source:
        reader = pa.ipc.open_file(source)
        schema = reader.schema

    types_dict = get_types_from_arrow_metadata(schema)

    column_types = {}
    for column_name, column_type in types_dict.items():
        spec_dict = column_type.to_string()

        dtype = spec_dict.get("dtype")
        _format = spec_dict.get("format")

        column_info = {
            "type": spec_dict.get("type"),
            "dtype": _format if _format else dtype,
        }

        if spec_dict.get("type") == "Categorical":
            column_info["categories"] = spec_dict.get("categories", [])
            column_info["num_categories"] = spec_dict.get("num_categories", 0)
            column_info["converted"] = spec_dict.get("converted", False)
            column_info["encoder"] = spec_dict.get("encoder", "one_hot")

        column_types[column_name] = column_info

    return column_types


# Not currently used, will be used to change column types after upload
@beartype
def update_columns_spec(dataset_path: str, columns: Dict) -> DashAIDataset:
    """Update the column specification of some dataset on secondary memory.

    If the column type isn't a Value or ClassLabel, the function will
    not change the type of the column.

    Parameters
    ----------
    dataset_path : str
        Path where the dataset is stored.
    columns : Dict
        Dict with columns and types to change

    Returns
    -------
    Dict
        Dict with the columns and types
    """
    if not isinstance(columns, dict):
        raise TypeError(f"types should be a dict, got {type(columns)}")

    # load the dataset from where its stored
    dataset = load_dataset(dataset_path)
    # copy the features with the columns ans types
    new_features = dataset.features
    for column in columns:
        if columns[column].type == "ClassLabel" or columns[column].type == "Value":
            pass

        # cast the column types with the changes
        try:
            dataset = dataset.cast(new_features)

        except ValueError as e:
            raise ValueError("Error while trying to cast the columns") from e
    return dataset


def get_dataset_info(dataset_path: str) -> object:
    """Return the info of the dataset with the number of rows,
    number of columns and splits size.

    Parameters
    ----------
    dataset_path : str
        Path where the dataset is stored.

    Returns
    -------
    object
        Dictionary with the information of the dataset
    """
    import json

    metadata_filepath = os.path.join(dataset_path, "splits.json")
    if os.path.exists(metadata_filepath):
        with open(metadata_filepath, "r", encoding="utf-8") as f:
            splits_data = json.load(f)
    else:
        splits_data = {"split_indices": {}}

    splits = splits_data.get("split_indices", {})
    train_indices = splits.get("train", [])
    test_indices = splits.get("test", [])
    val_indices = splits.get("validation", [])
    total_rows = splits_data.get("total_rows", 0)
    column_names = splits_data.get("column_names", [])

    return {
        "total_rows": total_rows,
        "total_columns": len(column_names),
        "column_names": column_names,
        "nan": splits_data.get("nan", {}),
        "train_size": len(train_indices),
        "test_size": len(test_indices),
        "val_size": len(val_indices),
        "train_indices": train_indices,
        "test_indices": test_indices,
        "val_indices": val_indices,
        **splits_data,
    }


@beartype
def update_dataset_splits(
    dataset: DashAIDataset, new_splits: object, is_random: bool
) -> DashAIDataset:
    """Update the split configuration of a DashAIDataset in place.

    Supports two modes: random proportional splits (floats summing to 1.0)
    and manual index-based splits (lists of row indices).

    Parameters
    ----------
    dataset : DashAIDataset
        Dataset whose :attr:`splits` metadata will be updated.
    new_splits : object
        Mapping with keys ``"train"``, ``"test"``, ``"validation"``. Values
        are floats (proportions, when ``is_random=True``) or lists of int
        (explicit row indices, when ``is_random=False``).
    is_random : bool
        If ``True``, ``new_splits`` values are fractional proportions and
        rows are assigned randomly. If ``False``, ``new_splits`` values are
        explicit index lists.

    Returns
    -------
    DashAIDataset
        The same ``dataset`` object with an updated ``splits`` dict.
    """
    n = dataset.num_rows
    if is_random:
        check_split_values(
            new_splits["train"], new_splits["test"], new_splits["validation"]
        )
        train_indexes, test_indexes, val_indexes = split_indexes(
            n, new_splits["train"], new_splits["test"], new_splits["validation"]
        )
    else:
        train_indexes = new_splits["train"]
        test_indexes = new_splits["test"]
        val_indexes = new_splits["validation"]
    dataset.splits["split_indices"] = {
        "train": train_indexes,
        "test": test_indexes,
        "validation": val_indexes,
    }
    return dataset


# I'm not completely sure what this function does in converting categorical indexes part
# I think it could be simplified since DashAITypes, but I don't want to break anything
def prepare_for_model_session(
    dataset: DashAIDataset, splits: dict, output_columns: List[str]
) -> object:
    """Prepare a dataset for a model training or prediction session.

    Applies the requested split configuration (manual, predefined, or random),
    separates features from targets, and encodes categorical output columns
    as integer indices.

    Parameters
    ----------
    dataset : DashAIDataset
        The unified dataset to split and preprocess.
    splits : dict
        Split configuration with at least a ``"splitType"`` key
        (``"manual"``, ``"predefined"``, or ``"random"``). Manual and
        predefined splits carry their row indexes in ``"splitted_indexes"``
        (``"train_indexes"``, ``"test_indexes"``, ``"val_indexes"``), or, for
        sessions created before the splits payload followed the splitter
        schema, in ``"train"``, ``"test"`` and ``"validation"`` index lists.
        Random splits carry float proportions summing to 1.0 and an optional
        ``"random_state"`` (``"seed"`` in older sessions).
    output_columns : list of str
        Names of the columns to use as model targets.

    Returns
    -------
    object
        A prepared dataset object (structure depends on internal helpers).
    """
    from contextlib import suppress

    splitType = splits.get("splitType")
    if splitType == "manual" or splitType == "predefined":
        # The indexes travel under "splitted_indexes"; sessions created before
        # the splits payload followed the splitter schema stored them under the
        # partition names instead.
        splitted_indexes = splits.get("splitted_indexes") or {}
        if splitted_indexes:
            train_indexes = splitted_indexes.get("train_indexes", [])
            test_indexes = splitted_indexes.get("test_indexes", [])
            val_indexes = splitted_indexes.get("val_indexes", [])
        else:
            train_indexes = splits["train"]
            test_indexes = splits["test"]
            val_indexes = splits["validation"]
        prepared_dataset = split_dataset(
            dataset,
            train_indexes=train_indexes,
            test_indexes=test_indexes,
            val_indexes=val_indexes,
        )
    else:
        n = len(dataset)
        labels = None
        if splits.get("stratify", False) and output_columns:
            output_column = output_columns[0]
            column_type = dataset.types[output_column]
            try:
                column_values = dataset[output_column]
                if isinstance(column_type, Categorical):
                    with suppress(Exception):
                        labels = (
                            [column_type.str2int(v) for v in column_values]
                            if column_values
                            else []
                        )
                else:
                    labels = [
                        int(x) if not isinstance(x, (list, tuple)) else int(x[0])
                        for x in column_values
                    ]
            except Exception as e:
                raise ValueError(
                    f"Error while trying to stratify the dataset: {e}"
                ) from e

        train_indexes, test_indexes, val_indexes = split_indexes(
            n,
            float(splits["train"]),
            float(splits["test"]),
            float(splits["validation"]),
            shuffle=splits.get("shuffle", False),
            seed=splits.get("random_state", splits.get("seed")),
            stratify=splits.get("stratify", False),
            labels=labels,
        )
        prepared_dataset = split_dataset(
            dataset,
            train_indexes=train_indexes,
            test_indexes=test_indexes,
            val_indexes=val_indexes,
        )
    return prepared_dataset, {
        "train_indexes": train_indexes,
        "test_indexes": test_indexes,
        "val_indexes": val_indexes,
    }


def modify_table(
    dataset: DashAIDataset,
    columns: Dict[str, object],
    types: Optional[Dict[str, DashAIDataType]] = None,
) -> DashAIDataset:
    """
    Modifies the pa.table and its pa.type of a column in a DashAIDataset.
    This function serves as a tool for models to modify the data in order to process it.

    Parameters
    ----------
    dataset : DashAIDataset
        The dataset to modify.
    columns: dict[str, pa.Array]
        A dictionary where keys are column names and values are the new PyArrow arrays.

    Returns
    -------
    DashAIDataset
        The modified dataset with the updated column type.
    """
    import pyarrow as pa

    original_table = dataset.arrow_table
    updated_columns = {}

    for name in dataset.column_names:
        if name in columns:
            updated_columns[name] = columns[name]
        else:
            updated_columns[name] = original_table[name]

    for name in columns:
        if name not in dataset.column_names:
            if types is None or name not in types:
                raise ValueError(
                    f"Missing DashAI type for new column '{name}', "
                    f"check if converter provides it."
                )
            updated_columns[name] = columns[name]

    new_table = pa.table(updated_columns)

    new_table = new_table.replace_schema_metadata(original_table.schema.metadata)
    new_table = (
        save_types_in_arrow_metadata(
            new_table, {col: types[col].to_string() for col in types}
        )
        if types
        else new_table
    )

    new_types = types if types else dataset.types

    return DashAIDataset(new_table, splits=dataset.splits, types=new_types)
