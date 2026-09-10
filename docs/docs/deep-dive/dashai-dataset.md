---
title: DashAIDataset
sidebar_label: DashAIDataset
sidebar_position: 9
---

# DashAIDataset

## What Is DashAIDataset?

`DashAIDataset` is dashAI's core dataset primitive. It extends the HuggingFace `Dataset` class with two additional responsibilities:

- **Semantic type metadata**: a `_types` dictionary (`Dict[str, DashAIDataType]`) that maps every column name to its dashAI semantic type (see [Semantic Types](/deep-dive/semantic-types)). This metadata is persisted inside the Apache Arrow schema so it survives save/load round trips.
- **Split metadata**: a `splits` dictionary that records which row indices belong to which split (`train`, `test`, `validation`), plus aggregate statistics computed during upload.

Every piece of data that flows through dashAI (upload, notebook transformations, model training, predictions) is represented as a `DashAIDataset`.

---

## Internal Structure

### Instance Attributes

| Attribute | Type                        | Description                                                      |
| --------- | --------------------------- | ---------------------------------------------------------------- |
| `_table`  | `pyarrow.Table`             | The underlying Arrow table. All column data lives here.          |
| `_types`  | `Dict[str, DashAIDataType]` | Semantic type for each column. Kept in sync with Arrow metadata. |
| `splits`  | `dict`                      | Split indices and computed statistics (see below).               |

### The `splits` Dictionary

`splits` is a plain Python dict. Its keys are populated progressively:

| Key                 | Set by                                    | Content                                                                  |
| ------------------- | ----------------------------------------- | ------------------------------------------------------------------------ |
| `split_indices`     | `split_dataset` / `update_dataset_splits` | `{"train": [...], "test": [...], "validation": [...]}` (row index lists) |
| `column_names`      | `compute_base_metadata` / `save_dataset`  | List of column names                                                     |
| `total_rows`        | `compute_base_metadata` / `save_dataset`  | Total row count                                                          |
| `nan`               | `compute_base_metadata`                   | Per column NaN counts                                                    |
| `general_info`      | `compute_metadata`                        | Row/column counts, memory, duplicates, dtype map                         |
| `numeric_stats`     | `compute_metadata`                        | Per column descriptive statistics for numeric columns                    |
| `categorical_stats` | `compute_metadata`                        | Per column value counts and top 5 for categorical columns                |
| `text_stats`        | `compute_metadata`                        | Length and word count statistics for text columns                        |
| `quality_info`      | `compute_metadata`                        | Completeness, constant columns, high cardinality columns, quality score  |
| `correlations`      | `compute_metadata`                        | Pearson correlation matrix for numeric columns                           |

### Arrow Metadata

Semantic types are serialised to the Arrow table's schema metadata under the key `dashai_types`. This means:

```python
table.schema.metadata[b"dashai_types"]  # JSON-serialised type map
```

The utilities `save_types_in_arrow_metadata()` and `get_types_from_arrow_metadata()` in `DashAI/back/types/utils.py` handle this serialisation. When `DashAIDataset` is constructed with `types=None`, it reads the type map directly from the Arrow metadata.

---

## On disk Format

`save_dataset` writes two files to a directory:

```
<dataset_path>/
├── data.arrow    # PyArrow IPC file - table + type metadata in schema
└── splits.json   # JSON - split indices, row counts, NaN map, computed stats
```

`load_dataset` reads both files and reconstructs the `DashAIDataset`. Types are recovered from the Arrow schema metadata, so no separate type file is needed.

---

## Key Instance Methods

### `get_split(split_name)`

Returns a new `DashAIDataset` containing only the rows of the requested split.

```python
train_ds = dataset.get_split("train")  # uses split_indices["train"]
```

`split_name` must exist in `splits["split_indices"]`. The returned dataset's `splits` metadata contains only that split's index list.

### `select_columns(column_names)`

Returns a new `DashAIDataset` with only the specified columns, copying the corresponding types.

```python
features_ds = dataset.select_columns(["age", "income", "city"])
```

### `sample(n, method, seed)`

Returns `n` rows as a plain Python `dict`. `method` controls selection:

| Method     | Behaviour                                  |
| ---------- | ------------------------------------------ |
| `"head"`   | First `n` rows                             |
| `"tail"`   | Last `n` rows                              |
| `"random"` | `n` random rows (reproducible with `seed`) |

### `compute_metadata()`

Runs all EDA computations and stores results in `self.splits`. Called once after upload. Requires `_types` to be set. Returns `self`.

### `compute_base_metadata()`

Lightweight subset of `compute_metadata()` that only sets `column_names`, `total_rows`, and `nan`. Used when full stats are not needed.

### `keys()`

Returns the list of available split names from `splits["split_indices"]`. Mirrors the `DatasetDict.keys()` interface so `DashAIDataset` can be used interchangeably in some contexts.

---

## Data Lifecycle Functions

These module level functions cover the full journey from raw input to training ready splits.

### Loading and Conversion

**`to_dashai_dataset(dataset, types=None)`**

Universal converter. Accepts `DashAIDataset` (pass through), HuggingFace `Dataset`, HuggingFace `DatasetDict`, or `pandas.DataFrame`. Multisplit `DatasetDict` inputs are merged via `merge_splits_with_metadata`.

```python
from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

ds = to_dashai_dataset(my_hf_dataset, types=my_type_map)
```

**`merge_splits_with_metadata(dataset_dict)`**

Concatenates all splits of a `DatasetDict` into a single `DashAIDataset` and records the row index ranges in `splits["split_indices"]`. The splits are merged in sorted key order.

### Persistence

**`save_dataset(dataset, path, schema=None)`**

Writes `data.arrow` and `splits.json` to `path`. If `schema` is provided, `transform_dataset_with_schema` is applied first.

**`load_dataset(dataset_path)`**

Reads `data.arrow` and `splits.json` from `dataset_path` and returns a `DashAIDataset`. Types are recovered from Arrow metadata.

**`get_columns_spec(dataset_path)`**

Reads only the Arrow schema (no row data) and returns a `Dict[str, Dict]` describing each column's type, dtype, and (for `Categorical` columns) the category list. Used by the API to return column metadata without loading the full dataset.

### Type Transformation

**`transform_dataset_with_schema(dataset, schema)`**

Applies a type schema to the dataset, casting columns to their target Arrow types and updating `_types`. The `schema` format is:

```python
schema = {
    "age": {"type": "Integer", "dtype": "int64"},
    "income": {"type": "Float", "dtype": "float64"},
    "city": {"type": "Categorical", "dtype": "string", "converted": False},
}
```

`Categorical` columns have their category list inferred from the actual data at this point, ensuring no values are silently excluded.

### Splitting

**`split_indexes(total_rows, train_size, test_size, val_size, seed, shuffle, stratify, labels)`**

Returns `(train_indexes, test_indexes, val_indexes)` as lists of integer row indices. Uses a two phase strategy:

1. Split all rows into `train` vs `test+validation`.
2. Split `test+validation` into `test` and `validation` proportionally.

Supports stratified splitting: pass the label array in `labels`.

**`split_dataset(dataset, train_indexes, test_indexes, val_indexes)`**

Partitions `dataset` into a `DatasetDict` with `"train"`, `"test"`, and `"validation"` keys, each being a `DashAIDataset`. Column types from the original dataset are preserved.

If all three index arguments are `None`, the function reads existing `split_indices` from `dataset.splits` instead.

**`update_dataset_splits(dataset, new_splits, is_random)`**

Updates `dataset.splits["split_indices"]` in place.

- `is_random=True`: `new_splits` values are float proportions; `split_indexes` is called to generate row lists.
- `is_random=False`: `new_splits` values are already row index lists; used directly.

### Training Preparation

**`prepare_for_model_session(dataset, splits, output_columns)`**

High level entry point used by the job system before training. Handles the full split pipeline:

1. Determines split type from `splits["splitType"]` (`"manual"`, `"predefined"`, or `"random"`).
2. Calls `split_dataset` with the appropriate index lists.
3. Returns `(prepared_dataset, index_map)` where `index_map` has keys `train_indexes`, `test_indexes`, `val_indexes`.

For random splits with `stratify=True`, it reads the output column values and passes them as labels to `split_indexes`.

---

## Modifying Data with `modify_table`

**`modify_table(dataset, columns, types=None)`**

Used inside converters and models to replace or add columns while preserving all other columns and metadata.

```python
import pyarrow as pa
from DashAI.back.dataloaders.classes.dashai_dataset import modify_table

new_col = pa.array([1.0, 2.0, 3.0], type=pa.float64())
result = modify_table(
    dataset, {"scaled_age": new_col}, types={"scaled_age": Float("float64")}
)
```

- Columns in `columns` that already exist in the dataset are replaced.
- New columns require a matching entry in `types`.
- Original Arrow metadata (including `dashai_types`) is preserved and extended.

---

## Relationship to Other Subsystems

```
DataLoader
  └─ loads raw file → DashAIDataset (types inferred by DashAIPtype)
        │
        ├─ Notebook workspace
        │     └─ Converter.fit_transform(DashAIDataset) → DashAIDataset
        │          (modify_table used internally)
        │
        └─ Model training
              └─ prepare_for_model_session → DatasetDict of DashAIDatasets
                    └─ select_columns → (X_train, y_train) pair
```

- **DataLoaders** produce `DashAIDataset` via `to_dashai_dataset`.
- **Converters** consume and return `DashAIDataset`, using `modify_table` to update columns.
- **Models** receive a `DatasetDict` from `prepare_for_model_session` and call `get_split` / `select_columns` to extract their inputs.
- **Explorers** receive a `DashAIDataset` and read `_types` to dispatch column appropriate visualisations.

---

## Source Files

| File                                                | Role                                                                                                |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `DashAI/back/dataloaders/classes/dashai_dataset.py` | `DashAIDataset` class and all module level functions                                                |
| `DashAI/back/types/utils.py`                        | Arrow ↔ dashAI type serialisation (`save_types_in_arrow_metadata`, `get_types_from_arrow_metadata`) |
| `DashAI/back/types/value_types.py`                  | Concrete value type classes used in `_types`                                                        |
| `DashAI/back/types/categorical.py`                  | `Categorical` type with `str2int` / `int2str` encoding                                              |
