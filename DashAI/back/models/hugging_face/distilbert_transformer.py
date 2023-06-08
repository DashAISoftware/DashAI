import json

import numpy as np
from datasets import DatasetDict
from transformers import (
    DistilBertForSequenceClassification,
    DistilBertTokenizer,
    Trainer,
    TrainingArguments,
)

from DashAI.back.models.text_classification_model import TextClassificationModel


class DistilBertTransformer(TextClassificationModel):
    """
    Pre-trained transformer DistilBERT allowing English text classification
    """

    MODEL = "DistilBertTransformer"
    with open(f"DashAI/back/models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)

    def __init__(self):
        """
        Initialize the transformer class by calling the pretrained model and its
        tokenizer. Include an attribute analogous to sklearn's check_is_fitted to
        see if it was fine-tuned.
        """
        self.model_name = "distilbert-base-uncased"
        self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_name)
        self.model = DistilBertForSequenceClassification.from_pretrained(
            self.model_name
        )
        self.fitted = False

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

    def fit(self, dataset: DatasetDict):
        """Fine-tuning the pre-trained model

        Parameters
        ----------
        dataset : DatasetDict
            Datasetdict with training data

        """

        train_dataset = dataset["train"]
        input_column = train_dataset.inputs_columns[0]
        output_column = train_dataset.outputs_columns[0]

        tokenizer_func = self.get_tokenizer(input_column, output_column)
        train_dataset = train_dataset.map(
            tokenizer_func, batched=True, batch_size=len(train_dataset)
        )
        train_dataset.set_format(
            "torch", columns=["input_ids", "attention_mask", "labels"]
        )

        # Arguments for fine-tuning
        training_args = TrainingArguments(
            output_dir="DashAI/back/models/hugging_face/prueba",
            num_train_epochs=2,
            per_device_train_batch_size=32,
            weight_decay=0.01,
            save_steps=1,
        )

        # The Trainer class is used for fine-tuning the model.
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
        )

        trainer.train()
        self.fitted = True
        return

    def predict(self, dataset: DatasetDict):
        """Predicting with the fine-tuned model

        Parameters
        ----------
        dataset : DatasetDict
            Datasetdict with training data

        Returns
        -------
        Numpy Array
            Numpy array with the probabilities for each class
        """
        test_dataset = dataset["test"]
        input_column = test_dataset.inputs_columns[0]
        output_column = test_dataset.outputs_columns[0]
        tokenizer_func = self.get_tokenizer(input_column, output_column)
        test_dataset = test_dataset.map(
            tokenizer_func, batched=True, batch_size=len(test_dataset)
        )
        test_dataset.set_format(
            "torch", columns=["input_ids", "attention_mask", "labels"]
        )

        probabilities = []

        # Iterate over each batch in the dataset
        for batch in test_dataset:
            # Make sure that the tensors are in the correct device.
            batch = {k: v.to(self.model.device) for k, v in batch.items()}

            outputs = self.model(**batch)

            # Takes the model probability using softmax
            probs = outputs.logits.softmax(dim=-1)

            probabilities.extend(probs.detach().cpu().numpy())
        return np.array(probabilities)
