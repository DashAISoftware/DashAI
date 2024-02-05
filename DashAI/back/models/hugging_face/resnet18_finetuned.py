"""DashAI implementation of DistilBERT model for image classification."""

import time

import datasets
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import models, transforms

from DashAI.back.models.image_classification_model import ImageClassificationModel


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

    class ResNet18Model(torch.nn.Module):
        def __init__(
            self,
            num_classes,
            learning_rate,
            momentum,
            weight_decay,
            step_size,
            gamma,
            device,
        ):
            super().__init__()
            self.learning_rate = learning_rate
            self.momentum = momentum
            self.weight_decay = weight_decay
            self.step_size = step_size
            self.gamma = gamma
            self.device = device

            self.model = models.resnet18(weights="DEFAULT")
            self.model.fc = nn.Linear(self.model.fc.in_features, num_classes)
            self.model = self.model.to(self.device)

            self.criterion: nn.CrossEntropyLoss = nn.CrossEntropyLoss()
            self.optimizer: optim.SGD = optim.SGD(
                self.parameters(),
                lr=self.learning_rate,
                momentum=self.momentum,
                weight_decay=self.weight_decay,
            )
            self.scheduler: optim.lr_scheduler.StepLR = optim.lr_scheduler.StepLR(
                self.optimizer, step_size=self.step_size, gamma=self.gamma
            )

        def fit(self, train_loader, num_epochs, dataset_len):
            since = time.time()

            # best_model_wts = copy.deepcopy(self.model.state_dict())
            best_acc = 0.0

            for epoch in range(num_epochs):
                print("Epoch {}/{}".format(epoch, num_epochs - 1))
                print("-" * 10)

                # Train model
                self.scheduler.step()
                self.model.train()

                running_loss = 0.0
                running_corrects = 0.0

                for inputs, labels in train_loader:
                    inputs, labels = inputs.to(self.device), labels.to(self.device)

                    self.optimizer.zero_grad()

                    outputs = self.model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss: torch.Tensor = self.criterion(outputs, labels)

                    loss.backward()
                    self.optimizer.step()

                    running_loss += loss.item() * inputs.size(0)
                    running_corrects += torch.sum(preds == labels.data)

                epoch_loss = running_loss / dataset_len
                epoch_acc = running_corrects.double() / dataset_len

                print("Train Loss: {:.4f} Acc: {:.4f}".format(epoch_loss, epoch_acc))

                if epoch_acc > best_acc:
                    best_acc = epoch_acc
                    # best_model_wts = copy.deepcopy(self.model.state_dict())

            time_elapsed = time.time() - since
            print(
                "Training complete in {:.0f}m {:.0f}s".format(
                    time_elapsed // 60, time_elapsed % 60
                )
            )
            print("Best val accucary: {:.4f}".format(best_acc))
            return self

        def predict(self, test_dataloader, test_dataset_len):
            self.model.eval()
            running_loss = 0.0
            running_corrects = 0.0
            preds_without_processing = []

            for inputs, labels in test_dataloader:
                inputs = inputs.to(self.device)
                labels = labels.to(self.device)

                with torch.set_grad_enabled(False):
                    outputs: torch.Tensor = self.model(inputs)
                    preds_without_processing += outputs.tolist()
                    _, preds = torch.max(outputs, 1)
                    loss = self.criterion(outputs, labels)

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / test_dataset_len
            epoch_acc = running_corrects.double() / test_dataset_len

            print("Val Loss: {:.4f} Acc: {:.4f}".format(epoch_loss, epoch_acc))
            return preds_without_processing

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
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.learning_rate = learning_rate
        self.max_epochs = max_epochs
        self.momentum = momentum
        self.weight_decay = weight_decay
        self.step_size = step_size
        self.gamma = gamma
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def determine_num_classes(self, dataset: datasets.Dataset):
        label_col_name = list(dataset.features.keys())[-1]
        label_values = dataset[label_col_name]
        return len(list(set(label_values)))

    def fit(self, dataset: datasets.Dataset):
        # 1. Determine the num of classes
        num_classes = self.determine_num_classes(dataset)

        # 2. Preprocess the dataset and create the dataloader
        img_dataset = self.ImagePytorchDataset(dataset)
        self.train_dataloader = DataLoader(
            img_dataset, batch_size=self.batch_size, shuffle=self.shuffle
        )

        # 3. Create the model
        self.model = self.ResNet18Model(
            num_classes,
            self.learning_rate,
            self.momentum,
            self.weight_decay,
            self.step_size,
            self.gamma,
            self.device,
        )

        # 4. Train the model
        self.model = self.model.fit(
            self.train_dataloader, self.max_epochs, len(dataset)
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
        return self.model.predict(dataloader, len(dataset))

    def save(self, filename: str):
        torch.save(self.model.state_dict(), filename)

    def load(self, filename: str):
        self.model.load_state_dict(torch.load(filename))
