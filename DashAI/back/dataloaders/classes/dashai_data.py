"""Common base class for every kind of data DashAI handles."""

from typing import ClassVar


class DashAIData:
    """Base class shared by DashAI datasets and documents.

    Attributes
    ----------
    DATA_KIND : str
        Identifier of the kind of data: ``"dataset"`` or ``"document"``.
        Empty on the base class itself.
    """

    DATA_KIND: ClassVar[str] = ""

    @classmethod
    def data_kind(cls) -> str:
        """Return the kind identifier of this data class.

        Returns
        -------
        str
            The value of ``DATA_KIND``.
        """
        return cls.DATA_KIND
