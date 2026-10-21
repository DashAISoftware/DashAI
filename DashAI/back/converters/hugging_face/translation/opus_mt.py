"""Opus MT translators, one converter per Helsinki-NLP checkpoint."""

from typing import Dict, Optional, Tuple

from DashAI.back.converters.hugging_face.translation.base import (
    TranslationConverter,
    TranslationSchema,
    language_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin

FAMILY = "Opus MT"

LanguageNames = Tuple[str, str, str, str, str]

NAMES: Dict[str, LanguageNames] = {
    "en": ("English", "inglés", "inglês", "Englisch", "英语"),
    "es": ("Spanish", "español", "espanhol", "Spanisch", "西班牙语"),
    "de": ("German", "alemán", "alemão", "Deutsch", "德语"),
    "fr": ("French", "francés", "francês", "Französisch", "法语"),
    "zh": ("Chinese", "chino", "chinês", "Chinesisch", "中文"),
    "pt": ("Portuguese", "portugués", "português", "Portugiesisch", "葡萄牙语"),
    "it": ("Italian", "italiano", "italiano", "Italienisch", "意大利语"),
    "ro": ("Romanian", "rumano", "romeno", "Rumänisch", "罗马尼亚语"),
    "ca": ("Catalan", "catalán", "catalão", "Katalanisch", "加泰罗尼亚语"),
    "gl": ("Galician", "gallego", "galego", "Galicisch", "加利西亚语"),
    "cmn_Hans": (
        "Chinese (Simplified)",
        "chino (simplificado)",
        "chinês (simplificado)",
        "Chinesisch (Vereinfacht)",
        "中文 (简体)",
    ),
    "cmn_Hant": (
        "Chinese (Traditional)",
        "chino (tradicional)",
        "chinês (tradicional)",
        "Chinesisch (Traditionell)",
        "中文 (繁体)",
    ),
    "yue_Hant": ("Cantonese", "cantonés", "cantonês", "Kantonesisch", "粤语"),
    "roa": (
        "Romance languages",
        "lenguas romances",
        "línguas românicas",
        "romanische Sprachen",
        "罗曼语族",
    ),
}

ROMANCE_TARGETS: Dict[str, str] = {
    "por": "pt",
    "spa": "es",
    "fra": "fr",
    "ita": "it",
    "ron": "ro",
    "cat": "ca",
    "glg": "gl",
}
CHINESE_TARGETS: Dict[str, str] = {
    "cmn_Hans": "cmn_Hans",
    "cmn_Hant": "cmn_Hant",
    "yue_Hant": "yue_Hant",
}


def label(names: LanguageNames) -> MultilingualString:
    """Turn the names of a language into a dropdown label.

    Parameters
    ----------
    names : LanguageNames
        Its names in English, Spanish, Portuguese, German and Chinese.

    Returns
    -------
    MultilingualString
        The name in every supported language.
    """
    en, es, pt, de, zh = names
    return MultilingualString(en=en, es=es, pt=pt, de=de, zh=zh)


def pair_name(
    source: LanguageNames, target: LanguageNames, family: str
) -> MultilingualString:
    """Name a translator for one language pair.

    Parameters
    ----------
    source : LanguageNames
        Names of the language it reads.
    target : LanguageNames
        Names of the language it writes.
    family : str
        The model family, such as ``"Opus MT"``.

    Returns
    -------
    MultilingualString
        Such as ``"Translator English to Spanish (Opus MT)"``.
    """
    return MultilingualString(
        en=f"Translator {source[0]} to {target[0]} ({family})",
        es=f"Traductor de {source[1]} a {target[1]} ({family})",
        pt=f"Tradutor de {source[2]} para {target[2]} ({family})",
        de=f"Übersetzer {source[3]} nach {target[3]} ({family})",
        zh=f"{source[4]}到{target[4]}翻译器（{family}）",
    )


def pair_description(
    source: LanguageNames, target: LanguageNames, repo: str
) -> MultilingualString:
    """Describe a small translator for one language pair.

    Parameters
    ----------
    source : LanguageNames
        Names of the language it reads.
    target : LanguageNames
        Names of the language it writes.
    repo : str
        The Hugging Face repo id of the model.

    Returns
    -------
    MultilingualString
        One sentence naming the languages and the model.
    """
    return MultilingualString(
        en=(
            f"Translates text from {source[0]} to {target[0]} with {repo}, a "
            "small model that runs well on a CPU."
        ),
        es=(
            f"Traduce texto de {source[1]} a {target[1]} con {repo}, un modelo "
            "pequeño que funciona bien en CPU."
        ),
        pt=(
            f"Traduz texto de {source[2]} para {target[2]} com {repo}, um modelo "
            "pequeno que roda bem em CPU."
        ),
        de=(
            f"Übersetzt Text von {source[3]} nach {target[3]} mit {repo}, einem "
            "kleinen Modell, das gut auf der CPU läuft."
        ),
        zh=(
            f"使用 {repo} 将{source[4]}文本翻译为{target[4]}，"
            "这个小模型在 CPU 上也能良好运行。"
        ),
    )


ROMANCE_LABELS = {token: label(NAMES[code]) for token, code in ROMANCE_TARGETS.items()}
CHINESE_LABELS = {token: label(NAMES[code]) for token, code in CHINESE_TARGETS.items()}


class OpusMtTranslator(TranslationConverter):
    """An Opus MT model that translates one language into another."""


class OpusMtMultiTargetTranslator(OpusMtTranslator):
    """An Opus MT model that writes the language named by a leading token.

    These checkpoints read a ``>>id<<`` token in front of every input to
    choose the target language among ``TARGETS``.
    """

    TARGETS: Dict[str, str] = {}
    DEFAULT_TARGET = ""

    def __init__(self, target_language: Optional[str] = None, **kwargs) -> None:
        """Store the target language and the shared options.

        Parameters
        ----------
        target_language : str, optional
            A key of ``TARGETS``. Default ``DEFAULT_TARGET``.
        **kwargs
            The options of :class:`TranslationConverter`.

        Raises
        ------
        ValueError
            If the target language is not one the model writes.
        """
        super().__init__(**kwargs)
        target_language = target_language or self.DEFAULT_TARGET
        if target_language not in self.TARGETS:
            raise ValueError(
                f"{type(self).__name__} cannot translate into "
                f"'{target_language}'. Valid options: {sorted(self.TARGETS)}."
            )
        self.target_language = target_language

    def source_prefix(self) -> str:
        """Return the token that selects the target language.

        Returns
        -------
        str
            Such as ``">>por<< "``.
        """
        return f">>{self.target_language}<< "


class OpusMtEnEsTranslator(OpusMtTranslator):
    """English to Spanish (Helsinki-NLP/opus-mt-en-es)."""

    MODEL_NAME = "Helsinki-NLP/opus-mt-en-es"
    DOWNLOAD_SIZE_BYTES = 315310815
    DISPLAY_NAME = pair_name(NAMES["en"], NAMES["es"], FAMILY)
    DESCRIPTION = pair_description(NAMES["en"], NAMES["es"], MODEL_NAME)


class OpusMtEsEnTranslator(OpusMtTranslator):
    """Spanish to English (Helsinki-NLP/opus-mt-es-en)."""

    MODEL_NAME = "Helsinki-NLP/opus-mt-es-en"
    DOWNLOAD_SIZE_BYTES = 315310760
    DISPLAY_NAME = pair_name(NAMES["es"], NAMES["en"], FAMILY)
    DESCRIPTION = pair_description(NAMES["es"], NAMES["en"], MODEL_NAME)


class OpusMtEnDeTranslator(OpusMtTranslator):
    """English to German (Helsinki-NLP/opus-mt-en-de)."""

    MODEL_NAME = "Helsinki-NLP/opus-mt-en-de"
    DOWNLOAD_SIZE_BYTES = 300772148
    DISPLAY_NAME = pair_name(NAMES["en"], NAMES["de"], FAMILY)
    DESCRIPTION = pair_description(NAMES["en"], NAMES["de"], MODEL_NAME)


class OpusMtDeEnTranslator(OpusMtTranslator):
    """German to English (Helsinki-NLP/opus-mt-de-en)."""

    MODEL_NAME = "Helsinki-NLP/opus-mt-de-en"
    DOWNLOAD_SIZE_BYTES = 300770208
    DISPLAY_NAME = pair_name(NAMES["de"], NAMES["en"], FAMILY)
    DESCRIPTION = pair_description(NAMES["de"], NAMES["en"], MODEL_NAME)


class OpusMtEnFrTranslator(OpusMtTranslator):
    """English to French (Helsinki-NLP/opus-mt-en-fr)."""

    MODEL_NAME = "Helsinki-NLP/opus-mt-en-fr"
    DOWNLOAD_SIZE_BYTES = 303750994
    DISPLAY_NAME = pair_name(NAMES["en"], NAMES["fr"], FAMILY)
    DESCRIPTION = pair_description(NAMES["en"], NAMES["fr"], MODEL_NAME)


class OpusMtFrEnTranslator(OpusMtTranslator):
    """French to English (Helsinki-NLP/opus-mt-fr-en)."""

    MODEL_NAME = "Helsinki-NLP/opus-mt-fr-en"
    HF_IGNORE_PATTERNS = [*HFDownloadableMixin.HF_IGNORE_PATTERNS, "*.bin"]
    DOWNLOAD_SIZE_BYTES = 303727012
    DISPLAY_NAME = pair_name(NAMES["fr"], NAMES["en"], FAMILY)
    DESCRIPTION = pair_description(NAMES["fr"], NAMES["en"], MODEL_NAME)


class OpusMtZhEnTranslator(OpusMtTranslator):
    """Chinese to English (Helsinki-NLP/opus-mt-zh-en)."""

    MODEL_NAME = "Helsinki-NLP/opus-mt-zh-en"
    DOWNLOAD_SIZE_BYTES = 315322845
    DISPLAY_NAME = pair_name(NAMES["zh"], NAMES["en"], FAMILY)
    DESCRIPTION = pair_description(NAMES["zh"], NAMES["en"], MODEL_NAME)


class OpusMtRoaEnTranslator(OpusMtTranslator):
    """Romance languages to English (Helsinki-NLP/opus-mt-roa-en)."""

    MODEL_NAME = "Helsinki-NLP/opus-mt-roa-en"
    DOWNLOAD_SIZE_BYTES = 315135823
    DISPLAY_NAME = pair_name(NAMES["roa"], NAMES["en"], FAMILY)
    DESCRIPTION = pair_description(NAMES["roa"], NAMES["en"], MODEL_NAME)


class OpusMtEnRoaTargetSchema(BaseSchema):
    """The target language of the English to Romance languages translator."""

    target_language: language_field(ROMANCE_LABELS, "por", target=True)  # type: ignore


class OpusMtEnRoaSchema(TranslationSchema, OpusMtEnRoaTargetSchema):
    """Options of the English to Romance languages translator."""


class OpusMtEnRoaTranslator(OpusMtMultiTargetTranslator):
    """English to a Romance language (Helsinki-NLP/opus-mt-en-roa)."""

    SCHEMA = OpusMtEnRoaSchema
    TARGETS = ROMANCE_TARGETS
    DEFAULT_TARGET = "por"
    MODEL_NAME = "Helsinki-NLP/opus-mt-en-roa"
    DOWNLOAD_SIZE_BYTES = 297844640
    DISPLAY_NAME = pair_name(NAMES["en"], NAMES["roa"], FAMILY)
    DESCRIPTION = pair_description(NAMES["en"], NAMES["roa"], MODEL_NAME)


class OpusMtEnZhTargetSchema(BaseSchema):
    """The target language of the English to Chinese translator."""

    target_language: language_field(CHINESE_LABELS, "cmn_Hans", target=True)  # type: ignore


class OpusMtEnZhSchema(TranslationSchema, OpusMtEnZhTargetSchema):
    """Options of the English to Chinese translator."""


class OpusMtEnZhTranslator(OpusMtMultiTargetTranslator):
    """English to Chinese (Helsinki-NLP/opus-mt-en-zh)."""

    SCHEMA = OpusMtEnZhSchema
    TARGETS = CHINESE_TARGETS
    DEFAULT_TARGET = "cmn_Hans"
    MODEL_NAME = "Helsinki-NLP/opus-mt-en-zh"
    DOWNLOAD_SIZE_BYTES = 315322114
    DISPLAY_NAME = pair_name(NAMES["en"], NAMES["zh"], FAMILY)
    DESCRIPTION = pair_description(NAMES["en"], NAMES["zh"], MODEL_NAME)
