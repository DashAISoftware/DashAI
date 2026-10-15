"""Generic contract for the optional query transformation stage.

A transformer maps a user message and the previous conversation messages to
one or more search queries. The LLM+prompt family is only one implementation;
a pretrained transformation model can implement the same interface and
register under the same type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Final, List, Sequence

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.core.utils import MultilingualString


@dataclass(frozen=True)
class QueryTransformationResult:
    """Typed output of a query transformation.

    Attributes
    ----------
    queries : List[str]
        The transformed search queries. A single-query technique (rewriting)
        is represented as a one-element list.
    """

    queries: List[str]

    def to_list(self) -> List[str]:
        """Return a copy of the queries as a plain list.

        Returns
        -------
        List[str]
            A shallow copy of ``queries``.
        """
        return list(self.queries)


class QueryTransformationSchema(BaseSchema):
    """Empty base schema for query transformations.

    Concrete transformers declare their own ``SCHEMA`` with the parameters
    they need (a prompt, an LLM model, a history window, ...).
    """


class BaseQueryTransformation(ConfigObject):
    """Base class for every query transformation component.

    Implementations decide how many of the previous conversation messages to
    use when transforming the current message. This window is a phase
    parameter for the implementations that need it.
    """

    TYPE: Final[str] = "QueryTransformation"
    SCHEMA = QueryTransformationSchema
    COMPATIBLE_COMPONENTS: List[str] = ["RAGTask"]
    REQUIRED_EXTRA_KWARGS = []

    DESCRIPTION: str = MultilingualString(
        en=(
            "Optional pre-retrieval stage that transforms a user message into "
            "one or more search queries."
        ),
        es=(
            "Etapa opcional previa a la recuperación que transforma el mensaje "
            "del usuario en una o varias consultas de búsqueda."
        ),
        pt=(
            "Etapa opcional antes da recuperação que transforma a mensagem do "
            "usuário em uma ou mais consultas de busca."
        ),
        de=(
            "Optionale Stufe vor dem Abruf, die eine Benutzernachricht in eine "
            "oder mehrere Suchanfragen umwandelt."
        ),
        zh="在检索之前将用户消息转换为一个或多个搜索查询的可选阶段。",
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Query Transformation",
        es="Transformación de Consulta",
        pt="Transformação de Consulta",
        de="Abfrage-Transformation",
        zh="查询转换",
    )

    def transform(
        self,
        message: str,
        history: Sequence[Dict[str, str]],
    ) -> QueryTransformationResult:
        """Transform a user message into one or more search queries.

        Parameters
        ----------
        message : str
            The current user message.
        history : Sequence[Dict[str, str]]
            The conversation as earlier chat entries (``{"role", "content"}``
            dicts, oldest first, excluding the current message). The
            implementation decides how many previous messages to use.

        Returns
        -------
        QueryTransformationResult
            One or more transformed queries.

        Raises
        ------
        NotImplementedError
            Always; concrete subclasses implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")
