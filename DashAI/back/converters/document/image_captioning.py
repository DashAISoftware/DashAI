"""Describe document images with a captioning model."""

from typing import Any, List, Tuple

from DashAI.back.converters.document.image_reader import ImageReader, keep_image_field
from DashAI.back.converters.hugging_face.pretrained_tool import device_field
from DashAI.back.core.schema_fields import int_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.utils import DEVICE_PLACEHOLDER


class ImageCaptioningSchema(BaseSchema):
    """Schema for the image captioning converter."""

    keep_image: keep_image_field()  # type: ignore
    max_tokens: schema_field(
        int_field(ge=5, le=100),
        40,
        description=MultilingualString(
            en="Longest caption, in model tokens (about 3/4 of a word each).",
            es=(
                "Leyenda más larga, en tokens del modelo (unos 3/4 de palabra cada "
                "uno)."
            ),
            pt=(
                "Legenda mais longa, em tokens do modelo (cerca de 3/4 de palavra "
                "cada)."
            ),
            de="Längste Bildunterschrift in Modell-Tokens (je etwa 3/4 Wort).",
            zh="说明文字的最大长度，以模型词元计（每个约 3/4 个单词）。",
        ),
        alias=MultilingualString(
            en="Maximum caption tokens",
            es="Máximo de tokens de la leyenda",
            pt="Máximo de tokens da legenda",
            de="Maximale Tokens der Bildunterschrift",
            zh="说明文字最大词元数",
        ),
    )  # type: ignore
    device: device_field()  # type: ignore


class ImageCaptioningConverter(ImageReader):
    """Describe each Image item in English with BLIP.

    ``Salesforce/blip-image-captioning-base`` writes a short English
    description, given as a caption item, so text tools and RAG can find
    figures and photos.
    """

    SCHEMA = ImageCaptioningSchema
    MODEL_NAME = "Salesforce/blip-image-captioning-base"
    DOWNLOAD_SIZE_BYTES = 990777070
    OUTPUT_KIND = "caption"
    DISPLAY_NAME = MultilingualString(
        en="Image Captioning",
        es="Descripción de Imágenes",
        pt="Legendagem de Imagens",
        de="Bildbeschreibung",
        zh="图像描述",
    )
    DESCRIPTION = MultilingualString(
        en="Writes an English caption for each image item (BLIP) as a caption item.",
        es=(
            "Escribe una leyenda en inglés para cada imagen (BLIP) como elemento "
            "caption."
        ),
        pt="Escreve uma legenda em inglês para cada imagem (BLIP) como item caption.",
        de=(
            "Schreibt für jedes Bild eine englische Beschreibung (BLIP) als "
            "Caption-Element."
        ),
        zh="为每个图像元素生成英文说明（BLIP），作为 caption 元素。",
    )

    def __init__(
        self,
        keep_image: bool = True,
        max_tokens: int = 40,
        device: str = DEVICE_PLACEHOLDER,
    ) -> None:
        """Store the captioning options.

        Parameters
        ----------
        keep_image : bool, optional
            Keep each image and insert its caption after it. Default True.
        max_tokens : int, optional
            Longest caption in tokens. Default 40.
        device : str, optional
            The device label the model runs on.
        """
        super().__init__()
        self.keep_source = keep_image
        self.max_tokens = max_tokens
        self.setup_device(device)

    def load_pretrained(self, source: str) -> Tuple[Any, Any]:
        """Load the BLIP processor and model.

        Parameters
        ----------
        source : str
            A local directory or the Hub repo id.

        Returns
        -------
        Tuple[Any, Any]
            The processor and the model, in evaluation mode on the device.
        """
        from transformers import BlipForConditionalGeneration, BlipProcessor

        processor = BlipProcessor.from_pretrained(source)
        model = BlipForConditionalGeneration.from_pretrained(source)
        return processor, model.to(self.device).eval()

    def read_images(self, images: List[Any]) -> List[str]:
        """Caption a batch of images.

        Parameters
        ----------
        images : List[PIL.Image.Image]
            RGB images.

        Returns
        -------
        List[str]
            One caption per image.
        """
        import torch

        processor, model = self.pretrained()
        inputs = processor(images=images, return_tensors="pt").to(self.device)
        with torch.no_grad():
            output = model.generate(**inputs, max_new_tokens=self.max_tokens)
        return processor.batch_decode(output, skip_special_tokens=True)
