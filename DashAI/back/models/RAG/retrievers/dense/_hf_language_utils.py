from typing import Dict, List, Tuple

LANGUAGE_LABELS: Dict[str, str] = {
    "af": "Afr",
    "ar": "Ara",
    "bg": "Bul",
    "bn": "Ben",
    "ca": "Cat",
    "cs": "Cze",
    "da": "Dan",
    "de": "Deu",
    "el": "Gre",
    "en": "Eng",
    "es": "Esp",
    "et": "Est",
    "fa": "Per",
    "fi": "Fin",
    "fr": "Fra",
    "he": "Heb",
    "hi": "Hin",
    "hr": "Cro",
    "hu": "Hun",
    "id": "Ind",
    "it": "Ita",
    "ja": "Jpn",
    "ko": "Kor",
    "lt": "Lit",
    "lv": "Lav",
    "mk": "Mac",
    "ms": "May",
    "multi": "Multi",
    "nl": "Dut",
    "no": "Nor",
    "pl": "Pol",
    "pt": "Por",
    "ro": "Rom",
    "ru": "Rus",
    "sk": "Slo",
    "sl": "Svn",
    "sr": "Srp",
    "sv": "Swe",
    "th": "Tha",
    "tr": "Tur",
    "uk": "Ukr",
    "ur": "Urd",
    "vi": "Vie",
    "zh": "Chi",
}

MAX_DISPLAY_LANGUAGES: int = 3


def compute_language_summary(languages: List[str]) -> Tuple[str, int]:
    """Build a human-readable summary and total count for a list of languages.

    Shows up to ``MAX_DISPLAY_LANGUAGES`` (3) labels; overflow is
    indicated with a ``+N`` suffix.

    Args:
        languages: List of ISO 639-1 language codes.

    Returns:
        A ``(summary_string, total_count)`` tuple.
    """
    if not languages:
        return "", 0
    labels = [LANGUAGE_LABELS.get(lang, lang.title()) for lang in languages]
    if len(labels) <= MAX_DISPLAY_LANGUAGES:
        return ", ".join(labels), len(languages)
    shown = labels[:MAX_DISPLAY_LANGUAGES]
    overflow = len(languages) - MAX_DISPLAY_LANGUAGES
    return f"{', '.join(shown)} +{overflow}", len(languages)


def build_model_language_summaries(
    models: Dict[str, dict],
) -> Dict[str, Dict[str, object]]:
    """Build per-model language summaries.

    Args:
        models: Mapping from model name to model info dicts (each
            containing a ``"languages"`` key).

    Returns:
        A dict mapping model name to ``{"summary": str, "count": int,
        "labels": list[str]}``.
    """
    result: Dict[str, Dict[str, object]] = {}
    for model_name, info in models.items():
        summary, count = compute_language_summary(info.get("languages", []))
        result[model_name] = {
            "summary": summary,
            "count": count,
            "labels": [
                LANGUAGE_LABELS.get(lang, lang.title())
                for lang in info.get("languages", [])
            ],
        }
    return result


def build_family_language_summary(
    models: Dict[str, dict],
) -> Tuple[str, int]:
    """Build a language summary across all models in a family.

    Collects unique languages from all models and summarises them.

    Args:
        models: Mapping from model name to model info dicts (each
            containing a ``"languages"`` key).

    Returns:
        A ``(summary_string, total_unique_count)`` tuple.
    """
    all_languages: List[str] = []
    seen: set[str] = set()
    for info in models.values():
        for lang in info.get("languages", []):
            if lang not in seen:
                seen.add(lang)
                all_languages.append(lang)
    return compute_language_summary(all_languages)
