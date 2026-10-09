"""OpusMtEnRoaTransformer model for English to Romance translation.

Unlike the single language-pair Opus-MT wrappers, the ``opus-mt-en-roa``
checkpoint is multi-target: it translates English into any of several Romance
languages, selected by prepending a sentence-initial language token
(``>>id<<``) to every source sentence. All of that extra handling lives in this
file so the shared :class:`OpusMtTransformerMixin` stays single-pair.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from DashAI.back.core.schema_fields import enum_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_opus_mt_transformer import (
    OpusMtTransformerMixin,
)
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformerSchema,
)

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

#: Human readable target language -> Marian language token id. Every id below is
#: a valid sentence-initial token in the ``opus-mt-en-roa`` vocabulary.
TARGET_LANG_TOKENS = {
    "Portuguese": "por",
    "Spanish": "spa",
    "French": "fra",
    "Italian": "ita",
    "Romanian": "ron",
    "Catalan": "cat",
    "Galician": "glg",
}


class OpusMtEnRoaTransformerSchema(OpusMtEnESTransformerSchema):
    """Schema for the English to Romance Opus-MT model.

    Adds the ``target_language`` selector on top of the shared Opus-MT training
    hyperparameters, since this checkpoint can translate into several languages.
    """

    target_language: schema_field(
        enum_field(enum=list(TARGET_LANG_TOKENS)),
        placeholder="French",
        description=MultilingualString(
            en="Romance language to translate the English input into.",
            es="Lengua romance a la que traducir la entrada en inglés.",
            pt="Língua românica para a qual traduzir a entrada em inglês.",
            de="Romanische Sprache, in die die englische Eingabe übersetzt wird.",
            zh="将英语输入翻译成的目标罗曼语。",
        ),
        alias=MultilingualString(
            en="Target language",
            es="Idioma de destino",
            pt="Idioma de destino",
            de="Zielsprache",
            zh="目标语言",
        ),
    )  # type: ignore


class OpusMtEnRoaTransformer(OpusMtTransformerMixin):
    """Pretrained transformer for English to Romance translation.

    Fine-tunes the Helsinki-NLP ``opus-mt-en-roa`` checkpoint, a multi-target
    MarianMT seq2seq model trained on parallel English to Romance corpora from
    the OPUS collection. The desired output language is chosen via the
    ``target_language`` parameter and injected as a sentence-initial ``>>id<<``
    token on every source sentence (required by this checkpoint), covering
    English to Portuguese among the other Romance targets.

    References
    ----------
    - [1] https://huggingface.co/Helsinki-NLP/opus-mt-en-roa
    - [2] https://opus.nlpl.eu/
    """

    MODEL_NAME: str = "Helsinki-NLP/opus-mt-en-roa"
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_opus-mt-en-roa"
    SCHEMA = OpusMtEnRoaTransformerSchema
    DOWNLOAD_SIZE_BYTES = 297844640
    DISPLAY_NAME: str = MultilingualString(
        en="Opus MT En-Roa Transformer",
        es="Transformer Opus MT En-Roa",
        pt="Transformer Opus MT En-Roa",
        de="Opus MT En-Roa Transformer",
        zh="Opus MT 英语-罗曼语翻译 Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Pretrained transformer for English to Romance translation "
            "(Portuguese, Spanish, French, Italian, Romanian, Catalan, "
            "Galician), selected via the target language parameter. Download "
            "its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "Transformer preentrenado para traducción del inglés a lenguas "
            "romances (portugués, español, francés, italiano, rumano, catalán, "
            "gallego), seleccionadas con el parámetro de idioma de destino. "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "Transformer pré-treinado para tradução do inglês para línguas "
            "românicas (português, espanhol, francês, italiano, romeno, catalão, "
            "galego), selecionadas pelo parâmetro de idioma de destino. Baixe "
            "seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Vortrainierter Transformer für die Übersetzung von Englisch in "
            "romanische Sprachen (Portugiesisch, Spanisch, Französisch, "
            "Italienisch, Rumänisch, Katalanisch, Galicisch), ausgewählt über "
            "den Zielsprachenparameter. Lädt die Gewichte vor der Nutzung von "
            "Hugging Face herunter (Internet erforderlich)."
        ),
        zh=(
            "用于英语到罗曼语翻译的预训练 Transformer（葡萄牙语、西班牙语、法语、"
            "意大利语、罗马尼亚语、加泰罗尼亚语、加利西亚语），通过目标语言参数选择。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#5E35B1"
    ICON: str = "Translate"

    def __init__(self, model=None, **kwargs):
        """Initialize the base model and build the language-token prefix.

        Parameters
        ----------
        model : transformers.PreTrainedModel or None
            Preloaded model to reuse instead of downloading weights.
        **kwargs
            Training hyperparameters plus ``target_language`` (a key of
            :data:`TARGET_LANG_TOKENS`).
        """
        # The shared mixin.load() rebuilds the model from saved hyperparameters
        # but has no knowledge of target_language, so it is absent from kwargs on
        # a load and would fail the required field schema validation. Supply a
        # placeholder to pass validation; load() restores the real value from
        # disk immediately after construction.
        kwargs.setdefault("target_language", next(iter(TARGET_LANG_TOKENS)))
        super().__init__(model=model, **kwargs)
        self.target_language = kwargs.get("target_language")
        self.lang_prefix = self._build_lang_prefix(self.target_language)

    @staticmethod
    def _build_lang_prefix(target_language: Optional[str]) -> str:
        """Return the ``>>id<< `` token for a target language, or ``""``."""
        if not target_language:
            return ""
        token = TARGET_LANG_TOKENS.get(target_language)
        if token is None:
            raise ValueError(
                f"Unsupported target_language '{target_language}'. Valid "
                f"options: {list(TARGET_LANG_TOKENS)}."
            )
        return f">>{token}<< "

    def tokenize_data(
        self, x: "DashAIDataset", y: Optional["DashAIDataset"] = None
    ) -> "DashAIDataset":
        """Tokenize like the base class but prepend the target language token.

        The ``opus-mt-en-roa`` checkpoint requires a sentence-initial ``>>id<<``
        token on the source to pick the output language; the target side is
        left untouched.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        is_y = bool(y)
        if not y:
            y = DashAIDataset.from_list([{"foo": 0}] * len(x))

        dataset = []
        input_column_name = x.column_names[0]
        output_column_name = y.column_names[0] if is_y else None

        for i, input_sample in enumerate(x):
            tokenized_input = self.tokenizer(
                self.lang_prefix + input_sample[input_column_name],
                truncation=True,
                padding="max_length",
                max_length=512,
            )
            sample = {
                "input_ids": tokenized_input["input_ids"],
                "attention_mask": tokenized_input["attention_mask"],
            }
            if is_y:
                output_sample = y[i]
                tokenized_output = self.tokenizer(
                    output_sample[output_column_name],
                    truncation=True,
                    padding="max_length",
                    max_length=512,
                )
                sample["labels"] = tokenized_output["input_ids"]
            dataset.append(sample)

        return DashAIDataset.from_list(dataset)

    def save(self, filename: Union[str, "Path"]) -> None:
        """Persist the model, recording the chosen target language."""
        from transformers import AutoConfig

        super().save(filename)
        config = AutoConfig.from_pretrained(filename)
        custom_params = getattr(config, "custom_params", {})
        custom_params["target_language"] = self.target_language
        config.custom_params = custom_params
        config.save_pretrained(filename)

    @classmethod
    def load(cls, filename: Union[str, "Path"]):
        """Restore a model instance and its target language prefix."""
        from transformers import AutoConfig

        loaded_model = super().load(filename)
        config = AutoConfig.from_pretrained(filename)
        target_language = getattr(config, "custom_params", {}).get("target_language")
        loaded_model.target_language = target_language
        loaded_model.lang_prefix = cls._build_lang_prefix(target_language)
        return loaded_model
