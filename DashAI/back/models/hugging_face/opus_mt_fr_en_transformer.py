"""OpusMtFrEnTransformer model for French to English translation."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_opus_mt_transformer import (
    OpusMtTransformerMixin,
)
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformerSchema,
)


class OpusMtFrEnTransformerSchema(OpusMtEnESTransformerSchema):
    """Schema for the French to English Opus-MT model."""


class OpusMtFrEnTransformer(OpusMtTransformerMixin):
    """Pretrained transformer for French to English translation.

    Fine-tunes the Helsinki-NLP ``opus-mt-fr-en`` checkpoint, a MarianMT
    seq2seq model trained on parallel French to English corpora from the OPUS
    collection.

    References
    ----------
    - [1] https://huggingface.co/Helsinki-NLP/opus-mt-fr-en
    - [2] https://opus.nlpl.eu/
    """

    MODEL_NAME: str = "Helsinki-NLP/opus-mt-fr-en"
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_opus-mt-fr-en"
    SCHEMA = OpusMtFrEnTransformerSchema
    DOWNLOAD_SIZE_BYTES = 604554697
    DISPLAY_NAME: str = MultilingualString(
        en="Opus MT Fr-En Transformer",
        es="Transformer Opus MT Fr-En",
        pt="Transformer Opus MT Fr-En",
        de="Opus MT Fr-En Transformer",
        zh="Opus MT 法英翻译 Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Pretrained transformer for French to English translation. "
            "Download its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "Transformer preentrenado para traducción francés-inglés. "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "Transformer pré-treinado para tradução francês-inglês. "
            "Baixe seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Vortrainierter Transformer für Französisch-Englisch-Übersetzung. "
            "Lädt die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "用于法语到英语翻译的预训练 Transformer。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#0097A7"
    ICON: str = "Translate"
