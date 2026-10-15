import re
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

    @staticmethod
    def render_placeholders(template: str, values: Dict[str, Any]) -> str:
        """Substitute every placeholder token in a single left-to-right pass.

        Matching is done against the *original* template only: a value inserted
        for one token is never re-scanned for further tokens. A user message or
        chunk that literally contains ``"{input}"`` (or any other token) is
        therefore preserved verbatim instead of being expanded again.

        Parameters
        ----------
        template : str
            Template containing zero or more placeholder tokens.
        values : Dict[str, Any]
            Mapping of placeholder token (for example ``"{input}"``) to its
            replacement value. Values are coerced with ``str``.

        Returns
        -------
        str
            The rendered template.
        """
        if not values:
            return template
        # Longest tokens first so a token that is a prefix of another (for
        # example ``"{n}"`` against ``"{n_max}"``) cannot shadow the longer one.
        tokens = sorted(values, key=len, reverse=True)
        pattern = re.compile("|".join(re.escape(token) for token in tokens))
        return pattern.sub(lambda match: str(values[match.group(0)]), template)

    @classmethod
    def render_optional(cls, template: str, key: str, value: Any) -> str:
        """Render an optional placeholder following the line-drop contract.

        When ``value`` is ``None`` every physical line containing ``key`` is
        removed, so an optional sentence collapses entirely instead of leaving
        a dangling fragment. Otherwise ``key`` is replaced in place with
        ``str(value)``.

        Parameters
        ----------
        template : str
            Template that may contain the optional placeholder token.
        key : str
            The optional placeholder token (for example ``"{n_max}"``).
        value : Any
            Replacement value. When ``None`` the token's lines are dropped.

        Returns
        -------
        str
            The rendered template.
        """
        if value is None:
            kept: List[str] = []
            for line in template.split("\n"):
                if key not in line:
                    kept.append(line)
            return "\n".join(kept)
        return template.replace(key, str(value))

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
