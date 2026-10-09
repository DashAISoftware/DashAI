"""DashAI implementation of BETO model for Spanish text classification."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_text_classification_transformer import (
    HuggingFaceTextClassificationTransformer,
)
from DashAI.back.models.hugging_face.distilbert_transformer import (
    DistilBertTransformerSchema,
)


class BetoTransformer(HuggingFaceTextClassificationTransformer):
    """Pretrained BETO model for Spanish text classification.

    BETO is a Spanish BERT trained on the Spanish Wikipedia and other Spanish
    corpora using the whole word masking strategy. It achieves state of the art
    results on several Spanish NLP benchmarks. Particularly useful for tasks
    involving Spanish text.

    References
    ----------
    - [1] Cañete, J. et al. (2020). "Spanish Pre-Trained BERT Model and
           Evaluation Data." PML4DC at ICLR 2020.
    - [2] https://huggingface.co/dccuchile/bert-base-spanish-wwm-cased
    """

    DISPLAY_NAME: str = MultilingualString(
        en="BETO Spanish BERT",
        es="BETO BERT en Español",
        pt="BETO BERT em Espanhol",
        de="BETO Spanisches BERT",
        zh="BETO 西班牙语 BERT",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Spanish BERT (BETO) pretrained on Spanish corpora. "
            "Download its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "BERT en español (BETO) preentrenado en corpus en español. "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "BERT em espanhol (BETO) pré-treinado em corpus em espanhol. "
            "Baixe seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Spanisches BERT (BETO) vortrainiert auf spanischen Korpora. "
            "Lädt die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "在西班牙语语料库上预训练的 BERT（BETO）模型。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#C62828"
    ICON: str = "RecordVoiceOver"
    SCHEMA = DistilBertTransformerSchema
    MODEL_NAME: str = "dccuchile/bert-base-spanish-wwm-cased"
    DOWNLOAD_SIZE_BYTES: int = 440350800
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_beto"
