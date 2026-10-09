"""OpusMtEnESTransformer model for English to Spanish translation."""

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    none_type,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_opus_mt_transformer import (
    OpusMtTransformerMixin,
)
from DashAI.back.models.utils import GPU_OR_CPU, GPU_OR_CPU_PLACEHOLDER


class OpusMtEnESTransformerSchema(BaseSchema):
    """Schema for Opus-MT translation models (MarianMT architecture).

    Shared by all Helsinki-NLP Opus-MT language pair wrappers. Controls
    training duration, batch size, learning rate, device, regularization, and
    metric logging frequency.
    """

    num_train_epochs: schema_field(
        int_field(ge=1),
        placeholder=1,
        description=MultilingualString(
            en="Total number of training epochs to perform.",
            es="Número total de épocas de entrenamiento a realizar.",
            pt="Número total de épocas de treinamento a realizar.",
            de="Gesamtanzahl der durchzuführenden Trainingsepochen.",
            zh="执行训练的总轮数。",
        ),
        alias=MultilingualString(
            en="Num train epochs",
            es="Número de épocas",
            pt="Número de épocas",
            de="Anzahl Trainingsepochen",
            zh="训练轮数",
        ),
    )  # type: ignore
    batch_size: schema_field(
        int_field(ge=1),
        placeholder=4,
        description=MultilingualString(
            en="The batch size per GPU/TPU core/CPU for training.",
            es="El tamaño de lote por núcleo GPU/TPU/CPU para entrenamiento.",
            pt="O tamanho do lote por núcleo GPU/TPU/CPU para treinamento.",
            de="Die Stapelgröße pro GPU/TPU-Kern/CPU für das Training.",
            zh="每个 GPU/TPU 核心/CPU 的训练批次大小。",
        ),
        alias=MultilingualString(
            en="Batch size",
            es="Tamaño de lote",
            pt="Tamanho do lote",
            de="Stapelgröße",
            zh="批次大小",
        ),
    )  # type: ignore
    learning_rate: schema_field(
        float_field(ge=0.0),
        placeholder=2e-5,
        description=MultilingualString(
            en="The initial learning rate for AdamW optimizer.",
            es="La tasa de aprendizaje inicial para el optimizador AdamW.",
            pt="A taxa de aprendizado inicial para o otimizador AdamW.",
            de="Die anfängliche Lernrate für den AdamW-Optimierer.",
            zh="AdamW 优化器的初始学习率。",
        ),
        alias=MultilingualString(
            en="Learning rate",
            es="Tasa de aprendizaje",
            pt="Taxa de aprendizado",
            de="Lernrate",
            zh="学习率",
        ),
    )  # type: ignore
    device: schema_field(
        enum_field(enum=GPU_OR_CPU),
        placeholder=GPU_OR_CPU_PLACEHOLDER,
        description=MultilingualString(
            en=(
                "Hardware on which training is run. GPU is recommended when "
                "available. If GPU is selected, all available GPUs are used."
            ),
            es=(
                "Hardware en el que se ejecuta el entrenamiento. Se recomienda "
                "GPU cuando está disponible. Si se selecciona GPU, se usan "
                "todas las GPUs disponibles."
            ),
            pt=(
                "Hardware no qual o treinamento é executado. GPU é recomendada "
                "quando disponível. Se GPU for selecionada, todas as GPUs "
                "disponíveis são usadas."
            ),
            de=(
                "Hardware, auf der das Training ausgeführt wird. GPU wird empfohlen, "
                "wenn verfügbar. Bei Auswahl von GPU werden alle verfügbaren GPUs "
                "verwendet."
            ),
            zh=(
                "运行训练所使用的硬件。推荐使用 GPU（如可用）。"
                "若选择 GPU，则使用所有可用的 GPU。"
            ),
        ),
        alias=MultilingualString(
            en="Device", es="Dispositivo", pt="Dispositivo", de="Gerät", zh="设备"
        ),
    )  # type: ignore
    weight_decay: schema_field(
        float_field(ge=0.0),
        placeholder=0.01,
        description=MultilingualString(
            en=(
                "L2 regularization coefficient applied via the AdamW optimizer "
                "to prevent overfitting."
            ),
            es=(
                "Coeficiente de regularización L2 aplicado mediante el "
                "optimizador AdamW para prevenir sobreajuste."
            ),
            pt=(
                "Coeficiente de regularização L2 aplicado pelo otimizador AdamW "
                "para evitar overfitting."
            ),
            de=(
                "L2-Regularisierungskoeffizient, der über den AdamW-Optimierer "
                "angewendet wird, um Überanpassung zu verhindern."
            ),
            zh=("通过 AdamW 优化器施加的 L2 正则化系数，用于防止过拟合。"),
        ),
        alias=MultilingualString(
            en="Weight decay",
            es="Decaimiento de pesos",
            pt="Decaimento de pesos",
            de="Gewichtsabnahme",
            zh="权重衰减",
        ),
    )  # type: ignore
    log_train_every_n_epochs: schema_field(
        none_type(int_field(ge=1)),
        placeholder=1,
        description=MultilingualString(
            en=("Log train metrics every N epochs. None disables per-epoch logging."),
            es=(
                "Registrar métricas de entrenamiento cada N épocas. "
                "None desactiva el registro por época."
            ),
            pt=(
                "Registrar métricas de treinamento a cada N épocas. "
                "None desativa o registro por época."
            ),
            de=(
                "Trainingsmetriken alle N Epochen protokollieren. "
                "None deaktiviert die epochenweise Protokollierung."
            ),
            zh=("每 N 个轮次记录一次训练指标。None 禁用按轮次记录。"),
        ),
        alias=MultilingualString(
            en="Log train every N epochs",
            es="Registrar entrenamiento cada N épocas",
            pt="Registrar treinamento a cada N épocas",
            de="Training alle N Epochen protokollieren",
            zh="每 N 轮记录训练",
        ),
    )  # type: ignore
    log_train_every_n_steps: schema_field(
        none_type(int_field(ge=1)),
        placeholder=None,
        description=MultilingualString(
            en=("Log train metrics every N steps. None disables per-step logging."),
            es=(
                "Registrar métricas de entrenamiento cada N pasos. "
                "None desactiva el registro por paso."
            ),
            pt=(
                "Registrar métricas de treinamento a cada N passos. "
                "None desativa o registro por passo."
            ),
            de=(
                "Trainingsmetriken alle N Schritte protokollieren. "
                "None deaktiviert die schrittweise Protokollierung."
            ),
            zh=("每 N 个步骤记录一次训练指标。None 禁用按步骤记录。"),
        ),
        alias=MultilingualString(
            en="Log train every N steps",
            es="Registrar entrenamiento cada N pasos",
            pt="Registrar treinamento a cada N passos",
            de="Training alle N Schritte protokollieren",
            zh="每 N 步记录训练",
        ),
    )  # type: ignore
    log_validation_every_n_epochs: schema_field(
        none_type(int_field(ge=1)),
        placeholder=1,
        description=MultilingualString(
            en=(
                "Log validation metrics every N epochs. "
                "None disables per-epoch logging."
            ),
            es=(
                "Registrar métricas de validación cada N épocas. "
                "None desactiva el registro por época."
            ),
            pt=(
                "Registrar métricas de validação a cada N épocas. "
                "None desativa o registro por época."
            ),
            de=(
                "Validierungsmetriken alle N Epochen protokollieren. "
                "None deaktiviert die epochenweise Protokollierung."
            ),
            zh=("每 N 个轮次记录一次验证指标。None 禁用按轮次记录。"),
        ),
        alias=MultilingualString(
            en="Log validation every N epochs",
            es="Registrar validación cada N épocas",
            pt="Registrar validação a cada N épocas",
            de="Validierung alle N Epochen protokollieren",
            zh="每 N 轮记录验证",
        ),
    )  # type: ignore
    log_validation_every_n_steps: schema_field(
        none_type(int_field(ge=1)),
        placeholder=None,
        description=MultilingualString(
            en=(
                "Log validation metrics every N steps. None disables per-step logging."
            ),
            es=(
                "Registrar métricas de validación cada N pasos. "
                "None desactiva el registro por paso."
            ),
            pt=(
                "Registrar métricas de validação a cada N passos. "
                "None desativa o registro por passo."
            ),
            de=(
                "Validierungsmetriken alle N Schritte protokollieren. "
                "None deaktiviert die schrittweise Protokollierung."
            ),
            zh=("每 N 个步骤记录一次验证指标。None 禁用按步骤记录。"),
        ),
        alias=MultilingualString(
            en="Log validation every N steps",
            es="Registrar validación cada N pasos",
            pt="Registrar validação a cada N passos",
            de="Validierung alle N Schritte protokollieren",
            zh="每 N 步记录验证",
        ),
    )  # type: ignore


class OpusMtEnESTransformer(OpusMtTransformerMixin):
    """Pretrained transformer for English to Spanish translation.

    Fine-tunes the Helsinki-NLP ``opus-mt-en-es`` checkpoint, a MarianMT
    seq2seq model trained on parallel English to Spanish corpora from the OPUS
    collection. Supports direct translation without pivot languages.

    References
    ----------
    - [1] https://huggingface.co/Helsinki-NLP/opus-mt-en-es
    - [2] https://opus.nlpl.eu/
    """

    MODEL_NAME: str = "Helsinki-NLP/opus-mt-en-es"
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_opus-mt-en-es"
    SCHEMA = OpusMtEnESTransformerSchema
    DOWNLOAD_SIZE_BYTES = 315310815
    DISPLAY_NAME: str = MultilingualString(
        en="Opus MT En-Es Transformer",
        es="Transformer Opus MT En-Es",
        pt="Transformer Opus MT En-Es",
        de="Opus MT En-Es Transformer",
        zh="Opus MT 英西翻译 Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Pretrained transformer for English to Spanish translation. "
            "Download its weights from Hugging Face before use (internet required)."
        ),
        es=(
            "Transformer preentrenado para traducción inglés-español. "
            "Descarga sus pesos de Hugging Face antes de usarlo (requiere internet)."
        ),
        pt=(
            "Transformer pré-treinado para tradução inglês-espanhol. "
            "Baixe seus pesos do Hugging Face antes de usar (requer internet)."
        ),
        de=(
            "Vortrainierter Transformer für Englisch-Spanisch-Übersetzung. "
            "Lädt die Gewichte vor der Nutzung von Hugging Face herunter "
            "(Internet erforderlich)."
        ),
        zh=(
            "用于英语到西班牙语翻译的预训练 Transformer。"
            "使用前需从 Hugging Face 下载权重（需要网络）。"
        ),
    )
    COLOR: str = "#FFA500"
    ICON: str = "Translate"
