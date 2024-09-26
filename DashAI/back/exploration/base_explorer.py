from abc import ABC, abstractmethod

from beartype.typing import Any, Dict, Final

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.schema_fields import BaseSchema
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
    - Create a new class that extends BaseExplorer.
    - Create a new schema that extends BaseExplorerSchema and
        replaces the SCHEMA attribute.
    - Implement the validate_parameters method.
    - Implement the launch_exploration method.
    - Implement the get_results method.
    - (Optional) Implement the save_exploration method to make your own
        save logic, if not, a pickle file will be saved by default with the result.
    """

    TYPE: Final[str] = "Explorer"
    SCHEMA: BaseExplorerSchema

    metadata: Dict[str, Any] = {}

    @classmethod
    def validate_parameters(cls, params: Dict[str, Any]) -> bool:
        """
        Validates the parameters of the explorer.

        Parameters
        ----------
        params : Dict[str, Any]
            The parameters to validate.

        Returns
        -------
        bool
            True if the parameters are valid, False otherwise.
        """
        return cls.SCHEMA.model_validate(params)

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """
        Get metadata values for the current explorer.

        Returns
        -------
        Dict[str, Any]
            Dictionary with the metadata containing valid dtypes and cardinality for
            the explorer columns.
        """
        metadata = cls.metadata
        # Set default values if not present
        if metadata.get("allowed_dtypes", None) is None:
            metadata["allowed_dtypes"] = ["*"]
        if metadata.get("restricted_dtypes", None) is None:
            metadata["restricted_dtypes"] = []
        if metadata.get("input_cardinality", None) is None:
            metadata["input_cardinality"] = {"min": 1}
        return metadata

    @abstractmethod
    def launch_exploration(self, dataset: DashAIDataset) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_results(
        self, exploration_path: str, orientation: str = "dict"
    ) -> Dict[str, Any]:
        raise NotImplementedError
