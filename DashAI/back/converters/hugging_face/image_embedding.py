"""HuggingFace image embedding converter"""

from typing import TYPE_CHECKING, Callable, Dict, Optional

from DashAI.back.converters.category.advanced_preprocessing import (
    AdvancedPreprocessingConverter,
)
from DashAI.back.converters.hugging_face_wrapper import HuggingFaceWrapper
from DashAI.back.core.schema_fields import (
    bool_field,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.utils import (
    DEVICE_ENUM,
    DEVICE_PLACEHOLDER,
    DEVICE_TO_IDX,
)
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Float

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


# Vision encoders offered for image embedding. Restricted to permissively
# licensed weights, Apache 2.0 here, so the component stays compatible with the
# project's MIT licence.
IMAGE_ENCODERS: Dict[str, str] = {
    "DINOv2 base": "facebook/dinov2-base",
    "DINOv2 small": "facebook/dinov2-small",
    "ResNet 50": "microsoft/resnet-50",
}

DEFAULT_IMAGE_ENCODER: str = "DINOv2 small"


class ImageEmbeddingSchema(BaseSchema):
    """Schema for ImageEmbedding converter hyperparameters."""

    model_name: schema_field(
        enum_field(list(IMAGE_ENCODERS)),
        DEFAULT_IMAGE_ENCODER,
        description=MultilingualString(
            en="Pretrained vision model used to encode images. All options are "
            "Apache 2.0 licensed, which is compatible with this project.",
            es="Modelo de visión preentrenado usado para codificar imágenes. "
            "Todas las opciones tienen licencia Apache 2.0, compatible con "
            "este proyecto.",
            pt="Modelo de visão pré treinado usado para codificar imagens. "
            "Todas as opções têm licença Apache 2.0, compatível com este "
            "projeto.",
            de="Vortrainiertes Bildverarbeitungsmodell zum Kodieren von "
            "Bildern. Alle Optionen stehen unter Apache 2.0 und sind mit "
            "diesem Projekt vereinbar.",
            zh="用于编码图像的预训练视觉模型。所有选项均为 Apache 2.0 许可，"
            "与本项目兼容。",
        ),
    )  # type: ignore

    device: schema_field(
        enum_field(DEVICE_ENUM),
        DEVICE_PLACEHOLDER,
        description=MultilingualString(
            en="Device to use for computation.",
            es="Dispositivo a usar para el cómputo.",
            pt="Dispositivo a usar para o processamento.",
            de="Gerät für die Berechnung.",
            zh="用于计算的设备。",
        ),
    )  # type: ignore

    batch_size: schema_field(
        int_field(ge=1),
        32,
        description=MultilingualString(
            en="Number of images to process at once.",
            es="Número de imágenes a procesar a la vez.",
            pt="Número de imagens a processar de uma vez.",
            de="Anzahl der gleichzeitig zu verarbeitenden Bilder.",
            zh="每次处理的图像数量。",
        ),
    )  # type: ignore

    keep_source_column: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en="When enabled, the original image column is kept alongside "
            "the new embedding columns instead of being removed.",
            es="Cuando está habilitado, la columna de imagen original se "
            "conserva junto a las nuevas columnas de embedding en lugar de "
            "eliminarse.",
            pt="Quando habilitado, a coluna de imagem original é mantida "
            "junto com as novas colunas de embedding, em vez de ser "
            "removida.",
            de="Wenn aktiviert, bleibt die ursprüngliche Bildspalte neben "
            "den neuen Embedding Spalten erhalten, anstatt entfernt zu "
            "werden.",
            zh="启用后，原始图像列将与新的嵌入列一起保留，而不会被删除。",
        ),
    )  # type: ignore


class ImageEmbeddingConverter(AdvancedPreprocessingConverter, HuggingFaceWrapper):
    """HuggingFace image embedding converter.

    Encodes every image column into dense float columns using a pretrained
    vision model. Unlike the text ``Embedding`` converter this template is
    based on, the source image column is kept by default, controlled by
    ``keep_source_column``, so a later stage can still reach the original
    pixels of the same saved dataset.
    """

    SCHEMA = ImageEmbeddingSchema
    DESCRIPTION = MultilingualString(
        en="Embed an image column into dense float columns using a "
        "HuggingFace vision model. Each detected image column is encoded "
        "and one Float column per embedding dimension is appended, named "
        "emb_{column}_{i}. The source image column is kept by default so "
        "a later stage can still access the original pixels.",
        es="Convierte una columna de imagen en columnas float densas "
        "usando un modelo de visión de HuggingFace. Cada columna de "
        "imagen detectada se codifica y se agrega una columna Float por "
        "dimensión del embedding, nombrada emb_{column}_{i}. La columna "
        "de imagen original se conserva de forma predeterminada para que "
        "una etapa posterior pueda seguir accediendo a los píxeles "
        "originales.",
        pt="Converte uma coluna de imagem em colunas float densas usando "
        "um modelo de visão do HuggingFace. Cada coluna de imagem "
        "detectada é codificada e uma coluna Float por dimensão do "
        "embedding é adicionada, nomeada emb_{column}_{i}. A coluna de "
        "imagem original é mantida por padrão para que uma etapa "
        "posterior ainda possa acessar os pixels originais.",
        de="Wandelt eine Bildspalte mithilfe eines "
        "Bildverarbeitungsmodells von HuggingFace in dichte Float Spalten "
        "um. Jede erkannte Bildspalte wird kodiert, und für jede "
        "Embedding Dimension wird eine Float Spalte mit dem Namen "
        "emb_{column}_{i} hinzugefügt. Die ursprüngliche Bildspalte "
        "bleibt standardmäßig erhalten, damit eine spätere Stufe "
        "weiterhin auf die ursprünglichen Pixel zugreifen kann.",
        zh="使用HuggingFace视觉模型将图像列转换为稠密的浮点列。每个检测到"
        "的图像列都会被编码，并为每个嵌入维度添加一个浮点列，命名为"
        "emb_{column}_{i}。默认情况下会保留原始图像列，以便后续阶段仍可"
        "以访问原始像素。",
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Embeds an image column into dense float columns.",
        es="Convierte una columna de imagen en columnas float densas.",
        pt="Converte uma coluna de imagem em colunas float densas.",
        de="Wandelt eine Bildspalte in dichte Float Spalten um.",
        zh="将图像列转换为稠密的浮点列。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Image Embedding",
        es="Embedding de Imagen",
        pt="Embedding de Imagem",
        de="Bildeinbettung",
        zh="图像嵌入",
    )

    CHANGES_ROW_COUNT = False

    metadata = {
        "allowed_types": [DashAIImage],
        "allowed_dtypes": [],
    }

    def __init__(
        self,
        encoder: Optional[Callable[[list], "np.ndarray"]] = None,
        **kwargs,
    ):
        """Initialise the image embedding converter and its schema parameters.

        Parameters
        ----------
        encoder : callable, optional
            A callable that takes a list of ``PIL.Image.Image`` and returns
            a ``numpy.ndarray`` of shape ``(n_images, n_dims)``. Reserved
            for tests: when provided, :meth:`_load_model` is never called,
            so no weights are downloaded. Default ``None``.
        **kwargs : dict
            model_name : str, optional
                Key of ``IMAGE_ENCODERS``, for example ``"DINOv2 base"``. A
                repository id is also accepted and used as given. Default
                ``DEFAULT_IMAGE_ENCODER``.
            device : str, optional
                Device label from ``DEVICE_ENUM``, for example ``"CPU"``
                or ``"GPU 0: ..."``. Resolved to a torch device string.
                Default ``"cpu"``.
            batch_size : int, optional
                Number of images per inference batch. Default ``32``.
            keep_source_column : bool, optional
                Whether to keep the original image column alongside the
                new embedding columns. Default ``True``.
        """
        super().__init__(**kwargs)
        self._encoder = encoder
        # The schema offers friendly names; resolve to the repository id here so
        # the rest of the class only ever deals with what transformers needs. An
        # unrecognised value is passed through, which keeps a hand written API
        # payload working and keeps this from silently substituting a model the
        # caller did not ask for.
        selected = kwargs.get("model_name", DEFAULT_IMAGE_ENCODER)
        self.model_name = IMAGE_ENCODERS.get(selected, selected)
        # DEVICE_ENUM entries are user facing labels such as
        # "GPU 0: NVIDIA ... " or "CPU", so map through DEVICE_TO_IDX to get a
        # torch device string.
        device_label = kwargs.get("device", DEVICE_PLACEHOLDER)
        device_index = DEVICE_TO_IDX.get(device_label, -1)
        self.device = f"cuda:{device_index}" if device_index >= 0 else "cpu"
        self.batch_size = kwargs.get("batch_size", 32)
        self.keep_source_column = kwargs.get("keep_source_column", True)
        self.model = None
        self.processor = None
        self.column_types: Dict[str, DashAIDataType] = {}

    def fit(
        self, x: "DashAIDataset", y: "DashAIDataset" = None
    ) -> "ImageEmbeddingConverter":
        """Validate the input dataset and load the vision model if needed.

        Checks that the dataset is non-empty and that every column holds
        image data, records each column's type for later use by
        :meth:`get_output_type`, and loads the pretrained model unless an
        encoder was already injected at construction time.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset whose columns must all be image typed.
        y : DashAIDataset or None, optional
            Ignored. Present for API compatibility. Default ``None``.

        Returns
        -------
        ImageEmbeddingConverter
            The fitted converter instance (``self``).

        Raises
        ------
        ValueError
            If ``x`` is empty or any column is not image typed.
        """
        if len(x) == 0:
            raise ValueError("Input dataset is empty")

        for column in x.column_names:
            if not isinstance(x.types.get(column), DashAIImage):
                raise ValueError(f"Column {column} must contain image data")

        self.column_types = dict(x.types)

        if self._encoder is None:
            self._load_model()

        return self

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the DashAI type produced for a given output column.

        Parameters
        ----------
        column_name : str or None, optional
            Name of the output column. Default ``None``.

        Returns
        -------
        DashAIDataType
            The type recorded in :attr:`column_types` when ``column_name``
            is one of the original columns carried through, for example
            the source image column when ``keep_source_column`` is true.
            Otherwise, a DashAI ``Float`` type backed by
            ``pyarrow.float32()``, since every column this converter adds
            is an embedding column.
        """
        import pyarrow as pa

        if column_name in self.column_types:
            return self.column_types[column_name]
        return Float(arrow_type=pa.float32())

    def _load_model(self):
        """Load the pretrained vision model and its image processor."""
        from transformers import AutoImageProcessor, AutoModel

        self.processor = AutoImageProcessor.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
        self.model.eval()
        self._encoder = self._encode_with_model

    def _encode_with_model(self, images: list) -> "np.ndarray":
        """Encode a list of images using the loaded model and processor.

        Parameters
        ----------
        images : list of PIL.Image.Image
            Images to encode.

        Returns
        -------
        numpy.ndarray
            Array of shape ``(n_images, n_dims)`` with one embedding row
            per image.
        """
        import torch

        inputs = self.processor(images=images, return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            pooled = getattr(outputs, "pooler_output", None)
            embeddings = (
                pooled if pooled is not None else outputs.last_hidden_state[:, 0]
            )

        # Backbones disagree on the shape of a pooled representation. A vision
        # transformer such as DINOv2 returns (batch, hidden), while a CNN such
        # as ResNet returns the spatially pooled (batch, channels, 1, 1). Flatten
        # everything after the batch dimension so a row is always one vector.
        embeddings = embeddings.reshape(embeddings.shape[0], -1)

        return embeddings.cpu().numpy()

    def _process_batch(self, batch: "DashAIDataset") -> "DashAIDataset":
        """Encode a batch of image columns into dense embedding vectors.

        Each image column is decoded to PIL and passed through
        :attr:`_encoder` in chunks of ``self.batch_size``. Resulting
        float32 vectors are stored as separate ``Float`` columns, named
        ``emb_{column}_{i}``. The source image columns are removed only
        when ``self.keep_source_column`` is false.

        Parameters
        ----------
        batch : DashAIDataset
            A slice of the full dataset. Each column must contain image
            values decodable by :meth:`DashAIImage.to_pil`, with no null
            cells.

        Returns
        -------
        DashAIDataset
            Dataset with one appended ``Float`` column per embedding
            dimension per source column. The source columns themselves
            are kept or removed depending on ``self.keep_source_column``.

        Raises
        ------
        ValueError
            If an image column holds a null cell in this batch, naming the
            column and the row index within this batch. This is reachable
            with a ``segment_i`` column from ``SAM3SegmentConverter``,
            which is null past however many objects an image actually had;
            silently substituting a placeholder would feed a fabricated
            feature vector into whatever trains on the embedding, so this
            is surfaced instead of guessed at. Lowering ``max_masks``,
            scoping this converter to ``segment_1`` only, or removing the
            rows with null cells beforehand all avoid the error; setting
            ``on_no_detection`` to ``keep_original`` does not, since it only
            fills rank 1 for a row with zero detections. The row index is
            relative to the batch being processed, not the whole dataset:
            ``HuggingFaceWrapper.transform`` chunks the dataset before
            calling this method and never passes the chunk's offset, so a
            dataset global index would be wrong for any dataset larger than
            one batch, which is worse than an index that plainly says what
            it is relative to.
        """
        import numpy as np
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        result_table = batch.arrow_table
        batch_columns = batch[:]

        for column in batch.column_names:
            column_values = batch_columns[column]
            images: list = []
            for row_index, value in enumerate(column_values):
                if value is None:
                    raise ValueError(
                        f"Column '{column}' has no image in row {row_index} "
                        "of the current processing batch: cannot embed a "
                        "null cell. This can happen with a segment column "
                        "produced by SAM3SegmentConverter, where an image "
                        "with fewer detected objects than max_masks leaves "
                        "the remaining ranks null. Lower max_masks, scope "
                        "this converter to segment_1 only, or remove the "
                        "rows with null cells before running this "
                        "converter."
                    )
                images.append(value.to_pil())

            chunks = []
            for start in range(0, len(images), self.batch_size):
                chunk = images[start : start + self.batch_size]
                chunks.append(np.asarray(self._encoder(chunk)))

            if not chunks:
                continue

            embeddings_np = np.concatenate(chunks, axis=0)

            # One row must be one flat vector. A backbone that returns a
            # spatially pooled tensor, or an injected encoder returning the
            # wrong shape, would otherwise surface as an opaque pyarrow
            # conversion error naming a nested list.
            if embeddings_np.ndim != 2:
                raise ValueError(
                    f"The encoder for column '{column}' returned an array of "
                    f"shape {embeddings_np.shape}; an embedding must be two "
                    "dimensional, one flat vector per image."
                )

            for i in range(embeddings_np.shape[1]):
                result_table = result_table.append_column(
                    f"emb_{column}_{i}",
                    pa.array(embeddings_np[:, i].tolist(), type=pa.float32()),
                )

        if not self.keep_source_column:
            for column in batch.column_names:
                col_idx = result_table.column_names.index(column)
                result_table = result_table.remove_column(col_idx)

        return DashAIDataset(result_table)
