import json
import shutil

import numpy as np
from datasets import DatasetDict
from sklearn.exceptions import NotFittedError
from transformers import (
    Trainer,
    TrainingArguments,
    ViTFeatureExtractor,
    ViTForImageClassification,
)

from DashAI.back.models.base_model import BaseModel
from DashAI.back.models.image_classification_model import ImageClassificationModel


class ViTTransformer(BaseModel, ImageClassificationModel):
    """
    Pre-trained transformer ViT allowing image classification
    """

    @classmethod
    def get_schema(cls):
        with open("DashAI/back/models/parameters/models_schemas/ViT.json") as f:
            cls.SCHEMA = json.load(f)
        return cls.SCHEMA

    def __init__(self, model=None, **kwargs):
        """
        Initialize the transformer class by calling the pretrained model and its
        feature extractor. Include an attribute analogous to sklearn's check_is_fitted
        to see if it was fine-tuned.
        """
        self.model_name = "google/vit-base-patch16-224"
        self.feature_extractor = ViTFeatureExtractor.from_pretrained(self.model_name)
        self.model = (
            model
            if model is not None
            else ViTForImageClassification.from_pretrained(self.model_name)
        )
        self.fitted = True if model is not None else False
        self.training_args = kwargs

    def get_preprocess_images(self, input_column: str, output_column: str):
        def preprocess_images(examples):
            inputs = self.feature_extractor(
                images=examples[input_column], return_tensors="pt", size=224
            )
            inputs["labels"] = examples[output_column]
            return inputs

        return preprocess_images

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

        feature_extractor_func = self.get_preprocess_images(input_column, output_column)
        train_dataset = train_dataset.map(feature_extractor_func, batched=True)

        # Arguments for fine-tuning
        training_args = TrainingArguments(
            output_dir="DashAI/back/user_models/temp_checkpoints_vit",
            save_steps=1,
            save_total_limit=1,
            **self.training_args,
        )

        # The Trainer class is used for fine-tuning the model.
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
        )

        trainer.train()
        self.fitted = True
        shutil.rmtree(
            "DashAI/back/user_models/temp_checkpoints_vit", ignore_errors=True
        )
        return

    def predict(self, dataset: DatasetDict, validation: bool = False):
        """
        Make a prediction with the fine-tuned model

        Parameters
        ----------
        dataset : DatasetDict
            Datasetdict with image data
        validation : bool
            boolean that defines if the model use validation or testing dataset

        Returns
        -------
        Numpy Array
            Numpy array with the probabilities for each class
        """
        if not self.fitted:
            raise NotFittedError(
                f"This {self.__class__.__name__} instance is not fitted yet. Call 'fit'"
                " with appropriate arguments before using this estimator."
            )

        if validation:
            test_dataset = dataset["validation"]
        else:
            test_dataset = dataset["test"]

        preprocess_images = self.get_preprocess_images("image", "label")
        test_dataset = test_dataset.map(preprocess_images, batched=True, batch_size=8)
        test_dataset.set_format("torch", columns=["pixel_values", "labels"])

        probabilities = []

        # Iterate over each batch in the dataset
        for i in range(len(test_dataset)):
            # Prepare a batch of images for the model
            batch = test_dataset[i]

            # Make sure that the tensors are in the correct device.
            batch = {k: v.to(self.model.device) for k, v in batch.items()}

            if batch["pixel_values"].dim() == 3:
                batch["pixel_values"] = batch["pixel_values"].unsqueeze(0)

            outputs = self.model(**batch)

            # Takes the model probability using softmax
            probs = outputs.logits.softmax(dim=-1)

            probabilities.extend(probs.detach().cpu().numpy())

        return np.array(probabilities)

    def save(self, filename=None):
        self.model.save_pretrained(filename)

    @classmethod
    def load(cls, filename):
        model = ViTForImageClassification.from_pretrained(filename)
        return cls(model=model)
