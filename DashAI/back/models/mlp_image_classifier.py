from typing import List

import datasets
import torch
import torch.nn as nn
import torch.optim as optim
import torch.utils.data
from torch.utils.data import DataLoader
from torchvision import transforms

from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    list_field,
    schema_field,
)
from DashAI.back.models.base_model import BaseModel
from DashAI.back.models.image_classification_model import ImageClassificationModel


class MLPImageClassifierSchema(BaseSchema):
    epoch_description = (
        "The number of epochs to train the model. An epoch is a full "
        "iteration over the training data. It must be an integer greater "
        "or equal than 1"
    )
    epochs: schema_field(
        int_field(ge=1),
        placeholder=10,
        description=(
            "The number of epochs to train the model. An epoch is a full iteration "
            "over the training data. It must be an integer greater or equal than 1"
        ),
    )  # type: ignore
    hidden_dims: schema_field(
        list_field(int_field(ge=1), min_items=1),
        placeholder=[128, 64],
        description=(
            "The hidden layers and their dimensions. Plase specify the number of "
            "units of each layer separated by commas."
        ),
    )  # type: ignore


class ImageDataset(torch.utils.data.Dataset):
    def __init__(self, dataset: datasets.Dataset):
        self.dataset = dataset
        self.transforms = transforms.Compose(
            [
                transforms.Resize((30, 30)),
                transforms.ToTensor(),
            ]
        )

        column_names = list(self.dataset.features.keys())
        self.image_col_name = column_names[0]
        if len(column_names) > 1:
            self.label_col_name = column_names[1]
        else:
            self.label_col_name = None
        self.tensor_shape = self.transforms(self.dataset[0][self.image_col_name]).shape

    def num_classes(self):
        if self.label_col_name is None:
            return 0
        label_column = self.dataset[self.label_col_name]
        return len(set(label_column))

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        if self.label_col_name is None:
            image = self.dataset[idx][self.image_col_name]
            image = self.transforms(image)
            return image
        image = self.dataset[idx][self.image_col_name]
        image = self.transforms(image)
        label = self.dataset[idx][self.label_col_name]
        return image, label


class MLP(nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dims):
        super().__init__()
        self.hidden_layers = nn.ModuleList()
        previous_dim = input_dim
        print(type(hidden_dims))

        for hidden_dim in hidden_dims:
            self.hidden_layers.append(nn.Linear(previous_dim, hidden_dim))
            previous_dim = hidden_dim

        self.output_layer = nn.Linear(previous_dim, output_dim)
        self.relu = nn.ReLU()

    def forward(self, input: torch.Tensor):
        batch_size = input.shape[0]
        x = input.view(batch_size, -1)

        for layer in self.hidden_layers:
            x = self.relu(layer(x))

        x = self.output_layer(x)
        return x


def fit_model(
    model: nn.Module,
    train_loader: DataLoader,
    epochs: int,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
):
    model.train()
    for _ in range(epochs):
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
    return model


def predict(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
):
    model.eval()
    probs_predicted = []
    with torch.no_grad():
        for images in dataloader:
            images = images.to(device)
            output_probs: torch.Tensor = model(images)
            probs_predicted += output_probs.tolist()
    return probs_predicted


class MLPImageClassifier(ImageClassificationModel, BaseModel):
    SCHEMA = MLPImageClassifierSchema

    def __init__(self, epochs: int = 10, hidden_dims=None, **kwargs):
        super().__init__(**kwargs)
        if hidden_dims is None:
            hidden_dims = [128, 64]
        self.epochs = epochs
        # Borrar esto y hacerlo bien
        self.hidden_dims = hidden_dims if hidden_dims is not None else [128, 64]
        self.hidden_dims = list(map(int, hidden_dims.split(",")))
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        print(hidden_dims)
        print(type(hidden_dims))
        print(epochs)
        print(type(epochs))

    def fit(self, x: datasets.Dataset, y: datasets.Dataset):
        dataset = datasets.Dataset.from_dict(
            {
                "image": x["image"],
                "label": y["label"],
            }
        )
        image_dataset = ImageDataset(dataset)
        input_dim = (
            image_dataset.tensor_shape[0]
            * image_dataset.tensor_shape[1]
            * image_dataset.tensor_shape[2]
        )
        output_dim = image_dataset.num_classes()
        train_loader = DataLoader(image_dataset, batch_size=32, shuffle=True)
        self.model = MLP(input_dim, output_dim, self.hidden_dims).to(self.device)
        self.criteria = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.005)
        self.model = fit_model(
            self.model,
            train_loader,
            self.epochs,
            self.criteria,
            self.optimizer,
            self.device,
        )

    def predict(self, x: datasets.Dataset):
        image_dataset = ImageDataset(x)
        test_loader = DataLoader(image_dataset, batch_size=32, shuffle=False)
        probs = predict(self.model, test_loader, self.device)
        return probs

    def save(self, filename: str) -> None:
        """Save the model in the specified path."""
        torch.save(self.model, filename)

    @staticmethod
    def load(filename: str) -> None:
        """Load the model of the specified path."""
        model = torch.load(filename)
        return model
