"""Persistence boundary for encrypted credentials."""

import logging
from datetime import datetime
from typing import Dict, Union

from DashAI.back.credentials.encryptor import CredentialEncryptor
from DashAI.back.dependencies.database.models import Credential

logger = logging.getLogger(__name__)


class CredentialStore:
    """Reads and writes encrypted credentials in the database.

    This is the only component that touches the credential table and the
    encryptor.
    """

    def __init__(self, session_factory, encryptor: CredentialEncryptor) -> None:
        """Initialize the store.

        Parameters
        ----------
        session_factory
            SQLAlchemy session factory (callable returning a session).
        encryptor : CredentialEncryptor
            Encryptor used to protect keys at rest.
        """
        self._session_factory = session_factory
        self._encryptor = encryptor

    def save(self, name: str, key: str) -> None:
        """Encrypt and persist a credential key, marking it verified.

        Parameters
        ----------
        name : str
            Credential component name.
        key : str
            Plaintext key to store.
        """
        encrypted = self._encryptor.encrypt(key)
        with self._session_factory() as db:
            row = db.query(Credential).filter_by(name=name).first()
            if row is None:
                row = Credential(name=name, encrypted_key=encrypted, verified=True)
                db.add(row)
            else:
                row.encrypted_key = encrypted
                row.verified = True
                row.last_modified = datetime.now()
            db.commit()

    def load(self, name: str) -> Union[str, None]:
        """Return the decrypted key for a credential, or None.

        Parameters
        ----------
        name : str
            Credential component name.

        Returns
        -------
        Union[str, None]
            Decrypted key, or None if not stored.
        """
        with self._session_factory() as db:
            row = db.query(Credential).filter_by(name=name).first()
            if row is None:
                return None
            return self._encryptor.decrypt(row.encrypted_key)

    def is_verified(self, name: str) -> bool:
        """Return whether a credential is stored and verified.

        Parameters
        ----------
        name : str
            Credential component name.

        Returns
        -------
        bool
            True if a verified key exists.
        """
        with self._session_factory() as db:
            row = db.query(Credential).filter_by(name=name).first()
            return bool(row and row.verified)

    def delete(self, name: str) -> None:
        """Remove a stored credential.

        Parameters
        ----------
        name : str
            Credential component name.
        """
        with self._session_factory() as db:
            row = db.query(Credential).filter_by(name=name).first()
            if row is not None:
                db.delete(row)
                db.commit()

    def all_statuses(self) -> Dict[str, bool]:
        """Return the verified status of every stored credential.

        Returns
        -------
        Dict[str, bool]
            Mapping of credential name to verified status.
        """
        with self._session_factory() as db:
            rows = db.query(Credential).all()
            return {row.name: bool(row.verified) for row in rows}
