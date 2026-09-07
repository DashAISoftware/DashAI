from abc import abstractmethod
from typing import Dict, Final, List

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.schema_fields.base_schema import BaseSchema


class BaseExtractor(ConfigObject):
    """Abstract base class for all document text extractors.

    Subclasses must implement extract(file_path) and override
    SUPPORTED_FILE_TYPES and optionally SCHEMA.
    """

    TYPE: Final[str] = "Extractor"
    SCHEMA: BaseSchema = BaseSchema
    SUPPORTED_FILE_TYPES: List[str] = []

    @abstractmethod
    def extract(self, file_path: str) -> str:
        """Extract text from the given file.

        Args:
            file_path: Absolute path to the file to extract text from.

        Returns:
            Extracted text content.

        Raises:
            RAGDocumentParsingError: If extraction fails.
        """

    def __init__(self, **kwargs):
        """Initialize extractor with optional parameters.

        Validates kwargs against the component schema if any are provided.
        Extractors are stateless — params are only used for validation and
        signature computation.
        """
        if kwargs:
            self.validate_and_transform(kwargs)

    @classmethod
    def get_metadata(cls) -> Dict[str, object]:
        """Return metadata for registry — primarily supported_file_types."""
        return {
            "supported_file_types": cls.SUPPORTED_FILE_TYPES,
        }
