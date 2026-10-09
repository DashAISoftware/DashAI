"""Shared base class for Helsinki-NLP Opus-MT translation transformers."""

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Union

from sklearn.exceptions import NotFittedError

from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin
from DashAI.back.models.translation_model import TranslationModel
from DashAI.back.models.utils import (
    GPU_OR_CPU_PLACEHOLDER,
    resolve_temp_checkpoint_dir,
)

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class OpusMtTransformerMixin(HFDownloadableMixin, TranslationModel):
    """Shared implementation for Helsinki-NLP Opus-MT translation wrappers.

    Subclasses must define ``MODEL_NAME`` (the HuggingFace checkpoint ID) and
    ``SCHEMA``. ``TEMP_CHECKPOINT_DIR`` defaults to a generic path but should
    be overridden with a model specific directory to avoid collisions between
    concurrent training runs of different language pairs.

    All seq2seq training, tokenization, inference, save, and load logic lives
    here so each language-pair subclass only needs to set class attributes.

    .. note::
        For fresh training the pretrained weights must be downloaded first via
        ``download()`` (this component requires a download). ``__init__`` with
        no ``pretrained_dir`` loads the tokenizer and model from the
        component's local download folder; it does not fetch from the Hugging
        Face Hub. When loading a previously saved run, ``pretrained_dir`` is
        set to the run directory so the tokenizer is read from there, making
        trained runs self-contained.
    """

    MODEL_NAME: str = ""
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_opus_mt"
    # Marian Opus-MT checkpoints are ~300 MB; declared statically for the UI.
    DOWNLOAD_SIZE_BYTES: int = 300_000_000

    @classmethod
    def hf_repos(cls):
        """Derive the single HuggingFace repo from the subclass MODEL_NAME.

        Returns
        -------
        list of tuple of (str, str)
            A single ``(repo_id, repo_type)`` pair derived from ``MODEL_NAME``,
            or an empty list when ``MODEL_NAME`` is not set.
        """
        return [(cls.MODEL_NAME, "model")] if cls.MODEL_NAME else []

    def __init__(self, model=None, pretrained_dir: Optional[str] = None, **kwargs):
        """Initialize tokenizer and seq2seq model.

        Parameters
        ----------
        model : transformers.PreTrainedModel or None
            Preloaded model to reuse instead of downloading weights.
        pretrained_dir : str or None
            Directory from which to load the tokenizer (and model weights when
            ``model`` is ``None``). When ``None`` the component's download
            folder is used, which is the correct path for fresh training. Pass
            the run directory when restoring a saved run so the trained run
            becomes self-contained and independent of the download folder.
        **kwargs
            Training hyperparameters forwarded to ``validate_and_transform``.
        """
        kwargs = self.validate_and_transform(kwargs)

        from transformers import AutoTokenizer

        if not self.MODEL_NAME:
            raise ValueError(
                f"{self.__class__.__name__} must define a non-empty MODEL_NAME."
            )

        self.model_name = self.MODEL_NAME
        source = pretrained_dir or str(self._repo_dir(self.MODEL_NAME))
        self.tokenizer = AutoTokenizer.from_pretrained(source)

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

            self.model = AutoModelForSeq2SeqLM.from_pretrained(source)
        else:
            self.model = model

        self.num_train_epochs = self.training_args.get("num_train_epochs", 2)
        self.fitted = model is not None

    def tokenize_data(
        self, x: "DashAIDataset", y: Optional["DashAIDataset"] = None
    ) -> "DashAIDataset":
        """Tokenize source (and optionally target) dataset for seq2seq training."""
        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

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
        """Fine-tune the Opus-MT model on translation data."""
        from transformers import Seq2SeqTrainer, Seq2SeqTrainingArguments

        from DashAI.back.models.hugging_face.metrics_callback import MetricsCallback

        dataset = self.tokenize_data(x_train, y_train)
        dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

        has_validation_data = x_validation is not None and y_validation is not None

        output_root = resolve_temp_checkpoint_dir(self.TEMP_CHECKPOINT_DIR)
        output_root.mkdir(parents=True, exist_ok=True)
        run_output_dir = tempfile.mkdtemp(
            prefix=f"{self.__class__.__name__.lower()}_",
            dir=str(output_root),
        )

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
        """Translate source texts using the fine-tuned model."""
        if not self.fitted:
            raise NotFittedError(
                f"This {self.__class__.__name__} instance is not fitted yet. "
                "Call 'train' with appropriate arguments before using this estimator."
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
        """Return the dataset unchanged (no preprocessing required)."""
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
            "fitted": self.fitted,
        }
        config.save_pretrained(save_dir)

    @classmethod
    def load(cls, filename: Union[str, "Path"]):
        """Restore a model instance from disk."""
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
            log_train_every_n_epochs=None,
            log_train_every_n_steps=None,
            log_validation_every_n_epochs=None,
            log_validation_every_n_steps=None,
        )
        loaded_model.fitted = custom_params.get("fitted", False)
        return loaded_model
