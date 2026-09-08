"""Kaggle credential."""

import logging
import os
from typing import Final

from DashAI.back.core.utils import MultilingualString
from DashAI.back.credentials.base_credential import BaseCredential

logger = logging.getLogger(__name__)


class KaggleCredential(BaseCredential):
    """Credential for the Kaggle API.

    The key is expected in the form ``"username:api_key"``.
    """

    DISPLAY_NAME: Final = MultilingualString(
        en="Kaggle",
        es="Kaggle",
        pt="Kaggle",
        de="Kaggle",
        zh="Kaggle",
    )
    DESCRIPTION: Final = MultilingualString(
        en="Kaggle API credential in the form 'username:key'.",
        es="Credencial de la API de Kaggle en el formato 'usuario:clave'.",
        pt="Credencial da API do Kaggle no formato 'usuario:chave'.",
        de="Zugangsdaten für die Kaggle API im Format 'benutzername:schluessel'.",
        zh="Kaggle API 凭证，格式为 'username:key'。",
    )
    ICON: str = "Key"

    @staticmethod
    def _split_key(key: str):
        """Split a ``"username:api_key"`` credential into its parts.

        Parameters
        ----------
        key : str
            Kaggle credential in the form ``"username:api_key"``.

        Returns
        -------
        tuple[str, str] or None
            ``(username, api_key)`` if well formed, otherwise None.
        """
        username, separator, api_key = key.partition(":")
        if not separator or not username or not api_key:
            return None
        return username, api_key

    def verify(self, key: str) -> bool:
        """Validate a Kaggle credential with the official ``kaggle`` library.

        The credentials are exported to the environment before importing
        ``kaggle``, because the package authenticates at import time and
        terminates the process when no credentials are available.

        Parameters
        ----------
        key : str
            Kaggle credential in the form ``"username:api_key"``.

        Returns
        -------
        bool
            True if the credential authenticates successfully.
        """
        parts = self._split_key(key)
        if parts is None:
            return False
        username, api_key = parts

        os.environ["KAGGLE_USERNAME"] = username
        os.environ["KAGGLE_KEY"] = api_key
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi

            api = KaggleApi()
            api.authenticate()
            # Perform an authenticated call to confirm the key is valid.
            api.competitions_list()
            return True
        except SystemExit:
            return False
        except Exception as exc:
            logger.info("Kaggle credential verification failed: %s", exc)
            return False

    def apply(self) -> None:
        """Export the stored Kaggle credentials to the environment.

        The official ``kaggle`` library reads ``KAGGLE_USERNAME`` and
        ``KAGGLE_KEY`` from the environment, so exporting them makes any later
        use of the library authenticated. No-op when nothing is stored.
        """
        key = self.get_key()
        if not key:
            return None
        parts = self._split_key(key)
        if parts is None:
            return None
        username, api_key = parts
        os.environ["KAGGLE_USERNAME"] = username
        os.environ["KAGGLE_KEY"] = api_key
        return None
