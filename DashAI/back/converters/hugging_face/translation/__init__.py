"""Converters that translate text, one per pretrained model."""

from DashAI.back.converters.hugging_face.translation.base import (
    TranslationConverter,
)
from DashAI.back.converters.hugging_face.translation.opus_mt import (
    OpusMtDeEnTranslator,
    OpusMtEnDeTranslator,
    OpusMtEnEsTranslator,
    OpusMtEnFrTranslator,
    OpusMtEnRoaTranslator,
    OpusMtEnZhTranslator,
    OpusMtEsEnTranslator,
    OpusMtFrEnTranslator,
    OpusMtMultiTargetTranslator,
    OpusMtRoaEnTranslator,
    OpusMtTranslator,
    OpusMtZhEnTranslator,
)

TRANSLATION_CONVERTERS = [
    OpusMtEnEsTranslator,
    OpusMtEsEnTranslator,
    OpusMtEnDeTranslator,
    OpusMtDeEnTranslator,
    OpusMtEnFrTranslator,
    OpusMtFrEnTranslator,
    OpusMtEnZhTranslator,
    OpusMtZhEnTranslator,
    OpusMtEnRoaTranslator,
    OpusMtRoaEnTranslator,
]

__all__ = [
    "TRANSLATION_CONVERTERS",
    "TranslationConverter",
    "OpusMtTranslator",
    "OpusMtMultiTargetTranslator",
    *[component.__name__ for component in TRANSLATION_CONVERTERS],
]
