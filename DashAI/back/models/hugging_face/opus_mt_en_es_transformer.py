import json
import shutil

from datasets import DatasetDict
from sklearn.exceptions import NotFittedError
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

from DashAI.back.models.base_model import BaseModel
from DashAI.back.models.translation_model import TranslationModel


class OpusMtEnESTransformer(BaseModel, TranslationModel):
    """
    Pre-trained transformer opus-mt-en-es allowing to translate english texts to spanish
    """

    @classmethod
    def get_schema(cls):
        with open(
            "DashAI/back/models/parameters/models_schemas/opus-mt-en-es.json"
        ) as f:
            cls.SCHEMA = json.load(f)
        return cls.SCHEMA

    def __init__(self, model=None, **kwargs):
        """
        Initialize the transformer class by calling the pretrained model and its
        tokenizer. Include an attribute analogous to sklearn's check_is_fitted to
        see if it was fine-tuned.
        """
        self.model_name = "Helsinki-NLP/opus-mt-en-es"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = (
            model
            if model is not None
            else AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        )
        self.fitted = True if model is not None else False
        self.training_args = kwargs

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

        def tokenize(examples):
            model_inputs = self.tokenizer(
                examples[input_column],
                truncation=True,
                padding="longest",
                return_tensors="pt",
            )
            labels = self.tokenizer(
                text_target=examples[output_column], truncation=True
            )
            model_inputs["labels"] = labels["input_ids"]
            return model_inputs

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

        def tokenize(examples):
            inputs = self.tokenizer(
                examples[input_column],
                truncation=True,
                padding="max_length",
                max_length=512,
            )
            outputs = self.tokenizer(
                examples[output_column],
                truncation=True,
                padding="max_length",
                max_length=512,
            )
            inputs["labels"] = outputs["input_ids"]
            return inputs

        train_dataset = train_dataset.map(tokenize, batched=True)
        train_dataset.set_format(
            "torch", columns=["input_ids", "attention_mask", "labels"]
        )

        # Arguments for fine-tuning
        training_args = Seq2SeqTrainingArguments(
            output_dir="DashAI/back/user_models/temp_checkpoints_opus-mt-en-es",
            save_steps=1,
            save_total_limit=1,
            **self.training_args,
        )

        # The Trainer class is used for fine-tuning the model.
        trainer = Seq2SeqTrainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
        )

        trainer.train()
        self.fitted = True
        shutil.rmtree(
            "DashAI/back/user_models/temp_checkpoints_opus-mt-en-es", ignore_errors=True
        )
        return

    def predict(self, dataset: DatasetDict, validation=False):
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
        if not self.fitted:
            raise NotFittedError(
                f"This {self.__class__.__name__} instance is not fitted yet. Call 'fit'"
                " with appropriate arguments before using this "
                "estimator."
            )
        if validation:
            test_dataset = dataset["validation"]
        else:
            test_dataset = dataset["test"]

        input_column = test_dataset.inputs_columns[0]

        def encode(examples):
            return self.tokenizer(
                examples[input_column],
                truncation=True,
                padding="max_length",
                max_length=512,
            )

        test_dataset = test_dataset.map(encode, batched=True)
        test_dataset.set_format(type="torch", columns=["input_ids", "attention_mask"])

        translations = []

        for example in test_dataset:
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
