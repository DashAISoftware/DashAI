from dataclasses import fields
from typing import Dict

from DashAI.back.core.utils import MultilingualString


def format_story(templates: Dict[str, str], **kwargs) -> MultilingualString:
    """Format a per-language template dict into a MultilingualString.

    Explainers use this to turn the deterministic values they compute (top
    features, SHAP values, curve trends, etc.) into a narrative available in
    every supported language, without each explainer having to repeat the
    per-language formatting boilerplate.

    Parameters
    ----------
    templates : Dict[str, str]
        Mapping from language code (``"en"``, ``"es"``, ``"pt"``, ``"de"``,
        ``"zh"``) to a ``str.format`` template. Every language accepted by
        :class:`MultilingualString` must be present.
    **kwargs : Any
        Values interpolated into each language's template via ``str.format``.

    Returns
    -------
    MultilingualString
        The same narrative, formatted in every supported language.
    """
    formatted = {
        lang: template.format(**kwargs) for lang, template in templates.items()
    }
    return MultilingualString(**formatted)


def concat_stories(
    *parts: MultilingualString, separator: str = ""
) -> MultilingualString:
    """Concatenate several MultilingualString narratives, language by language.

    Useful when a story is built from a main sentence plus an optional extra
    remark that only applies under certain conditions (e.g. appending a
    caveat when a feature's importance is negative).

    Parameters
    ----------
    *parts : MultilingualString
        The narratives to concatenate, in order.
    separator : str
        String inserted between parts for each language. Defaults to ``""``.

    Returns
    -------
    MultilingualString
        The concatenation of all parts, for every supported language.
    """
    langs = [field.name for field in fields(MultilingualString)]
    combined = {
        lang: separator.join(
            value for part in parts if (value := getattr(part, lang)) is not None
        )
        for lang in langs
    }
    return MultilingualString(**combined)
