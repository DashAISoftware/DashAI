"""DashAI implementation of DeBERTa-v3 for text classification.

This module provides a DashAI wrapper around the Hugging Face
``microsoft/deberta-v3-base`` checkpoint for sequence classification tasks.
It reuses the shared training and inference flow from
``HuggingFaceTextClassificationTransformer`` and exposes DashAI specific UI
metadata and schema configuration.
"""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_text_classification_transformer import (
    HuggingFaceTextClassificationTransformer,
)
from DashAI.back.models.hugging_face.distilbert_transformer import (
    DistilBertTransformerSchema,
)


class DebertaV3TransformerSchema(DistilBertTransformerSchema):
    """Schema for DeBERTa-v3 text classification hyperparameters.

    This schema inherits all hyperparameters from
    :class:`DistilBertTransformerSchema`, including optimization, device and
    metric logging controls, so DeBERTa-v3 integrates consistently with other
    Hugging Face text classifiers in DashAI.
    """


class DebertaV3Transformer(HuggingFaceTextClassificationTransformer):
    """Pretrained DeBERTa-v3 transformer for text classification.

    DeBERTa-v3 improves language understanding by combining disentangled
    attention and improved pretraining objectives, which often yields strong
    accuracy across a wide range of classification benchmarks.

    This wrapper uses ``microsoft/deberta-v3-base`` as the default backbone and
    relies on the shared Hugging Face training loop implemented in
    :class:`HuggingFaceTextClassificationTransformer`.

    References
    ----------
    - [1] https://huggingface.co/microsoft/deberta-v3-base
    - [2] https://huggingface.co/docs/transformers/model_doc/deberta-v2
    """

    DISPLAY_NAME: str = MultilingualString(
        en="DeBERTa-v3 Transformer",
        es="Transformer DeBERTa-v3",
        pt="Transformer DeBERTa-v3",
        de="DeBERTa-v3 Transformer",
        zh="DeBERTa-v3 Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en="DeBERTa-v3 model for robust text classification performance.",
        es="Modelo DeBERTa-v3 para clasificación de texto robusta.",
        pt="Modelo DeBERTa-v3 para classificação de texto robusta.",
        de="DeBERTa-v3-Modell für robuste Textklassifikationsleistung.",
        zh="用于鲁棒文本分类的 DeBERTa-v3 模型。",
    )
    COLOR: str = "#1E88E5"
    ICON: str = "Psychology"
    SCHEMA = DebertaV3TransformerSchema
    MODEL_NAME: str = "microsoft/deberta-v3-base"
    DOWNLOAD_SIZE_BYTES: int = 373616107
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_deberta_v3"
