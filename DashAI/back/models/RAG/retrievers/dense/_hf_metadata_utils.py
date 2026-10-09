from typing import Dict

from DashAI.back.models.RAG.retrievers.dense._hf_language_utils import (
    build_family_language_summary,
    build_model_language_summaries,
)


def build_retriever_metadata(
    models: Dict[str, dict],
    family_name: str,
    model_count: int,
) -> Dict[str, object]:
    """Build a metadata dictionary describing a retriever family.

    Args:
        models: Mapping from model name to model info dicts (each
            containing a ``"languages"`` key).
        family_name: Human-readable name for the model family.
        model_count: Total number of models in the family.

    Returns:
        A dictionary with keys ``family``, ``language_summary``,
        ``language_count``, ``model_count``, and ``model_languages``.
    """
    family_summary, family_count = build_family_language_summary(models)
    model_languages = build_model_language_summaries(models)
    return {
        "family": family_name,
        "language_summary": family_summary,
        "language_count": family_count,
        "model_count": model_count,
        "model_languages": model_languages,
    }
