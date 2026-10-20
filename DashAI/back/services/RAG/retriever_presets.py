"""Retriever preset recipes resolved from the component registry."""

from typing import Any, Dict, List, Optional

from DashAI.back.core.schema_fields.defaults import resolve_component_defaults
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.RAG_defaults import (
    DEFAULT_SEMANTIC_MODEL_NAME,
    DEFAULT_TOP_K,
    default_hybrid_retriever,
    default_keyword_retriever,
    default_semantic_retriever,
)

_SEMANTIC_MODEL_SHORT = DEFAULT_SEMANTIC_MODEL_NAME.rsplit("/", 1)[-1]

KEYWORD_PRESET_KEY = "keyword"
SEMANTIC_PRESET_KEY = "semantic"
HYBRID_PRESET_KEY = "hybrid"

#: Preset a session gets when it does not choose one. Keyword retrieval is the
#: only paradigm that needs no model download, so it is the one default that can
#: never make session creation fail with a "must be downloaded first" conflict.
DEFAULT_PRESET_KEY = KEYWORD_PRESET_KEY

_KEYWORD_NAME = MultilingualString(
    en="Keyword",
    es="Palabras clave",
    pt="Palavra-chave",
    de="Stichwort",
    zh="关键词",
)
_SEMANTIC_NAME = MultilingualString(
    en="Semantic",
    es="Semántico",
    pt="Semântico",
    de="Semantisch",
    zh="语义",
)
_HYBRID_NAME = MultilingualString(
    en="Hybrid",
    es="Híbrido",
    pt="Híbrido",
    de="Hybrid",
    zh="混合",
)


def _keyword_preset(top_k: int, registry) -> Dict[str, Any]:
    """Build the keyword preset from the centralized BM25 default.

    Parameters
    ----------
    top_k : int
        Number of chunks the recipe selects.
    registry : ComponentRegistry
        Registry used to resolve any parameter the centralized recipe omits.

    Returns
    -------
    Dict[str, Any]
        The keyword preset recipe with its display metadata.
    """
    ref = default_keyword_retriever(top_k)
    params = {**resolve_component_defaults(ref["component"], registry), **ref["params"]}
    return {
        "key": KEYWORD_PRESET_KEY,
        "display_name": _KEYWORD_NAME,
        "description": "BM25",
        "component": ref["component"],
        "params": params,
    }


def _semantic_preset(top_k: int, registry) -> Dict[str, Any]:
    """Build the semantic preset from the centralized dense default.

    Parameters
    ----------
    top_k : int
        Number of chunks the recipe selects.
    registry : ComponentRegistry
        Registry used to resolve any parameter the centralized recipe omits.

    Returns
    -------
    Dict[str, Any]
        The semantic preset recipe with its display metadata.
    """
    ref = default_semantic_retriever(top_k)
    params = {**resolve_component_defaults(ref["component"], registry), **ref["params"]}
    return {
        "key": SEMANTIC_PRESET_KEY,
        "display_name": _SEMANTIC_NAME,
        "description": _SEMANTIC_MODEL_SHORT,
        "component": ref["component"],
        "params": params,
    }


def _hybrid_preset(top_k: int, registry) -> Dict[str, Any]:
    """Build the hybrid preset from the centralized parallel default.

    Parameters
    ----------
    top_k : int
        Total number of chunks the recipe returns. The hybrid factory splits it
        between the keyword and semantic children.
    registry : ComponentRegistry
        Registry used to resolve any parameter the centralized recipe omits.

    Returns
    -------
    Dict[str, Any]
        The hybrid preset recipe with its display metadata.
    """
    ref = default_hybrid_retriever(top_k)
    params = {**resolve_component_defaults(ref["component"], registry), **ref["params"]}
    return {
        "key": HYBRID_PRESET_KEY,
        "display_name": _HYBRID_NAME,
        "description": f"BM25 + {_SEMANTIC_MODEL_SHORT}",
        "component": ref["component"],
        "params": params,
    }


def get_retriever_presets(top_k: int, registry) -> List[Dict[str, Any]]:
    """Return the three retriever preset recipes with ``top_k`` applied.

    Parameters
    ----------
    top_k : int
        Number of chunks each recipe selects (or the total for the hybrid).
    registry : ComponentRegistry
        Registry used to resolve each component's schema defaults.

    Returns
    -------
    List[Dict[str, Any]]
        Keyword, semantic and hybrid recipes, in that order.
    """
    return [
        _keyword_preset(top_k, registry),
        _semantic_preset(top_k, registry),
        _hybrid_preset(top_k, registry),
    ]


def get_default_retriever(registry, top_k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
    """Return the ``{component, params}`` ref for the default preset.

    Parameters
    ----------
    registry : ComponentRegistry
        Registry used to resolve each component's schema defaults.
    top_k : int, optional
        Number of chunks the default recipe selects. Defaults to
        :data:`DashAI.back.models.RAG.RAG_defaults.DEFAULT_TOP_K`.

    Returns
    -------
    Dict[str, Any]
        The default retriever configuration.
    """
    recipe = next(
        preset
        for preset in get_retriever_presets(top_k, registry)
        if preset["key"] == DEFAULT_PRESET_KEY
    )
    return {"component": recipe["component"], "params": recipe["params"]}


def _strip_top_k(value: Any) -> Any:
    """Drop every ``top_k`` entry from a nested params structure.

    A preset keeps its shape when the user only moves the Top-K slider, so
    matching a stored config against a recipe has to ignore that one key at
    every level (composite presets split it across their children).
    """
    if isinstance(value, dict):
        return {k: _strip_top_k(v) for k, v in value.items() if k != "top_k"}
    if isinstance(value, list):
        return [_strip_top_k(item) for item in value]
    return value


def match_preset_key(component: str, params: Dict[str, Any], registry) -> Optional[str]:
    """Return the preset key a retriever config corresponds to, if any.

    Parameters
    ----------
    component : str
        Retriever class name.
    params : dict
        Retriever parameters.
    registry : ComponentRegistry
        Registry used to resolve each candidate recipe.

    Returns
    -------
    str | None
        The matching preset key, or ``None`` for a custom configuration.
    """
    stripped = _strip_top_k(params)
    for preset in get_retriever_presets(DEFAULT_TOP_K, registry):
        if preset["component"] != component:
            continue
        if _strip_top_k(preset["params"]) == stripped:
            return preset["key"]
    return None


def effective_top_k(component: str, params: Dict[str, Any]) -> int:
    """Return how many chunks a retriever config actually returns.

    A composite retriever's own ``top_k`` (when it has one) bounds the result;
    otherwise the children's values add up.
    """
    if "top_k" in params and isinstance(params["top_k"], int):
        return params["top_k"]
    if "max_chunks" in params and isinstance(params["max_chunks"], int):
        return params["max_chunks"]
    children = params.get("children")
    if isinstance(children, list) and children:
        return sum(
            effective_top_k(child.get("component", ""), child.get("params", {}) or {})
            for child in children
            if isinstance(child, dict)
        )
    return 0
