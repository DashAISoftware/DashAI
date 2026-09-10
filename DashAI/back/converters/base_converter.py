from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Final, Type, Union

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

        return meta

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
