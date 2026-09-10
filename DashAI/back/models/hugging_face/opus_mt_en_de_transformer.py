"""OpusMtEnDeTransformer model for English to German translation."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_opus_mt_transformer import (
    OpusMtTransformerMixin,
)
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformerSchema,
)


class OpusMtEnDeTransformerSchema(OpusMtEnESTransformerSchema):
    """Schema for the English to German Opus-MT model."""


class OpusMtEnDeTransformer(OpusMtTransformerMixin):
    """Pretrained transformer for English to German translation.

    Fine-tunes the Helsinki-NLP ``opus-mt-en-de`` checkpoint, a MarianMT
    seq2seq model trained on parallel English to German corpora from the OPUS
    collection.

    References
    ----------
    - [1] https://huggingface.co/Helsinki-NLP/opus-mt-en-de
    - [2] https://opus.nlpl.eu/
    """

    MODEL_NAME: str = "Helsinki-NLP/opus-mt-en-de"
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_opus-mt-en-de"
    SCHEMA = OpusMtEnDeTransformerSchema
    DOWNLOAD_SIZE_BYTES = 300772148
    DISPLAY_NAME: str = MultilingualString(
        en="Opus MT En-De Transformer",
        es="Transformer Opus MT En-De",
        pt="Transformer Opus MT En-De",
        de="Opus MT En-De Transformer",
        zh="Opus MT 英德翻译 Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Pretrained transformer for English to German translation. "
            "Download its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "Transformer preentrenado para traducción inglés-alemán. "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "Transformer pré-treinado para tradução inglês-alemão. "
            "Baixe seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Vortrainierter Transformer für Englisch-Deutsch-Übersetzung. "
            "Lädt die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "用于英语到德语翻译的预训练 Transformer。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#455A64"
    ICON: str = "Translate"
