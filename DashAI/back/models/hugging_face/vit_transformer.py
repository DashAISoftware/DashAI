"""DashAI implementation of DistilBERT model for image classification."""

import shutil
from typing import Optional

import numpy as np
from datasets import Dataset
from sklearn.exceptions import NotFittedError
from transformers import (
    Trainer,
    TrainingArguments,
    ViTFeatureExtractor,
    ViTForImageClassification,
)

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.models.image_classification_model import ImageClassificationModel


class ViTTransformerSchema(BaseSchema):
    """ViT is a transformer that allows you to classify text in English."""

    num_train_epochs: schema_field(
        int_field(ge=1),
        placeholder=3,
        description="Total number of training epochs to perform.",
    )  # type: ignore
    batch_size: schema_field(
        int_field(ge=1),
        placeholder=8,
        description="The batch size per GPU/TPU core/CPU for training",
    )  # type: ignore
    learning_rate: schema_field(
        float_field(ge=0.0),
        placeholder=5e-5,
        description="The initial learning rate for AdamW optimizer",
    )  # type: ignore
    device: schema_field(
        enum_field(enum=["gpu", "cpu"]),
        placeholder="gpu",
        description="Hardware on which the training is run. If available, GPU is "
        "recommended for efficiency reasons. Otherwise, use CPU.",
    )  # type: ignore
    weight_decay: schema_field(
        float_field(ge=0.0),
        placeholder=0.0,
        description="Weight decay is a regularization technique used in training "
        "neural networks to prevent overfitting. In the context of the AdamW "
        "optimizer, the 'weight_decay' parameter is the rate at which the weights of "
        "all layers are reduced during training, provided that this rate is not zero.",
    )  # type: ignore


class ViTTransformer(ImageClassificationModel):
    """Pre-trained Vision Transformer (ViT) for image classification.

    Vision Transformer (ViT) is a transformer that is targeted at vision
    processing tasks such as image recognition.[1]

    References
    ----------
    [1] https://en.wikipedia.org/wiki/Vision_transformer
    [2] https://huggingface.co/docs/transformers/model_doc/vit
    """

    SCHEMA = ViTTransformerSchema

    def __init__(self, model=None, **kwargs):
        """Initialize the transformer.

        This process includes the instantiation of the pre-trained model and the
        associated feature extractor.
        """
        kwargs = self.validate_and_transform(kwargs)
        self.model_name = "google/vit-base-patch16-224"
        self.feature_extractor = ViTFeatureExtractor.from_pretrained(self.model_name)
        self.model = (
            model
            if model is not None
            else ViTForImageClassification.from_pretrained(self.model_name)
        )
        self.fitted = model is not None
        if model is None:
            self.training_args = kwargs
            self.batch_size = kwargs.pop("batch_size", 8)
            self.device = kwargs.pop("device", "gpu")

    def preprocess_images(self, x: Dataset, y: Optional[Dataset] = None):
        """Preprocess images for model input.

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

        # If the output datset is not given, create an empty dataset
        if not y:
            y = Dataset.from_list([{"foo": 0}] * len(x))
        # Initialize useful variables
        dataset = []
        input_column_name = x.column_names[0]
        output_column_name = y.column_names[0]

        # Preprocess both datasets
        for input_sample, output_sample in zip(x, y):  # noqa
            preprocessed_input = self.feature_extractor(
                images=input_sample[input_column_name], return_tensors="pt", size=224
            )
            reshaped_image = preprocessed_input["pixel_values"].reshape(
                (
                    preprocessed_input["pixel_values"].shape[1],
                    preprocessed_input["pixel_values"].shape[2],
                    preprocessed_input["pixel_values"].shape[3],
                )
            )
            dataset.append(
                {
                    "pixel_values": reshaped_image,
                    "labels": output_sample[output_column_name],
                }
            )
        return Dataset.from_list(dataset)

    def fit(self, x_train: Dataset, y_train: Dataset):
        """Fine-tune the pre-trained model.

        Parameters
        ----------
        x_train : Dataset
            Dataset with input training data.
        y_train: Dataset
            Dataset with output training data.

        """
        dataset = self.preprocess_images(x_train, y_train)

        # Arguments for fine-tuning
        training_args = TrainingArguments(
            output_dir="DashAI/back/user_models/temp_checkpoints_vit",
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
            "DashAI/back/user_models/temp_checkpoints_vit", ignore_errors=True
        )

    def predict(self, x_pred: Dataset) -> np.array:
        """Make a prediction with the fine-tuned model.

        Parameters
        ----------
        x_pred : Dataset
            Dataset with image data.

        Returns
        -------
        np.array
            Numpy array with the probabilities for each class.
        """
        if not self.fitted:
            raise NotFittedError(
                f"This {self.__class__.__name__} instance is not fitted yet. Call 'fit'"
                " with appropriate arguments before using this estimator."
            )

        dataset = self.preprocess_images(x_pred)
        dataset.set_format("torch", columns=["pixel_values", "labels"])

        probabilities = []

        # Iterate over each batch in the dataset
        for i in range(len(dataset)):
            # Prepare a batch of images for the model
            batch = dataset[i]

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
