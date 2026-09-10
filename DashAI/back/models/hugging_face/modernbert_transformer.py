"""DashAI implementation of ModernBERT for text classification.

This module exposes a DashAI wrapper for the
``answerdotai/ModernBERT-base`` sequence classification backbone. It builds on
the shared Hugging Face text classification base class to provide consistent
training, prediction, and persistence behavior across transformer models.
"""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_text_classification_transformer import (
    HuggingFaceTextClassificationTransformer,
)
from DashAI.back.models.hugging_face.distilbert_transformer import (
    DistilBertTransformerSchema,
)


class ModernBertTransformerSchema(DistilBertTransformerSchema):
    """Schema for ModernBERT text classification hyperparameters.

    Inherits all fields from :class:`DistilBertTransformerSchema`, including
    training controls, optimization settings and optional logging frequencies,
    so ModernBERT can be configured with the same interface as other DashAI
    Hugging Face classifiers.
    """


class ModernBertTransformer(HuggingFaceTextClassificationTransformer):
    """Pretrained ModernBERT transformer for text classification.

    ModernBERT is designed for strong efficiency and long context processing.
    This DashAI wrapper uses ``answerdotai/ModernBERT-base`` and increases the
    tokenizer context window through ``MAX_TOKEN_LENGTH = 8192``.

    References
    ----------
    - [1] https://huggingface.co/answerdotai/ModernBERT-base
    """

    DISPLAY_NAME: str = MultilingualString(
        en="ModernBERT Transformer",
        es="Transformer ModernBERT",
        pt="Transformer ModernBERT",
        de="ModernBERT Transformer",
        zh="ModernBERT Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en="Modern BERT model for efficient and robust text classification.",
        es="Modelo Modern BERT para clasificación de texto eficiente y robusta.",
        pt="Modelo Modern BERT para classificação de texto eficiente e robusta.",
        de="Modernes BERT-Modell für effiziente und robuste Textklassifikation.",
        zh="现代 BERT 模型，用于高效且鲁棒的文本分类。",
    )
    COLOR: str = "#455A64"
    ICON: str = "Psychology"
    SCHEMA = ModernBertTransformerSchema
    MODEL_NAME: str = "answerdotai/ModernBERT-base"
    DOWNLOAD_SIZE_BYTES: int = 1199464688
    MAX_TOKEN_LENGTH: int = 8192
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_modernbert"
