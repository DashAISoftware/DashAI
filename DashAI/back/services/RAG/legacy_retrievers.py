"""Translation of RAG retriever configurations saved by earlier versions.

Up to v0.10.0 a retriever named its vectorizer or its embedding model with
RAG specific components: ``BM25VectorizerModel``, ``TFIDFVectorizerModel`` and
the ``DenseEmbedding`` family, which picked a model through ``model_name``.
Those are regular converters now, so a stored ``retriever_model`` that still
names them fails validation and the session asks the user to choose a
retriever again. :func:`translate_legacy_retriever` rewrites such a
configuration into the current components wherever there is an exact
counterpart; the startup backfill saves the result only if it validates.
"""

import copy
from typing import Any, Dict, Optional

from DashAI.back.core.schema_fields.defaults import resolve_component_defaults

#: Sparse retrievers: legacy params key of their vectorizer, current vectorizer.
_SPARSE_VECTORIZERS = {
    "BM25Retriever": ("BM25Vectorizer", "BagOfWordsConverter"),
    "TFIDFRetriever": ("TFIDFVectorizer", "TFIDFConverter"),
}
#: ``TFIDFVectorizerModel`` stored an unset ``strip_accents`` or ``norm`` as this.
_LEGACY_NONE = "None"
_CPU_LABEL = "CPU"


def translate_legacy_retriever(ref: Any, registry) -> Any:
    """Rewrite a stored retriever reference into the current components.

    Children of composite retrievers are translated too. Parts without an
    exact counterpart, such as an embedding model no current converter
    serves, are left as they were, so the result can still fail validation.

    Parameters
    ----------
    ref : Any
        A ``{component, params}`` retriever reference.
    registry : ComponentRegistry
        Registry resolving the current components and their defaults.

    Returns
    -------
    Any
        A new reference; ``ref`` itself is never modified.
    """
    if not isinstance(ref, dict) or not isinstance(ref.get("params"), dict):
        return ref
    name = ref.get("component")
    params = copy.deepcopy(ref["params"])
    if isinstance(params.get("children"), list):
        params["children"] = [
            translate_legacy_retriever(child, registry) for child in params["children"]
        ]
    if name in _SPARSE_VECTORIZERS:
        legacy_key, current = _SPARSE_VECTORIZERS[name]
        legacy = params.pop(legacy_key, None)
        if isinstance(legacy, dict) and "vectorizer" not in params:
            params["vectorizer"] = {
                "component": current,
                "params": _with_defaults(
                    current, _vectorizer_params(legacy.get("params") or {}), registry
                ),
            }
    elif name == "DenseEmbeddingRetriever":
        embedding = _embedding_converter(params.get("embedding_model"), registry)
        if embedding is not None:
            params["embedding_model"] = embedding
    return {"component": name, "params": _with_defaults(name, params, registry)}


def _vectorizer_params(legacy: Dict[str, Any]) -> Dict[str, Any]:
    """Translate the parameters of a legacy RAG vectorizer.

    The legacy ``stop_words`` was a list of the user's own words, which is
    ``custom_stop_words`` now, and ``ngram_range`` became two bounds.

    Parameters
    ----------
    legacy : dict
        Parameters of ``BM25VectorizerModel`` or ``TFIDFVectorizerModel``.

    Returns
    -------
    dict
        Parameters for ``BagOfWordsConverter`` or ``TFIDFConverter``.
    """
    params = {
        key: None if value == _LEGACY_NONE else value for key, value in legacy.items()
    }
    words = params.pop("stop_words", None)
    params["stop_words"] = None
    params["custom_stop_words"] = list(words) if words else None
    ngram_range = params.pop("ngram_range", None)
    if isinstance(ngram_range, (list, tuple)) and len(ngram_range) == 2:
        params["lower_bound_ngrams"], params["upper_bound_ngrams"] = ngram_range
    return params


def _embedding_converter(ref: Any, registry) -> Optional[Dict[str, Any]]:
    """Return the converter reference serving a legacy embedding model.

    Parameters
    ----------
    ref : Any
        The legacy ``embedding_model`` reference, which names its model in
        ``params["model_name"]``.
    registry : ComponentRegistry
        Registry resolving the current components.

    Returns
    -------
    dict or None
        A ``{component, params}`` reference to the text embedding converter
        of that model, or None when no converter serves it.
    """
    if not isinstance(ref, dict) or not isinstance(ref.get("params"), dict):
        return None
    params = dict(ref["params"])
    current = _embedding_converters(registry).get(params.pop("model_name", None))
    if current is None:
        return None
    label = _device_label(current, params.pop("device", None), registry)
    if label is not None:
        params["device"] = label
    return {"component": current, "params": _with_defaults(current, params, registry)}


def _embedding_converters(registry) -> Dict[str, str]:
    """Map each served Hugging Face model to its text embedding converter.

    Parameters
    ----------
    registry : ComponentRegistry
        Registry holding the converters.

    Returns
    -------
    dict of str to str
        Model repo id to converter name.
    """
    from DashAI.back.converters.hugging_face.text_embedding.base import (
        TextEmbeddingConverter,
    )

    converters = {}
    for name, entry in registry.registry.get("Converter", {}).items():
        component_class = entry["class"]
        model_name = getattr(component_class, "MODEL_NAME", None)
        if model_name and issubclass(component_class, TextEmbeddingConverter):
            converters[model_name] = name
    return converters


def _device_label(component: str, legacy: Any, registry) -> Optional[str]:
    """Translate a legacy ``cpu`` / ``cuda`` device into a current label.

    Parameters
    ----------
    component : str
        The converter whose ``device`` options are used.
    legacy : Any
        The legacy device value.
    registry : ComponentRegistry
        Registry holding the converter schema.

    Returns
    -------
    str or None
        ``"CPU"``, the first GPU label, or None to keep the default device.
    """
    schema = registry[component]["schema"] or {}
    labels = schema.get("properties", {}).get("device", {}).get("enum") or []
    if legacy == "cpu" and _CPU_LABEL in labels:
        return _CPU_LABEL
    if legacy == "cuda":
        gpus = [label for label in labels if label != _CPU_LABEL]
        return gpus[0] if gpus else _CPU_LABEL
    return None


def _with_defaults(name: Any, params: Dict[str, Any], registry) -> Dict[str, Any]:
    """Complete a component's params with its defaults and drop unknown keys.

    Parameters
    ----------
    name : Any
        Component name.
    params : dict
        Parameters to keep.
    registry : ComponentRegistry
        Registry resolving the component schema.

    Returns
    -------
    dict
        ``params`` over the schema defaults, restricted to the schema fields;
        ``params`` unchanged for an unregistered component.
    """
    if not isinstance(name, str) or name not in registry:
        return params
    schema = registry[name]["schema"] or {}
    fields = set(schema.get("properties", {}))
    if not fields:
        return params
    defaults = resolve_component_defaults(name, registry)
    return {
        **defaults,
        **{key: value for key, value in params.items() if key in fields},
    }
