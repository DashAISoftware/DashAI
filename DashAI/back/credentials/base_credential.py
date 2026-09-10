"""Base class for DashAI platform credentials."""

from abc import ABC, abstractmethod
from typing import Final, Union

from kink import di

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.utils import MultilingualString


class BaseCredential(ConfigObject, ABC):
    """Abstract base class for all DashAI credentials.

    A credential authenticates against an external platform with a key and
    persists it (encrypted) so components that declare it in
    ``REQUIRED_CREDENTIALS`` or ``OPTIONAL_CREDENTIALS`` can use it.

    Subclasses only implement :meth:`verify` (the platform-specific network
    check) and optionally :meth:`apply` (push the key into the platform SDK).
    """

    TYPE: Final[str] = "Credential"
    DISPLAY_NAME: Union[str, MultilingualString] = ""
    DESCRIPTION: Union[str, MultilingualString] = ""
    ICON: str = "Key"

    @abstractmethod
    def verify(self, key: str) -> bool:
        """Check a key against the platform.

        Parameters
        ----------
        key : str
            The key to validate.

        Returns
        -------
        bool
            True if the key is valid.
        """
        raise NotImplementedError

    def auth(self, key: str) -> bool:
        """Validate and persist a key.

        Parameters
        ----------
        key : str
            The key to authenticate with.

        Returns
        -------
        bool
            True on success.

        Raises
        ------
        ValueError
            If the key fails verification.
        """
        if not self.verify(key):
            raise ValueError(
                f"Invalid credential for {type(self).__name__}: verification failed."
            )
        di["credential_store"].save(type(self).__name__, key)
        return True

    def get_key(self) -> Union[str, None]:
        """Return the stored decrypted key, or None.

        Returns
        -------
        Union[str, None]
            The decrypted key, or None if not authenticated.
        """
        return di["credential_store"].load(type(self).__name__)

    def is_authenticated(self) -> bool:
        """Return whether a verified key is stored.

        Returns
        -------
        bool
            True if authenticated.
        """
        return di["credential_store"].is_verified(type(self).__name__)

    def apply(self) -> None:
        """Push the stored key into the platform SDK if present.

        The default implementation is a no-op, which makes a credential safe to
        ``apply()`` even when unauthenticated (used by ``OPTIONAL_CREDENTIALS``).
        Override in subclasses that need to log in to an SDK.
        """
        return None
