"""GitHub credential."""

import logging
from typing import Final

from DashAI.back.core.utils import MultilingualString
from DashAI.back.credentials.base_credential import BaseCredential

logger = logging.getLogger(__name__)


class GithubCredential(BaseCredential):
    """Credential for the GitHub API."""

    DISPLAY_NAME: Final = MultilingualString(
        en="GitHub",
        es="GitHub",
        pt="GitHub",
        de="GitHub",
        zh="GitHub",
    )
    DESCRIPTION: Final = MultilingualString(
        en="Personal access token for the GitHub API.",
        es="Token de acceso personal para la API de GitHub.",
        pt="Token de acesso pessoal para a API do GitHub.",
        de="Persönliches Zugriffstoken für die GitHub API.",
        zh="用于 GitHub API 的个人访问令牌。",
    )
    ICON: str = "Key"

    def verify(self, key: str) -> bool:
        """Validate a GitHub token via the ``/user`` endpoint.

        Parameters
        ----------
        key : str
            GitHub personal access token.

        Returns
        -------
        bool
            True if the token is valid.
        """
        import requests

        try:
            response = requests.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {key}"},
                timeout=10,
            )
            return response.status_code == 200
        except Exception as exc:
            logger.info("GitHub credential verification failed: %s", exc)
            return False
