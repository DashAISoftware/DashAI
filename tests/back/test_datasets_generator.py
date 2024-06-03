import os
import pathlib
import shutil

import pandas as pd
from sklearn.model_selection import train_test_split


def generate_csv_test_dataset(
    name: str,
    df: pd.DataFrame,
    test_datasets_path: pathlib.Path,
    random_state: int,
) -> None:
    # generate dirs
    base_path = test_datasets_path / "csv" / name
    os.makedirs(base_path, exist_ok=True)
    os.makedirs(base_path / "split" / "train", exist_ok=True)
    os.makedirs(base_path / "split" / "test", exist_ok=True)
    os.makedirs(base_path / "split" / "val", exist_ok=True)
    os.makedirs(base_path / "bad_split" / "train", exist_ok=True)
    os.makedirs(base_path / "bad_split" / "test", exist_ok=True)
    os.makedirs(base_path / "bad_split" / "val", exist_ok=True)
    os.makedirs(base_path / "splits" / "train", exist_ok=True)
    os.makedirs(base_path / "splits" / "test", exist_ok=True)
    os.makedirs(base_path / "splits" / "val", exist_ok=True)

    # ---------------------------------------------------------------------------------
    # common cases
    df.to_csv(base_path / "comma.csv", sep=",", index=False)
    df.to_csv(base_path / "semicolon.csv", sep=";", index=False)
    df.to_csv(base_path / "tab.csv", sep="\t", index=False)
    df.to_csv(base_path / "vert_bar.csv", sep="|", index=False)

    # ---------------------------------------------------------------------------------
    # no header
    df.to_csv(
        base_path / "no_header.csv",
        sep=";",
        header=False,
        index=False,
    )

    # ---------------------------------------------------------------------------------
    # bad format
    df.to_csv(
        path_or_buf=base_path / "bad_format.csv",
        sep=";",
        header=False,
        index=False,
    )
    with open(base_path / "bad_format.csv", "w") as file:
        file.write("------")

    # ---------------------------------------------------------------------------------
    # empty file
    with open(base_path / "empty_file.csv", "w") as file:
        file.write("")

    # ---------------------------------------------------------------------------------
    # empty dataframe
    df.head(0).to_csv(
        path_or_buf=base_path / "empty_dataset.csv",
        sep=";",
        index=False,
    )

    # ---------------------------------------------------------------------------------
    # with splits
    if pd.api.types.is_float_dtype(df.target):
        train, rest = train_test_split(
            df,
            train_size=0.334,
            random_state=random_state,
        )
        test, val = train_test_split(
            rest,
            train_size=0.5,
            random_state=random_state,
        )

    else:
        train, rest = train_test_split(
            df,
            train_size=0.334,
            stratify=df.target,
            random_state=random_state,
        )
        test, val = train_test_split(
            rest,
            train_size=0.5,
            stratify=rest.target,
            random_state=random_state,
        )

    train.to_csv(
        path_or_buf=base_path / "split" / "train" / "train.csv",
        sep=";",
        index=False,
    )
    test.to_csv(
        path_or_buf=base_path / "split" / "test" / "test.csv",
        sep=";",
        index=False,
    )
    val.to_csv(
        path_or_buf=base_path / "split" / "val" / "val.csv",
        sep=";",
        index=False,
    )
    shutil.make_archive(str(base_path / "split"), "zip", base_path / "split")

    # ---------------------------------------------------------------------------------
    # with splits but bad folders
    train.to_csv(
        path_or_buf=base_path / "bad_split" / "train.csv",
        sep=";",
        index=False,
    )
    test.to_csv(
        path_or_buf=base_path / "bad_split" / "test.csv",
        sep=";",
        index=False,
    )
    val.to_csv(
        path_or_buf=base_path / "bad_split" / "val.csv",
        sep=";",
        index=False,
    )
    shutil.make_archive(
        str(base_path / "bad_split"),
        "zip",
        base_path / "bad_split",
    )

    # ---------------------------------------------------------------------------------
    # with several splits
    def get_start_end_idx(df, n, i):
        start_idx = int(i * len(df) / n)
        end_idx = min(int((i + 1) * len(df) / n), len(df))
        return start_idx, end_idx

    n = 5
    for i in range(n - 1):
        train_start, train_end = get_start_end_idx(train, n, i)
        train.iloc[train_start:train_end].to_csv(
            path_or_buf=base_path / "splits" / "train" / f"train_{i}.csv",
            sep=";",
            index=False,
        )

        test_start, test_end = get_start_end_idx(test, n, i)
        test.iloc[test_start:test_end].to_csv(
            path_or_buf=base_path / "splits" / "test" / f"test_{i}.csv",
            sep=";",
            index=False,
        )

        val_start, val_end = get_start_end_idx(test, n, i)
        val.iloc[val_start:val_end].to_csv(
            path_or_buf=base_path / "splits" / "val" / f"val_{i}.csv",
            sep=";",
            index=False,
        )
    shutil.make_archive(
        str(base_path / "splits"),
        "zip",
        base_path / "splits",
    )

    # TODO: splits with one error.
