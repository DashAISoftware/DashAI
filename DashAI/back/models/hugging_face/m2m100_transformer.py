"""M2M100 multilingual translation transformer for DashAI."""

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Union

from sklearn.exceptions import NotFittedError

from DashAI.back.core.schema_fields import schema_field, string_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.downloadable import (
    HFPretrainedDownloadMixin,
)
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformerSchema,
)
from DashAI.back.models.translation_model import TranslationModel
from DashAI.back.models.utils import (
    GPU_OR_CPU_PLACEHOLDER,
    resolve_temp_checkpoint_dir,
)

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class M2M100TransformerSchema(OpusMtEnESTransformerSchema):
    """Schema for the M2M100 multilingual translation model.

    Extends the standard translation schema with ``source_language`` and
    ``target_language`` fields, which accept ISO 639-1 language codes
    (e.g. ``"en"`` for English, ``"es"`` for Spanish, ``"fr"`` for French).
    """

    source_language: schema_field(
        string_field(),
        placeholder="en",
        description=MultilingualString(
            en=(
                "Source language ISO 639-1 code (e.g. 'en', 'es', 'fr', 'de'). "
                "Supports 100 languages."
            ),
            es=(
                "Código ISO 639-1 del idioma de origen (ej. 'en', 'es', 'fr', 'de'). "
                "Soporta 100 idiomas."
            ),
            pt=(
                "Código ISO 639-1 do idioma de origem (ex. 'en', 'es', 'fr', 'de'). "
                "Suporta 100 idiomas."
            ),
            de=(
                "ISO 639-1-Code der Quellsprache (z.B. 'en', 'es', 'fr', 'de'). "
                "Unterstützt 100 Sprachen."
            ),
            zh=(
                "源语言 ISO 639-1 代码（如 'en'、'es'、'fr'、'de'）。支持 100 种语言。"
            ),
        ),
        alias=MultilingualString(
            en="Source language",
            es="Idioma de origen",
            pt="Idioma de origem",
            de="Quellsprache",
            zh="源语言",
        ),
    )  # type: ignore
    target_language: schema_field(
        string_field(),
        placeholder="es",
        description=MultilingualString(
            en=(
                "Target language ISO 639-1 code (e.g. 'en', 'es', 'fr', 'de'). "
                "Supports 100 languages."
            ),
            es=(
                "Código ISO 639-1 del idioma destino (ej. 'en', 'es', 'fr', 'de'). "
                "Soporta 100 idiomas."
            ),
            pt=(
                "Código ISO 639-1 do idioma destino (ex. 'en', 'es', 'fr', 'de'). "
                "Suporta 100 idiomas."
            ),
            de=(
                "ISO 639-1-Code der Zielsprache (z.B. 'en', 'es', 'fr', 'de'). "
                "Unterstützt 100 Sprachen."
            ),
            zh=(
                "目标语言 ISO 639-1 代码（如 'en'、'es'、'fr'、'de'）。"
                "支持 100 种语言。"
            ),
        ),
        alias=MultilingualString(
            en="Target language",
            es="Idioma destino",
            pt="Idioma destino",
            de="Zielsprache",
            zh="目标语言",
        ),
    )  # type: ignore


class M2M100Transformer(HFPretrainedDownloadMixin, TranslationModel):
    """M2M100 multilingual seq2seq model for configurable language-pair translation.

    Fine-tunes the ``facebook/m2m100_418M`` checkpoint from Meta AI. The base
    model supports direct translation across 100 languages using ISO 639-1
    language codes (e.g. ``"en"``, ``"es"``, ``"fr"``). Unlike pivot-based
    systems, M2M100 translates directly between any supported pair.

    Target language generation is guided by ``forced_bos_token_id`` obtained
    from ``tokenizer.get_lang_id(target_language)``, identical in principle
    to the NLLB approach but using simpler ISO codes.

    References
    ----------
    - [1] https://huggingface.co/facebook/m2m100_418M
    - [2] Fan et al. (2021). "Beyond English-Centric Multilingual Machine
           Translation." JMLR 2021.
    """

    SCHEMA = M2M100TransformerSchema
    DISPLAY_NAME: str = MultilingualString(
        en="M2M-100 Multilingual Transformer",
        es="Transformer Multilingüe M2M-100",
        pt="Transformer Multilíngue M2M-100",
        de="M2M-100 Mehrsprachiger Transformer",
        zh="M2M-100 多语言 Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Facebook M2M-100 model for direct translation across 100 languages "
            "using ISO 639-1 codes. "
            "Download its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "Modelo M2M-100 de Facebook para traducción directa entre 100 idiomas "
            "usando códigos ISO 639-1. "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "Modelo M2M-100 do Facebook para tradução direta entre 100 idiomas "
            "usando códigos ISO 639-1. "
            "Baixe seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Facebook M2M-100-Modell für direkte Übersetzung zwischen 100 Sprachen "
            "mit ISO 639-1-Codes. "
            "Lädt die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "Facebook M2M-100 模型，使用 ISO 639-1 代码支持"
            " 100 种语言之间的直接翻译。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#6A1B9A"
    ICON: str = "Language"
    MODEL_NAME: str = "facebook/m2m100_418M"
    DOWNLOAD_SIZE_BYTES: int = 1941936305

    def __init__(self, model=None, pretrained_dir=None, **kwargs):
        kwargs = self.validate_and_transform(kwargs)

        from transformers import AutoTokenizer

        self.model_name = self._pretrained_source(pretrained_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        self.source_language = kwargs.get("source_language", "en")
        self.target_language = kwargs.get("target_language", "es")

        if hasattr(self.tokenizer, "src_lang"):
            self.tokenizer.src_lang = self.source_language

        self.training_args = {
            "num_train_epochs": kwargs.get("num_train_epochs", 2),
            "learning_rate": kwargs.get("learning_rate", 2e-5),
            "weight_decay": kwargs.get("weight_decay", 0.01),
        }
        self.batch_size = kwargs.get("batch_size", 4)
        self.device = kwargs.get("device") or GPU_OR_CPU_PLACEHOLDER
        self.log_train_every_n_epochs = kwargs.get("log_train_every_n_epochs", 1)
        self.log_train_every_n_steps = kwargs.get("log_train_every_n_steps", None)
        self.log_validation_every_n_epochs = kwargs.get(
            "log_validation_every_n_epochs", 1
        )
        self.log_validation_every_n_steps = kwargs.get(
            "log_validation_every_n_steps", None
        )

        if model is None:
            from transformers import AutoModelForSeq2SeqLM

            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        else:
            self.model = model

        self.num_train_epochs = self.training_args.get("num_train_epochs", 2)
        self.fitted = model is not None

    def tokenize_data(
        self, x: "DashAIDataset", y: Optional["DashAIDataset"] = None
    ) -> "DashAIDataset":
        """Tokenize with src_lang set for M2M100."""
        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        if hasattr(self.tokenizer, "src_lang"):
            self.tokenizer.src_lang = self.source_language

        is_y = bool(y)
        if not y:
            y = DashAIDataset.from_list([{"foo": 0}] * len(x))

        dataset = []
        input_column_name = x.column_names[0]
        output_column_name = y.column_names[0] if is_y else None

        for i, input_sample in enumerate(x):
            tokenized_input = self.tokenizer(
                input_sample[input_column_name],
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

    def train(
        self,
        x_train: "DashAIDataset",
        y_train: "DashAIDataset",
        x_validation: "DashAIDataset" = None,
        y_validation: "DashAIDataset" = None,
    ):
        """Fine-tune M2M100 on the configured language pair."""
        from transformers import Seq2SeqTrainer, Seq2SeqTrainingArguments

        from DashAI.back.models.hugging_face.metrics_callback import MetricsCallback

        dataset = self.tokenize_data(x_train, y_train)
        dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

        has_validation_data = x_validation is not None and y_validation is not None

        output_root = resolve_temp_checkpoint_dir(
            "DashAI/back/user_models/temp_checkpoints_m2m100"
        )
        output_root.mkdir(parents=True, exist_ok=True)
        run_output_dir = tempfile.mkdtemp(prefix="m2m100_", dir=str(output_root))

        training_args_obj = Seq2SeqTrainingArguments(
            output_dir=run_output_dir,
            save_steps=1,
            save_total_limit=1,
            per_device_train_batch_size=self.batch_size,
            per_device_eval_batch_size=self.batch_size,
            use_cpu=self.device.lower() != "gpu",
            **self.training_args,
        )

        metrics_callback = MetricsCallback(
            model_instance=self,
            x_train=x_train,
            y_train=y_train,
            x_val=x_validation,
            y_val=y_validation,
            total_epochs=self.num_train_epochs,
            log_training_every_n_epochs=self.log_train_every_n_epochs,
            log_training_every_n_steps=self.log_train_every_n_steps,
            log_val_every_n_epochs=(
                self.log_validation_every_n_epochs if has_validation_data else None
            ),
            log_val_every_n_steps=(
                self.log_validation_every_n_steps if has_validation_data else None
            ),
        )

        trainer = Seq2SeqTrainer(
            model=self.model,
            args=training_args_obj,
            train_dataset=dataset,
            callbacks=[metrics_callback],
        )

        self.fitted = True
        try:
            trainer.train()
        finally:
            shutil.rmtree(run_output_dir, ignore_errors=True)

        return self

    def predict(self, x_pred: "DashAIDataset") -> List:
        """Translate using forced_bos_token_id for the target language."""
        if not self.fitted:
            raise NotFittedError(
                f"This {self.__class__.__name__} instance is not fitted yet. "
                "Call 'train' before using this estimator."
            )

        if self.device.lower() == "gpu":
            self.model.to("cuda")
        else:
            self.model.to("cpu")
        self.model.eval()

        dataset = self.tokenize_data(x_pred)
        dataset.set_format(type="torch", columns=["input_ids", "attention_mask"])

        target_bos = self.tokenizer.get_lang_id(self.target_language)
        translations = []

        for example in dataset:
            inputs = {
                k: v.unsqueeze(0).to(self.model.device) for k, v in example.items()
            }
            outputs = self.model.generate(
                **inputs,
                forced_bos_token_id=target_bos,
            )
            translated_text = self.tokenizer.decode(
                outputs[0], skip_special_tokens=True
            )
            translations.append(translated_text)

        return translations

    def prepare_dataset(
        self, dataset: "DashAIDataset", is_fit: bool = False
    ) -> "DashAIDataset":
        """Return the dataset unchanged."""
        return dataset

    def save(self, filename: Union[str, "Path"]) -> None:
        """Persist model weights and hyperparameters to disk."""
        from transformers import AutoConfig

        save_dir = Path(filename)
        if save_dir.exists() and save_dir.is_file():
            save_dir.unlink()
        save_dir.mkdir(parents=True, exist_ok=True)

        self.model.save_pretrained(save_dir)
        self.tokenizer.save_pretrained(save_dir)
        config = AutoConfig.from_pretrained(save_dir)
        config.custom_params = {
            "num_train_epochs": self.training_args.get("num_train_epochs"),
            "batch_size": self.batch_size,
            "learning_rate": self.training_args.get("learning_rate"),
            "device": self.device,
            "weight_decay": self.training_args.get("weight_decay"),
            "source_language": self.source_language,
            "target_language": self.target_language,
            "fitted": self.fitted,
        }
        config.save_pretrained(save_dir)

    @classmethod
    def load(cls, filename: Union[str, "Path"]):
        """Restore an M2M100Transformer instance from disk."""
        from transformers import AutoConfig, AutoModelForSeq2SeqLM

        model = AutoModelForSeq2SeqLM.from_pretrained(filename)
        config = AutoConfig.from_pretrained(filename)
        custom_params = getattr(config, "custom_params", {})

        loaded_model = cls(
            model=model,
            pretrained_dir=str(filename),
            num_train_epochs=custom_params.get("num_train_epochs"),
            batch_size=custom_params.get("batch_size"),
            learning_rate=custom_params.get("learning_rate"),
            device=custom_params.get("device"),
            weight_decay=custom_params.get("weight_decay"),
            source_language=custom_params.get("source_language", "en"),
            target_language=custom_params.get("target_language", "es"),
            log_train_every_n_epochs=None,
            log_train_every_n_steps=None,
            log_validation_every_n_epochs=None,
            log_validation_every_n_steps=None,
        )
        loaded_model.fitted = custom_params.get("fitted", False)
        return loaded_model
