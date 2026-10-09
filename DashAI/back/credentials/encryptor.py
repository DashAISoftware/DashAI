"""Symmetric encryption for stored credential keys."""

import logging
import os
import stat
from pathlib import Path
from typing import Union

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


def load_or_create_key(
    key_path: Path,
    env_value: Union[str, None] = None,
    persist: bool = True,
) -> bytes:
    """Resolve the Fernet secret key.

    Resolution order: explicit ``env_value`` first, then an existing file at
    ``key_path``, otherwise a freshly generated key (persisted to ``key_path``
    when ``persist`` is True).

    Parameters
    ----------
    key_path : Path
        Location of the on-disk key file.
    env_value : Union[str, None]
        Key provided via environment variable, if any.
    persist : bool
        Whether to write a newly generated key to disk, by default True.

    Returns
    -------
    bytes
        The Fernet key as bytes.
    """
    if env_value:
        return env_value.encode()

    if key_path.exists():
        return key_path.read_bytes()

    key = Fernet.generate_key()
    if persist:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_bytes(key)
        try:
            os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            logger.warning("Could not restrict permissions on %s", key_path)
    return key


class CredentialEncryptor:
    """Encrypts and decrypts credential keys with Fernet."""

    def __init__(self, key: bytes) -> None:
        """Initialize the encryptor.

        Parameters
        ----------
        key : bytes
            A valid Fernet key.
        """
        self._fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext secret.

        Parameters
        ----------
        plaintext : str
            The secret to encrypt.

        Returns
        -------
        str
            The encrypted token.
        """
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, token: str) -> str:
        """Decrypt a token produced by :meth:`encrypt`.

        Parameters
        ----------
        token : str
            The encrypted token.

        Returns
        -------
        str
            The decrypted plaintext.

        Raises
        ------
        cryptography.fernet.InvalidToken
            If the token is invalid or was encrypted with a different key.
        """
        return self._fernet.decrypt(token.encode()).decode()
