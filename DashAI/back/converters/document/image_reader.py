"""Base for document converters that turn images into text items."""

from typing import TYPE_CHECKING, Any, List, Union

from DashAI.back.converters.category.document_processing import (
    DocumentProcessingConverter,
)
from DashAI.back.converters.document_converter import DocumentConverter
from DashAI.back.converters.hugging_face.pretrained_tool import (
    PretrainedTool,
    batches,
    open_image,
)
from DashAI.back.core.schema_fields import bool_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_image import DashAIImage

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


def keep_image_field() -> Any:
    """Return the schema field that keeps or replaces the read images.

    Returns
    -------
    Any
        A ``keep_image`` boolean field, true by default.
    """
    return schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en=(
                "Keep each image and insert its text right after it. Off, each "
                "image is replaced by its text, and images without text are "
                "removed."
            ),
            es=(
                "Conserva cada imagen e inserta su texto justo después. "
                "Desactivado, cada imagen se reemplaza por su texto y se "
                "eliminan las imágenes sin texto."
            ),
            pt=(
                "Mantém cada imagem e insere seu texto logo depois. Desativado, "
                "cada imagem é substituída pelo seu texto e as imagens sem texto "
                "são removidas."
            ),
            de=(
                "Behält jedes Bild und fügt seinen Text direkt danach ein. "
                "Ausgeschaltet wird jedes Bild durch seinen Text ersetzt, und "
                "Bilder ohne Text werden entfernt."
            ),
            zh=(
                "保留每张图片，并在其后插入其文本。关闭时，每张图片被其文本替换，没有文"
                "本的图片会被删除。"
            ),
        ),
        alias=MultilingualString(
            en="Keep images",
            es="Conservar imágenes",
            pt="Manter imagens",
            de="Bilder behalten",
            zh="保留图片",
        ),
    )


class ImageReader(DocumentProcessingConverter, PretrainedTool, DocumentConverter):
    """Turn each selected Image item into a Text item read from it.

    Subclasses implement :meth:`read_images` and set ``OUTPUT_KIND``. The
    text item takes the page of its image and comes right after it, or in
    its place when ``keep_image`` is off.
    """

    BATCH_SIZE = 2
    metadata = {"allowed_types": [DashAIImage], "allowed_dtypes": []}

    def read_images(self, images: List[Any]) -> List[str]:
        """Read the text of a batch of images.

        Parameters
        ----------
        images : List[PIL.Image.Image]
            RGB images.

        Returns
        -------
        List[str]
            The text of each image, empty when there is none.
        """
        raise NotImplementedError

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Return one Text item for every image with text.

        Parameters
        ----------
        x : DashAIDataset
            The selected Image items, in one column.
        y : DashAIDataset, optional
            Ignored.

        Returns
        -------
        DashAIDataset
            The text of each image that has some, with its source row.
        """
        values = x.arrow_table.column(0).to_pylist()
        texts: List[str] = []
        for batch in batches(values, self.BATCH_SIZE):
            texts.extend(self.read_images([open_image(value) for value in batch]))
        sources = [index for index, text in enumerate(texts) if text.strip()]
        return self.items_result(
            [texts[index].strip() for index in sources],
            sources,
            kinds=[self.OUTPUT_KIND] * len(sources),
        )
