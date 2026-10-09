from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class MultilingualString:
    en: str
    es: Optional[str] = None
    pt: Optional[str] = None
    de: Optional[str] = None
    zh: Optional[str] = None

    def get(self, lang: str) -> str:
        # Normalize: "zh-CN" → "zh", "zh,zh;q=0.9" → "zh"
        lang = lang.split(",")[0].split(";")[0].split("-")[0].strip()
        if lang == "es" and self.es:
            return self.es
        if lang == "pt" and self.pt:
            return self.pt
        if lang == "de" and self.de:
            return self.de
        if lang == "zh" and self.zh:
            return self.zh
        return self.en


def localize(value: Any, accept_language: Optional[str] = None) -> Any:
    """Recursively replace every MultilingualString with its localized string.

    Dicts and lists are walked; every other value is returned untouched. This is
    the single place that collapses multilingual metadata for an API response,
    so payloads reaching the frontend never carry language objects.

    Parameters
    ----------
    value : Any
        The structure to localize (dict, list, MultilingualString or scalar).
    accept_language : str | None
        The request's ``Accept-Language`` header. Defaults to English.

    Returns
    -------
    Any
        The same structure with MultilingualString values replaced by strings.
    """
    lang_code = (accept_language or "en").split("-")[0].lower() or "en"

    def _walk(item: Any) -> Any:
        if isinstance(item, MultilingualString):
            return item.get(lang_code)
        if isinstance(item, dict):
            return {key: _walk(sub) for key, sub in item.items()}
        if isinstance(item, list):
            return [_walk(sub) for sub in item]
        return item

    return _walk(value)
