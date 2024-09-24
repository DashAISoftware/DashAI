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

    ALLOWED_DTYPES: list[str] = ["*"]  # "*" means any dtype
    RESTRICTED_DTYPES: list[str] = []  # List of restricted dtypes
    INPUT_CARDINALITY: dict[str, int] = {
        "min": 1,
    }  # Dictionary with the cardinality of the input columns
    """
    Examples of INPUT_CARDINALITY:

    INPUT_CARDINALITY = {"min": 1}  # At least one column is required.\n
    INPUT_CARDINALITY = {"min": 2, "max": 5}  # Between 2 and 5 columns are required.\n
    INPUT_CARDINALITY = {"max": 5}  # Up to 5 columns.\n
    INPUT_CARDINALITY = {"exact": 3}  # Exactly 3 columns are required.

    min, max and exact can be combined together to define the cardinality
    of the input columns as needed.
    """

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
        metadata["allowed_dtypes"] = cls.ALLOWED_DTYPES
        metadata["input_cardinality"] = cls.INPUT_CARDINALITY
        metadata["restricted_dtypes"] = cls.RESTRICTED_DTYPES
        return metadata

    @abstractmethod
    def launch_exploration(self, dataset: DashAIDataset) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_results(self, exploration_path: str) -> Dict[str, Any]:
        raise NotImplementedError
