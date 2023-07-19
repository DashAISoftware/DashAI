import json
import shutil

import numpy as np
from sklearn.exceptions import NotFittedError
from transformers import (
    DistilBertForSequenceClassification,
    DistilBertTokenizer,
    Trainer,
    TrainingArguments,
)

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.models.text_classification_model import TextClassificationModel


class DistilBertTransformer(TextClassificationModel):
    """
    Pre-trained transformer DistilBERT allowing English text classification
    """

    @classmethod
    def get_schema(cls):
        with open("DashAI/back/models/parameters/models_schemas/DistilBERT.json") as f:
            cls.SCHEMA = json.load(f)
        return cls.SCHEMA

    def __init__(self, model=None, **kwargs):
        """
        Initialize the transformer class by calling the pretrained model and its
        tokenizer. Include an attribute analogous to sklearn's check_is_fitted to
        see if it was fine-tuned.
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

    def get_tokenizer(self, input_column: str, output_column: str):
        """Tokenize input and output

        Parameters
        ----------
        input_column : str
            name the input column to be tokenized
        output_column : str
            name the output column to be tokenized

        Returns
        -------
        Function
            Function for batch tokenization of the dataset
        """

        def tokenize(batch):
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

        return tokenize

    def fit(self, dataset: DashAIDataset):
        """Fine-tuning the pre-trained model

        Parameters
        ----------
        dataset : DashAIDataset
            DashAIDataset with training data

        """

        input_column = dataset.inputs_columns[0]
        output_column = dataset.outputs_columns[0]

        tokenizer_func = self.get_tokenizer(input_column, output_column)
        dataset = dataset.map(tokenizer_func, batched=True, batch_size=8)
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

    def predict(self, dataset: DashAIDataset):
        """Predicting with the fine-tuned model

        Parameters
        ----------
        dataset : DashAIDataset
            DashAIDataset with training data

        Returns
        -------
        Numpy Array
            Numpy array with the probabilities for each class
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
        dataset = dataset.map(tokenizer_func, batched=True, batch_size=len(dataset))
        dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

        probabilities = []

        # Iterate over each batch in the dataset
        for batch in dataset:
            # Make sure that the tensors are in the correct device.
            batch = {k: v.to(self.model.device) for k, v in batch.items()}

            outputs = self.model(**batch)

            # Takes the model probability using softmax
            probs = outputs.logits.softmax(dim=-1)

            probabilities.extend(probs.detach().cpu().numpy())
        return np.array(probabilities)

    def save(self, filename=None):
        self.model.save_pretrained(filename)

    @classmethod
    def load(cls, filename):
        model = DistilBertForSequenceClassification.from_pretrained(filename)
        return cls(model=model)
