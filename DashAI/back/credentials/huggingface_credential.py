"""HuggingFace Hub credential."""

import logging
from typing import Final

from DashAI.back.core.utils import MultilingualString
from DashAI.back.credentials.base_credential import BaseCredential

logger = logging.getLogger(__name__)


class HuggingFaceCredential(BaseCredential):
    """Credential for the HuggingFace Hub."""

    DISPLAY_NAME: Final = MultilingualString(
        en="HuggingFace",
        es="HuggingFace",
        pt="HuggingFace",
        de="HuggingFace",
        zh="HuggingFace",
    )
    DESCRIPTION: Final = MultilingualString(
        en="Access token for the HuggingFace Hub. Required for gated models and "
        "datasets.",
        es="Token de acceso para el HuggingFace Hub. Necesario para modelos y "
        "conjuntos de datos restringidos.",
        pt="Token de acesso para o HuggingFace Hub. Necessário para modelos e "
        "conjuntos de dados restritos.",
        de="Zugriffstoken für den HuggingFace Hub. Erforderlich für "
        "eingeschränkte Modelle und Datensätze.",
        zh="用于 HuggingFace Hub 的访问令牌。访问受限模型和数据集时需要。",
    )
    ICON: str = "Key"

    def verify(self, key: str) -> bool:
        """Validate a HuggingFace token via ``whoami``.

        Parameters
        ----------
        key : str
            HuggingFace access token.

        Returns
        -------
        bool
            True if the token is valid.
        """
        from huggingface_hub import HfApi

        try:
            HfApi().whoami(token=key)
            return True
        except Exception as exc:
            logger.info("HuggingFace credential verification failed: %s", exc)
            return False

    def apply(self) -> None:
        """Log in to the HuggingFace Hub if a key is stored."""
        key = self.get_key()
        if not key:
            return None
        from huggingface_hub import login

        login(token=key)
        return None
