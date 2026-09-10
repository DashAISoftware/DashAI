"""DashAI implementation of ALBERT model for English text classification."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_text_classification_transformer import (
    HuggingFaceTextClassificationTransformer,
)
from DashAI.back.models.hugging_face.distilbert_transformer import (
    DistilBertTransformerSchema,
)


class AlbertTransformer(HuggingFaceTextClassificationTransformer):
    """Pretrained ALBERT model for efficient English text classification.

    ALBERT (A Lite BERT) reduces BERT's parameters via crosslayer parameter
    sharing and factorised embedding parametrisation, making it significantly
    smaller and faster while retaining high accuracy. Requires the
    ``sentencepiece`` package for its tokeniser.

    References
    ----------
    - [1] Lan, Z. et al. (2020). "ALBERT: A Lite BERT for Self-supervised
           Learning of Language Representations." ICLR 2020.
    - [2] https://huggingface.co/albert-base-v2
    """

    DISPLAY_NAME: str = MultilingualString(
        en="ALBERT Transformer",
        es="Transformer ALBERT",
        pt="Transformer ALBERT",
        de="ALBERT Transformer",
        zh="ALBERT Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Parameter efficient BERT variant for English text classification. "
            "Download its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "Variante de BERT eficiente en parámetros para clasificación en inglés. "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "Variante do BERT eficiente em parâmetros para classificação de "
            "texto em inglês. "
            "Baixe seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Parametereffiziente BERT-Variante für englische Textklassifikation. "
            "Lädt die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "参数高效的 BERT 变体，用于英文文本分类。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#00838F"
    ICON: str = "Speed"
    SCHEMA = DistilBertTransformerSchema
    MODEL_NAME: str = "albert-base-v2"
    DOWNLOAD_SIZE_BYTES: int = 96833451
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_albert"
