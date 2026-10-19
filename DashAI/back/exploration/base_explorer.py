from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Final, List, Optional

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.artifacts import Artifact
from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.static.icons import Icon
from DashAI.back.types.utils import NON_NUMERIC_DTYPES  # noqa: F401

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class BaseExplorerSchema(BaseSchema):
    """
    Base schema for explorers, it defines the parameters to be used in each explorer.

    The schema should be assigned to the explorer class to define the parameters of
    its configuration.
    """


class BaseExplorer(ConfigObject, ABC):
    """
    Base class for explorers.
    Use this class as reference to create new explorers.

    To create a new explorer, you must:
    - Create a new schema that extends `BaseExplorerSchema`.
    - Create a new class that extends `BaseExplorer` and assign the
        previous schema to the `SCHEMA` attribute.
    - Implement the `launch_exploration` method.
    - Implement the `save_notebook` method.
    - Implement the `get_results` method.

    You can also optionally:
    - Implement the `validate_parameters` method if you want to validate
        the parameters in a custom way before creating/updating the database record.
    - Implement the `prepare_dataset` method if you want to prepare the
        dataset in a custom way before launching the exploration.
    - Add a display name to the `DISPLAY_NAME` attribute to show a custom
        name in the frontend.
    - Add a description to the `DESCRIPTION` attribute to show a custom
        description in the frontend.
    - Set ``REQUIRES_CONVERTER_REPORT`` to ``True`` if the explorer needs
        the report produced by a converter execution.
    - Set ``REQUIRES_CONVERTER_CLASS`` to the converter class name string
        (e.g. ``"Clustering"``) to restrict metadata loading to a specific
        converter type instead of the most recently finished converter of any
        type.
    """

    TYPE: Final[str] = "Explorer"
    DISPLAY_NAME: Final[str] = ""
    DESCRIPTION: Final[str] = ""
    SHORT_DESCRIPTION: Final[str] = ""
    IMAGE_PREVIEW: Final[str] = ""
    CATEGORY: Final[str] = "Other"
    ICON: Final[str] = Icon.Extension.value
    COLOR: Final[str] = "rgb(255, 255, 255)"
    REQUIRES_CONVERTER_REPORT: Final[bool] = False
    REQUIRES_CONVERTER_CLASS: Final[Optional[str]] = None
    SCHEMA: BaseExplorerSchema
    metadata: Dict[str, Any] = {}

    def __init__(self, **kwargs) -> None:
        """Initialize the explorer, storing any extra kwargs for later use.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments as defined in the
            explorer's SCHEMA.
        """
        self.kwargs = kwargs
        self.context: Dict[str, Any] = {}

    def set_context(self, context: Dict[str, Any]) -> None:
        """Set optional runtime context for explorers that need extra inputs.

        The default explorer contract remains dataset + columns + parameters.
        This context is an opt-in extension for explorers that declare extra
        runtime needs, such as converter execution report.
        """
        self.context = context

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Get metadata for the explorer, used by the DashAI frontend.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing display name, description,
            image preview path, category, icon, color, allowed semantic
            types, allowed dtypes, input cardinality constraints, and any
            optional capability flags declared by the explorer.
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
        meta["requires_converter_report"] = (
            cls.REQUIRES_CONVERTER_REPORT if cls.REQUIRES_CONVERTER_REPORT else False
        )
        meta["requires_converter_class"] = (
            cls.REQUIRES_CONVERTER_CLASS if cls.REQUIRES_CONVERTER_CLASS else None
        )
        meta["requires_download"] = bool(getattr(cls, "REQUIRES_DOWNLOAD", False))
        meta["download_size_bytes"] = getattr(cls, "DOWNLOAD_SIZE_BYTES", None)

        if meta.get("input_cardinality") is None:
            meta["input_cardinality"] = {"min": 1}

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

        # Drop internal-only flags that are not consumed by the frontend directly
        meta.pop("restricted_dtypes", None)
        meta.pop("numeric_categorical_only", None)

        # Ensure non_allowed_dtypes is always present for the frontend
        if "non_allowed_dtypes" not in meta:
            meta["non_allowed_dtypes"] = []

        return meta

    @classmethod
    def validate_parameters(cls, params: Dict[str, Any]) -> bool:
        """Validate explorer parameters against the explorer's schema.

        Parameters
        ----------
        params : Dict[str, Any]
            The configuration parameters to validate.

        Returns
        -------
        BaseExplorerSchema
            The validated and parsed schema instance.
            Subclasses that override this method may return a bool to
            indicate pass/fail without returning the model instance.

        Raises
        ------
        ValidationError
            If any parameter fails schema validation.
        """
        return cls.SCHEMA.model_validate(params)

    @classmethod
    def validate_columns(
        cls, explorer_info: Explorer, column_spec: Dict[str, Dict[str, str]]
    ) -> bool:
        """Validate that the selected columns satisfy the explorer's constraints.

        Checks column count against ``input_cardinality`` and checks each
        column's semantic type against ``allowed_types`` AND its dtype against
        ``allowed_dtypes`` (AND logic; empty list means no restriction on
        that dimension).

        Parameters
        ----------
        explorer_info : Explorer
            The database record for the explorer instance,
            including the selected columns.
        column_spec : Dict[str, Dict[str, str]]
            A mapping from column name to a dict with at least
            ``"type"`` (semantic type name) and ``"dtype"`` (dtype string).

        Returns
        -------
        bool
            True if all column constraints are satisfied, False otherwise.
        """
        metadata = cls.get_metadata()
        selected_columns = explorer_info.columns
        allowed_types = metadata.get("allowed_types", [])
        allowed_dtypes = metadata.get("allowed_dtypes", [])
        input_cardinality = metadata.get("input_cardinality", {})

        # Check cardinality
        n = len(selected_columns)
        if "exact" in input_cardinality and n != input_cardinality["exact"]:
            return False
        if "min" in input_cardinality and n < input_cardinality["min"]:
            return False
        if "max" in input_cardinality and n > input_cardinality["max"]:
            return False

        # Global dtype blacklist: dtypes that are never valid for this explorer.
        non_allowed_dtypes = metadata.get("non_allowed_dtypes", [])
        for column in selected_columns:
            column_name = column["columnName"]
            col_info = column_spec.get(column_name, {})
            col_type = col_info.get("type", "")
            col_dtype = col_info.get("dtype", "")

            if allowed_types and col_type not in allowed_types:
                return False
            if non_allowed_dtypes and col_dtype in non_allowed_dtypes:
                return False
            if allowed_dtypes and col_dtype not in allowed_dtypes:
                return False

        return True

    def prepare_dataset(
        self, loaded_dataset: "DashAIDataset", columns: List[Dict[str, Any]]
    ) -> "DashAIDataset":
        """Prepare the dataset by selecting only the columns
        needed for this exploration.

        Override this method in subclasses that need to load additional columns
        beyond those explicitly selected (e.g. a color-grouping column).

        Parameters
        ----------
        loaded_dataset : DashAIDataset
            The full dataset loaded from storage.
        columns : List[Dict[str, Any]]
            List of column descriptor dicts, each
            containing at least ``"columnName"``. Optional keys: ``"id"``,
            ``"valueType"``, ``"dataType"``.

        Returns
        -------
        DashAIDataset
            Dataset restricted to the requested columns.
        """
        # Select the columns
        columnNames = list({col["columnName"] for col in columns})
        loaded_dataset = loaded_dataset.select_columns(columnNames)
        return loaded_dataset

    @abstractmethod
    def launch_exploration(
        self, dataset: "DashAIDataset", explorer_info: Explorer
    ) -> Any:
        """Run the exploration and return the raw result.

        Parameters
        ----------
        dataset : DashAIDataset
            The prepared dataset (output of
            `prepare_dataset`).
        explorer_info : Explorer
            The database record for this explorer
            instance, including name, columns, and parameters.

        Returns
        -------
        Any
            The exploration result (e.g. a Plotly figure, a DataFrame).
        """
        raise NotImplementedError

    @abstractmethod
    def save_notebook(
        self,
        notebook_info: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Persist the exploration result to disk.

        Parameters
        ----------
        notebook_info : Notebook
            The notebook database record.
        explorer_info : Explorer
            The explorer database record.
        save_path : Path
            The directory where the result should be saved.
        result : Any
            The raw result returned by `launch_exploration`.

        Returns
        -------
        str
            The path of the saved result file as a POSIX string.
        """
        raise NotImplementedError

    @abstractmethod
    def get_results(
        self, exploration_path: str, options: Dict[str, Any]
    ) -> List[Artifact]:
        """Load a previously saved exploration result and turn it into artifacts.

        This runs once, when the exploration is created: the explorer job (or
        the pipeline exploration node) calls it right after `save_notebook`,
        normalizes the returned artifacts and stores them on disk. Read
        requests serve those stored artifacts, so this method is never called
        again for an existing exploration and the results keep rendering after
        the explorer is removed from the registry. Explorations created before
        artifacts were stored are upgraded by the artifact backfill, which
        calls this method one last time.

        Parameters
        ----------
        exploration_path : str
            Path to the file saved by `save_notebook`.
        options : Dict[str, Any]
            Optional rendering or filtering options. Kept for backwards
            compatibility; artifacts are built once, so no per request option
            reaches this method.

        Returns
        -------
        List[Artifact]
            A list of artifacts (:class:`PlotlyArtifact`,
            :class:`TableArtifact`, :class:`TextArtifact` or
            :class:`ImageArtifact`) describing the exploration result.
            Legacy explorers returning the old ``{"data", "type", "config"}``
            dict are upgraded by ``normalize_artifacts`` before storage.
        """
        raise NotImplementedError
