from abc import ABC, abstractmethod
from typing import ClassVar


class DashAIDataType(ABC):
    """Abstract base class for DashAI data types."""

    DISPLAY_NAME: ClassVar[str] = ""

    @classmethod
    def display_name(cls) -> str:
        """Return the name the frontend uses for this type.

        Returns
        -------
        str
            ``DISPLAY_NAME`` when the type sets one, otherwise the class name.
        """
        return cls.DISPLAY_NAME or cls.__name__

    @abstractmethod
    def to_string(self) -> str:
        """Convert to string representation."""
