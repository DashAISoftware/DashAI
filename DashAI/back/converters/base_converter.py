from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Final, List, Type, Union

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.schema_fields.base_schema import BaseSchema
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
    `changes_row_count` returns True (e.g. samplers).

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
        meta["n_components_features_bounded"] = getattr(
            cls, "N_COMPONENTS_FEATURES_BOUNDED", False
        )

        instance_slots = getattr(cls, "_default_output_slots", None)
        if instance_slots is None:
            try:
                instance_slots = cls().get_output_slots()
            except Exception:
                instance_slots = [{"slot": 0, "label": "output", "type": None}]
        meta["output_slots"] = cls.serialize_output_slots(instance_slots)

        # Serialize allowed_types class references → class name strings for the frontend
        raw_types = meta.get("allowed_types", [])
        meta["allowed_types"] = [t.__name__ for t in raw_types]

        # Normalize allowed_dtypes: absent or ["*"] → [] (empty means no restriction)
        if not meta.get("allowed_dtypes") or meta["allowed_dtypes"] == ["*"]:
            meta["allowed_dtypes"] = []

        # Ensure non_allowed_dtypes is always present for the frontend
        if "non_allowed_dtypes" not in meta:
            meta["non_allowed_dtypes"] = []

        # Drop restricted_dtypes (no converter uses it; it is always [])
        meta.pop("restricted_dtypes", None)

        return meta

    @staticmethod
    def serialize_output_slots(
        slots: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Serialize `get_output_slots()` entries for the frontend: each
        `type` is a live `DashAIDataType` instance (or `None`), replaced
        here with just its class name string (or `None`). Shared by
        `get_metadata()` (uses a default-constructed instance) and any
        caller that instead needs a specific converter *instance*'s real
        slots (e.g. one already configured with real params in a model
        session — see `get_converters_output_slots` in
        `api/api_v1/endpoints/model_sessions.py`)."""
        return [
            {
                "slot": s["slot"],
                "label": s["label"],
                "type": type(s["type"]).__name__ if s.get("type") is not None else None,
            }
            for s in slots
        ]

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

    def get_output_slots(self) -> List[Dict[str, Any]]:
        """Return the declared output slots for this converter.

        Most converters produce a single homogeneous output type for all
        their result columns, so the default derives one slot from
        `get_output_type()`. A converter whose output is genuinely
        heterogeneous (e.g. `SimpleImputer` with `add_indicator=True`,
        which produces both imputed columns and separate integer
        "missing indicator" columns) must override this to declare more
        than one slot.

        Returns
        -------
        list of dict
            Each entry is `{"slot": int, "label": str, "type": DashAIDataType}`.
        """
        return [{"slot": 0, "label": "output", "type": self.get_output_type()}]

    def classify_output_columns(
        self, real_column_names: List[str]
    ) -> Dict[int, List[str]]:
        """Split this converter's real, already-transformed output columns
        into the slots declared by `get_output_slots()`.

        The default assigns every real column to slot 0, correct for any
        converter with a single declared slot. A converter with more than
        one slot must override this to classify its own real column names
        (e.g. by a naming convention it controls).

        Parameters
        ----------
        real_column_names : list of str
            The real column names this converter actually produced/kept
            for one partition, after a real `fit`+`transform`.

        Returns
        -------
        dict
            Maps slot index to the real column names belonging to it.
        """
        return {0: list(real_column_names)}

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
