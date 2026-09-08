"""Promptable instance segmentation converter that appends ranked columns."""

import io
from typing import TYPE_CHECKING, Dict, Optional

from kink import di

from DashAI.back.converters.category.advanced_preprocessing import (
    AdvancedPreprocessingConverter,
)
from DashAI.back.core.schema_fields import (
    bool_field,
    enum_field,
    float_field,
    int_field,
    schema_field,
    string_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.downloadable import (
    HFPretrainedDownloadMixin,
    ProgressReporter,
)
from DashAI.back.models.utils import (
    DEVICE_ENUM,
    DEVICE_PLACEHOLDER,
    DEVICE_TO_IDX,
)
from DashAI.back.segmenters.rendering import render_binary_mask, render_segment
from DashAI.back.segmenters.sam3_segmenter import SAM3Segmenter
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Float

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
    from DashAI.back.segmenters.base_segmenter import BaseSegmenter

SEGMENT_COLUMN = "segment"
SCORE_COLUMN = "seg_score"
MASK_COLUMN = "mask"

_BACKGROUND_FILLS = ["black", "white", "blur"]
_NO_DETECTION_POLICIES = ["empty", "keep_original", "error"]


def _segment_column(rank: int) -> str:
    """Name of the segment image column for a given rank, 1 based."""
    return f"{SEGMENT_COLUMN}_{rank}"


def _score_column(rank: int) -> str:
    """Name of the confidence score column for a given rank, 1 based."""
    return f"{SCORE_COLUMN}_{rank}"


def _mask_column(rank: int) -> str:
    """Name of the binary mask column for a given rank, 1 based."""
    return f"{MASK_COLUMN}_{rank}"


class SAM3SegmentConverterSchema(BaseSchema):
    """Configuration schema for the SAM3 segmentation converter."""

    prompt: schema_field(
        string_field(),
        "",
        description=MultilingualString(
            en="Text describing the object to find in each image, for "
            "example 'cow'. Passed verbatim to the segmenter.",
            es="Texto que describe el objeto a buscar en cada imagen, por "
            "ejemplo 'vaca'. Se entrega tal cual al segmentador.",
            pt="Texto que descreve o objeto a ser encontrado em cada "
            "imagem, por exemplo 'vaca'. É repassado literalmente ao "
            "segmentador.",
            de="Text, der das in jedem Bild zu findende Objekt beschreibt, "
            "zum Beispiel 'Kuh'. Wird unverändert an den Segmentierer "
            "übergeben.",
            zh="描述要在每张图像中查找的对象的文本，例如“牛”。将原样传递给分割器。",
        ),
    )  # type: ignore

    image_column: schema_field(
        int_field(ge=1),
        1,
        description=MultilingualString(
            en="1 based index, among the columns selected in the scope, "
            "of the image column to segment.",
            es="Índice, con base 1, entre las columnas seleccionadas en "
            "el alcance, de la columna de imagen a segmentar.",
            pt="Índice, com base 1, entre as colunas selecionadas no "
            "escopo, da coluna de imagem a ser segmentada.",
            de="1 basierter Index, unter den im Geltungsbereich "
            "ausgewählten Spalten, der zu segmentierenden Bildspalte.",
            zh="范围内所选列中，要分割的图像列的索引，从 1 开始。",
        ),
    )  # type: ignore

    max_masks: schema_field(
        int_field(ge=1),
        1,
        description=MultilingualString(
            en="Maximum number of detected instances kept per image. "
            "Instances are ranked by descending confidence score, and only "
            "the top max_masks are kept. This also fixes the number of "
            "segment_i, seg_score_i, and, when keep_binary_mask is "
            "enabled, mask_i columns the converter produces, so the "
            "output schema depends on this configuration.",
            es="Número máximo de instancias detectadas que se conservan "
            "por imagen. Las instancias se clasifican por puntuación de "
            "confianza descendente, y se conservan solo las max_masks "
            "principales. Esto también fija la cantidad de columnas "
            "segment_i, seg_score_i y, cuando keep_binary_mask está "
            "habilitado, mask_i que produce el convertidor, por lo que el "
            "esquema de salida depende de esta configuración.",
            pt="Número máximo de instâncias detectadas mantidas por "
            "imagem. As instâncias são classificadas por pontuação de "
            "confiança descendente e apenas as max_masks principais são "
            "mantidas. Isso também fixa a quantidade de colunas "
            "segment_i, seg_score_i e, quando keep_binary_mask está "
            "habilitado, mask_i que o conversor produz, portanto o "
            "esquema de saída depende dessa configuração.",
            de="Maximale Anzahl der pro Bild beibehaltenen erkannten "
            "Instanzen. Instanzen werden nach absteigender "
            "Konfidenzwertung sortiert, und nur die top max_masks werden "
            "beibehalten. Dies legt außerdem die Anzahl der vom Konverter "
            "erzeugten Spalten segment_i, seg_score_i und, wenn "
            "keep_binary_mask aktiviert ist, mask_i fest, sodass das "
            "Ausgabeschema von dieser Konfiguration abhängt.",
            zh="每张图像保留的检测实例的最大数量。实例按置信度分数降序排"
            "列，仅保留前 max_masks 个。这也决定了转换器生成的 "
            "segment_i、seg_score_i 以及在启用 keep_binary_mask 时 "
            "mask_i 列的数量，因此输出模式取决于此配置。",
        ),
    )  # type: ignore

    min_score: schema_field(
        float_field(ge=0.0, le=1.0),
        0.5,
        description=MultilingualString(
            en="Minimum confidence score an instance must have to be kept.",
            es="Puntaje de confianza mínimo que debe tener una instancia "
            "para conservarse.",
            pt="Pontuação de confiança mínima que uma instância deve ter "
            "para ser mantida.",
            de="Mindestvertrauenswert, den eine Instanz haben muss, um "
            "beibehalten zu werden.",
            zh="实例被保留所需的最低置信度分数。",
        ),
    )  # type: ignore

    mask_threshold: schema_field(
        float_field(gt=0.0, lt=1.0),
        0.5,
        description=MultilingualString(
            en="Probability above which a pixel counts as part of the "
            "detected object. Lower values grow every mask, higher values "
            "tighten it. Unrelated to min_score, which drops whole "
            "instances by their confidence.",
            es="Probabilidad sobre la cual un píxel cuenta como parte del "
            "objeto detectado. Los valores más bajos agrandan cada "
            "máscara, los más altos la ajustan. No tiene relación con "
            "min_score, que descarta instancias completas según su "
            "confianza.",
            pt="Probabilidade acima da qual um pixel conta como parte do "
            "objeto detectado. Valores mais baixos aumentam cada máscara, "
            "valores mais altos a estreitam. Não tem relação com "
            "min_score, que descarta instâncias inteiras pela sua "
            "confiança.",
            de="Wahrscheinlichkeit, ab der ein Pixel als Teil des "
            "erkannten Objekts zählt. Niedrigere Werte vergrößern jede "
            "Maske, höhere Werte verengen sie. Unabhängig von min_score, "
            "das ganze Instanzen nach ihrer Konfidenz verwirft.",
            zh="像素被视为检测对象一部分的概率阈值。较低的值会扩大每个掩"
            "码，较高的值会收紧掩码。与 min_score 无关，后者按置信度丢弃"
            "整个实例。",
        ),
    )  # type: ignore

    min_area_fraction: schema_field(
        float_field(ge=0.0, le=1.0),
        0.0,
        description=MultilingualString(
            en="Minimum fraction of the image area an instance's mask "
            "must cover to be kept.",
            es="Fracción mínima del área de la imagen que la máscara de "
            "una instancia debe cubrir para conservarse.",
            pt="Fração mínima da área da imagem que a máscara de uma "
            "instância deve cobrir para ser mantida.",
            de="Mindestanteil der Bildfläche, den die Maske einer Instanz "
            "abdecken muss, um beibehalten zu werden.",
            zh="实例掩码必须覆盖的图像面积的最小比例，才能被保留。",
        ),
    )  # type: ignore

    crop_to_bbox: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en="When enabled, each emitted segment image is cropped to "
            "the detected object's bounding box instead of keeping the "
            "full original image size.",
            es="Cuando está habilitado, cada imagen de segmento emitida "
            "se recorta al cuadro delimitador del objeto detectado en "
            "lugar de conservar el tamaño original completo.",
            pt="Quando habilitado, cada imagem de segmento emitida é "
            "recortada para a caixa delimitadora do objeto detectado, em "
            "vez de manter o tamanho original completo.",
            de="Wenn aktiviert, wird jedes ausgegebene Segmentbild auf die "
            "Begrenzungsbox des erkannten Objekts zugeschnitten, anstatt "
            "die volle ursprüngliche Bildgröße beizubehalten.",
            zh="启用后，每个生成的分割图像都会被裁剪到检测对象的边界框，"
            "而不是保留完整的原始图像尺寸。",
        ),
    )  # type: ignore

    background_fill: schema_field(
        enum_field(enum=_BACKGROUND_FILLS),
        "black",
        description=MultilingualString(
            en="Fill applied to every pixel outside the detected object "
            "in the emitted segment image: 'black', 'white', or 'blur'.",
            es="Relleno aplicado a cada píxel fuera del objeto detectado "
            "en la imagen del segmento emitida: 'black', 'white' o "
            "'blur'.",
            pt="Preenchimento aplicado a cada pixel fora do objeto "
            "detectado na imagem do segmento emitida: 'black', 'white' ou "
            "'blur'.",
            de="Füllung, die auf jedes Pixel außerhalb des erkannten "
            "Objekts im ausgegebenen Segmentbild angewendet wird: "
            "'black', 'white' oder 'blur'.",
            zh="应用于生成的分割图像中检测对象之外每个像素的填充方式："
            "'black'、'white' 或 'blur'。",
        ),
    )  # type: ignore

    keep_binary_mask: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en="When enabled, an additional column with the object's "
            "binary mask as its own image is kept for each detected "
            "object.",
            es="Cuando está habilitado, se conserva una columna adicional "
            "con la máscara binaria del objeto como imagen propia para "
            "cada objeto detectado.",
            pt="Quando habilitado, uma coluna adicional com a máscara "
            "binária do objeto como sua própria imagem é mantida para "
            "cada objeto detectado.",
            de="Wenn aktiviert, wird für jedes erkannte Objekt eine "
            "zusätzliche Spalte mit der binären Maske des Objekts als "
            "eigenes Bild beibehalten.",
            zh="启用后，将为每个检测到的对象保留一个附加列，其中包含作为"
            "独立图像的对象二值掩码。",
        ),
    )  # type: ignore

    on_no_detection: schema_field(
        enum_field(enum=_NO_DETECTION_POLICIES),
        "empty",
        description=MultilingualString(
            en="What to do when no instance is detected in an image: "
            "'empty' leaves every segment and score cell null for that "
            "row, 'keep_original' fills segment_1 with the unmodified "
            "source image and seg_score_1 with 0.0 while leaving the rest "
            "null, or 'error' to stop.",
            es="Qué hacer cuando no se detecta ninguna instancia en una "
            "imagen: 'empty' deja nulas todas las celdas de segmento y "
            "puntaje de esa fila, 'keep_original' llena segment_1 con la "
            "imagen de origen sin modificar y seg_score_1 con 0.0 dejando "
            "el resto nulo, o 'error' para detenerse.",
            pt="O que fazer quando nenhuma instância é detectada em uma "
            "imagem: 'empty' deixa nulas todas as células de segmento e "
            "pontuação dessa linha, 'keep_original' preenche segment_1 "
            "com a imagem de origem não modificada e seg_score_1 com 0.0 "
            "deixando o restante nulo, ou 'error' para parar.",
            de="Was zu tun ist, wenn in einem Bild keine Instanz erkannt "
            "wird: 'empty' lässt alle Segment und Wertungszellen dieser "
            "Zeile null, 'keep_original' füllt segment_1 mit dem "
            "unveränderten Ausgangsbild und seg_score_1 mit 0.0 und lässt "
            "den Rest null, oder 'error', um abzubrechen.",
            zh="当图像中未检测到任何实例时该怎么办：'empty' 将该行的所有"
            "分割和得分单元格置空，'keep_original' 用未修改的源图像填充 "
            "segment_1、用 0.0 填充 seg_score_1，其余保持为空，或者 "
            "'error' 停止运行。",
        ),
    )  # type: ignore

    device: schema_field(
        enum_field(DEVICE_ENUM),
        DEVICE_PLACEHOLDER,
        description=MultilingualString(
            en="Device the segmentation model runs on. SAM 3 is a large model, "
            "so a GPU is considerably faster than the CPU.",
            es="Dispositivo en el que se ejecuta el modelo de segmentación. "
            "SAM 3 es un modelo grande, por lo que una GPU es "
            "considerablemente más rápida que la CPU.",
            pt="Dispositivo onde o modelo de segmentação é executado. O SAM 3 "
            "é um modelo grande, portanto uma GPU é consideravelmente mais "
            "rápida que a CPU.",
            de="Gerät, auf dem das Segmentierungsmodell läuft. SAM 3 ist ein "
            "großes Modell, daher ist eine GPU deutlich schneller als die CPU.",
            zh="运行分割模型的设备。SAM 3 是大模型，GPU 比 CPU 快得多。",
        ),
    )  # type: ignore


class SAM3SegmentConverter(HFPretrainedDownloadMixin, AdvancedPreprocessingConverter):
    """Detect a prompted object in every image and append ranked columns.

    Runs a promptable segmenter over the image column and appends, for every
    row, up to ``max_masks`` ranked pairs of columns: ``segment_i`` holds the
    i-th highest scoring detected object rendered as its own masked image,
    and ``seg_score_i`` holds that object's confidence. When
    ``keep_binary_mask`` is enabled, ``mask_i`` columns are appended too. The
    row count never changes: an image with fewer detected objects than
    ``max_masks`` simply leaves the remaining ``segment_i`` and
    ``seg_score_i`` (and, when enabled, ``mask_i``) cells null for that row.

    Because ``CHANGES_ROW_COUNT`` is false, the converter job folds the
    columns this converter produces back into the dataset with
    ``rebuild_dataset_with_transformed_columns``, which preserves every
    column left out of the scope untouched, but treats any *scoped* column
    absent from this converter's own return value as removed. ``transform``
    therefore returns every column of its input unchanged, verbatim,
    alongside the new ranked columns, rather than only the columns it
    actually computes. The scope is expected to cover only the image column
    (and any other image column the segmenter should also run over); the
    image to segment among the scoped columns is chosen through the
    ``image_column`` schema field.
    """

    SCHEMA = SAM3SegmentConverterSchema
    CHANGES_ROW_COUNT = False
    DESCRIPTION = MultilingualString(
        en="Detects every instance of a prompt in each image and appends "
        "2 times max_masks new columns, keeping every row unchanged: "
        "segment_1 through segment_k holds the i-th highest scoring "
        "detected object as its own masked image, and seg_score_1 "
        "through seg_score_k holds that object's confidence, where k is "
        "max_masks. When keep_binary_mask is enabled, mask_1 through "
        "mask_k are appended too. An image with fewer detected objects "
        "than max_masks leaves the remaining segment and score cells "
        "null for that row. Objects are ranked by descending confidence "
        "score and the top max_masks are kept. The image column is "
        "chosen through the image_column parameter, indexed among the "
        "columns selected in the scope. SAM 3 is a gated Hugging Face "
        "model, so using this converter requires prior authentication "
        "with a HuggingFace access token and accepting the model's terms. "
        "Weights are downloaded into the component's own folder. Model "
        "page: https://huggingface.co/facebook/sam3",
        es="Detecta cada instancia de un texto en cada imagen y agrega 2 "
        "veces max_masks columnas nuevas, sin modificar ninguna fila: "
        "segment_1 hasta segment_k contiene el i-ésimo objeto detectado "
        "con mayor puntaje como su propia imagen enmascarada, y "
        "seg_score_1 hasta seg_score_k contiene la confianza de ese "
        "objeto, donde k es max_masks. Cuando keep_binary_mask está "
        "habilitado, también se agregan mask_1 hasta mask_k. Una imagen "
        "con menos objetos detectados que max_masks deja nulas las "
        "celdas restantes de segmento y puntaje en esa fila. Los objetos "
        "se clasifican por puntaje de confianza descendente y se "
        "conservan los max_masks principales. La columna de imagen se "
        "elige mediante el parámetro image_column, indexado entre las "
        "columnas seleccionadas en el alcance. SAM 3 es un modelo "
        "restringido de Hugging Face, por lo que usar este convertidor "
        "requiere autenticación previa con un token de acceso de "
        "HuggingFace y aceptar los términos del modelo. Los pesos se "
        "descargan en la carpeta propia del componente. Página del "
        "modelo: https://huggingface.co/facebook/sam3",
        pt="Detecta cada instância de um texto em cada imagem e adiciona "
        "2 vezes max_masks novas colunas, sem alterar nenhuma linha: "
        "segment_1 até segment_k contém o i-ésimo objeto detectado com "
        "maior pontuação como sua própria imagem mascarada, e "
        "seg_score_1 até seg_score_k contém a confiança desse objeto, "
        "onde k é max_masks. Quando keep_binary_mask está habilitado, "
        "mask_1 até mask_k também são adicionadas. Uma imagem com menos "
        "objetos detectados do que max_masks deixa nulas as células "
        "restantes de segmento e pontuação nessa linha. Os objetos são "
        "classificados por pontuação de confiança descendente e os "
        "max_masks principais são mantidos. A coluna de imagem é "
        "escolhida através do parâmetro image_column, indexado entre as "
        "colunas selecionadas no escopo. SAM 3 é um modelo restrito do "
        "Hugging Face, portanto usar este conversor requer autenticação "
        "prévia com um token de acesso do HuggingFace e a aceitação dos "
        "termos do modelo. Os pesos são baixados na pasta própria do "
        "componente. Página do modelo: https://huggingface.co/facebook/sam3",
        de="Erkennt jede Instanz eines Textes in jedem Bild und fügt 2 "
        "mal max_masks neue Spalten hinzu, ohne eine Zeile zu verändern: "
        "segment_1 bis segment_k enthält das i-te am höchsten bewertete "
        "erkannte Objekt als eigenes maskiertes Bild, und seg_score_1 "
        "bis seg_score_k enthält den Vertrauenswert dieses Objekts, "
        "wobei k gleich max_masks ist. Wenn keep_binary_mask aktiviert "
        "ist, werden zusätzlich mask_1 bis mask_k hinzugefügt. Ein Bild "
        "mit weniger erkannten Objekten als max_masks lässt die "
        "verbleibenden Segment und Wertungszellen dieser Zeile null. "
        "Objekte werden nach absteigendem Vertrauenswert sortiert, und "
        "die obersten max_masks werden beibehalten. Die Bildspalte wird "
        "über den Parameter image_column gewählt, indexiert unter den im "
        "Geltungsbereich ausgewählten Spalten. SAM 3 ist ein "
        "zugangsbeschränktes Hugging-Face-Modell, daher erfordert die "
        "Nutzung dieses Konverters eine vorherige Authentifizierung mit "
        "einem HuggingFace-Zugriffstoken und die Annahme der "
        "Modellbedingungen. Die Gewichte werden in den eigenen Ordner der "
        "Komponente heruntergeladen. Modellseite: "
        "https://huggingface.co/facebook/sam3",
        zh="检测每张图像中提示文本描述的每个实例，并添加 2 倍 max_masks "
        "个新列，且不改变任何行：segment_1 到 segment_k 保存第 i 个得分"
        "最高的检测对象，作为其自身的掩码图像，seg_score_1 到 "
        "seg_score_k 保存该对象的置信度，其中 k 为 max_masks。启用 "
        "keep_binary_mask 时，还会添加 mask_1 到 mask_k。检测到的对象数"
        "量少于 max_masks 的图像，该行剩余的分割和得分单元格为空。对象"
        "按置信度降序排列，仅保留前 max_masks 个。图像列通过 "
        "image_column 参数选择，其索引对应范围内选定的列。SAM 3 是一个"
        "受限的 Hugging Face 模型，因此使用此转换器前需要使用 "
        "HuggingFace 访问令牌进行身份验证并接受模型条款。权重会下载到"
        "该组件自己的文件夹中。模型页面：https://huggingface.co/facebook/sam3",
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Segments a prompted object in each image, appending ranked "
        "segment and score columns.",
        es="Segmenta un objeto indicado en cada imagen, agregando "
        "columnas de segmento y puntaje clasificadas.",
        pt="Segmenta um objeto indicado em cada imagem, adicionando "
        "colunas de segmento e pontuação classificadas.",
        de="Segmentiert ein vorgegebenes Objekt in jedem Bild und fügt "
        "eingestufte Segment und Wertungsspalten hinzu.",
        zh="在每张图像中分割提示指定的对象，添加按排名排列的分割和得分列。",
    )
    DISPLAY_NAME = MultilingualString(
        en="SAM3 Segmenter",
        es="Segmentador SAM3",
        pt="Segmentador SAM3",
        de="SAM3 Segmentierer",
        zh="SAM3 分割器",
    )

    # Gated Hugging Face repo: HFPretrainedDownloadMixin derives hf_repos()
    # and _pretrained_source() from MODEL_NAME, and REQUIRED_CREDENTIALS
    # gates the component in the registry (required_credentials /
    # credentials_satisfied) until a HuggingFaceCredential is stored, the
    # same mechanism StableDiffusion3GenerationModel uses.
    MODEL_NAME: str = "facebook/sam3"
    DOWNLOAD_SIZE_BYTES: int = 3_440_000_000
    REQUIRED_CREDENTIALS = ["HuggingFaceCredential"]

    # Restricted to images: this converter only ever operates on an image
    # column, unlike the earlier tall layout, which needed every column in
    # scope and therefore could not restrict allowed_types at all.
    metadata = {"allowed_types": [DashAIImage], "allowed_dtypes": []}

    def __init__(self, segmenter=None, **kwargs):
        """Build the converter, optionally with an injected segmenter.

        Parameters
        ----------
        segmenter : BaseSegmenter, optional
            Segmenter to use. When omitted, ``_get_segmenter`` lazily builds
            a real ``SAM3Segmenter`` on first use, pointed at this
            component's own downloaded weights (or the Hub repo id as a
            fallback). Tests inject a fake so no weights are needed.
        kwargs : dict
            Configuration as declared by :class:`SAM3SegmentConverterSchema`.
        """
        super().__init__()
        self._segmenter = segmenter
        self.prompt = kwargs["prompt"]
        self.image_column = kwargs["image_column"]
        self.max_masks = kwargs["max_masks"]
        self.min_score = kwargs["min_score"]
        self.mask_threshold = kwargs["mask_threshold"]
        self.min_area_fraction = kwargs["min_area_fraction"]
        self.crop_to_bbox = kwargs["crop_to_bbox"]
        self.background_fill = kwargs["background_fill"]
        self.keep_binary_mask = kwargs["keep_binary_mask"]
        self.on_no_detection = kwargs["on_no_detection"]
        # DEVICE_ENUM entries are user facing labels such as "CPU" or
        # "GPU 0: NVIDIA ...", so map through DEVICE_TO_IDX to reach a torch
        # device string. Absent from a hand written payload means CPU.
        device_index = DEVICE_TO_IDX.get(kwargs.get("device", DEVICE_PLACEHOLDER), -1)
        self.device = f"cuda:{device_index}" if device_index >= 0 else "cpu"
        self.column_types: Dict[str, DashAIDataType] = {}

    @classmethod
    def download(cls, report: Optional[ProgressReporter] = None) -> None:
        """Log in to HuggingFace before downloading these gated weights.

        ``ComponentDownloadJob.run`` calls ``component_class.download(...)``
        directly, without applying any credential first, so downloading a
        gated repo through the download job only works today if a token
        happens to already be persisted on disk by some other path.
        ``HuggingFaceCredential.apply()`` is what performs the actual Hub
        login, and it is otherwise only invoked by ``_get_segmenter``, at
        inference time. This override closes that gap for this converter by
        applying the credential first and then delegating to
        ``HFPretrainedDownloadMixin.download`` for the actual
        ``snapshot_download``. ``get_credential`` is an instance method, but
        its body only resolves the credential class from the registry and
        never touches ``self``, so the same lookup is repeated here directly
        against the registry to keep this a classmethod.

        Parameters
        ----------
        report : ProgressReporter, optional
            Progress callback forwarded to
            ``HFPretrainedDownloadMixin.download``.
        """
        credential_class = di["component_registry"]["HuggingFaceCredential"]["class"]
        credential_class().apply()
        super().download(report)

    def fit(
        self, x: "DashAIDataset", y: "DashAIDataset" = None
    ) -> "SAM3SegmentConverter":
        """Record the incoming column types. No model state is learned.

        Parameters
        ----------
        x : DashAIDataset
            The scoped dataset the converter will later transform, normally
            just the image column.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        SAM3SegmentConverter
            The fitted converter instance (self).
        """
        self.column_types = x.types.copy()
        return self

    def _get_segmenter(self) -> "BaseSegmenter":
        """Return the segmenter to run, building a real one if none is set.

        When a segmenter was injected at construction time (the path every
        existing converter test relies on), it is returned unchanged and
        neither the HuggingFace credential nor the network are touched.
        Otherwise a real :class:`SAM3Segmenter` is built lazily, pointed at
        this component's own downloaded weights (or the Hub repo id as a
        fallback), after applying the stored HuggingFace credential so a
        gated download can authenticate.

        Returns
        -------
        BaseSegmenter
            The segmenter injected at construction time, or a lazily built
            ``SAM3Segmenter`` pointed at ``self._pretrained_source(None)``.
        """
        if self._segmenter is not None:
            return self._segmenter

        # apply() silently no-ops when no token is stored; the resulting
        # from_pretrained failure is turned into an actionable message by
        # SAM3Segmenter._ensure_loaded, naming the model page and the
        # required credential instead of a raw HTTP 401/403.
        self.get_credential("HuggingFaceCredential").apply()

        self._segmenter = SAM3Segmenter(
            model_source=self._pretrained_source(None),
            score_threshold=self.min_score,
            mask_threshold=self.mask_threshold,
            device=self.device,
        )
        return self._segmenter

    def _select(self, instances, image_area):
        """Filter and rank the instances detected in one image.

        Parameters
        ----------
        instances : list of SegmentInstance
            Instances as returned by the segmenter, in arbitrary order.
        image_area : int
            Total pixel count of the source image, used to turn
            ``min_area_fraction`` into an absolute pixel threshold.

        Returns
        -------
        list of SegmentInstance
            Instances passing both thresholds, sorted by descending score and
            truncated to ``max_masks``.
        """
        min_area = self.min_area_fraction * image_area

        kept = [
            instance
            for instance in instances
            if instance.score >= self.min_score and int(instance.mask.sum()) >= min_area
        ]
        kept.sort(key=lambda instance: instance.score, reverse=True)
        return kept[: self.max_masks]

    def transform(
        self, x: "DashAIDataset", y: "DashAIDataset" = None
    ) -> "DashAIDataset":
        """Segment every image and append ranked segment and score columns.

        Parameters
        ----------
        x : DashAIDataset
            The scoped dataset to segment, normally just the image column.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        DashAIDataset
            Every column of ``x`` unchanged, in its original position, plus
            ``segment_i`` and ``seg_score_i`` columns (and, when
            ``keep_binary_mask`` is true, ``mask_i``) for every rank from 1
            to ``max_masks``. Every scoped column must come back out, not
            just the image column: the converter job folds this return
            value into the dataset with
            ``rebuild_dataset_with_transformed_columns``, which treats any
            scoped column absent from this output as removed. Row count is
            unchanged, so this is a straight column graft onto ``x``'s own
            Arrow table, never a rebuild through pandas.

        Raises
        ------
        ValueError
            If ``image_column`` is out of range for the scoped columns, if
            the resolved column is not a :class:`DashAIImage` column, if a
            column this converter would add is itself present among the
            scoped columns, if an image in a row cannot be decoded, if
            a row has no detected instance and ``on_no_detection`` is set
            to ``error``, or if ``on_no_detection`` is ``empty`` and no row
            in the whole dataset produced any instance. The collision check
            only sees ``x``, the already scoped slice, not the whole
            dataset: under the documented scope of just the image column, a
            colliding name left behind by an earlier run is out of scope
            and therefore invisible here, so nothing is raised.
            ``_merge_transformed`` then folds this output back through
            ``rebuild_dataset_with_transformed_columns``, which silently
            uniquifies the name instead, for example appending
            ``segment_1_1`` beside the pre-existing ``segment_1``.
        """
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        column_names = x.column_names

        if self.image_column < 1 or self.image_column > len(column_names):
            raise ValueError(
                f"image_column {self.image_column} is out of range for a "
                f"scope with {len(column_names)} columns."
            )

        image_column_name = column_names[self.image_column - 1]
        if not isinstance(x.types.get(image_column_name), DashAIImage):
            raise ValueError(
                f"Column '{image_column_name}' selected by image_column is "
                "not an image column."
            )

        # column_names comes from x, the already scoped slice, not the whole
        # dataset, so this only catches a collision when the colliding
        # column is itself included in the scope. Under the documented
        # scope of just the image column, a segment_1 left behind by an
        # earlier run is out of scope and invisible here; in that case
        # rebuild_dataset_with_transformed_columns silently uniquifies the
        # name instead, appending segment_1_1 beside the original.
        reserved_names = []
        for rank in range(1, self.max_masks + 1):
            reserved_names.append(_segment_column(rank))
            reserved_names.append(_score_column(rank))
        if self.keep_binary_mask:
            for rank in range(1, self.max_masks + 1):
                reserved_names.append(_mask_column(rank))

        collisions = [name for name in reserved_names if name in column_names]
        if collisions:
            raise ValueError(
                "The dataset already contains columns this converter would "
                f"add: {collisions}."
            )

        segmenter = self._get_segmenter()

        segment_values: Dict[int, list] = {
            rank: [] for rank in range(1, self.max_masks + 1)
        }
        score_values: Dict[int, list] = {
            rank: [] for rank in range(1, self.max_masks + 1)
        }
        mask_values: Dict[int, list] = (
            {rank: [] for rank in range(1, self.max_masks + 1)}
            if self.keep_binary_mask
            else {}
        )

        any_detection = False

        for row_index in range(len(x)):
            row = x[row_index]
            image_value = row[image_column_name]
            try:
                pil_image = image_value.to_pil()
                # Pillow only parses the header in Image.open; pixel decoding
                # is deferred until the data is actually needed. Force it
                # here so a truncated or otherwise corrupt body is caught in
                # this row-indexed guard instead of surfacing later,
                # unguarded, from render_segment or the keep_original PNG
                # re-encode.
                pil_image.load()
            except Exception as error:
                raise ValueError(
                    f"Could not decode the image in row {row_index}. Fix or "
                    "remove the row before running the converter."
                ) from error

            source_path = image_value.path
            instances = segmenter.segment(pil_image, self.prompt)
            image_area = pil_image.size[0] * pil_image.size[1]
            selected_instances = self._select(instances, image_area)

            row_segments: list = []
            row_scores: list = []
            row_masks: list = []

            if selected_instances:
                any_detection = True
                for instance_index, instance in enumerate(selected_instances):
                    segment_bytes = render_segment(
                        pil_image, instance, self.crop_to_bbox, self.background_fill
                    )
                    row_segments.append(
                        {
                            "bytes": segment_bytes,
                            "path": f"{source_path}#{instance_index}",
                        }
                    )
                    row_scores.append(float(instance.score))
                    if self.keep_binary_mask:
                        mask_bytes = render_binary_mask(instance)
                        row_masks.append(
                            {
                                "bytes": mask_bytes,
                                "path": f"{source_path}#{instance_index}#mask",
                            }
                        )
            elif self.on_no_detection == "error":
                raise ValueError(
                    f"The prompt '{self.prompt}' matched no objects in row "
                    f"{row_index}, and on_no_detection is set to 'error'."
                )
            elif self.on_no_detection == "keep_original":
                buffer = io.BytesIO()
                # Convert before encoding: PNG cannot hold every PIL mode, so
                # a CMYK source (a JPEG out of a print workflow) would raise
                # "cannot write mode CMYK as PNG" here, outside the row
                # indexed guard above. render_segment already converts to RGB
                # for the detected rows, so this also keeps a single mode
                # across the whole segment column.
                pil_image.convert("RGB").save(buffer, format="PNG")
                row_segments.append(
                    {"bytes": buffer.getvalue(), "path": f"{source_path}#0"}
                )
                row_scores.append(0.0)
            # else "empty": every list stays empty, so every cell for this
            # row is padded to null below.

            for rank in range(1, self.max_masks + 1):
                index = rank - 1
                segment_values[rank].append(
                    row_segments[index] if index < len(row_segments) else None
                )
                score_values[rank].append(
                    row_scores[index] if index < len(row_scores) else None
                )
                if self.keep_binary_mask:
                    mask_values[rank].append(
                        row_masks[index] if index < len(row_masks) else None
                    )

        if self.on_no_detection == "empty" and not any_detection:
            raise ValueError(
                f"The prompt '{self.prompt}' matched no objects in any row of "
                "the dataset. Check the prompt, min_score, and "
                "min_area_fraction."
            )

        # An explicit Arrow type on every appended array, rather than letting
        # pandas/Arrow infer one, matters most for an all-null rank column:
        # with max_masks larger than the detections in every row, letting
        # the type be inferred from the data would produce Arrow's `null`
        # type instead of the declared DashAIImage/Float, breaking
        # to_pandas() dtype and concatenation with any other dataset from
        # this same converter.
        image_pa_type = pa.struct({"bytes": pa.binary(), "path": pa.string()})

        result_table = x.arrow_table
        output_types: Dict[str, DashAIDataType] = dict(x.types)

        for rank in range(1, self.max_masks + 1):
            segment_name = _segment_column(rank)
            score_name = _score_column(rank)
            result_table = result_table.append_column(
                segment_name, pa.array(segment_values[rank], type=image_pa_type)
            )
            result_table = result_table.append_column(
                score_name, pa.array(score_values[rank], type=pa.float64())
            )
            output_types[segment_name] = DashAIImage()
            output_types[score_name] = Float(pa.float64())
        if self.keep_binary_mask:
            for rank in range(1, self.max_masks + 1):
                mask_name = _mask_column(rank)
                result_table = result_table.append_column(
                    mask_name, pa.array(mask_values[rank], type=image_pa_type)
                )
                output_types[mask_name] = DashAIImage()

        return DashAIDataset(result_table, splits=x.splits, types=output_types)

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the DashAI type produced for a given output column.

        Parameters
        ----------
        column_name : str, optional
            Name of the column to look up. Defaults to None.

        Returns
        -------
        DashAIDataType
            ``DashAIImage()`` for a ``segment_i`` or ``mask_i`` column,
            ``Float(pa.float64())`` for a ``seg_score_i`` column, and the
            recorded type from ``self.column_types`` for any other column.
        """
        import pyarrow as pa

        if column_name is not None:
            if column_name.startswith((f"{SEGMENT_COLUMN}_", f"{MASK_COLUMN}_")):
                return DashAIImage()
            if column_name.startswith(f"{SCORE_COLUMN}_"):
                return Float(pa.float64())
        return self.column_types.get(column_name)
