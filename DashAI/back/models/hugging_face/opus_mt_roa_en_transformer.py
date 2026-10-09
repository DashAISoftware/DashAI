"""OpusMtRoaEnTransformer model for Romance to English translation."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_opus_mt_transformer import (
    OpusMtTransformerMixin,
)
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformerSchema,
)


class OpusMtRoaEnTransformerSchema(OpusMtEnESTransformerSchema):
    """Schema for the Romance to English Opus-MT model."""


class OpusMtRoaEnTransformer(OpusMtTransformerMixin):
    """Pretrained transformer for Romance to English translation.

    Fine-tunes the Helsinki-NLP ``opus-mt-roa-en`` checkpoint, a MarianMT
    seq2seq model trained on parallel Romance to English corpora from the OPUS
    collection. The target language is always English, so the source text is
    fed as-is without a language token; this covers Portuguese to English
    among the other Romance source languages.

    References
    ----------
    - [1] https://huggingface.co/Helsinki-NLP/opus-mt-roa-en
    - [2] https://opus.nlpl.eu/
    """

    MODEL_NAME: str = "Helsinki-NLP/opus-mt-roa-en"
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_opus-mt-roa-en"
    SCHEMA = OpusMtRoaEnTransformerSchema
    DOWNLOAD_SIZE_BYTES = 315135823
    DISPLAY_NAME: str = MultilingualString(
        en="Opus MT Roa-En Transformer",
        es="Transformer Opus MT Roa-En",
        pt="Transformer Opus MT Roa-En",
        de="Opus MT Roa-En Transformer",
        zh="Opus MT 罗曼语-英语翻译 Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Pretrained transformer for Romance to English translation "
            "(includes Portuguese to English). Download its weights from "
            "Hugging Face before use (internet required)."
        ),
        es=(
            "Transformer preentrenado para traducción de lenguas romances al "
            "inglés (incluye portugués a inglés). Descarga sus pesos de "
            "Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "Transformer pré-treinado para tradução de línguas românicas para o "
            "inglês (inclui português para inglês). Baixe seus pesos do "
            "Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Vortrainierter Transformer für die Übersetzung romanischer Sprachen "
            "ins Englische (einschließlich Portugiesisch nach Englisch). Lädt "
            "die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "用于罗曼语到英语翻译的预训练 Transformer（包括葡萄牙语到英语）。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#00796B"
    ICON: str = "Translate"
