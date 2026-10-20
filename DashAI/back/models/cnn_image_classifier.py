"""CNN-based image classifier for DashAI."""

from __future__ import annotations

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.image_explainable_model import GradCamCompatibleModel
from DashAI.back.models.supervised_model import SupervisedModel
from DashAI.back.models.utils import DEVICE_ENUM, DEVICE_PLACEHOLDER, DEVICE_TO_IDX


class CNNImageClassifierSchema(BaseSchema):
    """Configuration parameters for the CNN Image Classifier."""

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
                "Die Anzahl der Epochen zum Trainieren des Modells. Eine Epoche ist "
                "eine vollständige Iteration über die Trainingsdaten."
            ),
            zh=("训练模型的轮次数。一个轮次是对训练数据的一次完整迭代。"),
        ),
        alias=MultilingualString(
            en="Epochs", es="Épocas", pt="Épocas", de="Epochen", zh="训练轮次"
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
                "Anzahl der Bilder, die in jedem Trainingsschritt gemeinsam "
                "verarbeitet werden. Größere Werte beschleunigen das Training, "
                "erfordern jedoch mehr Arbeitsspeicher."
            ),
            zh=(
                "每个训练步骤中同时处理的图像数量。"
                "较大的值可加快训练速度，但需要更多内存。"
            ),
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
        int_field(ge=8),
        placeholder=64,
        description=MultilingualString(
            en=(
                "Images are resized to this value (in pixels) for both width "
                "and height before training. Must be at least 2^num_conv_blocks."
            ),
            es=(
                "Las imágenes se redimensionan a este valor (en píxeles) tanto "
                "en ancho como en alto. Debe ser al menos 2^num_conv_blocks."
            ),
            pt=(
                "As imagens são redimensionadas para este valor (em pixels) tanto "
                "em largura quanto em altura. Deve ser pelo menos 2^num_conv_blocks."
            ),
            de=(
                "Bilder werden vor dem Training auf diesen Wert (in Pixeln) für "
                "Breite und Höhe skaliert. Muss mindestens 2^num_conv_blocks betragen."
            ),
            zh=(
                "训练前将图像的宽度和高度调整为此值（像素）。"
                "必须至少为 2^num_conv_blocks。"
            ),
        ),
        alias=MultilingualString(
            en="Image size",
            es="Tamaño de imagen",
            pt="Tamanho da imagem",
            de="Bildgröße",
            zh="图像尺寸",
        ),
    )  # type: ignore

    num_conv_blocks: schema_field(
        int_field(ge=1, le=5),
        placeholder=3,
        description=MultilingualString(
            en=(
                "Number of convolutional blocks. Each block applies a "
                "convolution, ReLU activation, and max-pooling that halves "
                "the spatial dimensions."
            ),
            es=(
                "Número de bloques convolucionales. Cada bloque aplica una "
                "convolución, activación ReLU y max-pooling que reduce a la "
                "mitad las dimensiones espaciales."
            ),
            pt=(
                "Número de blocos convolucionais. Cada bloco aplica uma "
                "convolução, ativação ReLU e max-pooling que reduz à metade "
                "as dimensões espaciais."
            ),
            de=(
                "Anzahl der Faltungsblöcke. Jeder Block wendet eine Faltung, "
                "ReLU-Aktivierung und Max-Pooling an, das die räumlichen "
                "Dimensionen halbiert."
            ),
            zh=(
                "卷积块的数量。每个块依次执行卷积、ReLU 激活和最大池化，"
                "将空间维度减半。"
            ),
        ),
        alias=MultilingualString(
            en="Number of conv blocks",
            es="Número de bloques conv",
            pt="Número de blocos conv",
            de="Anzahl der Faltungsblöcke",
            zh="卷积块数量",
        ),
    )  # type: ignore

    initial_filters: schema_field(
        int_field(ge=8),
        placeholder=32,
        description=MultilingualString(
            en=(
                "Number of filters in the first convolutional block. "
                "Each subsequent block doubles this number."
            ),
            es=(
                "Número de filtros en el primer bloque convolucional. "
                "Cada bloque siguiente duplica este número."
            ),
            pt=(
                "Número de filtros no primeiro bloco convolucional. "
                "Cada bloco subsequente dobra este número."
            ),
            de=(
                "Anzahl der Filter im ersten Faltungsblock. "
                "Jeder nachfolgende Block verdoppelt diese Anzahl."
            ),
            zh=("第一个卷积块中的滤波器数量。每个后续块将此数量翻倍。"),
        ),
        alias=MultilingualString(
            en="Initial filters",
            es="Filtros iniciales",
            pt="Filtros iniciais",
            de="Anfangsfilter",
            zh="初始滤波器数",
        ),
    )  # type: ignore

    dropout_rate: schema_field(
        float_field(ge=0.0, lt=1.0),
        placeholder=0.0,
        description=MultilingualString(
            en=(
                "Fraction of neurons randomly deactivated before the output "
                "layer. Values between 0.2 and 0.5 help prevent overfitting. "
                "Use 0.0 to disable."
            ),
            es=(
                "Fracción de neuronas desactivadas aleatoriamente antes de la "
                "capa de salida. Valores entre 0.2 y 0.5 ayudan a prevenir el "
                "sobreajuste. Use 0.0 para desactivarlo."
            ),
            pt=(
                "Fração de neurônios desativados aleatoriamente antes da "
                "camada de saída. Valores entre 0.2 e 0.5 ajudam a prevenir o "
                "sobreajuste. Use 0.0 para desativar."
            ),
            de=(
                "Anteil der vor der Ausgabeschicht zufällig deaktivierten Neuronen. "
                "Werte zwischen 0.2 und 0.5 helfen, Überanpassung zu vermeiden. "
                "Mit 0.0 deaktivieren."
            ),
            zh=(
                "输出层之前随机停用的神经元比例。"
                "0.2 至 0.5 之间的值有助于防止过拟合。"
                "设为 0.0 以禁用。"
            ),
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
            zh=("Adam 优化器的 L2 正则化系数。典型值：1e-4 至 1e-2。"),
        ),
        alias=MultilingualString(
            en="Weight decay",
            es="Decaimiento de pesos",
            pt="Decaimento de pesos",
            de="Gewichtsabnahme",
            zh="权重衰减",
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
            en="Device",
            es="Dispositivo",
            pt="Dispositivo",
            de="Gerät",
            zh="设备",
        ),
    )  # type: ignore


def _make_image_dataset(x_dataset, y_dataset=None, image_size=64):
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

            self.tensor_shape = self.transforms(
                self.x_dataset[0][self.image_col_name].to_pil()
            ).shape

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


def _build_cnn_model(
    input_channels,
    input_size,
    num_classes,
    num_conv_blocks,
    initial_filters,
    dropout_rate,
):
    import torch.nn as nn

    class _CNNBlock(nn.Module):
        def __init__(self, in_channels, out_channels):
            super().__init__()
            self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
            self.relu = nn.ReLU()
            self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        def forward(self, x):
            return self.pool(self.relu(self.conv(x)))

    class _CNN(nn.Module):
        def __init__(self, in_ch, in_sz, n_cls, n_blocks, init_f, drop_r):
            super().__init__()
            self.conv_blocks = nn.ModuleList()
            out_ch = init_f
            for _ in range(n_blocks):
                self.conv_blocks.append(_CNNBlock(in_ch, out_ch))
                in_ch = out_ch
                out_ch *= 2

            final_spatial = in_sz // (2**n_blocks)
            flat_dim = in_ch * final_spatial * final_spatial
            self.dropout = nn.Dropout(drop_r)
            self.fc = nn.Linear(flat_dim, n_cls)

        def forward(self, x):
            for block in self.conv_blocks:
                x = block(x)
            x = x.view(x.size(0), -1)
            return self.fc(self.dropout(x))

    return _CNN(
        input_channels,
        input_size,
        num_classes,
        num_conv_blocks,
        initial_filters,
        dropout_rate,
    )


class CNNImageClassifier(SupervisedModel, GradCamCompatibleModel):
    """CNN-based image classifier.

    A convolutional neural network with configurable depth and width that
    learns spatial features hierarchically via conv→ReLU→pool blocks,
    followed by a dropout-regularized linear output layer.
    """

    SCHEMA = CNNImageClassifierSchema
    COMPATIBLE_COMPONENTS = ["ImageClassificationTask"]

    DISPLAY_NAME: str = MultilingualString(
        en="CNN Image Classifier",
        es="Clasificador de Imágenes CNN",
        pt="Classificador de Imagens CNN",
        zh="卷积神经网络图像分类器",
        de="CNN-Bildklassifikator",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "A Convolutional Neural Network (CNN) image classifier that learns "
            "spatial features through configurable conv→ReLU→pool blocks, "
            "with filters doubling at each stage."
        ),
        es=(
            "Un clasificador de imágenes basado en Red Neuronal Convolucional "
            "(CNN) que aprende características espaciales mediante bloques "
            "conv→ReLU→pool configurables, duplicando los filtros en cada etapa."
        ),
        pt=(
            "Um classificador de imagens baseado em Rede Neural Convolucional "
            "(CNN) que aprende características espaciais por meio de blocos "
            "conv→ReLU→pool configuráveis, dobrando os filtros em cada etapa."
        ),
        zh=(
            "基于卷积神经网络（CNN）的图像分类器，通过可配置的卷积→ReLU→池化块"
            "学习空间特征，每阶段滤波器数量翻倍。"
        ),
        de=(
            "Ein auf Convolutional Neural Network (CNN) basierender Bildklassifikator, "
            "der räumliche Merkmale über konfigurierbare Faltungs→ReLU→Pool-Blöcke "
            "erlernt, wobei sich die Filteranzahl in jeder Stufe verdoppelt."
        ),
    )
    COLOR: str = "#1565C0"
    ICON: str = "Layers"

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
        image_size=64,
        num_conv_blocks=3,
        initial_filters=32,
        dropout_rate=0.0,
        weight_decay=0.0,
        device=DEVICE_PLACEHOLDER,
        **kwargs,
    ):
        import torch

        self.epochs = epochs
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.image_size = image_size
        self.num_conv_blocks = num_conv_blocks
        self.initial_filters = initial_filters
        self.dropout_rate = dropout_rate
        self.weight_decay = weight_decay
        self._device_name = device
        self.device = torch.device(
            f"cuda:{DEVICE_TO_IDX.get(device)}"
            if DEVICE_TO_IDX.get(device, -1) >= 0
            else "cpu"
        )
        self.model = None
        self.optimizer = None
        self.input_channels = None
        self.num_classes = None
        self.idx_to_label = {}
        self.label_to_idx = {}

    def _validate_architecture(self):
        min_size = 2**self.num_conv_blocks
        if self.image_size < min_size:
            raise ValueError(
                f"image_size ({self.image_size}) must be at least "
                f"2^num_conv_blocks = {min_size} "
                f"for {self.num_conv_blocks} convolutional block(s)."
            )

    def get_inference_transform(self):
        """Return the transform applied to input images at inference time.

        Returns
        -------
        Callable
            Resize and tensor conversion matching the training pipeline
            (no normalization).
        """
        from torchvision import transforms

        return transforms.Compose(
            [
                transforms.Lambda(lambda img: img.convert("RGB")),
                transforms.Resize((self.image_size, self.image_size)),
                transforms.ToTensor(),
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
        """Train the CNN on the provided image dataset.

        Parameters
        ----------
        x_train : DashAIDataset
            Input dataset containing images.
        y_train : DashAIDataset
            Target dataset containing labels.
        x_validation : DashAIDataset, optional
            Validation input features. Defaults to None.
        y_validation : DashAIDataset, optional
            Validation target labels. Defaults to None.

        Returns
        -------
        CNNImageClassifier
            The trained model instance.
        """
        import torch
        import torch.nn as nn
        import torch.optim as optim
        import torch.utils.data

        from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum

        self._validate_architecture()

        image_dataset = _make_image_dataset(
            x_train, y_dataset=y_train, image_size=self.image_size
        )
        self.input_channels = image_dataset.tensor_shape[0]
        self.num_classes = image_dataset.num_classes()
        self.idx_to_label = image_dataset.idx_to_label
        self.label_to_idx = image_dataset.label_to_idx

        train_loader = torch.utils.data.DataLoader(
            image_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            collate_fn=self._collate_fn_with_labels,
        )

        self.model = _build_cnn_model(
            self.input_channels,
            self.image_size,
            self.num_classes,
            self.num_conv_blocks,
            self.initial_filters,
            self.dropout_rate,
        ).to(self.device)

        criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(
            self.model.parameters(),
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
                "num_conv_blocks": self.num_conv_blocks,
                "initial_filters": self.initial_filters,
                "dropout_rate": self.dropout_rate,
                "weight_decay": self.weight_decay,
                "device_name": self._device_name,
                "input_channels": self.input_channels,
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
        CNNImageClassifier
            Instance with loaded weights.
        """
        import torch
        import torch.optim as optim

        ckpt = torch.load(filename, map_location=torch.device("cpu"))
        instance = cls(
            epochs=ckpt["epochs"],
            learning_rate=ckpt["learning_rate"],
            batch_size=ckpt.get("batch_size", 32),
            image_size=ckpt.get("image_size", 64),
            num_conv_blocks=ckpt.get("num_conv_blocks", 3),
            initial_filters=ckpt.get("initial_filters", 32),
            dropout_rate=ckpt.get("dropout_rate", 0.0),
            weight_decay=ckpt.get("weight_decay", 0.0),
            device=ckpt.get("device_name", DEVICE_PLACEHOLDER),
        )
        instance.input_channels = ckpt["input_channels"]
        instance.num_classes = ckpt["num_classes"]
        instance.idx_to_label = ckpt.get("idx_to_label", {})
        instance.label_to_idx = ckpt.get("label_to_idx", {})
        instance.model = _build_cnn_model(
            instance.input_channels,
            instance.image_size,
            instance.num_classes,
            instance.num_conv_blocks,
            instance.initial_filters,
            instance.dropout_rate,
        )
        instance.model.load_state_dict(ckpt["model_state_dict"])
        instance.optimizer = optim.Adam(
            instance.model.parameters(),
            weight_decay=instance.weight_decay,
        )
        instance.optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        return instance
