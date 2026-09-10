"""DashAI implementation of XLM-RoBERTa model for multilingual text classification."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_text_classification_transformer import (
    HuggingFaceTextClassificationTransformer,
)
from DashAI.back.models.hugging_face.distilbert_transformer import (
    DistilBertTransformerSchema,
)


class XlmRobertaTransformer(HuggingFaceTextClassificationTransformer):
    """Pretrained XLM-RoBERTa model for multilingual text classification.

    XLM-RoBERTa is a multilingual version of RoBERTa trained on 2.5 TB of
    filtered CommonCrawl data covering 100 languages. It achieves strong
    performance on crosslingual classification without language specific
    fine-tuning. Requires the ``sentencepiece`` package for its tokeniser.

    References
    ----------
    - [1] Conneau, A. et al. (2020). "Unsupervised Cross-lingual Representation
           Learning at Scale." ACL 2020.
    - [2] https://huggingface.co/xlm-roberta-base
    """

    DISPLAY_NAME: str = MultilingualString(
        en="XLM-RoBERTa Transformer",
        es="Transformer XLM-RoBERTa",
        pt="Transformer XLM-RoBERTa",
        de="XLM-RoBERTa Transformer",
        zh="XLM-RoBERTa Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Multilingual RoBERTa for crosslingual text classification "
            "(100 languages). "
            "Download its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "RoBERTa multilingüe para clasificación de texto entre idiomas "
            "(100 idiomas). "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "RoBERTa multilingual para classificação de texto entre idiomas "
            "(100 idiomas). "
            "Baixe seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Mehrsprachiges RoBERTa für sprachübergreifende Textklassifikation "
            "(100 Sprachen). "
            "Lädt die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "支持跨语言文本分类的多语言 RoBERTa（100 种语言）。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#6A1B9A"
    ICON: str = "Language"
    SCHEMA = DistilBertTransformerSchema
    MODEL_NAME: str = "xlm-roberta-base"
    DOWNLOAD_SIZE_BYTES: int = 2245330190
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_xlm_roberta"
