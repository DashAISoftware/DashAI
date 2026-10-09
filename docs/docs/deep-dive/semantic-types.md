---
title: Semantic Types
sidebar_label: Semantic Types
sidebar_position: 4
---

# Semantic Types

## What Are Semantic Types?

When you upload a dataset, dashAI assigns a **semantic type** to each column. Semantic types go beyond raw storage formats (e.g., PyArrow `int32` or `string`) to express the ML meaningful nature of the data: is this column a continuous measurement, a discrete label, a free form text, a date?

This classification drives three critical behaviours throughout the platform:

- **Task compatibility**: only columns whose types match a task's requirements can be selected as inputs or outputs.
- **Converter chaining**: converters declare the type they accept and the type they produce, enabling safe preprocessing pipelines.
- **Label encoding**: categorical output columns are automatically integer encoded before training and decoded back to string labels after prediction.

---

## Type Hierarchy

All semantic types inherit from a common abstract base class, `DashAIDataType`.

```
DashAIDataType
├── DashAIValue          # abstract parent for all value types
│   ├── Integer          # int8, int16, int32, int64 (signed or unsigned)
│   ├── Float            # float16, float32, float64
│   ├── Text             # string with encoding (default: UTF-8)
│   ├── Date             # calendar date (default format: YYYY-MM-DD)
│   ├── Time             # time of day (default format: HH:mm:ss)
│   ├── Timestamp        # datetime with timezone (default: YYYY-MM-DD HH:mm:ss)
│   ├── Duration         # elapsed time with unit (s, ms, us, ns)
│   ├── Decimal          # precise decimal (128 or 256-bit, with precision and scale)
│   └── Binary           # raw binary data
└── Categorical          # discrete labels with str ↔ int encoding map
```

`DashAIValue` types represent continuous or ordered measurements. `Categorical` is a separate branch because it carries additional structure: the full list of unique categories and a bijective encoding mapping.

---

## Concrete Types

### Value Types

| Type        | Key attributes                    | Typical use                                 |
| ----------- | --------------------------------- | ------------------------------------------- |
| `Integer`   | `dtype` (e.g. `int64`), `signed`  | Count features, ordinal encoded labels      |
| `Float`     | `dtype` (e.g. `float64`)          | Continuous measurements, regression targets |
| `Text`      | `dtype` (`string`), `encoding`    | Free form text, NLP tasks                   |
| `Date`      | `format` (default `YYYY-MM-DD`)   | Calendar dates                              |
| `Time`      | `format` (default `HH:mm:ss`)     | Time of day values                          |
| `Timestamp` | `format`, `timezone`              | Datetime with timezone                      |
| `Duration`  | `unit` (`s`, `ms`, `us`, `ns`)    | Time intervals                              |
| `Decimal`   | `precision`, `scale`, `bit_width` | High precision numerics                     |
| `Binary`    | -                                 | Raw byte payloads                           |

### Categorical

`Categorical` is the most structurally rich type. It stores:

- `categories`: ordered list of unique string values (`["cat", "dog", "bird"]`)
- `dtype`: underlying PyArrow storage type (`string`, `int64`, etc.)
- `encoding` / `str2int`: dictionary mapping each category to an integer (`{"cat": 0, "dog": 1, "bird": 2}`)
- `decoding` / `int2str`: reverse mapping (`{0: "cat", 1: "dog", 2: "bird"}`)
- `converted`: flag indicating whether the column has already been integer encoded

`Categorical` is used for all classification target columns and for any feature column that contains a discrete set of labels (e.g., country, product category).

---

## Type Inference

Types are assigned automatically when a dataset is loaded. dashAI supports two inference methods, selectable at upload time.

### Primary: `DashAIPtype`

Uses the **ptype** probabilistic type inference model, which analyses each column's values to estimate the most likely semantic type. Supported ptype outputs and their dashAI mappings:

| ptype output    | dashAI type                             |
| --------------- | --------------------------------------- |
| `integer`       | `Integer` (`int64`)                     |
| `float`         | `Float` (`float64`)                     |
| `string`        | `Text` (`string`, UTF-8)                |
| `boolean`       | `Categorical` (`string`)                |
| `categorical`   | `Categorical` (`string`)                |
| `date-iso-8601` | `Text` (date parsing not yet automatic) |
| `date-eu`       | `Text`                                  |
| `float_comma`   | `Float` (comma decimal normalised)      |

After ptype classification, any column whose unique value count and ratio fall within configurable thresholds is further promoted to `Categorical` regardless of the original ptype output.

### Fallback: `DummyCategoricalInference`

A lightweight heuristic used when ptype is unavailable:

- String columns with fewer than 10 unique values → `Categorical`
- Integer columns with fewer than 10 unique values → `Categorical`
- All other integer columns → `Integer`
- All other string columns → `Text`
- Float columns → `Float`

### Special cases

- PyArrow `bool` columns are always mapped to `Categorical` (two category: `True`/`False`).
- PyArrow dictionary encoded columns are mapped to `Categorical` with an initially empty category list.

---

## Type Persistence

Semantic types are serialised to **Apache Arrow table metadata** under the key `dashai_types` and stored alongside the dataset's Arrow IPC file. This means:

- Types survive save/load round trips without reinference.
- Notebooks inherit the types of their source dataset.
- Converters that change a column's type update the metadata in place.

The relevant utilities are `save_types_in_arrow_metadata()` and `get_types_from_arrow_metadata()` in `DashAI/back/types/utils.py`.

---

## How Types Are Used

### Task Compatibility

Every task class declares the semantic types it accepts for input and output columns via a `metadata` dictionary:

```python
metadata = {
    "inputs_types": [Float, Integer, Categorical],  # allowed input column types
    "outputs_types": [Categorical],  # required output column type
    "inputs_cardinality": "n",  # any number of inputs
    "outputs_cardinality": 1,  # exactly one output
}
```

Before training, `validate_dataset_for_task()` checks that every selected column's semantic type is in the allowed set. Columns that do not match are rejected with a descriptive error.

**Type requirements by task:**

| Task                        | Allowed input types               | Required output type             |
| --------------------------- | --------------------------------- | -------------------------------- |
| `TabularClassificationTask` | `Float`, `Integer`, `Categorical` | `Categorical`                    |
| `RegressionTask`            | `Float`, `Integer`, `Categorical` | `Float` or `Integer`             |
| `TextClassificationTask`    | `Text` (exactly 1 column)         | `Categorical` (exactly 1 column) |
| `TranslationTask`           | `Text` (exactly 1 column)         | `Text` (exactly 1 column)        |

### Converter Type Contracts

Each converter implements `get_output_type(column_name)` to declare the semantic type of each output column. This allows dashAI to track the type of every column through a multistep preprocessing pipeline.

**Common converter contracts:**

| Converter                        | Input type         | Output type                                |
| -------------------------------- | ------------------ | ------------------------------------------ |
| `OneHotEncoder`                  | `Categorical`      | `Integer` (one binary column per category) |
| `OrdinalEncoder`                 | `Categorical`      | `Integer`                                  |
| `LabelEncoder`                   | `Categorical`      | `Integer`                                  |
| `LabelBinarizer`                 | `Categorical`      | `Integer`                                  |
| `StandardScaler`                 | `Integer`, `Float` | `Float`                                    |
| `MinMaxScaler`                   | `Integer`, `Float` | `Float`                                    |
| `Normalizer`                     | `Integer`, `Float` | `Float`                                    |
| `Binarizer`                      | `Integer`, `Float` | `Integer`                                  |
| `TFIDFConverter`                 | `Text`             | `Float`                                    |
| `BagOfWordsConverter`            | `Text`             | `Float`                                    |
| `TokenizerConverter`             | `Text`             | `Integer`                                  |
| `PCA`, `TruncatedSVD`, `FastICA` | `Integer`, `Float` | `Float`                                    |

### Label Encoding

Classification tasks require a `Categorical` output column, but most ML models require numeric targets. dashAI handles this automatically:

1. **Before training**: `categorical_label_encoder()` converts each `Categorical` output column to `Integer` using the `Categorical` type's `str2int` map. The mapping is saved so that it can be reversed.
2. **After prediction**: `process_predictions()` applies the reverse `int2str` map to convert integer predictions back to their original string labels before displaying results or saving to disk.

No manual encoding step is needed from the user.

### Type Validation

When a user manually changes a column's semantic type in the UI, `validate_type_change()` checks whether the conversion is safe and feasible:

| From \ To     |       `Integer`        |      `Float`       | `Text` |      `Categorical`       | `Date` | `Time` | `Timestamp` |
| ------------- | :--------------------: | :----------------: | :----: | :----------------------: | :----: | :----: | :---------: |
| `Integer`     |           -            |        Yes         |  Yes   | Yes (if low cardinality) |   -    |   -    |      -      |
| `Float`       | Yes (if whole numbers) |         -          |  Yes   | Yes (if low cardinality) |   -    |   -    |      -      |
| `Text`        |   Yes (if parseable)   | Yes (if parseable) |   -    | Yes (if low cardinality) |  Yes   |  Yes   |     Yes     |
| `Categorical` |          Yes           |        Yes         |  Yes   |            -             |   -    |   -    |      -      |
| `Date`        |           -            |         -          |  Yes   |            -             |   -    |   -    |      -      |
| `Time`        |           -            |         -          |  Yes   |            -             |   -    |   -    |      -      |
| `Timestamp`   |           -            |         -          |  Yes   |            -             |   -    |   -    |      -      |

If the conversion is not safe (e.g., promoting a high cardinality text column to `Categorical`), the validator returns a descriptive error before any data is modified.

---

## Source Files

| File                                         | Role                                            |
| -------------------------------------------- | ----------------------------------------------- |
| `DashAI/back/types/dashai_data_type.py`      | Abstract base class `DashAIDataType`            |
| `DashAI/back/types/dashai_value.py`          | Abstract intermediate class `DashAIValue`       |
| `DashAI/back/types/value_types.py`           | Concrete value type classes                     |
| `DashAI/back/types/categorical.py`           | `Categorical` type with encoding logic          |
| `DashAI/back/types/utils.py`                 | Arrow ↔ dashAI type conversion, metadata I/O    |
| `DashAI/back/types/type_validation.py`       | `validate_type_change()` and suitability checks |
| `DashAI/back/types/inf/inference_methods.py` | `DashAIPtype` and `DummyCategoricalInference`   |
| `DashAI/back/types/inf/type_inference.py`    | `infer_types()` entry point                     |
