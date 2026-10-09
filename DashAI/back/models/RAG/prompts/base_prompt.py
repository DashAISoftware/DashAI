from typing import Any, Dict, Final, List

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.schema_fields import BaseSchema, schema_field, string_field


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


class BasePrompt(ConfigObject):
    """
    Base class for all RAG prompt templates.
    This class defines the interface for creating and formatting prompts.
    """

    TYPE: Final[str] = "Prompt"
    SCHEMA = PromptSchema
    DESCRIPTION: str = "Base class for RAG prompts."
    DISPLAY_NAME: str = "Base RAG Prompt"
    REQUIRED_EXTRA_KWARGS = []

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Return the prompt-specific metadata declared by the subclass.

        Returns
        -------
        Dict[str, Any]
            A copy of the class ``metadata`` attribute, or an empty dict when
            the subclass does not declare one.
        """
        return dict(getattr(cls, "metadata", {}))

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
