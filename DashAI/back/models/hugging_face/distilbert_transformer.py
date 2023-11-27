"""DashAI implementation of DistilBERT model for english classification."""
import shutil
from typing import Any, Callable, Dict, Union

import numpy as np
from datasets import Dataset
from sklearn.exceptions import NotFittedError
from transformers import (
    DistilBertForSequenceClassification,
    DistilBertTokenizer,
    Trainer,
    TrainingArguments,
)

from DashAI.back.models.text_classification_model import TextClassificationModel


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

    def __init__(self, model=None, **kwargs):
        """Initialize the transformer model.

        The process includes the instantiation of the pre-trained model and the
        associated tokenizer.
        """
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

    def get_tokenizer(self, labels: Union[Dataset, None]) -> Callable:
        """Tokenize input and output.

        Parameters
        ----------
        labels:
            Dataset with the labels of the training data.

        Returns
        -------
        Function
            Function for batch tokenization of the dataset.
        """

        def _tokenize(batch, idx) -> Dict[str, Any]:
            return {
                "input_ids": self.tokenizer(
                    batch[idx],
                    padding="max_length",
                    truncation=True,
                    max_length=512,
                )["input_ids"],
                "attention_mask": self.tokenizer(
                    batch[idx],
                    padding="max_length",
                    truncation=True,
                    max_length=512,
                )["attention_mask"],
                "labels": labels[idx] if labels else None,
            }

        return _tokenize

    def fit(self, x: Dataset, y: Dataset):
        """Fine-tune the pre-trained model.

        Parameters
        ----------
        dataset : DashAIDataset
            DashAIDataset with training data.

        """

        tokenizer_func = self.get_tokenizer(y)
        dataset = x.map(
            tokenizer_func, batched=True, batch_size=self.batch_size, with_indices=True
        )
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

    def predict(self, x: Dataset) -> np.array:
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

        tokenizer_func = self.get_tokenizer()
        dataset = x.map(
            tokenizer_func, batched=True, batch_size=self.batch_size, with_indices=True
        )
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
