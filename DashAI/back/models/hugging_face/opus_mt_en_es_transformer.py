"""OpusMtEnESTransformer model for english-spanish translation DashAI implementation."""

import shutil
from typing import List, Optional

from datasets import Dataset
from sklearn.exceptions import NotFittedError
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

from DashAI.back.core.schema_fields import (
    BaseSchema,
    float_field,
    int_field,
    schema_field,
    string_field,
)
from DashAI.back.models.translation_model import TranslationModel


class OpusMtEnESTransformerSchema(BaseSchema):
    """opus-mt-en-es is a transformer pre-trained model that allows translation of
    texts from English to Spanish.
    """

    num_train_epochs: schema_field(
        int_field(ge=1),
        placeholder=1,
        description="Total number of training epochs to perform.",
    )  # type: ignore
    batch_size: schema_field(
        int_field(ge=1),
        placeholder=16,
        description="The batch size per GPU/TPU core/CPU for training",
    )  # type: ignore
    learning_rate: schema_field(
        float_field(ge=0.0),
        placeholder=2e-5,
        description="The initial learning rate for AdamW optimizer",
    )  # type: ignore
    device: schema_field(
        string_field(enum=["gpu", "cpu"]),
        placeholder="gpu",
        description="Hardware on which the training is run. If available, GPU is "
        "recommended for efficiency reasons. Otherwise, use CPU.",
    )  # type: ignore
    weight_decay: schema_field(
        float_field(ge=0.0),
        placeholder=0.01,
        description="Weight decay is a regularization technique used in training "
        "neural networks to prevent overfitting. In the context of the AdamW "
        "optimizer, the 'weight_decay' parameter is the rate at which the weights of "
        "all layers are reduced during training, provided that this rate is not zero.",
    )  # type: ignore


class OpusMtEnESTransformer(TranslationModel):
    """Pre-trained transformer for english-spanish translation.

    This model fine-tunes the pre-trained model opus-mt-en-es.
    """

    SCHEMA = OpusMtEnESTransformerSchema

    def __init__(self, model=None, **kwargs):
        """Initialize the transformer.

        This process includes the instantiation of the pre-trained model and the
        associated tokenizer.
        """
        kwargs = self.validate_and_transform(kwargs)
        self.model_name = "Helsinki-NLP/opus-mt-en-es"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if model is None:
            self.training_args = kwargs
            self.batch_size = kwargs.pop("batch_size", 16)
            self.device = kwargs.pop("device", "gpu")
        self.model = (
            model
            if model is not None
            else AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        )
        self.fitted = model is not None

    def tokenize_data(self, x: Dataset, y: Optional[Dataset] = None) -> Dataset:
        """Tokenize input and output.

        Parameters
        ----------
        x: Dataset
            Dataset with the input data to preprocess.
        y: Optional Dataset
            Dataset with the output data to preprocess.

        Returns
        -------
        Dataset
            Dataset with the processed data.
        """
        is_y = bool(y)
        if not y:
            y = Dataset.from_list([{"foo": 0}] * len(x))
        # Initialize useful variables
        dataset = []
        input_column_name = x.column_names[0]
        output_column_name = y.column_names[0]

        # Preprocess both datasets
        for input_sample, output_sample in zip(x, y):  # noqa
            tokenized_input = self.tokenizer(
                input_sample[input_column_name],
                truncation=True,
                padding="max_length",
                max_length=512,
            )
            tokenized_output = (
                self.tokenizer(
                    output_sample[output_column_name],
                    truncation=True,
                    padding="max_length",
                    max_length=512,
                )
                if is_y
                else None
            )
            sample = {
                "input_ids": tokenized_input["input_ids"],
                "attention_mask": tokenized_input["attention_mask"],
                "labels": tokenized_output["input_ids"]
                if is_y
                else y[output_column_name],
            }
            dataset.append(sample)
        return Dataset.from_list(dataset)

    def fit(self, x_train: Dataset, y_train: Dataset):
        """Fine-tune the pre-trained model.

        Parameters
        ----------
        x_train : Dataset
            Dataset with input training data.
        y_train : Dataset
            Dataset with output training data.

        """

        dataset = self.tokenize_data(x_train, y_train)
        dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

        # Arguments for fine-tuning
        training_args = Seq2SeqTrainingArguments(
            output_dir="DashAI/back/user_models/temp_checkpoints_opus-mt-en-es",
            save_steps=1,
            save_total_limit=1,
            per_device_train_batch_size=self.batch_size,
            per_device_eval_batch_size=self.batch_size,
            no_cuda=self.device != "gpu",
            **self.training_args,
        )

        # The Trainer class is used for fine-tuning the model.
        trainer = Seq2SeqTrainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
        )

        trainer.train()
        self.fitted = True
        shutil.rmtree(
            "DashAI/back/user_models/temp_checkpoints_opus-mt-en-es", ignore_errors=True
        )
        return self

    def predict(self, x_pred: Dataset) -> List:
        """Predict with the fine-tuned model.

        Parameters
        ----------
        x_pred : Dataset
            Dataset with text data.

        Returns
        -------
        List
            list of translations made by the model.
        """
        if not self.fitted:
            raise NotFittedError(
                f"This {self.__class__.__name__} instance is not fitted yet. Call 'fit'"
                " with appropriate arguments before using this "
                "estimator."
            )

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

    def save(self, filename=None):
        self.model.save_pretrained(filename)

    @classmethod
    def load(cls, filename):
        model = AutoModelForSeq2SeqLM.from_pretrained(filename)
        return cls(model=model)
