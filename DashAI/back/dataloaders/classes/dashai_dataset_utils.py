from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from DashAI.back.types.categorical import Categorical
from DashAI.back.types.utils import to_arrow_types
from DashAI.back.types.value_types import Float, Text

if TYPE_CHECKING:
    from sklearn.preprocessing import OneHotEncoder

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

# Data Transformations

# Categorical Transformations


def categorical_label_encoder(
    dataset: "DashAIDataset",
    columns: list = None,
) -> Tuple["DashAIDataset", Dict[str, Dict[str, int]]]:
    """Convert categorical columns from the DashAIDataset to label encoded integers.

    Parameters
    ----------
    dataset : DashAIDataset
        The dataset containing both non categorical
        and categorical columns to be label encoded.
    columns : list, optional
        If given, only encode categorical columns whose names are in this list.
        Other categorical columns pass through unchanged.

    Returns
    -------
    DashAIDataset
        A new DashAIDataset with categorical columns converted to
        label encoded integers.
    encodings : dict
        A dictionary containing the encodings for each categorical column,
        where keys are column names and values.
    """
    import pyarrow as pa

    from DashAI.back.dataloaders.classes.dashai_dataset import modify_table

    new_columns = {}
    table = dataset.arrow_table
    encodings = {}

    for col, _type in dataset.types.items():
        array = table[col]
        # Check every column dashai_type to find the categorical ones
        if isinstance(_type, Categorical) and (columns is None or col in columns):
            encodings[col] = dict(_type._str2int)  # Store the encoding for later use

            # Need to check everything later, predictions and model reuse.
            if not _type.converted:
                values = [_type.str2int(x.as_py()) for x in array]
                new_columns[col] = pa.array(values, type=pa.int64())
            else:
                new_columns[col] = array
        else:
            new_columns[col] = array

    return modify_table(dataset, columns=new_columns, types=dataset.types), encodings


# This function is used to apply the encodings stored in the model
# to the categorical columns in the dataset.
def apply_categorical_label_encoder(
    dataset: "DashAIDataset", encodings: Dict[str, Dict[str, int]]
) -> "DashAIDataset":
    """Apply Model stored encodings to the categorical columns in the dataset.

    Parameters
    ----------
    dataset : DashAIDataset
        The dataset containing both non categorical and categorical columns
        to be label encoded.
    encodings : dict
        A dictionary containing the encodings for each categorical column,
        where keys are column names and values are dictionaries
        mapping original values to encoded integers.

    Returns
    -------
    DashAIDataset
        A new DashAIDataset with categorical columns converted to
        label encoded integers using the provided encodings.

    """
    import pyarrow as pa

    from DashAI.back.dataloaders.classes.dashai_dataset import modify_table

    table = dataset.arrow_table
    new_columns = {}
    types = dataset.types

    for col in table.column_names:
        array = table[col]
        _type = types.get(col)

        if col in encodings and isinstance(_type, Categorical) and not _type.converted:
            # Apply the stored encodings to the categorical columns

            encoding = encodings[col]
            try:
                categories = _type.categories
                cat_type = Categorical(categories, encoding=encoding)
                encoded_values = [cat_type.str2int(x.as_py()) for x in array]
                new_columns[col] = pa.array(encoded_values, type=pa.int64())

                types[col] = cat_type
            except KeyError as e:
                raise ValueError(
                    f"Value {e} not found in encoding for column '{col}'"
                ) from e
        else:
            # If no encoding is provided or the column has no type info,
            # keep the original column
            new_columns[col] = array
    return modify_table(dataset, columns=new_columns, types=types)


def vectorize_text(
    dataset: "DashAIDataset",
) -> "DashAIDataset":
    """Tokenise all ``Text``-typed columns by splitting on whitespace.

    Each text column is replaced by a ``list<string>`` column where every
    entry is a list of space-delimited tokens. Non-text columns are preserved
    unchanged.

    Parameters
    ----------
    dataset : DashAIDataset
        Input dataset whose text columns will be tokenised.

    Returns
    -------
    DashAIDataset
        A new dataset with text columns replaced by token-list columns.
    """
    import pyarrow as pa

    from DashAI.back.dataloaders.classes.dashai_dataset import modify_table

    new_columns = {}
    table = dataset.arrow_table
    for col, _type in dataset.types.items():
        array = table[col]
        if isinstance(_type, Text):
            # Assuming a simple vectorization by splitting on spaces
            # In practice, you might want to use more sophisticated methods
            # like TF-IDF or word embeddings
            new_columns[col] = pa.array(
                [x.split() if x is not None else [] for x in array],
                type=pa.list_(pa.string()),
            )
        else:
            new_columns[col] = pa.array(array, type=to_arrow_types(_type.dtype))
    transformed_dataset = modify_table(dataset, columns=new_columns)
    return transformed_dataset


# One-Hot Encoding for categorical columns


def categorical_one_hot_encoder(
    dataset: "DashAIDataset",
    encoder: Optional["OneHotEncoder"] = None,
    columns: list = None,
) -> Tuple["DashAIDataset", "OneHotEncoder", List[str]]:
    """Convert categorical columns from the DashAIDataset to one hot encoded columns.

    Parameters
    ----------
    dataset : DashAIDataset
        The dataset containing categorical columns to be one hot encoded.
    encoder : OneHotEncoder, optional
        Prefitted encoder to use. If None, a new encoder will be fitted.
    columns : list, optional
        If given, only one hot encode columns in this list. Other categorical
        columns pass through unchanged.

    Returns
    -------
    DashAIDataset
        A new DashAIDataset with categorical columns replaced by one hot columns.
    OneHotEncoder
        The fitted encoder (for reuse during prediction).
    List[str]
        List of original categorical column names that were encoded.
    """
    import numpy as np
    import pandas as pd
    import pyarrow as pa
    from sklearn.preprocessing import OneHotEncoder

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

    types = dataset.types

    categorical_cols = [
        col
        for col, _type in types.items()
        if isinstance(_type, Categorical) and (columns is None or col in columns)
    ]

    if not categorical_cols:
        return dataset, None, []

    data_df = dataset.to_pandas()
    cat_data = data_df[categorical_cols].astype(str)

    if encoder is None:
        encoder = OneHotEncoder(
            sparse_output=False,
            handle_unknown="ignore",  # Ignore unknown categories during transform
            dtype=np.float64,
        )
        encoded_array = encoder.fit_transform(cat_data)
    else:
        encoded_array = encoder.transform(cat_data)

    feature_names = encoder.get_feature_names_out(categorical_cols)

    encoded_df = pd.DataFrame(encoded_array, columns=feature_names, index=data_df.index)

    data_df = data_df.drop(columns=categorical_cols)
    data_df = pd.concat([data_df, encoded_df], axis=1)

    new_table = pa.Table.from_pandas(data_df, preserve_index=False)

    new_types = {col: t for col, t in types.items() if col not in categorical_cols}
    for col_name in feature_names:
        new_types[col_name] = Float(arrow_type=pa.float64())

    new_dataset = DashAIDataset(
        new_table,
        types=new_types,
        splits=dataset.splits,
    )

    return new_dataset, encoder, categorical_cols


def apply_categorical_one_hot_encoder(
    dataset: "DashAIDataset",
    encoder: "OneHotEncoder",
    categorical_cols: List[str],
) -> "DashAIDataset":
    """Apply a prefitted OneHotEncoder to categorical columns in the dataset.

    Parameters
    ----------
    dataset : DashAIDataset
        The dataset containing categorical columns to be one hot encoded.
    encoder : OneHotEncoder
        Prefitted encoder from training.
    categorical_cols : List[str]
        List of categorical column names to encode.

    Returns
    -------
    DashAIDataset
        A new DashAIDataset with categorical columns replaced by one hot columns.
    """
    import pandas as pd
    import pyarrow as pa

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

    if encoder is None or not categorical_cols:
        return dataset

    types = dataset.types
    data_df = dataset.to_pandas()

    missing_cols = [col for col in categorical_cols if col not in data_df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing categorical columns in dataset: {missing_cols}. "
            f"Expected columns: {categorical_cols}"
        )

    cat_data = data_df[categorical_cols].astype(str)
    # handle_unknown='ignore' will set unknown categories to all zeros
    encoded_array = encoder.transform(cat_data)

    feature_names = encoder.get_feature_names_out(categorical_cols)

    encoded_df = pd.DataFrame(encoded_array, columns=feature_names, index=data_df.index)

    data_df = data_df.drop(columns=categorical_cols)
    data_df = pd.concat([data_df, encoded_df], axis=1)

    new_table = pa.Table.from_pandas(data_df, preserve_index=False)

    new_types = {col: t for col, t in types.items() if col not in categorical_cols}
    for col_name in feature_names:
        new_types[col_name] = Float(arrow_type=pa.float64())

    new_dataset = DashAIDataset(
        new_table,
        types=new_types,
        splits=dataset.splits,
    )

    return new_dataset
