from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Final, List, Union

from starlette.datastructures import UploadFile

from DashAI.back.tasks.utils import get_bytes_with_type_filetype

if TYPE_CHECKING:
    from datasets import DatasetDict

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class BaseTask:
    """Base class for DashAI compatible tasks."""

    TYPE: Final[str] = "Task"

    PREDICTS_FORWARD_ONLY: bool = False

    @property
    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        """Return the schema of components compatible with this task.

        Concrete subclasses must implement this property to return a mapping
        that describes which models, metrics, and other components are compatible
        with the task.

        Returns
        -------
        Dict[str, Any]
            A dictionary whose keys are component category names (e.g.
            ``"models"``, ``"metrics"``) and whose values are lists or
            mappings of the compatible component classes or identifiers.

        Raises
        ------
        NotImplementedError
            If the subclass does not provide an implementation.
        """
        raise NotImplementedError

    @classmethod
    def _column_groups(cls, side: str) -> List[Dict[str, Any]]:
        """Read one side of the contract as a list of type groups.

        A task says what its columns may be as a list of groups, each naming a
        set of interchangeable types and how many columns of that set it takes:

        .. code-block:: python

            "inputs": [
                {"types": [Date], "cardinality": 1},
                {"types": [Float, Integer], "cardinality": {"min": 1, "max": "n"}},
            ]

        Grouping is what lets a task ask for one date column and any number of
        numeric ones at the same time. A single cardinality for the whole side
        cannot say that: it can only demand a total, so it would accept two
        dates and no numbers as readily as the intended shape.

        The older flat spelling, ``inputs_types`` alongside
        ``inputs_cardinality``, is still read and means a single group, so
        tasks and plugins written against it keep working unchanged.

        Parameters
        ----------
        side : str
            Either ``"inputs"`` or ``"outputs"``.

        Returns
        -------
        list of dict
            One entry per group, each with ``"types"`` (a tuple of type
            classes), ``"min"`` (an int) and ``"max"`` (an int or ``"n"``).
        """
        metadata = cls.metadata

        if side in metadata:
            declared = metadata[side]
        else:
            declared = [
                {
                    "types": metadata[f"{side}_types"],
                    "cardinality": metadata[f"{side}_cardinality"],
                }
            ]

        return [
            {
                "types": tuple(group["types"]),
                **cls._bounds(group.get("cardinality", "n")),
            }
            for group in declared
        ]

    @staticmethod
    def _bounds(cardinality: Any) -> Dict[str, Any]:
        """Read a declared cardinality as a minimum and a maximum.

        Parameters
        ----------
        cardinality : Any
            An int for an exact count, ``"n"`` for any number, or a mapping
            with ``"min"`` and ``"max"`` for a range whose ``"max"`` may itself
            be ``"n"``.

        Returns
        -------
        dict
            A mapping with keys ``"min"`` and ``"max"``.
        """
        if isinstance(cardinality, dict):
            return {
                "min": cardinality.get("min", 0),
                "max": cardinality.get("max", "n"),
            }
        if cardinality == "n":
            return {"min": 0, "max": "n"}
        return {"min": cardinality, "max": cardinality}

    @staticmethod
    def _total_cardinality(groups: List[Dict[str, Any]]) -> Any:
        """State a whole side's cardinality the way the flat contract did.

        Kept so every consumer of the two-key metadata, the column picker
        among them, reads the same value it always did for the tasks that
        declare a single group.

        Parameters
        ----------
        groups : list of dict
            The normalised groups of one side.

        Returns
        -------
        int or str
            The exact total when every group is exact, otherwise ``"n"``.
        """
        if all(group["min"] == group["max"] for group in groups):
            return sum(group["min"] for group in groups)
        return "n"

    @staticmethod
    def _type_name(dashai_type) -> str:
        """Name a type the way the frontend and the columns themselves do.

        A DashAI type reports its own name through ``display_name()``, which
        matches what a column emits via ``to_string()``. These lists may also
        hold foreign classes, for example HuggingFace dataset features or a
        plugin's own types, so those fall back to the class name.

        Parameters
        ----------
        dashai_type : type
            One of the declared type classes.

        Returns
        -------
        str
            The name to show for it.
        """
        getter = getattr(dashai_type, "display_name", None)
        return getter() if callable(getter) else dashai_type.__name__

    @staticmethod
    def _cardinality_text(group: Dict[str, Any]) -> str:
        """Say a group's cardinality the way an error message should read it.

        Parameters
        ----------
        group : dict
            A normalised group.

        Returns
        -------
        str
            For example ``"1"``, ``"n"``, ``"at least 1"`` or ``"1 to 3"``.
        """
        minimum, maximum = group["min"], group["max"]
        if maximum == "n":
            return "n" if minimum == 0 else f"at least {minimum}"
        if minimum == maximum:
            return str(minimum)
        return f"{minimum} to {maximum}"

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Return serialisable metadata for the current task.

        The contract is reported twice. ``"inputs"`` and ``"outputs"`` carry
        the per-group form, which is the only one that can tell "one date and
        any number of numbers" apart from "any number of dates or numbers".
        ``"inputs_types"`` and the three keys beside it carry the flattened
        view every existing consumer already reads, unchanged for the tasks
        that declare a single group.

        Type classes become their string names throughout so the result can be
        JSON-serialised by the DashAI frontend.

        Parameters
        ----------
        cls : type
            The task class (injected automatically by Python for classmethods).

        Returns
        -------
        Dict[str, Any]
            Dictionary with keys ``"inputs_types"``, ``"outputs_types"``,
            ``"inputs_cardinality"``, ``"outputs_cardinality"``, ``"inputs"``
            and ``"outputs"``.
        """
        parsed_metadata: dict = {}

        for side in ("inputs", "outputs"):
            groups = cls._column_groups(side)

            names: List[str] = []
            for group in groups:
                for dashai_type in group["types"]:
                    name = cls._type_name(dashai_type)
                    if name not in names:
                        names.append(name)

            parsed_metadata[f"{side}_types"] = names
            parsed_metadata[f"{side}_cardinality"] = cls._total_cardinality(groups)
            parsed_metadata[side] = [
                {
                    "types": [cls._type_name(t) for t in group["types"]],
                    "min": group["min"],
                    "max": group["max"],
                }
                for group in groups
            ]

        return parsed_metadata

    def _validate_side(
        self,
        columns: List[str],
        types: Dict[str, Any],
        side: str,
    ) -> None:
        """Check one side's columns against the groups the task declares.

        Each column is charged to the first group that accepts its type and
        still has room, so a task asking for one date and any number of
        numbers reads a date, a number and a number as a full match rather
        than as three columns competing for one slot.

        Parameters
        ----------
        columns : list of str
            The selected column names.
        types : dict
            The dataset's column types, keyed by column name.
        side : str
            Either ``"inputs"`` or ``"outputs"``.

        Raises
        ------
        TypeError
            If a column's type belongs to none of the groups.
        ValueError
            If a group ends up with a number of columns outside its bounds.
        """
        groups = self._column_groups(side)
        counts = [0] * len(groups)
        label = "Input" if side == "inputs" else "Output"

        for column in columns:
            column_type = types[column]
            matching = [
                index
                for index, group in enumerate(groups)
                if isinstance(column_type, group["types"])
            ]
            if not matching:
                raise TypeError(
                    f"{column_type} is not an allowed type for {side[:-1]} columns."
                )

            with_room = [
                index
                for index in matching
                if groups[index]["max"] == "n" or counts[index] < groups[index]["max"]
            ]
            counts[(with_room or matching)[0]] += 1

        for group, count in zip(groups, counts, strict=True):
            if count < group["min"] or (group["max"] != "n" and count > group["max"]):
                of_types = (
                    ""
                    if len(groups) == 1
                    else " for columns of type "
                    + ", ".join(self._type_name(t) for t in group["types"])
                )
                raise ValueError(
                    f"{label} cardinality ({count}) does not match task "
                    f"cardinality ({self._cardinality_text(group)}){of_types}"
                )

    def validate_dataset_for_task(
        self,
        dataset: "DashAIDataset",
        dataset_name: str,
        input_columns: List[str],
        output_columns: List[str],
    ) -> None:
        """Validate a dataset for the current task.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset to be validated
        dataset_name : str
            Dataset name
        input_columns : list of str
            Names of the columns selected as inputs.
        output_columns : list of str
            Names of the columns selected as outputs.
        """
        types = dataset._types
        self._validate_side(input_columns, types, "inputs")
        self._validate_side(output_columns, types, "outputs")

    def prepare_for_task(
        self,
        dataset: Union["DatasetDict", "DashAIDataset"],
        input_columns: List[str],
        output_columns: List[str],
    ) -> "DashAIDataset":
        """Prepare and validate a dataset for this task.

        Ensures the dataset is a ``DashAIDataset`` instance, then validates
        that the selected input and output columns match the types and
        cardinality declared in :attr:`metadata`.

        Parameters
        ----------
        dataset : DatasetDict or DashAIDataset
            The dataset to prepare. If a ``DatasetDict`` is supplied it is
            converted to ``DashAIDataset`` automatically.
        input_columns : list of str
            Names of columns to use as model inputs.
        output_columns : list of str
            Names of columns to use as model outputs/targets.

        Returns
        -------
        DashAIDataset
            The validated dataset, ready to be passed to a model.

        Raises
        ------
        TypeError
            If any input or output column has a type not allowed by this task.
        ValueError
            If the number of input or output columns violates the task's
            cardinality constraints.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

        dashai_dataset = to_dashai_dataset(dataset)
        self.validate_dataset_for_task(
            dashai_dataset,
            dataset_name=getattr(dashai_dataset, "name", "dataset"),
            input_columns=input_columns,
            output_columns=output_columns,
        )
        return dashai_dataset

    @abstractmethod
    def num_labels(self, dataset: "DashAIDataset", output_column: str) -> int | None:
        """Get the number of unique labels in the output column.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset used for training
        output_column : str
            Output column

        Returns
        -------
        int | None
            Number of unique labels or None if not applicable
        """
        raise NotImplementedError

    def _validate_and_normalize_value(
        self,
        value: Any,
        column_spec: Dict[str, Any],
        column_name: str,
        row_idx: int,
    ) -> Any:
        """Validate and normalize a value against expected column specification.

        Parameters
        ----------
        value : Any
            Value to validate
        column_spec : Dict[str, Any]
            Column specification with 'type', 'dtype', 'categories', etc.
        column_name : str
            Name of the column being validated
        row_idx : int
            Index of the row being validated

        Returns
        -------
        Any
            Normalized value

        Raises
        ------
        ValueError
            If categorical value is not in allowed categories
        TypeError
            If value doesn't match expected type
        """
        import numpy as np

        col_type = column_spec.get("type")
        dtype = column_spec.get("dtype")

        if col_type == "Categorical":
            categories = column_spec.get("categories", [])

            if dtype and dtype.startswith("int"):
                if isinstance(value, bool):
                    raise TypeError(
                        f"Row {row_idx}, column '{column_name}': "
                        f"Boolean cannot be converted to integer categorical"
                    )
                try:
                    normalized_value = int(float(value))
                except (TypeError, ValueError) as e:
                    raise TypeError(
                        f"Row {row_idx}, column '{column_name}': "
                        f"Cannot convert '{value}' to integer categorical"
                    ) from e

            elif dtype and dtype.startswith("float"):
                if isinstance(value, bool):
                    raise TypeError(
                        f"Row {row_idx}, column '{column_name}': "
                        f"Boolean cannot be converted to float categorical"
                    )
                try:
                    normalized_value = float(value)
                except (TypeError, ValueError) as e:
                    raise TypeError(
                        f"Row {row_idx}, column '{column_name}': "
                        f"Cannot convert '{value}' to float categorical"
                    ) from e

            elif dtype == "bool":
                if isinstance(value, bool):
                    normalized_value = value
                elif isinstance(value, str):
                    if value.lower() in ("true", "1", "yes"):
                        normalized_value = True
                    elif value.lower() in ("false", "0", "no"):
                        normalized_value = False
                    else:
                        raise ValueError(
                            f"Row {row_idx}, column '{column_name}': "
                            f"Cannot convert '{value}' to boolean"
                        )
                else:
                    raise TypeError(
                        f"Row {row_idx}, column '{column_name}': "
                        f"Expected boolean categorical, got {type(value).__name__}"
                    )

            else:
                # String categorical
                normalized_value = str(value)

            if str(normalized_value) not in [str(cat) for cat in categories]:
                raise ValueError(
                    f"Row {row_idx}, column '{column_name}': "
                    f"Value '{value}' is not valid. "
                    f"Allowed: {categories}"
                )

            return normalized_value

        if col_type == "Float":
            if isinstance(value, bool):
                raise TypeError(
                    f"Row {row_idx}, column '{column_name}': "
                    f"Boolean cannot be converted to Float"
                )
            try:
                return float(value)
            except (TypeError, ValueError) as e:
                raise TypeError(
                    f"Row {row_idx}, column '{column_name}': "
                    f"Cannot convert '{value}' to Float"
                ) from e

        if col_type == "Integer":
            if isinstance(value, bool):
                raise TypeError(
                    f"Row {row_idx}, column '{column_name}': "
                    f"Boolean cannot be converted to Integer"
                )
            try:
                int_val = int(value)
                if isinstance(value, float) and not np.isclose(value, int_val):
                    raise TypeError(
                        f"Row {row_idx}, column '{column_name}': "
                        f"Float value '{value}' has decimals, cannot convert to Integer"
                    )
                return int_val
            except (TypeError, ValueError) as e:
                raise TypeError(
                    f"Row {row_idx}, column '{column_name}': "
                    f"Cannot convert '{value}' to Integer"
                ) from e

        if col_type == "Text":
            return str(value)

        # Unknown type
        return value

    def process_manual_input(
        self, manual_input: List[dict], dataset_path: str
    ) -> "DashAIDataset":
        """Process manual input data into a DashAIDataset with type validation.

        Parameters
        ----------
        manual_input : List[dict]
            List of dictionaries representing manual input data.
        dataset_path : str
            Path to the training dataset (used to get column specs for validation)

        Returns
        -------
        DashAIDataset
            Processed DashAIDataset from manual input.

        Raises
        ------
        ValueError
            If input cardinality doesn't match or categorical value is invalid
        TypeError
            If input types don't match expected types
        """
        from pandas import DataFrame

        from DashAI.back.dataloaders.classes.dashai_dataset import (
            get_columns_spec,
            to_dashai_dataset,
            transform_dataset_with_schema,
        )

        columns_spec = get_columns_spec(dataset_path)
        inputs_cardinality = self.get_metadata()["inputs_cardinality"]

        if inputs_cardinality != "n" and len(manual_input[0]) != inputs_cardinality:
            raise ValueError(
                f"Input cardinality ({len(manual_input[0])}) does not "
                f"match task cardinality ({inputs_cardinality})"
            )

        mapped_inputs = []
        for row_idx, input_dict in enumerate(manual_input):
            row = {}
            for col_name, value in input_dict.items():
                column_spec = columns_spec.get(col_name)
                if not column_spec:
                    raise ValueError(
                        f"Column '{col_name}' not found in training dataset"
                    )

                # File case (image, audio, video, etc.)
                if isinstance(value, UploadFile):
                    file_bytes = value.file.read()
                    data, detected_type = get_bytes_with_type_filetype(file_bytes)
                    expected_type = column_spec.get("type", "")
                    if detected_type.lower() != expected_type.lower():
                        raise TypeError(
                            f"Row {row_idx}, column '{col_name}': "
                            f"File type '{detected_type}' doesn't match "
                            f"expected type '{expected_type}'"
                        )
                    if detected_type == "image":
                        # Store in the same struct format used by the image dataloader
                        # so DashAIDataset.__getitem__ can wrap it in DashAIImage.
                        fname = getattr(value, "filename", None) or ""
                        row[col_name] = {"bytes": data, "path": fname}
                    else:
                        row[col_name] = data

                # File saved to disk by job queue
                elif isinstance(value, dict) and "__image_file__" in value:
                    file_path_on_disk = value["__image_file__"]
                    with open(file_path_on_disk, "rb") as f:
                        file_bytes = f.read()
                    data, detected_type = get_bytes_with_type_filetype(file_bytes)
                    expected_type = column_spec.get("type", "")
                    if detected_type.lower() != expected_type.lower():
                        raise TypeError(
                            f"Row {row_idx}, column '{col_name}': "
                            f"File type '{detected_type}' doesn't match "
                            f"expected type '{expected_type}'"
                        )
                    if detected_type == "image":
                        import os

                        row[col_name] = {
                            "bytes": data,
                            "path": os.path.basename(file_path_on_disk),
                        }
                    else:
                        row[col_name] = data

                # Primitive value
                else:
                    normalized_value = self._validate_and_normalize_value(
                        value, column_spec, col_name, row_idx
                    )
                    row[col_name] = normalized_value

            mapped_inputs.append(row)

        # Convert to DataFrame first
        mapped_inputs_df = DataFrame(mapped_inputs)

        # Convert to DashAIDataset and apply schema transformation
        # This ensures categorical encoding is applied
        dashai_dataset = to_dashai_dataset(mapped_inputs_df)
        dashai_dataset = transform_dataset_with_schema(dashai_dataset, columns_spec)

        return dashai_dataset
