"""Shared classes for Hugging Face text classification transformers.

This module defines the common implementation used by DashAI wrappers around
Hugging Face sequence classification models (for example DistilBERT,
DeBERTa-v3, and ModernBERT). It centralizes tokenizer/model initialization,
dataset preparation, training, prediction, and model persistence logic.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from sklearn.exceptions import NotFittedError

from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin
from DashAI.back.models.text_classification_model import TextClassificationModel
from DashAI.back.models.utils import (
    GPU_OR_CPU_PLACEHOLDER,
    resolve_temp_checkpoint_dir,
)
from DashAI.back.types.categorical import Categorical

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class HuggingFaceTextClassificationTransformer(
    HFDownloadableMixin, TextClassificationModel
):
    """Base implementation for Hugging Face text classification wrappers.

    Subclasses are expected to define at least ``MODEL_NAME`` and optionally
    override class attributes such as ``MAX_TOKEN_LENGTH`` and
    ``TEMP_CHECKPOINT_DIR``. The class provides:

    - Automatic tokenizer and model loading from Hugging Face Hub.
    - Training via ``transformers.Trainer`` with DashAI metric callbacks.
    - Inference returning per class probability matrices.
    - Save/load utilities that preserve custom training parameters.

    .. note::
        The pretrained weights must be downloaded from the Hugging Face Hub
        (internet access required) before the model can be used.
    """

    MODEL_NAME: str = ""
    TEMP_CHECKPOINT_DIR: str = (
        "DashAI/back/user_models/temp_checkpoints_hf_text_classification"
    )
    MAX_TOKEN_LENGTH: int = 512
    # Approximate on-disk size of the pretrained checkpoint; subclasses override
    # with a value closer to their specific model for the download UI.
    DOWNLOAD_SIZE_BYTES: int = 450_000_000

    @classmethod
    def hf_repos(cls):
        """Derive the single HuggingFace repo from the subclass ``MODEL_NAME``.

        Returns
        -------
        list of tuple of (str, str)
            A single ``(repo_id, repo_type)`` pair derived from ``MODEL_NAME``,
            or an empty list when ``MODEL_NAME`` is not set.
        """
        return [(cls.MODEL_NAME, "model")] if cls.MODEL_NAME else []

    def _pretrained_source(self, pretrained_dir: Optional[str]) -> str:
        """Resolve where to load the tokenizer and weights from.

        Prefers an explicit ``pretrained_dir`` (a saved run), then the local
        component download folder when the weights are present, and finally
        falls back to the Hugging Face Hub repo id. Downloading is enforced by
        the run/session gates before real use; the Hub fallback keeps direct
        instantiation working when nothing has been downloaded.

        Parameters
        ----------
        pretrained_dir : str or None
            Directory of a previously saved run, if any.

        Returns
        -------
        str
            A path or repo id accepted by ``from_pretrained``.
        """
        if pretrained_dir:
            return pretrained_dir
        try:
            if self.is_downloaded():
                return str(self._repo_dir(self.MODEL_NAME))
        except Exception:
            pass
        return self.MODEL_NAME

    def __init__(self, model=None, pretrained_dir: Optional[str] = None, **kwargs):
        """Initialize the transformer model.

        The process includes the instantiation of the pretrained model and the
        associated tokenizer. When ``model`` is ``None`` a fresh pretrained
        model checkpoint is loaded from HuggingFace; when a model object
        is supplied the tokenizer is reused without redownloading weights.

        Parameters
        ----------
        model : transformers.PreTrainedModel or None, optional
            An already loaded HuggingFace model to reuse. If ``None`,
            the model will be loaded from the Hugging Face Hub based on
            ``MODEL_NAME``.
        **kwargs : dict
            Additional hyperparameters forwarded to ``validate_and_transform``
            and used to configure training arguments (e.g. ``num_labels``,
            ``batch_size``, ``epochs``).
        """

        self.num_labels = kwargs.pop("num_labels", None)
        kwargs.pop("model_name", None)

        kwargs = self.validate_and_transform(kwargs)

        from transformers import AutoTokenizer

        if not self.MODEL_NAME:
            raise ValueError(
                f"{self.__class__.__name__} must define a non-empty MODEL_NAME."
            )

        self.model_name = self._pretrained_source(pretrained_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        self.log_train_every_n_epochs = kwargs.get("log_train_every_n_epochs", 1)
        self.log_train_every_n_steps = kwargs.get("log_train_every_n_steps", None)
        self.log_validation_every_n_epochs = kwargs.get(
            "log_validation_every_n_epochs", 1
        )
        self.log_validation_every_n_steps = kwargs.get(
            "log_validation_every_n_steps", None
        )

        self.training_args_params = {
            "num_train_epochs": kwargs.get("num_train_epochs", 2),
            "learning_rate": kwargs.get("learning_rate", 5e-5),
            "weight_decay": kwargs.get("weight_decay", 0.01),
        }
        self.batch_size = kwargs.get("batch_size", 16)
        self.device = kwargs.get("device") or GPU_OR_CPU_PLACEHOLDER

        if model is not None:
            self.model = model
            if self.num_labels is not None and hasattr(self.model, "config"):
                self.model.config.num_labels = self.num_labels
                if self.num_labels > 1:
                    self.model.config.problem_type = "single_label_classification"
        else:
            from transformers import AutoConfig, AutoModelForSequenceClassification

            model_config = AutoConfig.from_pretrained(self.model_name)
            if self.num_labels is not None:
                model_config.num_labels = self.num_labels
                if self.num_labels > 1:
                    model_config.problem_type = "single_label_classification"
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name, config=model_config
            )

        self.fitted = False
        self.encodings = {}  # Store encodings for categorical columns

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        """Fine-tune the model on the provided classification data.

        Parameters
        ----------
        x_train : DashAIDataset
            Input text features for training.
        y_train : DashAIDataset
            Target labels for training.
        x_validation : DashAIDataset
            Input text features for validation.
        y_validation : DashAIDataset
            Target labels for validation.

        Returns
        -------
        HuggingFaceTextClassificationTransformer
            The fine-tuned model instance.
        """
        import shutil
        import tempfile

        import torch
        from transformers import (
            AutoConfig,
            AutoModelForSequenceClassification,
            DataCollatorWithPadding,
            Trainer,
            TrainingArguments,
        )

        from DashAI.back.models.hugging_face.metrics_callback import MetricsCallback

        output_column_name = y_train.column_names[0]

        if self.num_labels is None:
            self.num_labels = len(y_train.unique(output_column_name))
            config = AutoConfig.from_pretrained(
                self.model_name, num_labels=self.num_labels
            )
            if self.num_labels > 1:
                config.problem_type = "single_label_classification"
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name, config=config
            )

        x_train_prepared = self.prepare_dataset(x_train, is_fit=True)
        y_train_prepared = self.prepare_dataset(y_train, is_fit=True)
        train_dataset = x_train_prepared.add_column(
            "label", y_train_prepared[output_column_name]
        )

        has_validation_data = x_validation is not None and y_validation is not None
        validation_dataset = None
        if has_validation_data:
            x_validation_prepared = self.prepare_dataset(x_validation)
            y_validation_prepared = self.prepare_dataset(y_validation)
            validation_dataset = x_validation_prepared.add_column(
                "label", y_validation_prepared[output_column_name]
            )

        num_epochs = self.training_args_params.get("num_train_epochs", 2)
        use_gpu = self.device.lower() == "gpu"
        can_use_fp16 = torch.cuda.is_available() and use_gpu

        base_output_dir = resolve_temp_checkpoint_dir(self.TEMP_CHECKPOINT_DIR)
        base_output_dir.mkdir(parents=True, exist_ok=True)
        run_output_dir = tempfile.mkdtemp(
            prefix=f"{self.__class__.__name__.lower()}_",
            dir=str(base_output_dir),
        )

        training_args_obj = TrainingArguments(
            output_dir=run_output_dir,
            save_strategy="epoch",
            per_device_train_batch_size=self.batch_size,
            per_device_eval_batch_size=self.batch_size,
            eval_strategy="no",
            use_cpu=not use_gpu,
            fp16=can_use_fp16,
            **self.training_args_params,
        )

        data_collator = DataCollatorWithPadding(tokenizer=self.tokenizer)

        metrics_callback = MetricsCallback(
            model_instance=self,
            x_train=x_train,
            y_train=y_train,
            x_val=x_validation,
            y_val=y_validation,
            total_epochs=num_epochs,
            log_training_every_n_epochs=self.log_train_every_n_epochs,
            log_training_every_n_steps=self.log_train_every_n_steps,
            log_val_every_n_epochs=(
                self.log_validation_every_n_epochs if has_validation_data else None
            ),
            log_val_every_n_steps=(
                self.log_validation_every_n_steps if has_validation_data else None
            ),
        )

        trainer = Trainer(
            model=self.model,
            args=training_args_obj,
            train_dataset=train_dataset,
            eval_dataset=validation_dataset,
            data_collator=data_collator,
            callbacks=[metrics_callback],
        )

        self.fitted = True
        try:
            trainer.train()
        finally:
            shutil.rmtree(run_output_dir, ignore_errors=True)

        return self

    def predict(self, x_pred: "DashAIDataset"):
        """Predict with the fine-tuned model.

        Parameters
        ----------
        x_pred : DashAIDataset
            Dataset with text data.

        Returns
        -------
        List
            List of predicted probabilities for each class.
        """

        if not self.fitted:
            raise NotFittedError(
                f"This {self.__class__.__name__} instance is not fitted yet. Call 'fit'"
                " with appropriate arguments before using this estimator."
            )

        pred_dataset = self.prepare_dataset(x_pred)

        import numpy as np
        from torch.utils.data import DataLoader
        from transformers import DataCollatorWithPadding

        data_collator = DataCollatorWithPadding(tokenizer=self.tokenizer)
        text_columns = [col for col in x_pred.column_names if col != "label"]
        if len(text_columns) != 1:
            raise ValueError(f"Expected exactly one text column, found: {text_columns}")

        pred_loader = DataLoader(
            pred_dataset.remove_columns(text_columns[0]),
            batch_size=self.batch_size,
            collate_fn=data_collator,
        )

        probabilities = []

        for batch in pred_loader:
            inputs = {
                k: v.to(self.model.device) for k, v in batch.items() if k != "labels"
            }

            outputs = self.model(**inputs)
            probs = outputs.logits.softmax(dim=-1)
            probabilities.append(probs.detach().cpu().numpy())

        return np.vstack(probabilities)

    def prepare_dataset(
        self, dataset: "DashAIDataset", is_fit: bool = False
    ) -> "DashAIDataset":
        """Apply the model transformations to the dataset.

        Parameters
        ----------
        dataset : DashAIDataset
            The dataset to be transformed.
        is_fit : bool
            Whether this is for fitting (True) or prediction (False).

        Returns
        -------
        DashAIDataset
            The prepared dataset ready to be converted to
            an accepted format in the model.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset_utils import (
            apply_categorical_label_encoder,
            categorical_label_encoder,
        )

        has_categorical = any(
            isinstance(col_type, Categorical) for col_type in dataset.types.values()
        )

        if has_categorical:
            if is_fit:
                dataset, encodings = categorical_label_encoder(dataset)
                self.encodings.update(encodings)
            else:
                dataset = apply_categorical_label_encoder(dataset, self.encodings)
            return dataset

        return self.tokenize_data(dataset)

    def tokenize_data(self, dataset: "DashAIDataset") -> "DashAIDataset":
        """Tokenize the input data.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset with the input data to preprocess.

        Returns
        -------
        DashAIDataset
            Dataset with the tokenized input data.
        """
        text_columns = [
            col
            for col in dataset.column_names
            if not isinstance(dataset.types.get(col), Categorical)
        ]
        if len(text_columns) != 1:
            raise ValueError(f"Expected exactly one text column, found: {text_columns}")

        return dataset.map(
            lambda batch: self.tokenizer(
                batch[text_columns[0]],
                truncation=True,
                padding=True,
                max_length=self.MAX_TOKEN_LENGTH,
            ),
            batched=True,
        )

    def save(self, filename: Union[str, "Path"]) -> None:
        """Store the fine-tuned model and its configuration to disk.

        Saves the model weights via ``save_pretrained`` and embeds the
        hyperparameters (epochs, batch size, learning rate, etc.) into the
        Hugging Face config so they can be restored by :meth:`load`.

        Parameters
        ----------
        filename : str or Path
            Directory path where the model files will be written.
        """
        from transformers import AutoConfig

        save_dir = Path(filename)
        if save_dir.exists() and save_dir.is_file():
            save_dir.unlink()
        save_dir.mkdir(parents=True, exist_ok=True)

        self.model.save_pretrained(save_dir)
        # Persist the tokenizer alongside the weights so a saved run is
        # self-contained and does not depend on the component download folder.
        self.tokenizer.save_pretrained(save_dir)
        config = AutoConfig.from_pretrained(save_dir)
        config.custom_params = {
            "num_train_epochs": self.training_args_params.get("num_train_epochs"),
            "batch_size": self.batch_size,
            "learning_rate": self.training_args_params.get("learning_rate"),
            "device": self.device,
            "weight_decay": self.training_args_params.get("weight_decay"),
            "num_labels": self.num_labels,
            "fitted": self.fitted,
        }
        config.save_pretrained(save_dir)

    @classmethod
    def load(
        cls, filename: Union[str, "Path"]
    ) -> "HuggingFaceTextClassificationTransformer":
        """Restore a HuggingFaceTextClassificationTransformer instance from disk.

        Reads the Hugging Face config to recover the custom hyperparameters
        saved by :meth:`save`, then reconstructs the model and wraps it in a
        new :class:`HuggingFaceTextClassificationTransformer` instance.

        Parameters
        ----------
        filename : str or Path
            Directory path from which the model files will be read.

        Returns
        -------
        HuggingFaceTextClassificationTransformer
            The restored model instance with ``fitted`` set to the persisted
            value.
        """
        from transformers import AutoConfig, AutoModelForSequenceClassification

        config = AutoConfig.from_pretrained(filename)
        custom_params = getattr(config, "custom_params", {})

        model = AutoModelForSequenceClassification.from_pretrained(
            filename, num_labels=custom_params.get("num_labels")
        )

        loaded_model = cls(
            model=model,
            pretrained_dir=str(filename),
            num_labels=custom_params.get("num_labels"),
            num_train_epochs=custom_params.get("num_train_epochs", 2),
            batch_size=custom_params.get("batch_size", 16),
            learning_rate=custom_params.get("learning_rate", 5e-5),
            device=custom_params.get("device", GPU_OR_CPU_PLACEHOLDER),
            weight_decay=custom_params.get("weight_decay", 0.01),
            log_train_every_n_epochs=None,
            log_train_every_n_steps=None,
            log_validation_every_n_epochs=None,
            log_validation_every_n_steps=None,
        )
        loaded_model.fitted = custom_params.get("fitted", False)
        return loaded_model
