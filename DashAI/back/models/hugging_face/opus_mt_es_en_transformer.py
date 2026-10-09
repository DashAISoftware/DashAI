"""OpusMtEsENTransformer model for Spanish to English translation."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_opus_mt_transformer import (
    OpusMtTransformerMixin,
)
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformerSchema,
)


class OpusMtEsENTransformerSchema(OpusMtEnESTransformerSchema):
    """Schema for the Spanish to English Opus-MT model.

    Inherits all fields from ``OpusMtEnESTransformerSchema``.
    """


class OpusMtEsENTransformer(OpusMtTransformerMixin):
    """Pretrained transformer for Spanish to English translation.

    Fine-tunes the Helsinki-NLP ``opus-mt-es-en`` checkpoint, a MarianMT
    seq2seq model trained on parallel Spanish to English corpora from the OPUS
    collection. Supports direct translation without pivot languages.

    References
    ----------
    - [1] https://huggingface.co/Helsinki-NLP/opus-mt-es-en
    - [2] https://opus.nlpl.eu/
    """

    MODEL_NAME: str = "Helsinki-NLP/opus-mt-es-en"
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_opus-mt-es-en"
    SCHEMA = OpusMtEsENTransformerSchema
    DOWNLOAD_SIZE_BYTES = 315310760
    DISPLAY_NAME: str = MultilingualString(
        en="Opus MT Es-En Transformer",
        es="Transformer Opus MT Es-En",
        pt="Transformer Opus MT Es-En",
        de="Opus MT Es-En Transformer",
        zh="Opus MT 西英翻译 Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Pretrained transformer for Spanish to English translation. "
            "Download its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "Transformer preentrenado para traducción español-inglés. "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "Transformer pré-treinado para tradução espanhol-inglês. "
            "Baixe seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Vortrainierter Transformer für Spanisch-Englisch-Übersetzung. "
            "Lädt die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "用于西班牙语到英语翻译的预训练 Transformer。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#FF8A65"
    ICON: str = "Translate"
