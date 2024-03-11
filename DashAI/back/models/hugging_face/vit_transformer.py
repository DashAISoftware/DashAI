"""DashAI implementation of DistilBERT model for image classification."""
import shutil

import numpy as np
from sklearn.exceptions import NotFittedError
from transformers import (
    Trainer,
    TrainingArguments,
    ViTFeatureExtractor,
    ViTForImageClassification,
)

from DashAI.back.core.schema_fields import (
    BaseSchema,
    float_field,
    int_field,
    schema_field,
    string_field,
)
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
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
        string_field(enum=["gpu", "cpu"]),
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
            self.batch_size = kwargs.pop("batch_size")
            self.device = kwargs.pop("device")

    def get_preprocess_images(self, input_column: str, output_column: str):
        """Preprocess images for model input.

        Parameters
        ----------
        input_column : str
            name of the column containing the images to be preprocessed.
        output_column : str
            name of the column containing the output labels for the images.

        Returns
        -------
        Function
            a function that preprocesses images and outputs a dictionary
            containing processed images and corresponding labels.
        """

        def _preprocess_images(examples):
            inputs = self.feature_extractor(
                images=examples[input_column], return_tensors="pt", size=224
            )
            inputs["labels"] = examples[output_column]
            return inputs

        return _preprocess_images

    def fit(self, dataset: DashAIDataset):
        """Fine-tune the pre-trained model.

        Parameters
        ----------
        dataset : DashAIDataset
            DashAiDataset with training data.

        """
        input_column = dataset.inputs_columns[0]
        output_column = dataset.outputs_columns[0]

        feature_extractor_func = self.get_preprocess_images(input_column, output_column)
        dataset = dataset.map(feature_extractor_func, batched=True)

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
        return self

    def predict(self, dataset: DashAIDataset) -> np.array:
        """Make a prediction with the fine-tuned model.

        Parameters
        ----------
        dataset : DashAIDataset
            DashAIDataset with image data.

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

        input_column = dataset.inputs_columns[0]
        output_column = dataset.outputs_columns[0]
        preprocess_images = self.get_preprocess_images(input_column, output_column)

        dataset = dataset.map(preprocess_images, batched=True)
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
