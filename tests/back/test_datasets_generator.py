import os
import pathlib
import shutil
from typing import Tuple

import pandas as pd
from sklearn.model_selection import train_test_split


def _get_batch_indexes(df, n, i):
    start_idx = int(i * len(df) / n)
    end_idx = min(int((i + 1) * len(df) / n), len(df))
    return start_idx, end_idx


def _get_test_splits(
    df: pd.DataFrame,
    random_state: int,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # generate splits
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

    return train, test, val


class CSVTestDatasetGenerator:
    def __init__(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        ouptut_path: pathlib.Path,
        random_state: int,
    ) -> None:
        base_path = pathlib.Path(ouptut_path) / "csv" / dataset_name
        os.makedirs(base_path, exist_ok=True)

        self._generate_common_casses(base_path=base_path, df=df)
        self._generate_bad_formats(base_path=base_path, df=df)
        self._gernerate_splits(base_path=base_path, df=df, random_state=random_state)

    def _generate_common_casses(self, base_path: pathlib.Path, df: pd.DataFrame):
        # different separators.
        df.to_csv(base_path / "comma.csv", sep=",", index=False)
        df.to_csv(base_path / "semicolon.csv", sep=";", index=False)
        df.to_csv(base_path / "tab.csv", sep="\t", index=False)
        df.to_csv(base_path / "vert_bar.csv", sep="|", index=False)

        # no header.
        df.to_csv(
            base_path / "no_header.csv",
            sep=";",
            header=False,
            index=False,
        )
        # empty dataframe.
        df.head(0).to_csv(
            path_or_buf=base_path / "empty_dataset.csv",
            sep=";",
            index=False,
        )

    def _generate_bad_formats(self, base_path: pathlib.Path, df: pd.DataFrame):
        # bad format.
        df.to_csv(
            path_or_buf=base_path / "bad_format.csv",
            sep=";",
            header=False,
            index=False,
        )
        with open(base_path / "bad_format.csv", "a") as file:
            file.write(";;;;;;;;;;;;;;;;;;;;;;;;#$%&--")

        # empty file.
        with open(base_path / "empty_file.csv", "w") as file:
            file.write("")

    def _gernerate_splits(
        self, base_path: pathlib.Path, df: pd.DataFrame, random_state: int
    ):
        os.makedirs(base_path / "split" / "train", exist_ok=True)
        os.makedirs(base_path / "split" / "test", exist_ok=True)
        os.makedirs(base_path / "split" / "val", exist_ok=True)

        os.makedirs(base_path / "splits" / "train", exist_ok=True)
        os.makedirs(base_path / "splits" / "test", exist_ok=True)
        os.makedirs(base_path / "splits" / "val", exist_ok=True)

        os.makedirs(base_path / "bad_split" / "train", exist_ok=True)  # noqa: ERA001
        os.makedirs(base_path / "bad_split" / "test", exist_ok=True)  # noqa: ERA001
        os.makedirs(base_path / "bad_split" / "val", exist_ok=True)  # noqa: ERA001

        train, test, val = _get_test_splits(df, random_state)

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
        shutil.make_archive(
            str(base_path / "split"),
            "zip",
            base_path / "split",
        )

        # with batched splits.
        n = 5
        for i in range(n):
            train_start, train_end = _get_batch_indexes(train, n, i)
            train.iloc[train_start:train_end].to_csv(
                path_or_buf=base_path / "splits" / "train" / f"train_{i}.csv",
                sep=";",
                index=False,
            )

            test_start, test_end = _get_batch_indexes(test, n, i)
            test.iloc[test_start:test_end].to_csv(
                path_or_buf=base_path / "splits" / "test" / f"test_{i}.csv",
                sep=";",
                index=False,
            )

            val_start, val_end = _get_batch_indexes(val, n, i)
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

        # with splits but wrong folder structure
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


class JSONTestDatasetGenerator:
    def __init__(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        ouptut_path: pathlib.Path,
        random_state: int,
    ) -> None:
        base_path = pathlib.Path(ouptut_path) / "json" / dataset_name
        os.makedirs(base_path, exist_ok=True)

        self._generate_common_casses(base_path=base_path, df=df)
        self._generate_bad_formats(base_path=base_path, df=df)
        self._gernerate_splits(base_path=base_path, df=df, random_state=random_state)

    def _generate_common_casses(self, base_path: pathlib.Path, df: pd.DataFrame):
        # NOTE: the only two orient currently working on our implementation is table
        # and records.
        # split, column, value and index and record orients are disabled.
        df.to_json(
            base_path / "records.json",
            orient="records",
            force_ascii=False,
        )
        df.to_json(
            base_path / "table.json",
            orient="table",
            index=False,
            force_ascii=False,
        )
        df.to_json(
            path_or_buf=base_path / "table_force_ascii.json",
            orient="table",
            index=False,
            force_ascii=True,
        )

        # empty dataframe.
        df.head(0).to_json(
            path_or_buf=base_path / "empty_dataset.json",
            orient="table",
        )

    def _generate_bad_formats(self, base_path: pathlib.Path, df: pd.DataFrame):
        # bad format.
        df.to_json(
            path_or_buf=base_path / "bad_format.json",
            orient="table",
        )
        with open(base_path / "bad_format.json", "a") as file:
            file.write("#$%&--")

        # empty file.
        with open(base_path / "empty_file.json", "w") as file:
            file.write("")

    def _gernerate_splits(
        self, base_path: pathlib.Path, df: pd.DataFrame, random_state: int
    ):
        os.makedirs(base_path / "split" / "train", exist_ok=True)
        os.makedirs(base_path / "split" / "test", exist_ok=True)
        os.makedirs(base_path / "split" / "val", exist_ok=True)

        os.makedirs(base_path / "splits" / "train", exist_ok=True)
        os.makedirs(base_path / "splits" / "test", exist_ok=True)
        os.makedirs(base_path / "splits" / "val", exist_ok=True)

        os.makedirs(base_path / "bad_split" / "train", exist_ok=True)  # noqa: ERA001
        os.makedirs(base_path / "bad_split" / "test", exist_ok=True)  # noqa: ERA001
        os.makedirs(base_path / "bad_split" / "val", exist_ok=True)  # noqa: ERA001

        train, test, val = _get_test_splits(df, random_state)

        train.to_json(
            path_or_buf=base_path / "split" / "train" / "train.json",
            orient="table",
            index=False,
        )
        test.to_json(
            path_or_buf=base_path / "split" / "test" / "test.json",
            orient="table",
            index=False,
        )
        val.to_json(
            path_or_buf=base_path / "split" / "val" / "val.json",
            orient="table",
            index=False,
        )
        shutil.make_archive(
            str(base_path / "split"),
            "zip",
            base_path / "split",
        )

        # with batched splits.
        n = 5
        for i in range(n):
            train_start, train_end = _get_batch_indexes(train, n, i)
            train.iloc[train_start:train_end].to_json(
                path_or_buf=base_path / "splits" / "train" / f"train_{i}.json",
                orient="table",
                index=False,
            )

            test_start, test_end = _get_batch_indexes(test, n, i)
            test.iloc[test_start:test_end].to_json(
                path_or_buf=base_path / "splits" / "test" / f"test_{i}.json",
                orient="table",
                index=False,
            )

            val_start, val_end = _get_batch_indexes(val, n, i)
            val.iloc[val_start:val_end].to_json(
                path_or_buf=base_path / "splits" / "val" / f"val_{i}.json",
                orient="table",
                index=False,
            )
        shutil.make_archive(
            str(base_path / "splits"),
            "zip",
            base_path / "splits",
        )

        # with splits but wrong folder structure
        train.to_json(
            path_or_buf=base_path / "bad_split" / "train.json",
            orient="table",
            index=False,
        )
        test.to_json(
            path_or_buf=base_path / "bad_split" / "test.json",
            orient="table",
            index=False,
        )
        val.to_json(
            path_or_buf=base_path / "bad_split" / "val.json",
            orient="table",
            index=False,
        )
        shutil.make_archive(
            str(base_path / "bad_split"),
            "zip",
            base_path / "bad_split",
        )


class ExcelTestDatasetGenerator:
    def __init__(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        ouptut_path: pathlib.Path,
        random_state: int,
    ) -> None:
        base_path = pathlib.Path(ouptut_path) / "excel" / dataset_name
        os.makedirs(base_path, exist_ok=True)

        self._generate_common_casses(base_path=base_path, df=df)
        self._generate_bad_formats(base_path=base_path, df=df)
        self._gernerate_splits(base_path=base_path, df=df, random_state=random_state)

    def _generate_common_casses(self, base_path: pathlib.Path, df: pd.DataFrame):
        df.to_excel(
            base_path / "basic.xlsx",
            index=False,
        )
        df.to_excel(
            base_path / "with_sheet_name.xlsx",
            sheet_name="table_1",
            index=False,
        )
        df.to_excel(
            base_path / "no_header.xlsx",
            header=False,
            index=False,
        )

        # empty dataframe.
        df.head(0).to_excel(
            base_path / "empty_dataset.xlsx",
            index=False,
        )

    def _generate_bad_formats(self, base_path: pathlib.Path, df: pd.DataFrame):
        # bad format.
        df.to_excel(
            base_path / "bad_format.xlsx",
            index=False,
        )
        with open(base_path / "bad_format.xlsx", "ab") as file:
            file.write(b"#$%&--")

        # empty file.
        with open(base_path / "empty_file.xlsx", "w") as file:
            file.write("")

    def _gernerate_splits(
        self, base_path: pathlib.Path, df: pd.DataFrame, random_state: int
    ):
        os.makedirs(base_path / "split" / "train", exist_ok=True)
        os.makedirs(base_path / "split" / "test", exist_ok=True)
        os.makedirs(base_path / "split" / "val", exist_ok=True)

        os.makedirs(base_path / "splits" / "train", exist_ok=True)
        os.makedirs(base_path / "splits" / "test", exist_ok=True)
        os.makedirs(base_path / "splits" / "val", exist_ok=True)

        os.makedirs(base_path / "bad_split" / "train", exist_ok=True)  # noqa: ERA001
        os.makedirs(base_path / "bad_split" / "test", exist_ok=True)  # noqa: ERA001
        os.makedirs(base_path / "bad_split" / "val", exist_ok=True)  # noqa: ERA001

        train, test, val = _get_test_splits(df, random_state)

        train.to_excel(base_path / "split" / "train" / "train.xlsx", index=False)
        test.to_excel(base_path / "split" / "test" / "test.xlsx", index=False)
        val.to_excel(base_path / "split" / "val" / "val.xlsx", index=False)
        shutil.make_archive(
            str(base_path / "split"),
            "zip",
            base_path / "split",
        )

        # with batched splits.
        n = 5
        for i in range(n):
            train_start, train_end = _get_batch_indexes(train, n, i)
            train.iloc[train_start:train_end].to_excel(
                base_path / "splits" / "train" / f"train_{i}.xlsx", index=False
            )

            test_start, test_end = _get_batch_indexes(test, n, i)
            test.iloc[test_start:test_end].to_excel(
                base_path / "splits" / "test" / f"test_{i}.xlsx", index=False
            )

            val_start, val_end = _get_batch_indexes(val, n, i)
            val.iloc[val_start:val_end].to_excel(
                base_path / "splits" / "val" / f"val_{i}.xlsx", index=False
            )
        shutil.make_archive(
            str(base_path / "splits"),
            "zip",
            base_path / "splits",
        )

        # with splits but wrong folder structure
        train.to_excel(base_path / "bad_split" / "train.xlsx", index=False)
        test.to_excel(base_path / "bad_split" / "test.xlsx", index=False)
        val.to_excel(base_path / "bad_split" / "val.xlsx", index=False)
        shutil.make_archive(
            str(base_path / "bad_split"),
            "zip",
            base_path / "bad_split",
        )
