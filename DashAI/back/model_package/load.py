"""Open an exported model package and predict with it, outside the app.

Nothing here touches the database, the job queue or the kink container: the
package carries the classes to import, the fitted objects and the training
column types, and prediction runs the same three steps the app runs
(``process_manual_input``, the session preprocessor, ``predict_labels``).
"""

import importlib
import json
import pickle
import shutil
import tempfile
import weakref
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from DashAI.back.model_package.manifest import (
    MANIFEST_ENTRY,
    MODEL_ENTRY,
    PREPROCESSOR_ENTRY,
    SCHEMA_ENTRY,
    ModelPackageError,
    check_manifest,
)

NOT_A_PACKAGE = "{path} is not a DashAI model package"
REQUIRED_MANIFEST_KEYS = (
    "format_version",
    "model",
    "task",
    "input_columns",
    "output_columns",
)


def _import_class(reference: Dict[str, str]) -> type:
    """Import a class named by the manifest, or say which one is missing."""
    try:
        module = importlib.import_module(reference["module"])
        return getattr(module, reference["class"])
    except (ImportError, AttributeError) as e:
        raise ModelPackageError(
            f"This model needs {reference['module']}.{reference['class']}, "
            "which is not available. It may come from a plugin or a DashAI "
            "version that is not installed."
        ) from e


def _native(value: Any) -> Any:
    """Turn a numpy scalar into the plain Python value the task validates."""
    import numpy as np

    return value.item() if isinstance(value, np.generic) else value


def _to_rows(data: Any, skip_columns: List[str]) -> List[Dict[str, Any]]:
    """Plain dict rows from a DataFrame or an iterable of dicts.

    The target columns are dropped: a CSV like the training one carries them,
    and tasks with a fixed input cardinality would otherwise reject the row.
    """
    if hasattr(data, "to_dict") and not isinstance(data, dict):
        records = data.to_dict(orient="records")
    else:
        records = list(data)
    return [
        {key: _native(value) for key, value in row.items() if key not in skip_columns}
        for row in records
    ]


class PackagedModel:
    """A trained DashAI model loaded from a package, ready to predict."""

    def __init__(
        self,
        manifest: Dict[str, Any],
        model: Any,
        task: Any,
        preprocessor: Optional[Any],
        schema_path: Path,
    ) -> None:
        self._manifest = manifest
        self._model = model
        self._task = task
        self._preprocessor = preprocessor
        self._schema_path = schema_path

    @property
    def info(self) -> Dict[str, Any]:
        """The package manifest: model, task, columns, versions and metrics."""
        return json.loads(json.dumps(self._manifest))

    def predict(self, data: Any) -> list:
        """Predict one value per row of raw data.

        Parameters
        ----------
        data : pandas.DataFrame or list of dict
            Rows with the columns of the original dataset, before any
            preprocessing. Target columns, if present, are dropped.

        Returns
        -------
        list
            One prediction per row: a label for classification, a number for
            regression.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
        from DashAI.back.units.predict_unit import predict_labels

        rows = _to_rows(data, self._manifest["output_columns"])
        if not rows:
            return []
        schema_path = str(self._schema_path)
        self._check_columns(rows[0], load_dataset(schema_path).column_names)
        dataset = self._task.process_manual_input(rows, schema_path)
        if self._preprocessor is not None:
            dataset = self._preprocessor.transform_dataset(dataset)
        predictions = predict_labels(
            self._task,
            model=self._model,
            model_input=dataset,
            train_dataset=load_dataset(schema_path),
            input_columns=self._manifest["input_columns"],
            output_column=self._manifest["output_columns"][0],
        )
        return [_native(value) for value in predictions]

    def _check_columns(self, row: Dict[str, Any], dataset_columns: List[str]) -> None:
        """Name every input column the rows lack, before anything reads them.

        Only columns of the original dataset are required: with preprocessing,
        some model inputs are derived columns the caller never provides.
        """
        expected = [
            column
            for column in self._manifest["input_columns"]
            if column in dataset_columns
        ]
        missing = [column for column in expected if column not in row]
        if missing:
            raise ModelPackageError(
                f"Missing input columns: {', '.join(missing)}. "
                f"This model expects: {', '.join(expected)}"
            )


def load_model(path: Union[str, Path]) -> PackagedModel:
    """Load a model exported from DashAI.

    Warning: a package contains pickled Python objects, and loading it runs
    code. Only load packages from sources you trust.

    Parameters
    ----------
    path : str or Path
        Path to a ``.dashai-model`` file.

    Raises
    ------
    ModelPackageError
        If the file is not a package, its format is newer than this DashAI
        reads, or a plugin it needs is not installed.
    """
    if not Path(path).is_file():
        raise ModelPackageError(f"{path} does not exist or is not a file")

    workdir = Path(tempfile.mkdtemp(prefix="dashai-model-"))
    try:
        try:
            with zipfile.ZipFile(path) as archive:
                archive.extractall(workdir)
            manifest = json.loads(
                (workdir / MANIFEST_ENTRY).read_text(encoding="utf-8")
            )
        except (
            zipfile.BadZipFile,
            FileNotFoundError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as e:
            raise ModelPackageError(NOT_A_PACKAGE.format(path=path)) from e
        # Any zip may hold a manifest.json; only ours has these keys.
        if not isinstance(manifest, dict) or any(
            key not in manifest for key in REQUIRED_MANIFEST_KEYS
        ):
            raise ModelPackageError(NOT_A_PACKAGE.format(path=path))

        check_manifest(manifest)
        model_class = _import_class(manifest["model"])
        task = _import_class(manifest["task"])()
        model = model_class.load(str(workdir / MODEL_ENTRY))
        preprocessor = None
        if manifest.get("has_preprocessing"):
            with open(workdir / PREPROCESSOR_ENTRY, "rb") as handle:
                preprocessor = pickle.load(handle)
    except BaseException:
        shutil.rmtree(workdir, ignore_errors=True)
        raise

    packaged = PackagedModel(
        manifest, model, task, preprocessor, workdir / SCHEMA_ENTRY
    )
    # The extracted files live as long as the model object does.
    weakref.finalize(packaged, shutil.rmtree, workdir, True)
    return packaged
