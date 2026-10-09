"""Chunking preset recipes resolved from the component registry.

Mirrors :mod:`DashAI.back.services.RAG.retriever_presets`: the backend owns the
friendly name, the human summary and the concrete ``{component, params}``
recipe, so the frontend only has to render what it receives.
"""

import math
from typing import Any, Dict, List

from DashAI.back.core.schema_fields.defaults import resolve_component_defaults
from DashAI.back.core.utils import MultilingualString

#: Chunker every preset is built on. Character based so no download is needed.
DEFAULT_CHUNKER = "CharacterChunkModel"

#: Rough characters-per-token ratio used to turn a chunk size into a token
#: estimate for display. Character based chunking counts characters, so this is
#: the only place that converts between the two units.
CHARS_PER_TOKEN = 4

#: Preset key that a session gets when it does not choose one.
DEFAULT_PRESET_KEY = "paragraph"

_SIZE_SUMMARY = MultilingualString(
    en="{chars} characters ≈ {tokens} tokens",
    es="{chars} caracteres ≈ {tokens} tokens",
    pt="{chars} caracteres ≈ {tokens} tokens",
    de="{chars} Zeichen ≈ {tokens} Tokens",
    zh="{chars} 字符 ≈ {tokens} 标记",
)

_PRESETS: List[Dict[str, Any]] = [
    {
        "key": "small",
        "display_name": MultilingualString(
            en="Small chunks",
            es="Largo de varias oraciones",
            pt="Fragmentos pequenos",
            de="Kleine Chunks",
            zh="小块",
        ),
        "config": {"chunk_size": 250, "chunk_overlap": 25},
    },
    {
        "key": "paragraph",
        "display_name": MultilingualString(
            en="Paragraph length",
            es="Largo de un párrafo",
            pt="Tamanho de parágrafo",
            de="Absatzlänge",
            zh="段落长度",
        ),
        "config": {"chunk_size": 500, "chunk_overlap": 50},
    },
    {
        "key": "page",
        "display_name": MultilingualString(
            en="Page chunk",
            es="Largo de una página",
            pt="Fragmento de página",
            de="Seiten-Chunk",
            zh="页面块",
        ),
        "config": {"chunk_size": 2000, "chunk_overlap": 200},
    },
    {
        "key": "large",
        "display_name": MultilingualString(
            en="Large sections",
            es="Secciones grandes",
            pt="Seções grandes",
            de="Große Abschnitte",
            zh="大节",
        ),
        "config": {"chunk_size": 4000, "chunk_overlap": 400},
    },
]


def estimate_tokens(chars: int) -> int:
    """Return the token estimate for a character count."""
    return math.ceil(chars / CHARS_PER_TOKEN)


def _describe(chunk_size: int) -> MultilingualString:
    """Build the localized ``N characters ≈ M tokens`` summary."""
    values = {"chars": chunk_size, "tokens": estimate_tokens(chunk_size)}
    return MultilingualString(
        **{
            lang: getattr(_SIZE_SUMMARY, lang).format(**values)
            for lang in ("en", "es", "pt", "de", "zh")
        }
    )


def _build(preset: Dict[str, Any], registry) -> Dict[str, Any]:
    """Resolve one preset into a full ``{component, params}`` recipe."""
    params = resolve_component_defaults(DEFAULT_CHUNKER, registry)
    params.update(preset["config"])
    return {
        "key": preset["key"],
        "display_name": preset["display_name"],
        "description": _describe(preset["config"]["chunk_size"]),
        "component": DEFAULT_CHUNKER,
        "params": params,
    }


def get_chunking_presets(registry) -> List[Dict[str, Any]]:
    """Return every chunking preset recipe, resolved against the registry."""
    return [_build(preset, registry) for preset in _PRESETS]


def get_default_chunking(registry) -> Dict[str, Any]:
    """Return the ``{component, params}`` ref for the default preset."""
    preset = next(p for p in _PRESETS if p["key"] == DEFAULT_PRESET_KEY)
    recipe = _build(preset, registry)
    return {"component": recipe["component"], "params": recipe["params"]}


def match_preset_key(component: str, params: Dict[str, Any]) -> str | None:
    """Return the preset key a chunking config corresponds to, if any.

    Parameters
    ----------
    component : str
        Chunker class name.
    params : dict
        Chunker parameters.

    Returns
    -------
    str | None
        The matching preset key, or ``None`` for a custom configuration.
    """
    if component != DEFAULT_CHUNKER:
        return None
    for preset in _PRESETS:
        config = preset["config"]
        if all(params.get(key) == value for key, value in config.items()):
            return preset["key"]
    return None
