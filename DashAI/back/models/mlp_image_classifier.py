"""MLP-based image classifier for DashAI."""

from __future__ import annotations

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    list_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.base_model import BaseModel
from DashAI.back.models.image_explainable_model import OcclusionSaliencyCompatibleModel
from DashAI.back.models.utils import DEVICE_ENUM, DEVICE_PLACEHOLDER, DEVICE_TO_IDX


class MLPImageClassifierSchema(BaseSchema):
    """Configuration parameters for the MLP Image Classifier."""

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
            zh="训练模型的轮数。一轮表示对训练数据的一次完整迭代。",
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

    hidden_dims: schema_field(
        list_field(int_field(ge=1), min_items=1),
        placeholder=[128, 64],
        description=MultilingualString(
            en=(
                "The hidden layers and their dimensions. Specify the number "
                "of units of each layer separated by commas."
            ),
            es=(
                "Las capas ocultas y sus dimensiones. Especifique el número "
                "de unidades de cada capa separadas por comas."
            ),
            pt=(
                "As camadas ocultas e suas dimensões. Especifique o número "
                "de unidades de cada camada separadas por vírgulas."
            ),
            de=(
                "Die verdeckten Schichten und ihre Dimensionen. Geben Sie die Anzahl "
                "der Einheiten jeder Schicht durch Kommas getrennt an."
            ),
            zh="隐藏层及其维度。用逗号分隔各层的单元数。",
        ),
        alias=MultilingualString(
            en="Hidden layer dimensions",
            es="Dimensiones de capas ocultas",
            pt="Dimensões das camadas ocultas",
            de="Dimensionen der verdeckten Schichten",
            zh="隐藏层维度",
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
                "Número de imágenes procesadas juntas en cada paso de entrenamiento. "
                "Valores más grandes aceleran el entrenamiento "
                "pero requieren más memoria."
            ),
            pt=(
                "Número de imagens processadas juntas em cada etapa de treinamento. "
                "Valores maiores aceleram o treinamento "
                "mas requerem mais memória."
            ),
            de=(
                "Anzahl der in jedem Trainingsschritt gemeinsam verarbeiteten Bilder. "
                "Größere Werte beschleunigen das Training, erfordern aber mehr "
                "Speicher."
            ),
            zh=(
                "每个训练步骤中同时处理的图像数量。较大的值加快训练速度，"
                "但需要更多内存。"
            ),
        ),
        alias=MultilingualString(
            en="Batch size",
            es="Tamaño de lote",
            pt="Tamanho do lote",
            de="Batch-Größe",
            zh="批大小",
        ),
    )  # type: ignore

    image_size: schema_field(
        int_field(ge=8),
        placeholder=64,
        description=MultilingualString(
            en=(
                "Images are resized to this value (in pixels) for both width "
                "and height before training. Larger sizes preserve more detail "
                "but increase training time."
            ),
            es=(
                "Las imágenes se redimensionan a este valor (en píxeles) "
                "tanto en ancho como en alto antes del entrenamiento. "
                "Tamaños más grandes preservan más detalle "
                "pero aumentan el tiempo de entrenamiento."
            ),
            pt=(
                "As imagens são redimensionadas para este valor (em pixels) "
                "tanto em largura quanto em altura antes do treinamento. "
                "Tamanhos maiores preservam mais detalhes "
                "mas aumentam o tempo de treinamento."
            ),
            de=(
                "Bilder werden vor dem Training auf diesen Wert (in Pixeln) "
                "für Breite und Höhe skaliert. Größere Werte erhalten mehr Details, "
                "erhöhen jedoch die Trainingszeit."
            ),
            zh="训练前将图像的宽和高缩放至该像素值。较大的尺寸保留更多细节，但会增加训练时间。",
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
                "Fraction of neurons randomly deactivated during each training step. "
                "Values between 0.2 and 0.5 help prevent overfitting. "
                "Use 0.0 to disable."
            ),
            es=(
                "Fracción de neuronas desactivadas aleatoriamente en cada paso de "
                "entrenamiento. Valores entre 0.2 y 0.5 ayudan a prevenir "
                "el sobreajuste. Use 0.0 para desactivarlo."
            ),
            pt=(
                "Fração de neurônios desativados aleatoriamente em cada etapa de "
                "treinamento. Valores entre 0.2 e 0.5 ajudam a prevenir "
                "o sobreajuste. Use 0.0 para desativar."
            ),
            de=(
                "Anteil der in jedem Trainingsschritt zufällig deaktivierten Neuronen. "
                "Werte zwischen 0.2 und 0.5 helfen, Überanpassung zu verhindern. "
                "Verwenden Sie 0.0 zum Deaktivieren."
            ),
            zh=(
                "每个训练步骤中随机停用的神经元比例。"
                "0.2 到 0.5 之间的值有助于防止过拟合。设为 0.0 可禁用。"
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
                "L2 regularization coefficient for the Adam optimizer. Penalizes large "
                "weights to improve generalization. Typical values: 1e-4 to 1e-2."
            ),
            es=(
                "Coeficiente de regularización L2 para el optimizador Adam. Penaliza "
                "pesos grandes para mejorar la generalización. "
                "Valores típicos: 1e-4 a 1e-2."
            ),
            pt=(
                "Coeficiente de regularização L2 para o otimizador Adam. Penaliza "
                "pesos grandes para melhorar a generalização. "
                "Valores típicos: 1e-4 a 1e-2."
            ),
            de=(
                "L2-Regularisierungskoeffizient für den Adam-Optimierer. "
                "Bestraft große Gewichte zur Verbesserung der Generalisierung. "
                "Typische Werte: 1e-4 bis 1e-2."
            ),
            zh=(
                "Adam 优化器的 L2 正则化系数。通过惩罚过大的权重来提升泛化能力。"
                "典型值：1e-4 到 1e-2。"
            ),
        ),
        alias=MultilingualString(
            en="Weight decay",
            es="Decaimiento de pesos",
            pt="Decaimento de pesos",
            de="Gewichtsverfall",
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
            de="Für Training und Inferenz verwendetes Hardware-Gerät (CPU/GPU).",
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


def _build_mlp_model(input_dim, output_dim, hidden_dims, dropout_rate=0.0):
    import torch.nn as nn

    class _MLP(nn.Module):
        def __init__(self, in_dim, out_dim, h_dims, drop_r):
            super().__init__()
            self.hidden_layers = nn.ModuleList()
            self.dropout_layers = nn.ModuleList()
            prev_dim = in_dim
            for h_dim in h_dims:
                self.hidden_layers.append(nn.Linear(prev_dim, h_dim))
                self.dropout_layers.append(nn.Dropout(drop_r))
                prev_dim = h_dim
            self.output_layer = nn.Linear(prev_dim, out_dim)
            self.relu = nn.ReLU()

        def forward(self, x):
            batch_size = x.shape[0]
            x = x.view(batch_size, -1)
            for layer, dropout in zip(
                self.hidden_layers, self.dropout_layers, strict=True
            ):
                x = dropout(self.relu(layer(x)))
            return self.output_layer(x)

    return _MLP(input_dim, output_dim, hidden_dims, dropout_rate)


class MLPImageClassifier(BaseModel, OcclusionSaliencyCompatibleModel):
    """MLP-based image classifier.

    A feed-forward neural network that flattens image pixels and passes them
    through configurable hidden layers with ReLU activation for classification.
    """

    SCHEMA = MLPImageClassifierSchema
    COMPATIBLE_COMPONENTS = ["ImageClassificationTask"]

    DISPLAY_NAME: str = MultilingualString(
        en="MLP Image Classifier",
        es="Clasificador de Imágenes MLP",
        pt="Classificador de Imagens MLP",
        de="MLP-Bildklassifikator",
        zh="多层感知机图像分类器",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "A Multi-Layer Perceptron (MLP) image classifier that flattens "
            "image pixels and passes them through configurable fully-connected "
            "hidden layers with ReLU activation for classification."
        ),
        es=(
            "Un clasificador de imágenes basado en Perceptrón Multicapa (MLP) "
            "que aplana los píxeles de la imagen y los pasa por capas ocultas "
            "completamente conectadas con activación ReLU para clasificación."
        ),
        pt=(
            "Um classificador de imagens baseado em Perceptron Multicamada (MLP) "
            "que achata os pixels da imagem e os passa por camadas ocultas "
            "completamente conectadas com ativação ReLU para classificação."
        ),
        de=(
            "Ein Bildklassifikator auf Basis eines Mehrschichtigen Perzeptrons (MLP), "
            "der Bildpixel abflacht und durch konfigurierbare vollständig verbundene "
            "verdeckte Schichten mit ReLU-Aktivierung zur Klassifikation leitet."
        ),
        zh=(
            "基于多层感知机（MLP）的图像分类器，将图像像素展平后"
            "通过可配置的全连接隐藏层（ReLU激活）进行分类。"
        ),
    )
    COLOR: str = "#E91E63"
    ICON: str = "ImageSearch"

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
        hidden_dims=None,
        batch_size=32,
        image_size=64,
        dropout_rate=0.0,
        weight_decay=0.0,
        device=DEVICE_PLACEHOLDER,
        **kwargs,
    ):
        import torch

        if hidden_dims is None:
            hidden_dims = [128, 64]
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.hidden_dims = hidden_dims
        self.batch_size = batch_size
        self.image_size = image_size
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
        self.input_dim = None
        self.output_dim = None
        self.idx_to_label = {}
        self.label_to_idx = {}

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
        labels = dataset[col_name]
        encoded = [self.label_to_idx.get(label, -1) for label in labels]
        table = pa.table({col_name: encoded})
        return DashAIDataset(table)

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        """Train the MLP on the provided image dataset.

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
        MLPImageClassifier
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

        self.input_dim = (
            image_dataset.tensor_shape[0]
            * image_dataset.tensor_shape[1]
            * image_dataset.tensor_shape[2]
        )
        self.output_dim = image_dataset.num_classes()
        self.idx_to_label = image_dataset.idx_to_label
        self.label_to_idx = image_dataset.label_to_idx

        train_loader = torch.utils.data.DataLoader(
            image_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            collate_fn=self._collate_fn_with_labels,
        )

        self.model = _build_mlp_model(
            self.input_dim, self.output_dim, self.hidden_dims, self.dropout_rate
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
                outputs = self.model(images)
                loss = criterion(outputs, labels)
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
        """Make predictions on the input dataset.

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
        test_loader = torch.utils.data.DataLoader(
            image_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            collate_fn=self._collate_fn_no_labels,
        )

        self.model.to(self.device)
        self.model.eval()
        all_probs = []
        with torch.no_grad():
            for images in test_loader:
                images = images.to(self.device)
                logits = self.model(images)
                probs = torch.softmax(logits, dim=1)
                all_probs.append(probs.cpu())

        return (
            torch.cat(all_probs, dim=0).numpy()
            if all_probs
            else np.empty((0, self.output_dim))
        )

    def save(self, filename: str) -> None:
        """Save the model checkpoint to disk.

        Parameters
        ----------
        filename : str
            Path where the checkpoint will be saved.
        """
        import torch

        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "epochs": self.epochs,
            "learning_rate": self.learning_rate,
            "hidden_dims": self.hidden_dims,
            "batch_size": self.batch_size,
            "image_size": self.image_size,
            "dropout_rate": self.dropout_rate,
            "weight_decay": self.weight_decay,
            "device_name": self._device_name,
            "input_dim": self.input_dim,
            "output_dim": self.output_dim,
            "idx_to_label": self.idx_to_label,
            "label_to_idx": self.label_to_idx,
        }
        torch.save(checkpoint, filename)

    @classmethod
    def load(cls, filename: str):
        """Load a model checkpoint from disk.

        Parameters
        ----------
        filename : str
            Path to the checkpoint file.

        Returns
        -------
        MLPImageClassifier
            Instance with loaded weights.
        """
        import torch
        import torch.optim as optim

        checkpoint = torch.load(filename, map_location=torch.device("cpu"))
        instance = cls(
            epochs=checkpoint["epochs"],
            learning_rate=checkpoint["learning_rate"],
            hidden_dims=checkpoint["hidden_dims"],
            batch_size=checkpoint.get("batch_size", 32),
            image_size=checkpoint.get("image_size", 64),
            dropout_rate=checkpoint.get("dropout_rate", 0.0),
            weight_decay=checkpoint.get("weight_decay", 0.0),
            device=checkpoint.get("device_name", DEVICE_PLACEHOLDER),
        )
        instance.input_dim = checkpoint["input_dim"]
        instance.output_dim = checkpoint["output_dim"]
        instance.model = _build_mlp_model(
            instance.input_dim,
            instance.output_dim,
            instance.hidden_dims,
            instance.dropout_rate,
        )
        instance.model.load_state_dict(checkpoint["model_state_dict"])
        instance.optimizer = optim.Adam(
            instance.model.parameters(),
            weight_decay=instance.weight_decay,
        )
        instance.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        instance.idx_to_label = checkpoint.get("idx_to_label", {})
        instance.label_to_idx = checkpoint.get("label_to_idx", {})
        return instance
