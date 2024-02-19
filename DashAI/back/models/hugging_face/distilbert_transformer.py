"""DashAI implementation of DistilBERT model for english classification."""
import shutil
from typing import Any, Callable, Dict

import numpy as np
from sklearn.exceptions import NotFittedError
from transformers import (
    DistilBertForSequenceClassification,
    DistilBertTokenizer,
    Trainer,
    TrainingArguments,
)

from DashAI.back.core.schema_fields import (
    BaseSchema,
    float_field,
    int_field,
    string_field,
)
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.models.text_classification_model import TextClassificationModel


class DistilBertTransformerSchema(BaseSchema):
    """Distilbert is a transformer that allows you to classify text in English.
    The implementation is based on huggingface distilbert-base in the case of
    the uncased model, i.e. distilbert-base-uncased.
    """

    num_train_epochs: int_field(
        description="Total number of training epochs to perform.", default=3, ge=1
    )
    batch_size: int_field(
        description="The batch size per GPU/TPU core/CPU for training",
        default=8,
        ge=1,
    )
    learning_rate: float_field(
        description="The initial learning rate for AdamW optimizer",
        default=5e-5,
        ge=0.0,
    )
    device: string_field(
        description="Hardware on which the training is run. If available, GPU is "
        "recommended for efficiency reasons. Otherwise, use CPU.",
        default="gpu",
        enum=["gpu", "cpu"],
    )
    weight_decay: float_field(
        description="Weight decay is a regularization technique used in training "
        "neural networks to prevent overfitting. In the context of the AdamW "
        "optimizer, the 'weight_decay' parameter is the rate at which the weights of "
        "all layers are reduced during training, provided that this rate is not zero.",
        default=0.0,
        ge=0.0,
    )


class DistilBertTransformer(TextClassificationModel):
    """Pre-trained transformer DistilBERT allowing English text classification.

    DistilBERT is a small, fast, cheap and light Transformer model trained by
    distilling BERT base.
    It has 40% less parameters than bert-base-uncased, runs 60% faster while preserving
    over 95% of BERT's performances as measured on the GLUE language understanding
    benchmark [1].

    References
    ----------
    [1] https://huggingface.co/docs/transformers/model_doc/distilbert
    """

    SCHEMA = DistilBertTransformerSchema

    def __init__(self, model=None, **kwargs):
        """Initialize the transformer model.

        The process includes the instantiation of the pre-trained model and the
        associated tokenizer.
        """
        kwargs = self.validate_and_transform(kwargs)
        self.model_name = "distilbert-base-uncased"
        self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_name)
        self.model = (
            model
            if model is not None
            else DistilBertForSequenceClassification.from_pretrained(self.model_name)
        )
        self.fitted = model is not None
        if model is None:
            self.training_args = kwargs
            self.batch_size = kwargs.pop("batch_size")
            self.device = kwargs.pop("device")

    def get_tokenizer(self, input_column: str, output_column: str) -> Callable:
        """Tokenize input and output.

        Parameters
        ----------
        input_column : str
            name the input column to be tokenized.
        output_column : str
            name the output column to be tokenized.

        Returns
        -------
        Function
            Function for batch tokenization of the dataset.
        """

        def _tokenize(batch) -> Dict[str, Any]:
            return {
                "input_ids": self.tokenizer(
                    batch[input_column],
                    padding="max_length",
                    truncation=True,
                    max_length=512,
                )["input_ids"],
                "attention_mask": self.tokenizer(
                    batch[input_column],
                    padding="max_length",
                    truncation=True,
                    max_length=512,
                )["attention_mask"],
                "labels": batch[output_column],
            }

        return _tokenize

    def fit(self, dataset: DashAIDataset):
        """Fine-tune the pre-trained model.

        Parameters
        ----------
        dataset : DashAIDataset
            DashAIDataset with training data.

        """
        input_column = dataset.inputs_columns[0]
        output_column = dataset.outputs_columns[0]

        tokenizer_func = self.get_tokenizer(input_column, output_column)
        dataset = dataset.map(tokenizer_func, batched=True, batch_size=self.batch_size)
        dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

        # Arguments for fine-tuning
        training_args = TrainingArguments(
            output_dir="DashAI/back/user_models/temp_checkpoints_distilbert",
            save_steps=1,
            save_total_limit=1,
            per_device_train_batch_size=self.batch_size,
            per_device_eval_batch_size=self.batch_size,
            no_cuda=self.device != "gpu",
            **self.training_args,
        )

        # The Trainer class is used for fine-tuning the model.
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
        )

        trainer.train()
        self.fitted = True
        shutil.rmtree(
            "DashAI/back/user_models/temp_checkpoints_distilbert", ignore_errors=True
        )

        return self

    def predict(self, dataset: DashAIDataset) -> np.array:
        """Make a prediction with the fine-tuned model.

        Parameters
        ----------
        dataset : DashAIDataset
            DashAIDataset with text data.

        Returns
        -------
        np.array
            Numpy array with the probabilities for each class.
        """
        if not self.fitted:
            raise NotFittedError(
                f"This {self.__class__.__name__} instance is not fitted yet. Call 'fit'"
                " with appropriate arguments before using this "
                "estimator."
            )

        input_column = dataset.inputs_columns[0]
        output_column = dataset.outputs_columns[0]
        tokenizer_func = self.get_tokenizer(input_column, output_column)
        dataset = dataset.map(tokenizer_func, batched=True, batch_size=self.batch_size)
        dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

        probabilities = []

        # Calculate the number of batches
        num_batches = len(dataset) // self.batch_size + (
            len(dataset) % self.batch_size > 0
        )

        # Iterate over each batch
        for i in range(num_batches):
            start_idx = i * self.batch_size
            end_idx = start_idx + self.batch_size

            # Extract the batch from the dataset
            batch = {
                "input_ids": dataset["input_ids"][start_idx:end_idx],
                "attention_mask": dataset["attention_mask"][start_idx:end_idx],
                "labels": dataset["labels"][start_idx:end_idx],
            }

            # Make sure that the tensors are in the correct device.
            batch = {k: v.to(self.model.device) for k, v in batch.items()}
            outputs = self.model(**batch)

            # Takes the model probability using softmax
            probs = outputs.logits.softmax(dim=-1)
            probabilities.extend(probs.detach().cpu().numpy())

        return np.array(probabilities)

    def save(self, filename: str) -> None:
        self.model.save_pretrained(filename)

    @classmethod
    def load(cls, filename: str) -> Any:
        model = DistilBertForSequenceClassification.from_pretrained(filename)
        return cls(model=model)
