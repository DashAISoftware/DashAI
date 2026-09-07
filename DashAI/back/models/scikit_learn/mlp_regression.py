from typing import TYPE_CHECKING

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    int_field,
    none_type,
    optimizer_float_field,
    optimizer_int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.categorical_encoder_mixin import CategoricalEncoderMixin
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.utils import DEVICE_ENUM, DEVICE_PLACEHOLDER, DEVICE_TO_IDX

if TYPE_CHECKING:
    from numpy import ndarray

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class MLPRegressorSchema(BaseSchema):
    """Schema that configures the Multi-layer Perceptron (MLP) Regressor.

    The MLP Regressor is a fully-connected feedforward neural network with a single
    hidden layer, trained with backpropagation using the Adam optimiser and mean
    squared error loss. It is used for tabular regression tasks. The underlying
    implementation uses PyTorch (``torch.nn``).
    """

    hidden_size: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 16,
            "lower_bound": 1,
            "upper_bound": 64,
        },
        description=MultilingualString(
            en="Number of neurons in the hidden layer.",
            es="Número de neuronas en la capa oculta.",
            pt="Número de neurônios na camada oculta.",
            de="Anzahl der Neuronen in der verdeckten Schicht.",
            zh="隐藏层的神经元数量。",
        ),
        alias=MultilingualString(
            en="Hidden size",
            es="Tamaño oculto",
            pt="Tamanho oculto",
            de="Verdeckte Schichtgröße",
            zh="隐藏层大小",
        ),
    )  # type: ignore

    activation: schema_field(
        enum_field(enum=["relu", "tanh", "sigmoid", "identity"]),
        placeholder="relu",
        description=MultilingualString(
            en="Activation function.",
            es="Función de activación.",
            pt="Função de ativação.",
            de="Aktivierungsfunktion.",
            zh="激活函数。",
        ),
        alias=MultilingualString(
            en="Activation",
            es="Activación",
            pt="Ativação",
            de="Aktivierung",
            zh="激活函数",
        ),
    )  # type: ignore

    learning_rate: schema_field(
        optimizer_float_field(ge=1e-6, le=1.0),
        placeholder={
            "optimize": False,
            "fixed_value": 0.001,
            "lower_bound": 1e-6,
            "upper_bound": 1.0,
        },
        description=MultilingualString(
            en="Initial learning rate for the optimizer.",
            es="Tasa de aprendizaje inicial para el optimizador.",
            pt="Taxa de aprendizado inicial para o otimizador.",
            de="Anfängliche Lernrate für den Optimierer.",
            zh="优化器的初始学习率。",
        ),
        alias=MultilingualString(
            en="Learning rate",
            es="Tasa de aprendizaje",
            pt="Taxa de aprendizado",
            de="Lernrate",
            zh="学习率",
        ),
    )  # type: ignore

    epochs: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 20,
            "lower_bound": 1,
            "upper_bound": 50,
        },
        description=MultilingualString(
            en="Total number of training passes over the dataset.",
            es="Número total de pasadas de entrenamiento sobre el conjunto de datos.",
            pt="Número total de passagens de treinamento sobre o conjunto de dados.",
            de="Gesamtanzahl der Trainingsdurchläufe über den Datensatz.",
            zh="对数据集的总训练轮数。",
        ),
        alias=MultilingualString(
            en="Epochs", es="Épocas", pt="Épocas", de="Epochen", zh="训练轮数"
        ),
    )  # type: ignore

    batch_size: schema_field(
        none_type(int_field(ge=1)),
        placeholder=32,
        description=MultilingualString(
            en=(
                "Number of samples per gradient update during training. "
                "If greater than dataset size or None, uses full dataset."
            ),
            es=(
                "Número de muestras por actualización de gradiente durante el "
                "entrenamiento. Si es mayor que el tamaño del dataset o None, "
                "usa el dataset completo."
            ),
            pt=(
                "Número de amostras por atualização de gradiente durante o "
                "treinamento. Se maior que o tamanho do conjunto ou None, "
                "usa o conjunto completo."
            ),
            de=(
                "Anzahl der Stichproben pro Gradienten-Update während des Trainings. "
                "Bei größer als Datensatzgröße oder None wird der vollständige "
                "Datensatz verwendet."
            ),
            zh="训练时每次梯度更新的样本数。若大于数据集大小或为None，则使用全部数据集。",
        ),
        alias=MultilingualString(
            en="Batch size",
            es="Tamaño de lote",
            pt="Tamanho do lote",
            de="Stapelgröße",
            zh="批量大小",
        ),
    )  # type: ignore

    device: schema_field(
        enum_field(enum=DEVICE_ENUM),
        placeholder=DEVICE_PLACEHOLDER,
        description=MultilingualString(
            en="Hardware device (CPU/GPU).",
            es="Dispositivo de hardware (CPU/GPU).",
            pt="Dispositivo de hardware (CPU/GPU).",
            de="Hardwaregerät (CPU/GPU).",
            zh="硬件设备（CPU/GPU）。",
        ),
        alias=MultilingualString(
            en="Device", es="Dispositivo", pt="Dispositivo", de="Gerät", zh="设备"
        ),
    )  # type: ignore

    log_train_every_n_epochs: schema_field(
        none_type(int_field(ge=1)),
        placeholder=1,
        description=MultilingualString(
            en=(
                "Log metrics for train split every n epochs during training. "
                "If None, it won't log per epoch."
            ),
            es=(
                "Registrar métricas del split de entrenamiento cada n épocas. "
                "Si es None, no registrará por época."
            ),
            pt=(
                "Registrar métricas do split de treinamento a cada n épocas. "
                "Se None, não registrará por época."
            ),
            de=(
                "Trainingsmetriken jede n-te Epoche protokollieren. "
                "Bei None keine Protokollierung pro Epoche."
            ),
            zh="训练时每n个轮次记录训练集指标。若为None，则不按轮次记录。",
        ),
        alias=MultilingualString(
            en="Log train every N epochs",
            es="Registrar entrenamiento cada N épocas",
            pt="Registrar treinamento a cada N épocas",
            de="Training alle N Epochen protokollieren",
            zh="每N轮记录训练指标",
        ),
    )  # type: ignore

    log_train_every_n_steps: schema_field(
        none_type(int_field(ge=1)),
        placeholder=None,
        description=MultilingualString(
            en=(
                "Log metrics for train split every n steps during training. "
                "If None, it won't log per step."
            ),
            es=(
                "Registrar métricas del split de entrenamiento cada n pasos. "
                "Si es None, no registrará por paso."
            ),
            pt=(
                "Registrar métricas do split de treinamento a cada n passos. "
                "Se None, não registrará por passo."
            ),
            de=(
                "Trainingsmetriken jeden n-ten Schritt protokollieren. "
                "Bei None keine Protokollierung pro Schritt."
            ),
            zh="训练时每n步记录训练集指标。若为None，则不按步数记录。",
        ),
        alias=MultilingualString(
            en="Log train every N steps",
            es="Registrar entrenamiento cada N pasos",
            pt="Registrar treinamento a cada N passos",
            de="Training alle N Schritte protokollieren",
            zh="每N步记录训练指标",
        ),
    )  # type: ignore

    log_validation_every_n_epochs: schema_field(
        none_type(int_field(ge=1)),
        placeholder=1,
        description=MultilingualString(
            en=(
                "Log metrics for validation split every n epochs during training. "
                "If None, it won't log per epoch."
            ),
            es=(
                "Registrar métricas del split de validación cada n épocas. "
                "Si es None, no registrará por época."
            ),
            pt=(
                "Registrar métricas do split de validação a cada n épocas. "
                "Se None, não registrará por época."
            ),
            de=(
                "Validierungsmetriken jede n-te Epoche protokollieren. "
                "Bei None keine Protokollierung pro Epoche."
            ),
            zh="训练时每n个轮次记录验证集指标。若为None，则不按轮次记录。",
        ),
        alias=MultilingualString(
            en="Log validation every N epochs",
            es="Registrar validación cada N épocas",
            pt="Registrar validação a cada N épocas",
            de="Validierung alle N Epochen protokollieren",
            zh="每N轮记录验证指标",
        ),
    )  # type: ignore

    log_validation_every_n_steps: schema_field(
        none_type(int_field(ge=1)),
        placeholder=None,
        description=MultilingualString(
            en=(
                "Log metrics for validation split every n steps during training. "
                "If None, it won't log per step."
            ),
            es=(
                "Registrar métricas del split de validación cada n pasos. "
                "Si es None, no registrará por paso."
            ),
            pt=(
                "Registrar métricas do split de validação a cada n passos. "
                "Se None, não registrará por passo."
            ),
            de=(
                "Validierungsmetriken jeden n-ten Schritt protokollieren. "
                "Bei None keine Protokollierung pro Schritt."
            ),
            zh="训练时每n步记录验证集指标。若为None，则不按步数记录。",
        ),
        alias=MultilingualString(
            en="Log validation every N steps",
            es="Registrar validación cada N pasos",
            pt="Registrar validação a cada N passos",
            de="Validierung alle N Schritte protokollieren",
            zh="每N步记录验证指标",
        ),
    )  # type: ignore


class MLPRegression(CategoricalEncoderMixin, RegressionModel):
    """Single hidden-layer MLP regressor implemented in PyTorch.

    A Multi-layer Perceptron (MLP) is a feedforward neural network composed of an
    input layer, one hidden layer of configurable width, and a single linear output
    neuron. The hidden layer uses a configurable activation function (ReLU, tanh,
    sigmoid, or identity). The network is trained by minimising the mean squared
    error using the Adam optimiser and mini-batch gradient descent via
    backpropagation.

    Key hyperparameters include ``hidden_size`` (number of neurons in the hidden
    layer), ``activation``, ``learning_rate``, ``epochs``, ``batch_size``, and
    ``device`` (CPU or GPU). The model also supports per-epoch and per-step metric
    logging. The implementation uses PyTorch (``torch.nn``).

    References
    ----------
    - [1] Rumelhart, D.E., Hinton, G.E., & Williams, R.J. (1986).
           "Learning representations by back-propagating errors."
           Nature, 323(6088), 533-536. https://doi.org/10.1038/323533a0
    - [2] Kingma, D.P. & Ba, J. (2015). "Adam: A Method for Stochastic
           Optimization." ICLR 2015. https://arxiv.org/abs/1412.6980
    """

    SCHEMA = MLPRegressorSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Multi-layer Perceptron (MLP) Regression",
        es="Perceptrón Multicapa (MLP) Regresión",
        pt="Regressor MLP",
        de="Mehrschichtiges Perzeptron (MLP) Regression",
        zh="多层感知机（MLP）回归",
    )
    DESCRIPTION: str = MultilingualString(
        en="Neural network with multiple hidden layers for regression.",
        es="Red neuronal con múltiples capas ocultas para regresión.",
        pt="Rede neural com múltiplas camadas ocultas para regressão.",
        de="Neuronales Netz mit mehreren verdeckten Schichten für Regression.",
        zh="具有多个隐藏层的神经网络，用于回归任务。",
    )
    COLOR: str = "#FF7043"
    ICON: str = "Psychology"

    def __init__(self, **kwargs) -> None:
        """Initialize the MLP regressor and set up the inner PyTorch module class.

        Parameters
        ----------
        **kwargs : dict
            Configuration keyword arguments matching ``MLPRegressorSchema`` fields,
            including ``hidden_size``, ``activation``, ``learning_rate``, ``epochs``,
            ``batch_size``, and ``device``.
        """
        import torch.nn as nn

        class MLP(nn.Module):
            """Single hidden-layer feedforward network built as a ``nn.Sequential``.

            Used internally by ``MLPRegression`` to create a configurable
            MLP with one hidden layer, the chosen activation function, and a
            linear output layer.
            """

            def __init__(self, input_dim, hidden_size, activation_name):
                """Build the sequential MLP architecture.

                Parameters
                ----------
                input_dim : int
                    Number of input features.
                hidden_size : int
                    Number of units in the single hidden layer.
                activation_name : str
                    Activation function name: one of ``"relu"``, ``"tanh"``,
                    ``"sigmoid"``, or ``"identity"``.  Defaults to ReLU if the
                    name is not recognised.
                """
                super().__init__()
                activations = {
                    "relu": nn.ReLU(),
                    "tanh": nn.Tanh(),
                    "sigmoid": nn.Sigmoid(),
                    "identity": nn.Identity(),
                }
                self.model = nn.Sequential(
                    nn.Linear(input_dim, hidden_size),
                    activations.get(activation_name, nn.ReLU()),
                    nn.Linear(hidden_size, 1),
                )

            def forward(self, x):
                """Run a forward pass through the network.

                Parameters
                ----------
                x : torch.Tensor
                    Input tensor of shape ``(batch_size, input_dim)``.

                Returns
                -------
                torch.Tensor
                    Output tensor of shape ``(batch_size, 1)``.
                """
                return self.model(x)

        self.mlp = MLP

        self.params = kwargs
        self.device = (
            f"cuda:{DEVICE_TO_IDX.get(kwargs.get('device'))}"
            if DEVICE_TO_IDX.get(kwargs.get("device"), -1) >= 0
            else "cpu"
        )
        self.model = None

        # Initialise the categorical encoder state inherited from
        # CategoricalEncoderMixin. These fields are persisted by ``save`` and
        # restored by ``load`` so ``predict`` reuses the training-time encoders.
        self._setup_categorical_encoders()

    def train(
        self,
        x_train: "DashAIDataset",
        y_train: "DashAIDataset",
        x_validation: "DashAIDataset" = None,
        y_validation: "DashAIDataset" = None,
    ) -> "MLPRegression":
        """Train the MLP regressor using Adam optimiser and MSE loss.

        Parameters
        ----------
        x_train : DashAIDataset
            The input features for training.
        y_train : DashAIDataset
            The regression targets for training.
        x_validation : DashAIDataset, optional
            Input features for validation metric logging. Defaults to None.
        y_validation : DashAIDataset, optional
            Target values for validation metric logging. Defaults to None.

        Returns
        -------
        MLPRegression
            The trained model instance (self).
        """
        import torch

        # 1. Prepare Data
        x_values = self.prepare_dataset(x_train, is_fit=True).to_pandas().values
        y_values = self.prepare_output(y_train, is_fit=True).to_pandas().values

        X_tensor = torch.tensor(x_values, dtype=torch.float32).to(self.device)
        y_tensor = (
            torch.tensor(y_values, dtype=torch.float32).view(-1, 1).to(self.device)
        )

        # 2. Init Model & Optimizer
        self.model = self.mlp(
            input_dim=X_tensor.shape[1],
            hidden_size=self.params.get("hidden_size", 100),
            activation_name=self.params.get("activation", "relu"),
        ).to(self.device)

        optimizer = torch.optim.Adam(
            self.model.parameters(), lr=self.params.get("learning_rate", 0.001)
        )
        criterion = torch.nn.MSELoss()

        # 3. Training Loop using Epochs
        total_epochs = self.params.get("epochs", 3)
        batch_size = self.params.get("batch_size")
        if batch_size is None or batch_size > X_tensor.size(0):
            batch_size = X_tensor.size(0)

        global_step = 0
        for epoch in range(total_epochs):
            self.model.train()
            indices = torch.randperm(X_tensor.size(0))

            for i in range(0, X_tensor.size(0), batch_size):
                # Set model to train mode
                self.model.train()

                batch_idx = indices[i : i + batch_size]
                train_loss = criterion(
                    self.model(X_tensor[batch_idx]), y_tensor[batch_idx]
                )

                optimizer.zero_grad()
                train_loss.backward()
                optimizer.step()

                # Increment global step counter
                global_step += 1

                # Set model to eval for metric calculation
                self.model.eval()

                # Train metrics per step
                if self.log_train_every_n_steps and (
                    global_step % self.log_train_every_n_steps == 0
                ):
                    self.calculate_metrics(
                        split=SplitEnum.TRAIN,
                        level=LevelEnum.STEP,
                        x_data=x_train,
                        y_data=y_train,
                        log_index=global_step,
                    )

                # Validation metrics per step
                if (
                    self.log_validation_every_n_steps
                    and global_step % self.log_validation_every_n_steps == 0
                ):
                    self.calculate_metrics(
                        split=SplitEnum.VALIDATION,
                        level=LevelEnum.STEP,
                        x_data=x_validation,
                        y_data=y_validation,
                        log_index=global_step,
                    )

            # Set model to eval for metric calculation
            self.model.eval()

            # Train metrics per epoch
            if (
                self.log_train_every_n_epochs
                and (epoch + 1) % self.log_train_every_n_epochs == 0
            ):
                self.calculate_metrics(
                    split=SplitEnum.TRAIN,
                    level=LevelEnum.EPOCH,
                    x_data=x_train,
                    y_data=y_train,
                    log_index=epoch + 1,
                )

            # Validation metrics per epoch
            if (
                self.log_validation_every_n_epochs
                and (epoch + 1) % self.log_validation_every_n_epochs == 0
            ):
                self.calculate_metrics(
                    split=SplitEnum.VALIDATION,
                    level=LevelEnum.EPOCH,
                    x_data=x_validation,
                    y_data=y_validation,
                    log_index=epoch + 1,
                )

        return self

    def predict(self, x: "DashAIDataset") -> "ndarray":
        """Generate regression predictions for the input dataset.

        Parameters
        ----------
        x : DashAIDataset
            The input features to predict on.

        Returns
        -------
        ndarray
            Predicted continuous values as a 1-D NumPy array.
        """
        return self.predict_prepared(self.prepare_dataset(x, is_fit=False).to_pandas())

    def predict_prepared(self, features) -> "ndarray":
        """Predict from a feature matrix already in the model's feature space.

        Parameters
        ----------
        features : pandas.DataFrame or numpy.ndarray
            Feature matrix as produced by ``prepare_dataset``.

        Returns
        -------
        ndarray
            Predicted continuous values as a 1-D NumPy array.
        """
        import numpy as np
        import torch

        self.model.eval()
        x_proc = np.asarray(getattr(features, "values", features), dtype="float32")
        x_tensor = torch.tensor(x_proc, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            return self.model(x_tensor).cpu().numpy().flatten()

    def save(self, filename: str) -> None:
        """Save the trained model weights and configuration to disk.

        Parameters
        ----------
        filename : str
            Path where the model checkpoint will be saved.
        """
        import torch

        torch.save(
            {
                "state": self.model.state_dict(),
                "params": self.params,
                "input_dim": self.model.model[0].in_features,
                "encodings": self.encodings,
                "one_hot_encoder": self.one_hot_encoder,
                "categorical_columns": self.categorical_columns,
            },
            filename,
        )

    @staticmethod
    def load(filename: str) -> "MLPRegression":
        """Restore an ``MLPRegression`` instance from a saved checkpoint.

        Parameters
        ----------
        filename : str
            Path to the checkpoint file saved by ``save``.

        Returns
        -------
        MLPRegression
            The restored model instance with loaded weights.
        """
        import torch

        # weights_only=False is required because the checkpoint stores the
        # fitted categorical encoders (e.g. a scikit-learn OneHotEncoder), which
        # are not part of torch's safe-globals allowlist.
        data = torch.load(filename, weights_only=False)
        instance = MLPRegression(**data["params"])

        # Rebuild the model architecture using saved input_dim
        instance.model = instance.mlp(
            input_dim=data["input_dim"],
            hidden_size=instance.params.get("hidden_size", 5),
            activation_name=instance.params.get("activation", "relu"),
        ).to(instance.device)

        # Load the trained weights
        instance.model.load_state_dict(data["state"])

        # Restore the categorical encoders so predictions match training-time
        # preprocessing.
        instance.encodings = data.get("encodings", {})
        instance.one_hot_encoder = data.get("one_hot_encoder")
        instance.categorical_columns = data.get("categorical_columns", [])

        return instance
