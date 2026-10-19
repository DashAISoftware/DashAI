from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Final, List, Optional, Type, Union

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.preprocessing.structure_types import (
    BlockItem,
    ColumnItem,
    RowsNotSupportedError,
    StateItem,
    StructureDelta,
    type_fields,
)
from DashAI.back.static.icons import Icon
from DashAI.back.types.dashai_data_type import DashAIDataType

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class BaseConverterSchema(BaseSchema):
    """
    Base schema for converters, it defines the parameters to be used in each converter.

    The schema should be assigned to the converter class to define the parameters of
    its configuration.
    """


class BaseConverter(ConfigObject, ABC):
    """Abstract base class for all data converters in DashAI.

    Converters modify dataset columns in a supervised or unsupervised way.
    Operations include scaling, encoding, dimensionality reduction, imputation,
    and feature engineering. Converters do not add or remove rows unless
    `CHANGES_ROW_COUNT` is True (e.g. samplers).

    All converters must implement `fit`, `transform`, and `get_output_type`.
    """

    TYPE: Final[str] = "Converter"
    DISPLAY_NAME: Final[str] = ""
    DESCRIPTION: Final[str] = ""
    SHORT_DESCRIPTION: Final[str] = ""
    IMAGE_PREVIEW: Final[str] = ""
    CATEGORY: Final[str] = "Other"
    ICON: Final[str] = Icon.Extension.value
    COLOR: Final[str] = "rgb(255, 255, 255)"
    SUPERVISED: bool = False
    CHANGES_ROW_COUNT: bool = False
    # Whether `fit` computes anything from the actual values of the input
    # data (e.g. a mean, a vocabulary, learned components) rather than just
    # validating shapes/types or applying a fixed, user-specified rule.
    # Defaults to True (the conservative choice): a converter added without
    # setting this explicitly warns about possible leakage rather than
    # silently skipping the warning for a converter that does learn from
    # data. Used to flag possible data leakage when applied inside a
    # notebook, where fit/transform runs on the whole dataset with no
    # train/test split.
    LEARNS_FROM_DATA: bool = True
    # True for converters that never transform values, only keep or drop
    # whole columns as-is (feature selection, variance thresholding): the
    # output type of a surviving column is always exactly its input type, no
    # arithmetic involved. Lets a caller that already knows the real input
    # type (e.g. the Models-module wizard, once a real scope is chosen) use
    # that instead of this class's own best-effort get_output_type() guess,
    # which — called on a bare unfitted instance — has no idea what column
    # it will actually run on.
    PRESERVES_INPUT_TYPE: bool = False
    # What the converter does to the columns in its scope, used to estimate
    # the dataset structure of a session's converter chain before any fit
    # (see infer_output_columns):
    # - "replace": same columns, values (and maybe types) changed
    # - "add": keeps its scope columns and adds new ones
    # - "expand": consumes its scope columns and outputs new ones
    # - "select": keeps a subset of its scope columns, unchanged
    # - "rows": changes the row count (not supported in sessions yet)
    # None (e.g. an older plugin) is treated as "expand" with an unknown
    # column count, which never promises a column that may not exist.
    COLUMN_OPERATION: Optional[str] = None
    # For a "rows" converter, where it runs in a session's preprocessing:
    # - "train": only on the training split, never on validation, test or
    #   prediction inputs (resampling);
    # - "splits": on train, validation and test, never on prediction inputs
    #   (row removal; the converter must implement rows_to_keep).
    # None means sessions do not support it yet.
    ROWS_APPLY_TO: Optional[str] = None
    SCHEMA: BaseConverterSchema

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Get metadata for the converter, used by the DashAI frontend.

        Parameters
        ----------
        cls : type
            The converter class (injected automatically by Python for
            classmethods).

        Returns
        -------
        Dict[str, Any]
            Dictionary containing display name, short description, image
            preview path, category, icon, color, and whether the converter
            is supervised.
        """
        meta: Dict[str, Any] = dict(getattr(cls, "metadata", {}) or {})
        meta["display_name"] = cls.DISPLAY_NAME if cls.DISPLAY_NAME else cls.__name__
        meta["short_description"] = (
            cls.SHORT_DESCRIPTION if cls.SHORT_DESCRIPTION else ""
        )
        meta["image_preview"] = cls.IMAGE_PREVIEW if cls.IMAGE_PREVIEW else ""
        meta["category"] = cls.CATEGORY if cls.CATEGORY else "Other"
        meta["icon"] = cls.ICON if cls.ICON else Icon.Extension.value
        meta["color"] = cls.COLOR if cls.COLOR else "rgb(255, 255, 255)"
        meta["requires_download"] = bool(getattr(cls, "REQUIRES_DOWNLOAD", False))
        meta["download_size_bytes"] = getattr(cls, "DOWNLOAD_SIZE_BYTES", None)
        meta["supervised"] = cls.SUPERVISED
        meta["changes_row_count"] = cls.CHANGES_ROW_COUNT
        meta["preserves_input_type"] = cls.PRESERVES_INPUT_TYPE
        meta["learns_from_data"] = cls.LEARNS_FROM_DATA
        meta["column_operation"] = cls.COLUMN_OPERATION
        meta["rows_apply_to"] = cls.ROWS_APPLY_TO
        meta["n_components_features_bounded"] = getattr(
            cls, "N_COMPONENTS_FEATURES_BOUNDED", False
        )

        # Serialize allowed_types to the names the frontend compares against.
        # A DashAI type reports its own name via display_name(), which is the
        # same string a column emits through to_string(), so the two always
        # agree.
        raw_types = meta.get("allowed_types", [])
        meta["allowed_types"] = [
            t.display_name() if hasattr(t, "display_name") else t.__name__
            for t in raw_types
        ]

        # Normalize allowed_dtypes: absent or ["*"] → [] (empty means no restriction)
        if not meta.get("allowed_dtypes") or meta["allowed_dtypes"] == ["*"]:
            meta["allowed_dtypes"] = []

        # Ensure non_allowed_dtypes is always present for the frontend
        if "non_allowed_dtypes" not in meta:
            meta["non_allowed_dtypes"] = []

        # Same default the explorers get (base_explorer.get_metadata): a
        # converter that transforms selected columns needs at least one. Without
        # it the key arrived absent or None, the column picker read it as "no
        # requirement", and a converter was never disabled for a dataset whose
        # columns it cannot accept — so SMOTE was offered for a table of
        # strings, which it refuses.
        if meta.get("input_cardinality") is None:
            meta["input_cardinality"] = {"min": 1}

        # Drop restricted_dtypes (no converter uses it; it is always [])
        meta.pop("restricted_dtypes", None)

        # A representative output type, so the Models-module wizard can show
        # "this converter's group is typed X" before any real fit exists.
        # Not every converter can be instantiated with no arguments (some
        # require constructor params with no default), so this is
        # best-effort: None means "unknown until configured".
        try:
            # output_dtype is the concrete storage dtype (e.g. "int64"), so a
            # group column can show one instead of "unknown" before any real
            # fit exists.
            meta["output_type"], meta["output_dtype"] = type_fields(
                cls().get_output_type()
            )
        except Exception:
            meta["output_type"] = None
            meta["output_dtype"] = None

        return meta

    def get_report(self) -> Union[Dict[str, Any], None]:
        """Return the converter report produced after execution, if any.

        The report complements the transformed dataset with information that
        helps downstream tools (explorers, visualisations) interpret what the
        converter did during its pipeline step. Persisted to disk per converter
        execution. Optional — converters that produce no supplementary
        information return ``None``.

        Returns
        -------
        Dict[str, Any] or None
            JSON-serializable report dict, or ``None`` when the converter does
            not produce one.
        """
        return None

    def build_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Wrap converter-specific data with the producer converter name.

        Subclasses pass only information that is useful after the conversion
        has finished. Configuration parameters are already persisted with the
        converter DB row.
        """
        return {"converter": self.__class__.__name__, **data}

    def infer_output_columns(self, inputs: List[StateItem]) -> StructureDelta:
        """Estimate what this converter does to its scope, without any data.

        Called on an instance built with the user's params but never fit, so
        a session wizard can show which columns exist after each step of a
        converter chain. The default follows COLUMN_OPERATION; converters
        that know more (e.g. an exact column count from `n_components`, or
        output names built from their inputs) override it.

        Parameters
        ----------
        inputs : list of ColumnItem | BlockItem
            The dataset state items in this converter's scope.

        Returns
        -------
        StructureDelta
            The scope items that survive (maybe retyped) and the new items.

        Raises
        ------
        RowsNotSupportedError
            If the converter changes the row count.
        """
        operation = type(self).COLUMN_OPERATION or "expand"
        if operation == "rows":
            if type(self).ROWS_APPLY_TO not in ("train", "splits"):
                raise RowsNotSupportedError(type(self).__name__)
            return StructureDelta(kept=list(inputs), drops_unscoped=True)
        if operation == "replace":
            return StructureDelta(kept=[self._retype(item) for item in inputs])
        if operation == "add":
            return StructureDelta(kept=list(inputs), added=self._default_blocks())
        if operation == "select":
            return StructureDelta(added=self._selection_blocks(inputs))
        return StructureDelta(added=self._default_blocks())

    def rows_to_keep(self, x: "DashAIDataset") -> List[int]:
        """Positions of the rows of x that survive this converter.

        Required for converters with ROWS_APPLY_TO = "splits": the session
        runtime cuts the whole split (inputs and target together) with these
        positions instead of taking the converter's own output, so the
        target never misaligns.

        Parameters
        ----------
        x : DashAIDataset
            The converter's scope columns of one split.

        Returns
        -------
        list of int
            0-based positions of the kept rows, in order.

        Raises
        ------
        NotImplementedError
            For a converter that does not report which rows it keeps.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not report which rows it keeps."
        )

    def _retype(self, item: StateItem) -> StateItem:
        """Copy an item replaced in place with this converter's output type."""
        if type(self).PRESERVES_INPUT_TYPE:
            return item
        column_name = item.name if isinstance(item, ColumnItem) else None
        type_name, dtype = type_fields(self.get_output_type(column_name))
        return item.model_copy(update={"type": type_name, "dtype": dtype})

    def _default_blocks(self, count: Optional[int] = None) -> List[StateItem]:
        """One block typed with this converter's output type.

        Parameters
        ----------
        count : int, optional
            The block's column count, when params determine it. Defaults to
            None (known only after fit).
        """
        type_name, dtype = type_fields(self.get_output_type())
        return [BlockItem(type=type_name, dtype=dtype, count=count)]

    def _selected_count(self, inputs: List[StateItem]) -> Optional[int]:
        """How many scope columns a "select" converter keeps, if params say.

        None (the default) means it depends on the data, e.g. a statistical
        test threshold. Overridden by selectors with a fixed count (`k`).
        """
        return None

    def _selection_blocks(self, inputs: List[StateItem]) -> List[StateItem]:
        """One block per distinct input type, since selection keeps types.

        A selector says at most how many columns survive, never which ones,
        so its output is always symbolic, even with a known count.
        """
        by_type: Dict[Optional[str], List[StateItem]] = {}
        for item in inputs:
            by_type.setdefault(item.type, []).append(item)
        count = self._selected_count(inputs) if len(by_type) == 1 else None
        blocks = []
        for type_name, items in by_type.items():
            dtypes = {item.dtype for item in items}
            blocks.append(
                BlockItem(
                    type=type_name,
                    dtype=dtypes.pop() if len(dtypes) == 1 else None,
                    count=count,
                )
            )
        return blocks

    @abstractmethod
    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the DashAI data type produced by this converter for a given column.

        Each converter must implement this to declare what type its output columns
        will have after transformation, so that DashAI can update the dataset schema.

        Parameters
        ----------
        column_name : str, optional
            The name of the output column. Useful for
            converters that may produce different types per column. Defaults to None.

        Returns
        -------
        DashAIDataType
            The output data type for the specified column.
        """
        raise NotImplementedError

    @abstractmethod
    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> Type[BaseConverter]:
        """Fit the converter to the training data.

        For unsupervised converters (e.g. scalers, PCA), only `x` is used.
        For supervised converters (e.g. feature selectors), both `x` and `y`
        must be provided.

        Parameters
        ----------
        x : DashAIDataset
            The input dataset to fit the converter on.
        y : DashAIDataset, optional
            Target labels for supervised converters.
            Defaults to None.

        Returns
        -------
        BaseConverter
            The fitted converter instance (self).
        """
        raise NotImplementedError

    @abstractmethod
    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Apply the fitted converter to transform the dataset.

        Must be called after `fit`. The converter is applied to `x` and
        the resulting DashAIDataset is returned with updated column types.

        Parameters
        ----------
        x : DashAIDataset
            The input dataset to transform.
        y : DashAIDataset, optional
            Target vectors. Not used by most
            converters. Defaults to None.

        Returns
        -------
        DashAIDataset
            The transformed dataset with updated column types.
        """
        raise NotImplementedError
