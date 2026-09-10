"""DashAI implementation of RoBERTa model for English text classification."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_text_classification_transformer import (
    HuggingFaceTextClassificationTransformer,
)
from DashAI.back.models.hugging_face.distilbert_transformer import (
    DistilBertTransformerSchema,
)


class RobertaTransformer(HuggingFaceTextClassificationTransformer):
    """Pretrained RoBERTa model for English text classification.

    RoBERTa (Robustly Optimised BERT Pre-training Approach) improves upon BERT
    by training longer with larger mini-batches, removing the next sentence
    prediction objective, and using dynamic masking. It achieves consistently
    higher performance on NLP benchmarks than BERT.

    References
    ----------
    - [1] Liu, Y. et al. (2019). "RoBERTa: A Robustly Optimized BERT Pretraining
           Approach." arXiv:1907.11692.
    - [2] https://huggingface.co/roberta-base
    """

    DISPLAY_NAME: str = MultilingualString(
        en="RoBERTa Transformer",
        es="Transformer RoBERTa",
        pt="Transformer RoBERTa",
        de="RoBERTa Transformer",
        zh="RoBERTa Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Robustly optimised BERT for English text classification. "
            "Download its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "BERT optimizado robustamente para clasificación de texto en inglés. "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "BERT otimizado robustamente para classificação de texto em inglês. "
            "Baixe seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Robust optimiertes BERT für englische Textklassifikation. "
            "Lädt die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "经过鲁棒优化的 BERT，用于英文文本分类。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#E65100"
    ICON: str = "SmartToy"
    SCHEMA = DistilBertTransformerSchema
    MODEL_NAME: str = "roberta-base"
    DOWNLOAD_SIZE_BYTES: int = 1003342916
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_roberta"
