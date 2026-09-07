"""Kaggle credential."""

import logging
import os
import sys
from typing import Final

from DashAI.back.core.utils import MultilingualString
from DashAI.back.credentials.base_credential import BaseCredential

logger = logging.getLogger(__name__)

_AUTH_METHOD_ACCESS_TOKEN: Final = "ACCESS_TOKEN"


class KaggleCredential(BaseCredential):
    """Credential for the Kaggle API.

    The key is a single Kaggle API access token (e.g. ``"KGAT_..."``), generated
    at ``https://www.kaggle.com/settings/api``.
    """

    DISPLAY_NAME: Final = MultilingualString(
        en="Kaggle",
        es="Kaggle",
        pt="Kaggle",
        de="Kaggle",
        zh="Kaggle",
    )
    DESCRIPTION: Final = MultilingualString(
        en=(
            "Kaggle API access token (e.g. 'KGAT_...'), generated at "
            "https://www.kaggle.com/settings/api."
        ),
        es=(
            "Token de acceso de la API de Kaggle (p. ej. 'KGAT_...'), generado "
            "en https://www.kaggle.com/settings/api."
        ),
        pt=(
            "Token de acesso da API do Kaggle (ex.: 'KGAT_...'), gerado em "
            "https://www.kaggle.com/settings/api."
        ),
        de=(
            "Kaggle-API-Zugriffstoken (z. B. 'KGAT_...'), erstellt unter "
            "https://www.kaggle.com/settings/api."
        ),
        zh=(
            "Kaggle API 访问令牌（例如 'KGAT_...'），在 "
            "https://www.kaggle.com/settings/api 生成。"
        ),
    )
    ICON: str = "Key"

    def verify(self, key: str) -> bool:
        """Validate a Kaggle access token with the official ``kaggle`` library.

        The token is exported to the environment before importing ``kaggle``,
        because the package authenticates at import time.  ``authenticate()``
        introspects the token against Kaggle, so a token that authenticates with
        method ``ACCESS_TOKEN`` is valid.

        Parameters
        ----------
        key : str
            Kaggle API access token.

        Returns
        -------
        bool
            True if the token authenticates successfully.
        """
        if not key or not key.strip():
            return False

        os.environ["KAGGLE_API_TOKEN"] = key
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi

            api = KaggleApi()
            api.authenticate()
            return api.config_values.get("auth_method") == _AUTH_METHOD_ACCESS_TOKEN
        except SystemExit:
            return False
        except Exception as exc:
            logger.info("Kaggle credential verification failed: %s", exc)
            return False

    def apply(self) -> None:
        """Export the stored Kaggle token to the environment.

        The official ``kaggle`` library reads ``KAGGLE_API_TOKEN`` from the
        environment.  When the module was already imported (and therefore its
        module-level ``kaggle.api`` instance was authenticated without the
        token), re-authenticate it so later calls use the token.  No-op when
        nothing is stored.
        """
        key = self.get_key()
        if not key:
            return None

        os.environ["KAGGLE_API_TOKEN"] = key
        if "kaggle" in sys.modules:
            try:
                import kaggle

                kaggle.api.authenticate()
            except Exception:
                logger.debug("Could not re-authenticate the kaggle module")
        return None
