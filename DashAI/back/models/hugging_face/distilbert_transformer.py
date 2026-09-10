"""DashAI implementation of DistilBERT model for english classification."""

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    none_type,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.base_text_classification_transformer import (
    HuggingFaceTextClassificationTransformer,
)
from DashAI.back.models.utils import GPU_OR_CPU, GPU_OR_CPU_PLACEHOLDER


class DistilBertTransformerSchema(BaseSchema):
    """Distilbert is a transformer that allows you to classify text in English.
    The implementation is based on huggingface distilbert-base in the case of
    the uncased model, i.e. distilbert-base-uncased.
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
        placeholder=16,
        description=MultilingualString(
            en="The batch size per GPU/TPU core/CPU for training",
            es="El tamaño de lote por núcleo GPU/TPU/CPU para entrenamiento",
            pt="O tamanho do lote por núcleo GPU/TPU/CPU para treinamento",
            de="Die Stapelgröße pro GPU/TPU-Kern/CPU für das Training",
            zh="每个 GPU/TPU 核心/CPU 的训练批次大小",
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
        placeholder=3e-5,
        description=MultilingualString(
            en="The initial learning rate for AdamW optimizer",
            es="La tasa de aprendizaje inicial para el optimizador AdamW",
            pt="A taxa de aprendizado inicial para o otimizador AdamW",
            de="Die anfängliche Lernrate für den AdamW-Optimierer",
            zh="AdamW 优化器的初始学习率",
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
                "Hardware on which the training is run. If available, GPU is "
                "recommended for efficiency reasons. Otherwise, use CPU."
            ),
            es=(
                "Hardware en el que se ejecuta el entrenamiento. Si está disponible, "
                "se recomienda GPU por razones de eficiencia. De lo contrario, use CPU."
            ),
            pt=(
                "Hardware no qual o treinamento é executado. Se disponível, GPU é "
                "recomendada por razões de eficiência. Caso contrário, use CPU."
            ),
            de=(
                "Hardware, auf der das Training ausgeführt wird. Falls verfügbar, wird "
                "GPU aus Effizienzgründen empfohlen. Andernfalls CPU verwenden."
            ),
            zh="训练运行所用硬件。如有 GPU，建议使用以提高效率，否则使用 CPU。",
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
                "Weight decay is a regularization technique used in training "
                "neural networks to prevent overfitting. In the context of the AdamW "
                "optimizer, the 'weight_decay' parameter is the rate at which the "
                "weights of all layers are reduced during training, provided that "
                "this rate is not zero."
            ),
            es=(
                "Weight decay es una técnica de regularización usada en el "
                "entrenamiento de redes neuronales para prevenir sobreajuste. En el "
                "contexto del optimizador AdamW, el parámetro 'weight_decay' es la "
                "tasa a la cual los pesos de todas las capas se reducen durante el "
                "entrenamiento, siempre que esta tasa no sea cero."
            ),
            pt=(
                "O decaimento de peso é uma técnica de regularização usada no "
                "treinamento de redes neurais para prevenir sobreajuste. No contexto "
                "do otimizador AdamW, o parâmetro 'weight_decay' é a taxa na qual os "
                "pesos de todas as camadas são reduzidos durante o treinamento, desde "
                "que esta taxa não seja zero."
            ),
            de=(
                "Gewichtsabnahme ist eine Regularisierungstechnik im Training "
                "neuronaler Netze zur Vermeidung von Überanpassung. Im Kontext des "
                "AdamW-Optimierers ist 'weight_decay' die Rate, mit der die Gewichte "
                "aller Schichten während des Trainings reduziert werden, sofern diese "
                "Rate nicht null ist."
            ),
            zh=(
                "权重衰减是神经网络训练中用于防止过拟合的正则化技术。"
                "在 AdamW 优化器中，'weight_decay' 参数表示训练过程中各层权重的"
                "衰减速率，当该速率不为零时生效。"
            ),
        ),
        alias=MultilingualString(
            en="Weight decay",
            es="Decaimiento de pesos",
            pt="Decaimento de peso",
            de="Gewichtsabnahme",
            zh="权重衰减",
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
                "Trainingsmetriken alle n Epochen protokollieren. "
                "Bei None wird kein epochenweises Protokoll erstellt."
            ),
            zh="训练期间每 n 个轮次记录训练集指标。若为 None，则不按轮次记录。",
        ),
        alias=MultilingualString(
            en="Log train every N epochs",
            es="Registrar entrenamiento cada N épocas",
            pt="Registrar treinamento a cada N épocas",
            de="Training alle N Epochen protokollieren",
            zh="每 N 轮记录训练指标",
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
                "Trainingsmetriken alle n Schritte protokollieren. "
                "Bei None wird kein schrittweises Protokoll erstellt."
            ),
            zh="训练期间每 n 步记录训练集指标。若为 None，则不按步骤记录。",
        ),
        alias=MultilingualString(
            en="Log train every N steps",
            es="Registrar entrenamiento cada N pasos",
            pt="Registrar treinamento a cada N passos",
            de="Training alle N Schritte protokollieren",
            zh="每 N 步记录训练指标",
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
                "Validierungsmetriken alle n Epochen protokollieren. "
                "Bei None wird kein epochenweises Protokoll erstellt."
            ),
            zh="训练期间每 n 个轮次记录验证集指标。若为 None，则不按轮次记录。",
        ),
        alias=MultilingualString(
            en="Log validation every N epochs",
            es="Registrar validación cada N épocas",
            pt="Registrar validação a cada N épocas",
            de="Validierung alle N Epochen protokollieren",
            zh="每 N 轮记录验证指标",
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
                "Validierungsmetriken alle n Schritte protokollieren. "
                "Bei None wird kein schrittweises Protokoll erstellt."
            ),
            zh="训练期间每 n 步记录验证集指标。若为 None，则不按步骤记录。",
        ),
        alias=MultilingualString(
            en="Log validation every N steps",
            es="Registrar validación cada N pasos",
            pt="Registrar validação a cada N passos",
            de="Validierung alle N Schritte protokollieren",
            zh="每 N 步记录验证指标",
        ),
    )  # type: ignore


class DistilBertTransformer(HuggingFaceTextClassificationTransformer):
    """Pretrained transformer DistilBERT allowing English text classification.

    DistilBERT is a small, fast, cheap and light Transformer model trained by
    distilling BERT base.
    It has 40% less parameters than bert-base-uncased, runs 60% faster while preserving
    over 95% of BERT's performances as measured on the GLUE language understanding
    benchmark [1].

    References
    ----------
    - [1] https://huggingface.co/docs/transformers/model_doc/distilbert
    """

    DISPLAY_NAME: str = MultilingualString(
        en="DistilBERT Transformer",
        es="Transformer DistilBERT",
        pt="Transformer DistilBERT",
        de="DistilBERT Transformer",
        zh="DistilBERT Transformer",
    )
    DESCRIPTION: str = MultilingualString(
        en="Distilled BERT model for efficient text classification.",
        es="Modelo BERT destilado para clasificación de texto eficiente.",
        pt="Modelo BERT destilado para classificação de texto eficiente.",
        de="Destilliertes BERT-Modell für effiziente Textklassifikation.",
        zh="蒸馏 BERT 模型，用于高效文本分类。",
    )
    COLOR: str = "#96008E"
    ICON: str = "Psychology"
    SCHEMA = DistilBertTransformerSchema
    MODEL_NAME: str = "distilbert-base-uncased"
    DOWNLOAD_SIZE_BYTES: int = 536641210
    TEMP_CHECKPOINT_DIR: str = "DashAI/back/user_models/temp_checkpoints_distilbert"
