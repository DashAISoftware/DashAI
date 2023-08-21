import shutil
from typing import List

from sklearn.exceptions import NotFittedError
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.models.translation_model import TranslationModel


class OpusMtEnESTransformer(TranslationModel):
    """
    Pre-trained transformer opus-mt-en-es allowing to translate english texts
    to spanish.
    """

    def __init__(self, model=None, **kwargs):
        """
        Initialize the transformer class by calling the pretrained model and its
        tokenizer. Include an attribute analogous to sklearn's check_is_fitted to
        see if it was fine-tuned.
        """
        self.model_name = "Helsinki-NLP/opus-mt-en-es"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if model is None:
            self.training_args = kwargs
            self.batch_size = kwargs.pop("batch_size")
            self.device = kwargs.pop("device")
        self.model = (
            model
            if model is not None
            else AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        )
        self.fitted = model is not None

    def fit(self, dataset: DashAIDataset):
        """Fine-tune the pre-trained model.

        Parameters
        ----------
        dataset : DashAIDataset
            DashAIDataset with training data.

        """

        input_column = dataset.inputs_columns[0]
        output_column = dataset.outputs_columns[0]

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

        dataset = dataset.map(tokenize, batched=True)
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

    def predict(self, dataset: DashAIDataset) -> List:
        """Predict with the fine-tuned model.

        Parameters
        ----------
        dataset : DashAIDataset
            DashAIDataset with text data.

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

        input_column = dataset.inputs_columns[0]

        def encode(examples):
            return self.tokenizer(
                examples[input_column],
                truncation=True,
                padding="max_length",
                max_length=512,
            )

        dataset = dataset.map(encode, batched=True)
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
