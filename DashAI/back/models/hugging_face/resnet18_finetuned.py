"""DashAI implementation of DistilBERT model for image classification."""

import datasets
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import models, transforms

from DashAI.back.models.image_classification_model import ImageClassificationModel


def fit(
    model: torch.nn.Module,
    train_loader: DataLoader,
    criterion: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.StepLR,
    device: torch.device,
    num_epochs: int,
    dataset_len: int,
):
    for epoch in range(num_epochs):
        print("Epoch {}/{}".format(epoch, num_epochs - 1))
        print("-" * 10)

        # Train model
        scheduler.step()
        model.train()

        running_loss = 0.0
        running_corrects = 0.0

        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()

            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            loss: torch.Tensor = criterion(outputs, labels)

            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data)

        epoch_loss = running_loss / dataset_len
        epoch_acc = running_corrects.double() / dataset_len

        print("Train Loss: {:.4f} Acc: {:.4f}".format(epoch_loss, epoch_acc))
    return model


def predict(
    model: torch.nn.Module,
    test_dataloader: DataLoader,
    device: torch.device,
    criterion: torch.nn.Module,
    test_dataset_len: int,
):
    model.eval()
    running_loss = 0.0
    running_corrects = 0.0
    preds_without_processing = []

    for inputs, labels in test_dataloader:
        inputs = inputs.to(device)
        labels = labels.to(device)

        with torch.set_grad_enabled(False):
            outputs: torch.Tensor = model(inputs)
            preds_without_processing += outputs.tolist()
            _, preds = torch.max(outputs, 1)
            loss = criterion(outputs, labels)

        running_loss += loss.item() * inputs.size(0)
        running_corrects += torch.sum(preds == labels.data)

    epoch_loss = running_loss / test_dataset_len
    epoch_acc = running_corrects.double() / test_dataset_len

    print("Val Loss: {:.4f} Acc: {:.4f}".format(epoch_loss, epoch_acc))
    return preds_without_processing


class ResNet18Finetuned(ImageClassificationModel):
    class ImagePytorchDataset(torch.utils.data.Dataset):
        def __init__(self, dataset: datasets.Dataset):
            self.dataset = dataset
            self.transform = transforms.Compose(
                [
                    transforms.Resize(256),
                    transforms.CenterCrop(224),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                    ),
                ]
            )

            column_names = list(self.dataset.features.keys())
            self.image_col_name = column_names[0]
            self.label_col_name = column_names[1]

        def __len__(self):
            return len(self.dataset)

        def __getitem__(self, idx):
            image = self.dataset[idx][self.image_col_name]
            image = self.transform(image)
            label = self.dataset[idx][self.label_col_name]
            return image, label

    def __init__(
        self,
        batch_size: int = 8,
        shuffle: bool = True,
        learning_rate: float = 0.001,
        max_epochs: int = 5,
        momentum: float = 0.9,
        weight_decay: float = 1e-4,
        step_size: int = 6,
        gamma: float = 0.1,
    ) -> None:
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.weight_decay = weight_decay
        self.step_size = step_size
        self.gamma = gamma
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.max_epochs = max_epochs

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.model = models.resnet18(weights="DEFAULT")

        self.criterion: nn.CrossEntropyLoss = nn.CrossEntropyLoss()

    def determine_num_classes(self, dataset: datasets.Dataset):
        label_col_name = list(dataset.features.keys())[-1]
        label_values = dataset[label_col_name]
        return len(list(set(label_values)))

    def fit(self, dataset: datasets.Dataset):
        # 1. Determine the num of classes
        num_classes = self.determine_num_classes(dataset)

        # 2. Change the last layer of the model to have the correct number of classes
        self.model.fc = nn.Linear(self.model.fc.in_features, num_classes)
        self.model = self.model.to(self.device)

        # 3. Create the optimizer and scheduler
        optimizer: optim.SGD = optim.SGD(
            self.model.parameters(),
            lr=self.learning_rate,
            momentum=self.momentum,
            weight_decay=self.weight_decay,
        )
        scheduler: optim.lr_scheduler.StepLR = optim.lr_scheduler.StepLR(
            optimizer, step_size=self.step_size, gamma=self.gamma
        )

        # 4. Create the dataloader
        img_dataset = self.ImagePytorchDataset(dataset)
        self.train_dataloader = DataLoader(
            img_dataset, batch_size=self.batch_size, shuffle=self.shuffle
        )

        # 5. Train the model
        self.model = fit(
            self.model,
            self.train_dataloader,
            self.criterion,
            optimizer,
            scheduler,
            self.device,
            self.max_epochs,
            len(dataset),
        )

    def predict(self, dataset: datasets.Dataset):
        """
        Realiza predicciones sobre un conjunto de datos.

        Args:
            dataset: Dataset con las imágenes a predecir.

        Returns:
            Lista con las predicciones de la clase para cada imagen.
        """

        img_dataset = self.ImagePytorchDataset(dataset)
        dataloader = DataLoader(img_dataset, batch_size=self.batch_size, shuffle=False)
        preds = predict(
            self.model, dataloader, self.device, self.criterion, len(dataset)
        )
        return preds

    def save(self, filename: str):
        torch.save(self.model.state_dict(), filename)

    def load(self, filename: str):
        self.model.load_state_dict(torch.load(filename))
