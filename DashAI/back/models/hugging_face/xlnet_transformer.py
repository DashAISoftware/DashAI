"""DashAI implementation of XLNet model for English text classification."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_text_classification_transformer import (
    HuggingFaceTextClassificationTransformer,
)
from DashAI.back.models.hugging_face.distilbert_transformer import (
    DistilBertTransformerSchema,
)


class XlnetTransformer(HuggingFaceTextClassificationTransformer):
    """Pretrained XLNet model for English text classification.

    XLNet is an autoregressive language model that maximises the expected
    log-likelihood over all permutations of the factorisation order. Unlike BERT,
    XLNet does not rely on a corrupted input and can model bidirectional context
    without masking, often outperforming BERT on various NLP tasks.

    References
    ----------
    - [1] Yang, Z. et al. (2019). "XLNet: Generalised Autoregressive Pretraining
           for Language Understanding." NeurIPS 2019.
    - [2] https://huggingface.co/xlnet-base-cased
    """

    DISPLAY_NAME: str = MultilingualString(
        en="XLNet Transformer",
        es="Transformer XLNet",
        pt="Transformer XLNet",
        de="XLNet Transformer",
        zh="XLNet Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Autoregressive XLNet model for English text classification. "
            "Download its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "Modelo XLNet autorregresivo para clasificación de texto en inglés. "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "Modelo XLNet autorregressivo para classificação de texto em inglês. "
            "Baixe seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Autoregressives XLNet-Modell für englische Textklassifikation. "
            "Lädt die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "自回归 XLNet 模型，用于英文文本分类。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#37474F"
    ICON: str = "AutoAwesome"
    SCHEMA = DistilBertTransformerSchema
    MODEL_NAME: str = "xlnet-base-cased"
    DOWNLOAD_SIZE_BYTES: int = 469226606
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_xlnet"
