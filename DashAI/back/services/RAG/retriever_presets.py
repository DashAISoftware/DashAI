"""Retriever preset recipes resolved from the component registry."""

from typing import Any, Dict, List, Optional

from DashAI.back.core.schema_fields.defaults import resolve_component_defaults
from DashAI.back.core.utils import MultilingualString

_SEMANTIC_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_SEMANTIC_MODEL_SHORT = "paraphrase-multilingual-MiniLM-L12-v2"

#: Preset a session gets when it does not choose one. Keyword retrieval is the
#: only paradigm that needs no model download, so it is the one default that can
#: never make session creation fail with a "must be downloaded first" conflict.
DEFAULT_PRESET_KEY = "keyword"

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
    params = resolve_component_defaults("BM25Retriever", registry)
    params["top_k"] = top_k
    return {
        "key": "keyword",
        "display_name": _KEYWORD_NAME,
        "description": "BM25",
        "component": "BM25Retriever",
        "params": params,
    }


def _semantic_preset(top_k: int, registry) -> Dict[str, Any]:
    params = resolve_component_defaults("DenseEmbeddingRetriever", registry)
    params["embedding_model"]["params"]["model_name"] = _SEMANTIC_MODEL_NAME
    params["top_k"] = top_k
    return {
        "key": "semantic",
        "display_name": _SEMANTIC_NAME,
        "description": _SEMANTIC_MODEL_SHORT,
        "component": "DenseEmbeddingRetriever",
        "params": params,
    }


def _hybrid_preset(top_k: int, registry) -> Dict[str, Any]:
    keyword_k = (top_k + 1) // 2  # ceil(top_k / 2)
    semantic_k = top_k // 2  # floor(top_k / 2)

    keyword_params = resolve_component_defaults("BM25Retriever", registry)
    keyword_params["top_k"] = keyword_k

    semantic_params = resolve_component_defaults("DenseEmbeddingRetriever", registry)
    semantic_params["embedding_model"]["params"]["model_name"] = _SEMANTIC_MODEL_NAME
    semantic_params["top_k"] = semantic_k

    return {
        "key": "hybrid",
        "display_name": _HYBRID_NAME,
        "description": f"BM25 + {_SEMANTIC_MODEL_SHORT}",
        "component": "ParallelRetriever",
        "params": {
            "merge_strategy": "round_robin",
            "children": [
                {"component": "BM25Retriever", "params": keyword_params},
                {"component": "DenseEmbeddingRetriever", "params": semantic_params},
            ],
        },
    }


def get_retriever_presets(top_k: int, registry) -> List[Dict[str, Any]]:
    """Return the three retriever preset recipes with ``top_k`` applied."""
    return [
        _keyword_preset(top_k, registry),
        _semantic_preset(top_k, registry),
        _hybrid_preset(top_k, registry),
    ]


def get_default_retriever(registry, top_k: int = 10) -> Dict[str, Any]:
    """Return the ``{component, params}`` ref for the default preset."""
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
    for preset in get_retriever_presets(10, registry):
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
    children = params.get("children")
    if isinstance(children, list) and children:
        return sum(
            effective_top_k(child.get("component", ""), child.get("params", {}) or {})
            for child in children
            if isinstance(child, dict)
        )
    return 0
