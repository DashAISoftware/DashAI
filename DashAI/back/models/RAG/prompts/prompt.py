from typing import Any, Dict, List

from DashAI.back.core.schema_fields import BaseSchema, schema_field, string_field
from DashAI.back.models.base_model import BaseModel


class PromptSchema(BaseSchema):
    """Schema for prompt templates.

    Attributes:
        template: The prompt template string with placeholders.
    """

    template: schema_field(
        string_field(),
        placeholder="",
        description="The prompt template with placeholders.",
    )  # type: ignore


class Prompt(BaseModel):
    """
    Base class for all RAG prompt templates.
    This class defines the interface for creating and formatting prompts.
    """

    SCHEMA = PromptSchema
    DESCRIPTION: str = "Base class for RAG prompts."
    DISPLAY_NAME: str = "Base RAG Prompt"
    REQUIRED_EXTRA_KWARGS = []

    def load(self, filename: str = "") -> None:
        """Load a prompt from a file.

        Args:
            filename: Path to the file to load from. If empty, uses the
                default.
        """

    def save(self, filename: str = "") -> None:
        """Save the prompt to a file.

        Args:
            filename: Path to save to. If empty, uses the default.
        """

    def train(self, **kwargs: Any) -> None:
        """No-op training method for compatibility with the model interface.

        Args:
            **kwargs: Ignored.
        """

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Retrieve class metadata.

        Returns:
            Dictionary of metadata attributes including download requirements
            from BaseModel, plus any prompt-specific metadata if defined.
        """
        # Start with BaseModel metadata (includes requires_download)
        metadata = super().get_metadata()
        # Add prompt-specific metadata if defined
        if hasattr(cls, "metadata"):
            metadata.update(cls.metadata)
        return metadata

    @classmethod
    def get_required_placeholders(cls) -> List[str]:
        """
        Get the list of required placeholders for the prompt template.
        Returns:
            List[str]: List of required placeholders.
        Raises:
            AttributeError: If the subclass does not define 'required_placeholders'.
        """
        if not hasattr(cls, "required_placeholders"):
            raise AttributeError(
                f"Prompt subclass {cls.__name__} must define "
                "'required_placeholders' class attribute."
            )
        return cls.required_placeholders

    def get_optional_placeholders(self) -> List[str]:
        """
        Get the list of optional placeholders for the prompt template.
        Returns:
            List[str]: List of optional placeholders.
        Raises:
            AttributeError: If the subclass does not define 'optional_placeholders'.
        """
        if not hasattr(self, "optional_placeholders"):
            raise AttributeError(
                f"Prompt subclass {type(self).__name__} must define "
                "'optional_placeholders' class attribute."
            )
        return self.optional_placeholders

    @classmethod
    def validate_template(cls, template: str) -> bool:
        """
        Validate that the template contains all required placeholders.
        Args:
            template (str): The prompt template to be validated.
        Returns:
            bool: True if the template is valid, False otherwise.
        """
        return all(placeholder in template for placeholder in cls.required_placeholders)

    def format(self, input: str, **kwargs: Any) -> str:
        """
        Instantiate and format the prompt.
        Args:
            input (str): The input to be formatted.
            **kwargs: Additional keyword arguments for formatting.
        Returns:
            str: The formatted prompt.
        """
        raise NotImplementedError("Subclasses must implement this method.")
