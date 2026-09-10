"""DashAI implementation of BERT model for English text classification."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_text_classification_transformer import (
    HuggingFaceTextClassificationTransformer,
)
from DashAI.back.models.hugging_face.distilbert_transformer import (
    DistilBertTransformerSchema,
)


class BertTransformer(HuggingFaceTextClassificationTransformer):
    """Pretrained BERT model for English text classification.

    BERT (Bidirectional Encoder Representations from Transformers) pretrains deep
    bidirectional representations by jointly conditioning on both left and right
    context in all layers. Fine-tuned BERT achieves strong results on a wide range
    of text classification tasks.

    References
    ----------
    - [1] Devlin, J. et al. (2019). "BERT: Pre-training of Deep Bidirectional
           Transformers for Language Understanding." NAACL 2019.
    - [2] https://huggingface.co/bert-base-uncased
    """

    DISPLAY_NAME: str = MultilingualString(
        en="BERT Transformer",
        es="Transformer BERT",
        pt="Transformer BERT",
        de="BERT Transformer",
        zh="BERT Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Bidirectional BERT model for English text classification. "
            "Download its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "Modelo BERT bidireccional para clasificación de texto en inglés. "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "Modelo BERT bidirecional para classificação de texto em inglês. "
            "Baixe seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Bidirektionales BERT-Modell für englische Textklassifikation. "
            "Lädt die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "双向 BERT 模型，用于英文文本分类。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#1565C0"
    ICON: str = "Psychology"
    SCHEMA = DistilBertTransformerSchema
    MODEL_NAME: str = "bert-base-uncased"
    DOWNLOAD_SIZE_BYTES: int = 881643453
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_bert"
