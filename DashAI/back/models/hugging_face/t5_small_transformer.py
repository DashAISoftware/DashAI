"""T5SmallTransformer model for English-to-{German, French, Romanian} translation."""

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Union

from sklearn.exceptions import NotFittedError

from DashAI.back.core.schema_fields import enum_field, schema_field
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


_T5_SUPPORTED_LANGUAGES = ["German", "French", "Romanian"]


class T5SmallTransformerSchema(OpusMtEnESTransformerSchema):
    """Schema for the T5-small translation model.

    Extends the standard translation schema with a ``target_language`` field
    restricted to the languages covered by T5's pre-training tasks:
    German, French, and Romanian (source is always English).
    """

    target_language: schema_field(
        enum_field(_T5_SUPPORTED_LANGUAGES),
        placeholder="German",
        description=MultilingualString(
            en=(
                "Target language for translation. "
                "Supported: 'German', 'French', 'Romanian'. "
                "T5-small translates from English only."
            ),
            es=(
                "Idioma destino para la traducción. "
                "Soportados: 'German', 'French', 'Romanian'. "
                "T5-small traduce solo desde inglés."
            ),
            pt=(
                "Idioma de destino para a tradução. "
                "Suportados: 'German', 'French', 'Romanian'. "
                "T5-small traduz somente a partir do inglês."
            ),
            de=(
                "Zielsprache für die Übersetzung. "
                "Unterstützt: 'German', 'French', 'Romanian'. "
                "T5-small übersetzt nur aus dem Englischen."
            ),
            zh=(
                "翻译的目标语言。"
                "支持：'German'、'French'、'Romanian'。"
                "T5-small 仅从英语翻译。"
            ),
        ),
        alias=MultilingualString(
            en="Target language",
            es="Idioma destino",
            pt="Idioma de destino",
            de="Zielsprache",
            zh="目标语言",
        ),
    )  # type: ignore


class T5SmallTransformer(HFPretrainedDownloadMixin, TranslationModel):
    """T5-small seq2seq model for English-to-{German, French, Romanian} translation.

    Fine-tunes the ``t5-small`` checkpoint from Google. Translation direction is
    controlled by a task prefix prepended to each source sentence, e.g.
    ``"translate English to German: <text>"``.

    Supported target languages: German, French, Romanian (T5 pre-training scope).
    The source language is always English.

    References
    ----------
    - [1] https://huggingface.co/t5-small
    - [2] Raffel et al. (2020). "Exploring the Limits of Transfer Learning with a
           Unified Text-to-Text Transformer." JMLR 2020.
    """

    SCHEMA = T5SmallTransformerSchema
    DISPLAY_NAME: str = MultilingualString(
        en="T5-Small Translation Transformer",
        es="Transformer de Traducción T5-Small",
        pt="Transformer de Tradução T5-Small",
        de="T5-Small Übersetzungs-Transformer",
        zh="T5-Small 翻译 Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Google T5-small model for English-to-{German, French, Romanian} "
            "translation using task prefixes. "
            "Download its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "Modelo T5-small de Google para traducción inglés-{alemán, francés, "
            "rumano} usando prefijos de tarea. "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "Modelo T5-small do Google para tradução inglês-{alemão, francês, "
            "romeno} usando prefixos de tarefa. "
            "Baixe seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Google T5-small-Modell für Englisch-zu-{Deutsch, Französisch, Rumänisch}-"
            "Übersetzung mit Aufgabenpräfixen. "
            "Lädt die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "谷歌 T5-small 模型，通过任务前缀实现英语到德语/法语/罗马尼亚语翻译。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#00695C"
    ICON: str = "Language"
    MODEL_NAME: str = "t5-small"
    DOWNLOAD_SIZE_BYTES: int = 486302401

    def __init__(self, model=None, pretrained_dir=None, **kwargs):
        kwargs = self.validate_and_transform(kwargs)

        from transformers import AutoTokenizer

        self.model_name = self._pretrained_source(pretrained_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        self.target_language = kwargs.get("target_language", "German")

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

    def _make_prefix(self) -> str:
        return f"translate English to {self.target_language}: "

    def tokenize_data(
        self, x: "DashAIDataset", y: Optional["DashAIDataset"] = None
    ) -> "DashAIDataset":
        """Prepend the T5 task prefix and tokenize source/target texts."""
        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        prefix = self._make_prefix()
        is_y = bool(y)
        if not y:
            y = DashAIDataset.from_list([{"foo": 0}] * len(x))

        dataset = []
        input_column_name = x.column_names[0]
        output_column_name = y.column_names[0] if is_y else None

        for i, input_sample in enumerate(x):
            text = prefix + input_sample[input_column_name]
            tokenized_input = self.tokenizer(
                text,
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
        """Fine-tune T5-small on the configured translation direction."""
        from transformers import Seq2SeqTrainer, Seq2SeqTrainingArguments

        from DashAI.back.models.hugging_face.metrics_callback import MetricsCallback

        dataset = self.tokenize_data(x_train, y_train)
        dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

        has_validation_data = x_validation is not None and y_validation is not None

        output_root = resolve_temp_checkpoint_dir(
            "DashAI/back/user_models/temp_checkpoints_t5_small"
        )
        output_root.mkdir(parents=True, exist_ok=True)
        run_output_dir = tempfile.mkdtemp(prefix="t5_small_", dir=str(output_root))

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
        """Translate from English to the configured target language."""
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

        translations = []
        for example in dataset:
            inputs = {
                k: v.unsqueeze(0).to(self.model.device) for k, v in example.items()
            }
            outputs = self.model.generate(**inputs)
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
            "target_language": self.target_language,
            "fitted": self.fitted,
        }
        config.save_pretrained(save_dir)

    @classmethod
    def load(cls, filename: Union[str, "Path"]):
        """Restore a T5SmallTransformer instance from disk."""
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
            target_language=custom_params.get("target_language", "German"),
            log_train_every_n_epochs=None,
            log_train_every_n_steps=None,
            log_validation_every_n_epochs=None,
            log_validation_every_n_steps=None,
        )
        loaded_model.fitted = custom_params.get("fitted", False)
        return loaded_model
