"""Shared base class for torchvision-based image classifiers."""

from __future__ import annotations

import abc

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.base_model import BaseModel
from DashAI.back.models.image_explainable_model import GradCamCompatibleModel
from DashAI.back.models.utils import DEVICE_ENUM, DEVICE_PLACEHOLDER, DEVICE_TO_IDX


class TorchvisionImageClassifierSchema(BaseSchema):
    """Shared training parameters for torchvision-based image classifiers."""

    epochs: schema_field(
        int_field(ge=1),
        placeholder=10,
        description=MultilingualString(
            en=(
                "The number of epochs to train the model. An epoch is a full "
                "iteration over the training data."
            ),
            es=(
                "El número de épocas para entrenar el modelo. Una época es una "
                "iteración completa sobre los datos de entrenamiento."
            ),
            pt=(
                "O número de épocas para treinar o modelo. Uma época é uma "
                "iteração completa sobre os dados de treinamento."
            ),
            de=(
                "Die Anzahl der Trainingsepochen. Eine Epoche ist ein vollständiger "
                "Durchlauf über die Trainingsdaten."
            ),
            zh="训练模型的轮数。一轮是对训练数据的完整遍历。",
        ),
        alias=MultilingualString(
            en="Epochs", es="Épocas", pt="Épocas", de="Epochen", zh="训练轮数"
        ),
    )  # type: ignore

    learning_rate: schema_field(
        float_field(gt=0.0),
        placeholder=0.001,
        description=MultilingualString(
            en="Learning rate for the Adam optimizer.",
            es="Tasa de aprendizaje para el optimizador Adam.",
            pt="Taxa de aprendizado para o otimizador Adam.",
            de="Lernrate für den Adam-Optimierer.",
            zh="Adam 优化器的学习率。",
        ),
        alias=MultilingualString(
            en="Learning rate",
            es="Tasa de aprendizaje",
            pt="Taxa de aprendizado",
            de="Lernrate",
            zh="学习率",
        ),
    )  # type: ignore

    batch_size: schema_field(
        int_field(ge=1),
        placeholder=32,
        description=MultilingualString(
            en=(
                "Number of images processed together in each training step. "
                "Larger values speed up training but require more memory."
            ),
            es=(
                "Número de imágenes procesadas juntas en cada paso de "
                "entrenamiento. Valores más grandes aceleran el entrenamiento "
                "pero requieren más memoria."
            ),
            pt=(
                "Número de imagens processadas juntas em cada etapa de "
                "treinamento. Valores maiores aceleram o treinamento "
                "mas requerem mais memória."
            ),
            de=(
                "Anzahl der gemeinsam verarbeiteten Bilder in jedem Trainingsschritt. "
                "Größere Werte beschleunigen das Training, erfordern jedoch mehr "
                "Speicher."
            ),
            zh="每个训练步骤中同时处理的图像数量。较大的值可加速训练但需要更多内存。",
        ),
        alias=MultilingualString(
            en="Batch size",
            es="Tamaño de lote",
            pt="Tamanho do lote",
            de="Stapelgröße",
            zh="批量大小",
        ),
    )  # type: ignore

    image_size: schema_field(
        int_field(ge=32),
        placeholder=224,
        description=MultilingualString(
            en=(
                "Images are resized to this value (in pixels) for both width "
                "and height. Use 224 for ImageNet-pretrained models."
            ),
            es=(
                "Las imágenes se redimensionan a este valor (en píxeles) tanto "
                "en ancho como en alto. Use 224 para modelos preentrenados "
                "en ImageNet."
            ),
            pt=(
                "As imagens são redimensionadas para este valor (em pixels) tanto "
                "em largura quanto em altura. Use 224 para modelos pré-treinados "
                "no ImageNet."
            ),
            de=(
                "Bilder werden auf diesen Wert (in Pixeln) für Breite und Höhe "
                "skaliert. Für ImageNet-vortrainierte Modelle wird 224 empfohlen."
            ),
            zh="图像将被缩放到此像素值（宽和高）。ImageNet 预训练模型建议使用 224。",
        ),
        alias=MultilingualString(
            en="Image size",
            es="Tamaño de imagen",
            pt="Tamanho da imagem",
            de="Bildgröße",
            zh="图像尺寸",
        ),
    )  # type: ignore

    dropout_rate: schema_field(
        float_field(ge=0.0, lt=1.0),
        placeholder=0.0,
        description=MultilingualString(
            en=(
                "Dropout rate applied before the output layer. "
                "Values between 0.2 and 0.5 help prevent overfitting."
            ),
            es=(
                "Tasa de dropout aplicada antes de la capa de salida. "
                "Valores entre 0.2 y 0.5 ayudan a prevenir el sobreajuste."
            ),
            pt=(
                "Taxa de dropout aplicada antes da camada de saída. "
                "Valores entre 0.2 e 0.5 ajudam a prevenir o sobreajuste."
            ),
            de=(
                "Dropout-Rate vor der Ausgabeschicht. "
                "Werte zwischen 0.2 und 0.5 helfen, Überanpassung zu verhindern."
            ),
            zh="在输出层前应用的 Dropout 率。0.2 到 0.5 之间的值有助于防止过拟合。",
        ),
        alias=MultilingualString(
            en="Dropout rate",
            es="Tasa de dropout",
            pt="Taxa de dropout",
            de="Dropout-Rate",
            zh="Dropout 率",
        ),
    )  # type: ignore

    weight_decay: schema_field(
        float_field(ge=0.0),
        placeholder=0.0,
        description=MultilingualString(
            en=(
                "L2 regularization coefficient for the Adam optimizer. "
                "Typical values: 1e-4 to 1e-2."
            ),
            es=(
                "Coeficiente de regularización L2 para el optimizador Adam. "
                "Valores típicos: 1e-4 a 1e-2."
            ),
            pt=(
                "Coeficiente de regularização L2 para o otimizador Adam. "
                "Valores típicos: 1e-4 a 1e-2."
            ),
            de=(
                "L2-Regularisierungskoeffizient für den Adam-Optimierer. "
                "Typische Werte: 1e-4 bis 1e-2."
            ),
            zh="Adam 优化器的 L2 正则化系数。典型值：1e-4 到 1e-2。",
        ),
        alias=MultilingualString(
            en="Weight decay",
            es="Decaimiento de pesos",
            pt="Decaimento de pesos",
            de="Gewichtsabnahme",
            zh="权重衰减",
        ),
    )  # type: ignore

    pretrained: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en=(
                "If True, loads weights pretrained on ImageNet. "
                "Recommended when your dataset is small or similar to natural images."
            ),
            es=(
                "Si es True, carga pesos preentrenados en ImageNet. "
                "Recomendado cuando el dataset es pequeño o similar "
                "a imágenes naturales."
            ),
            pt=(
                "Se True, carrega pesos pré-treinados no ImageNet. "
                "Recomendado quando o conjunto de dados é pequeno ou similar "
                "a imagens naturais."
            ),
            de=(
                "Falls True, werden auf ImageNet vortrainierte Gewichte geladen. "
                "Empfohlen bei kleinen Datensätzen oder ähnlichen Bilddaten."
            ),
            zh=(
                "若为 True，加载 ImageNet 预训练权重。"
                "数据集较小或与自然图像相似时推荐使用。"
            ),
        ),
        alias=MultilingualString(
            en="Pretrained",
            es="Preentrenado",
            pt="Pré-treinado",
            de="Vortrainiert",
            zh="预训练",
        ),
    )  # type: ignore

    freeze_backbone: schema_field(
        bool_field(),
        placeholder=False,
        description=MultilingualString(
            en=(
                "If True, freezes the convolutional backbone and only trains "
                "the classifier head. Useful for very small datasets."
            ),
            es=(
                "Si es True, congela el backbone convolucional y solo entrena "
                "el clasificador final. Útil para datasets muy pequeños."
            ),
            pt=(
                "Se True, congela o backbone convolucional e treina apenas "
                "o classificador final. Útil para conjuntos de dados muito pequenos."
            ),
            de=(
                "Falls True, wird das konvolutionale Backbone eingefroren und nur "
                "der Klassifikationskopf trainiert. Nützlich bei sehr kleinen "
                "Datensätzen."
            ),
            zh="若为 True，冻结卷积主干，仅训练分类头。适用于数据集非常小的情况。",
        ),
        alias=MultilingualString(
            en="Freeze backbone",
            es="Congelar backbone",
            pt="Congelar backbone",
            de="Backbone einfrieren",
            zh="冻结主干",
        ),
    )  # type: ignore

    device: schema_field(
        enum_field(enum=DEVICE_ENUM),
        placeholder=DEVICE_PLACEHOLDER,
        description=MultilingualString(
            en="Hardware device used for training and inference (CPU/GPU).",
            es="Dispositivo de hardware para entrenamiento e inferencia (CPU/GPU).",
            pt="Dispositivo de hardware usado para treinamento e inferência (CPU/GPU).",
            de="Hardwaregerät für Training und Inferenz (CPU/GPU).",
            zh="用于训练和推理的硬件设备（CPU/GPU）。",
        ),
        alias=MultilingualString(
            en="Device", es="Dispositivo", pt="Dispositivo", de="Gerät", zh="设备"
        ),
    )  # type: ignore


def _make_image_dataset(x_dataset, y_dataset=None, image_size=224):
    import torch.utils.data
    from torchvision import transforms

    class _ImageDataset(torch.utils.data.Dataset):
        def __init__(self, x_ds, y_ds, img_size):
            self.x_dataset = x_ds
            self.y_dataset = y_ds
            self.transforms = transforms.Compose(
                [
                    transforms.Lambda(lambda img: img.convert("RGB")),
                    transforms.Resize((img_size, img_size)),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225],
                    ),
                ]
            )

            self.image_col_name = list(x_ds.features.keys())[0]
            self.label_col_name = (
                list(y_ds.features.keys())[0] if y_ds is not None else None
            )

            self.label_to_idx = {}
            self.idx_to_label = {}
            if self.label_col_name:
                y_cat = (getattr(y_ds, "types", {}) or {}).get(self.label_col_name)
                if y_cat is not None and getattr(y_cat, "categories", None):
                    unique_labels = sorted(y_cat.categories)
                else:
                    unique_labels = sorted(set(self.y_dataset[self.label_col_name]))
                self.label_to_idx = {
                    label: idx for idx, label in enumerate(unique_labels)
                }
                self.idx_to_label = {
                    idx: label for label, idx in self.label_to_idx.items()
                }

        def num_classes(self):
            if self.label_col_name is None:
                return 0
            return len(self.label_to_idx)

        def __len__(self):
            return len(self.x_dataset)

        def __getitem__(self, idx):
            image = self.transforms(self.x_dataset[idx][self.image_col_name].to_pil())
            if self.label_col_name is None:
                return image
            label_str = self.y_dataset[idx][self.label_col_name]
            return image, self.label_to_idx[label_str]

    return _ImageDataset(x_dataset, y_dataset, image_size)


class TorchvisionImageClassifier(BaseModel, GradCamCompatibleModel, abc.ABC):
    """Abstract base for torchvision image classifiers.

    Subclasses must implement:
    - ``_build_backbone(num_classes, pretrained)``: return the adapted model.
    - ``_classifier_head()``: return the head module unfrozen when
      ``freeze_backbone=True``.
    """

    SCHEMA = TorchvisionImageClassifierSchema
    COMPATIBLE_COMPONENTS = ["ImageClassificationTask"]

    @abc.abstractmethod
    def _build_backbone(self, num_classes: int, pretrained: bool):
        """Build and return the adapted torchvision model."""

    @abc.abstractmethod
    def _classifier_head(self):
        """Return the classifier head module (kept trainable when freezing)."""

    @staticmethod
    def _collate_fn_with_labels(batch):
        import torch

        images = torch.stack([item[0] for item in batch])
        labels = torch.tensor([item[1] for item in batch], dtype=torch.long)
        return images, labels

    @staticmethod
    def _collate_fn_no_labels(batch):
        import torch

        return torch.stack(batch)

    def __init__(
        self,
        epochs=10,
        learning_rate=0.001,
        batch_size=32,
        image_size=224,
        dropout_rate=0.0,
        weight_decay=0.0,
        pretrained=True,
        freeze_backbone=False,
        device=DEVICE_PLACEHOLDER,
        **kwargs,
    ):
        import torch

        self.epochs = epochs
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.image_size = image_size
        self.dropout_rate = dropout_rate
        self.weight_decay = weight_decay
        self.pretrained = pretrained
        self.freeze_backbone = freeze_backbone
        self._device_name = device
        self.device = torch.device(
            f"cuda:{DEVICE_TO_IDX.get(device)}"
            if DEVICE_TO_IDX.get(device, -1) >= 0
            else "cpu"
        )
        self.model = None
        self.optimizer = None
        self.num_classes = None
        self.idx_to_label = {}
        self.label_to_idx = {}

    def _freeze_backbone_params(self):
        for p in self.model.parameters():
            p.requires_grad = False
        for p in self._classifier_head().parameters():
            p.requires_grad = True

    def get_inference_transform(self):
        """Return the transform applied to input images at inference time.

        Returns
        -------
        Callable
            Resize, tensor conversion and the ImageNet normalization used
            by the training pipeline.
        """
        from torchvision import transforms

        return transforms.Compose(
            [
                transforms.Lambda(lambda img: img.convert("RGB")),
                transforms.Resize((self.image_size, self.image_size)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

    def prepare_output(self, dataset, is_fit=False):
        """Encode string labels to integer indices matching the model's class order."""
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        if not self.label_to_idx:
            return dataset

        col_name = dataset.column_names[0]
        encoded = [self.label_to_idx.get(lbl, -1) for lbl in dataset[col_name]]
        return DashAIDataset(pa.table({col_name: encoded}))

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        """Fine-tune the backbone on the provided image dataset.

        Parameters
        ----------
        x_train : DashAIDataset
            Input dataset containing images.
        y_train : DashAIDataset
            Target dataset containing string labels.
        x_validation : DashAIDataset, optional
            Validation input features. Defaults to None.
        y_validation : DashAIDataset, optional
            Validation target labels. Defaults to None.

        Returns
        -------
        BaseTorchvisionImageClassifier
            The trained model instance.
        """
        import torch
        import torch.nn as nn
        import torch.optim as optim
        import torch.utils.data

        from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum

        image_dataset = _make_image_dataset(
            x_train, y_dataset=y_train, image_size=self.image_size
        )
        self.num_classes = image_dataset.num_classes()
        self.idx_to_label = image_dataset.idx_to_label
        self.label_to_idx = image_dataset.label_to_idx

        train_loader = torch.utils.data.DataLoader(
            image_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            collate_fn=self._collate_fn_with_labels,
        )

        self.model = self._build_backbone(self.num_classes, self.pretrained).to(
            self.device
        )

        if self.freeze_backbone:
            self._freeze_backbone_params()

        criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(
            filter(lambda p: p.requires_grad, self.model.parameters()),
            lr=self.learning_rate,
            weight_decay=self.weight_decay,
        )

        for epoch in range(self.epochs):
            self.model.train()
            for images, labels in train_loader:
                images, labels = images.to(self.device), labels.to(self.device)
                self.optimizer.zero_grad()
                loss = criterion(self.model(images), labels)
                loss.backward()
                self.optimizer.step()

            self.model.eval()
            self.calculate_metrics(
                split=SplitEnum.TRAIN,
                level=LevelEnum.EPOCH,
                x_data=x_train,
                y_data=y_train,
                log_index=epoch + 1,
            )
            if x_validation is not None:
                self.calculate_metrics(
                    split=SplitEnum.VALIDATION,
                    level=LevelEnum.EPOCH,
                    x_data=x_validation,
                    y_data=y_validation,
                    log_index=epoch + 1,
                )

        return self

    def predict(self, x):
        """Return per class probability matrix for each image.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset containing images.

        Returns
        -------
        np.ndarray
            Array of shape (n_samples, n_classes) with softmax probabilities.
        """
        import numpy as np
        import torch
        import torch.utils.data

        image_dataset = _make_image_dataset(
            x, y_dataset=None, image_size=self.image_size
        )
        loader = torch.utils.data.DataLoader(
            image_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            collate_fn=self._collate_fn_no_labels,
        )

        self.model.to(self.device)
        self.model.eval()
        all_probs = []
        with torch.no_grad():
            for images in loader:
                logits = self.model(images.to(self.device))
                all_probs.append(torch.softmax(logits, dim=1).cpu().numpy())

        return np.concatenate(all_probs, axis=0)

    def save(self, filename: str) -> None:
        """Save the model checkpoint to disk.

        Parameters
        ----------
        filename : str
            Path where the checkpoint will be saved.
        """
        import torch

        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "epochs": self.epochs,
                "learning_rate": self.learning_rate,
                "batch_size": self.batch_size,
                "image_size": self.image_size,
                "dropout_rate": self.dropout_rate,
                "weight_decay": self.weight_decay,
                "pretrained": self.pretrained,
                "freeze_backbone": self.freeze_backbone,
                "device_name": self._device_name,
                "num_classes": self.num_classes,
                "idx_to_label": self.idx_to_label,
                "label_to_idx": self.label_to_idx,
            },
            filename,
        )

    @classmethod
    def load(cls, filename: str):
        """Load a model checkpoint from disk.

        Parameters
        ----------
        filename : str
            Path to the checkpoint file.

        Returns
        -------
        BaseTorchvisionImageClassifier
            Instance with loaded weights.
        """
        import torch
        import torch.optim as optim

        ckpt = torch.load(filename, map_location=torch.device("cpu"))
        instance = cls(
            epochs=ckpt["epochs"],
            learning_rate=ckpt["learning_rate"],
            batch_size=ckpt.get("batch_size", 32),
            image_size=ckpt.get("image_size", 224),
            dropout_rate=ckpt.get("dropout_rate", 0.0),
            weight_decay=ckpt.get("weight_decay", 0.0),
            pretrained=False,
            freeze_backbone=ckpt.get("freeze_backbone", False),
            device=ckpt.get("device_name", DEVICE_PLACEHOLDER),
        )
        instance.num_classes = ckpt["num_classes"]
        instance.idx_to_label = ckpt.get("idx_to_label", {})
        instance.label_to_idx = ckpt.get("label_to_idx", {})
        instance.model = instance._build_backbone(
            instance.num_classes, pretrained=False
        )
        instance.model.load_state_dict(ckpt["model_state_dict"])
        instance.optimizer = optim.Adam(
            filter(lambda p: p.requires_grad, instance.model.parameters()),
            weight_decay=instance.weight_decay,
        )
        instance.optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        return instance
