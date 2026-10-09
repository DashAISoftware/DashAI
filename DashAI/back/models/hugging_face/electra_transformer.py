"""DashAI implementation of ELECTRA model for English text classification."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_text_classification_transformer import (
    HuggingFaceTextClassificationTransformer,
)
from DashAI.back.models.hugging_face.distilbert_transformer import (
    DistilBertTransformerSchema,
)


class ElectraTransformer(HuggingFaceTextClassificationTransformer):
    """Pretrained ELECTRA model for efficient English text classification.

    ELECTRA uses a replaced token detection pretraining objective: a generator
    produces plausible token replacements while a discriminator is trained to
    identify which tokens were replaced. This allows ELECTRA to train on all
    input tokens rather than only masked ones, making pretraining more efficient.

    References
    ----------
    - [1] Clark, K. et al. (2020). "ELECTRA: Pre-training Text Encoders as
           Discriminators Rather Than Generators." ICLR 2020.
    - [2] https://huggingface.co/google/electra-small-discriminator
    """

    DISPLAY_NAME: str = MultilingualString(
        en="ELECTRA Transformer",
        es="Transformer ELECTRA",
        pt="Transformer ELECTRA",
        de="ELECTRA Transformer",
        zh="ELECTRA Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Sample efficient ELECTRA discriminator for text classification. "
            "Download its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "Discriminador ELECTRA eficiente en muestras para clasificación de texto. "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "Discriminador ELECTRA eficiente em amostras para classificação de texto. "
            "Baixe seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Stichprobeneffizienter ELECTRA-Diskriminator für Textklassifikation. "
            "Lädt die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "样本高效的 ELECTRA 判别器，用于文本分类。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#558B2F"
    ICON: str = "ElectricBolt"
    SCHEMA = DistilBertTransformerSchema
    MODEL_NAME: str = "google/electra-small-discriminator"
    DOWNLOAD_SIZE_BYTES: int = 54946248
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_electra"
