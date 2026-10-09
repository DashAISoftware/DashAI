"""OpusMtEnFrTransformer model for English to French translation."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_opus_mt_transformer import (
    OpusMtTransformerMixin,
)
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformerSchema,
)


class OpusMtEnFrTransformerSchema(OpusMtEnESTransformerSchema):
    """Schema for the English to French Opus-MT model."""


class OpusMtEnFrTransformer(OpusMtTransformerMixin):
    """Pretrained transformer for English to French translation.

    Fine-tunes the Helsinki-NLP ``opus-mt-en-fr`` checkpoint, a MarianMT
    seq2seq model trained on parallel English to French corpora from the OPUS
    collection.

    References
    ----------
    - [1] https://huggingface.co/Helsinki-NLP/opus-mt-en-fr
    - [2] https://opus.nlpl.eu/
    """

    MODEL_NAME: str = "Helsinki-NLP/opus-mt-en-fr"
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_opus-mt-en-fr"
    SCHEMA = OpusMtEnFrTransformerSchema
    DOWNLOAD_SIZE_BYTES = 303750994
    DISPLAY_NAME: str = MultilingualString(
        en="Opus MT En-Fr Transformer",
        es="Transformer Opus MT En-Fr",
        pt="Transformer Opus MT En-Fr",
        de="Opus MT En-Fr Transformer",
        zh="Opus MT 英法翻译 Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Pretrained transformer for English to French translation. "
            "Download its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "Transformer preentrenado para traducción inglés-francés. "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "Transformer pré-treinado para tradução inglês-francês. "
            "Baixe seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Vortrainierter Transformer für Englisch-Französisch-Übersetzung. "
            "Lädt die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "用于英语到法语翻译的预训练 Transformer。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#1976D2"
    ICON: str = "Translate"
