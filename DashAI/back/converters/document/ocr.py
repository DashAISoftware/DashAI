"""Read the text in document images with an OCR model."""

from typing import Any, List, Tuple

from DashAI.back.converters.document.image_reader import ImageReader, keep_image_field
from DashAI.back.converters.hugging_face.pretrained_tool import device_field
from DashAI.back.core.schema_fields import int_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.utils import DEVICE_PLACEHOLDER


class OCRSchema(BaseSchema):
    """Schema for the OCR converter."""

    keep_image: keep_image_field()  # type: ignore
    max_tokens: schema_field(
        int_field(ge=16, le=8192),
        2048,
        description=MultilingualString(
            en=(
                "Most text read from one image, in model tokens. Raise it for "
                "full pages of small print."
            ),
            es=(
                "Máximo de texto leído de una imagen, en tokens del modelo. "
                "Súbelo para páginas completas con letra pequeña."
            ),
            pt=(
                "Máximo de texto lido de uma imagem, em tokens do modelo. "
                "Aumente para páginas inteiras com letra pequena."
            ),
            de=(
                "Höchstmenge Text pro Bild in Modell-Tokens. Für ganze Seiten "
                "mit kleiner Schrift erhöhen."
            ),
            zh="从一张图片读取的最大文本量（模型词元）。对小字号整页可调高。",
        ),
        alias=MultilingualString(
            en="Maximum tokens per image",
            es="Máximo de tokens por imagen",
            pt="Máximo de tokens por imagem",
            de="Maximale Tokens pro Bild",
            zh="每张图片最大词元数",
        ),
    )  # type: ignore
    device: device_field()  # type: ignore


class OCRConverter(ImageReader):
    """Read the text in Image items with GOT-OCR 2.0.

    ``stepfun-ai/GOT-OCR-2.0-hf`` reads printed text, including whole pages,
    in many languages. Each image with text gives a paragraph item.
    """

    SCHEMA = OCRSchema
    MODEL_NAME = "stepfun-ai/GOT-OCR-2.0-hf"
    DOWNLOAD_SIZE_BYTES = 1139871246
    OUTPUT_KIND = "paragraph"
    DISPLAY_NAME = MultilingualString(
        en="OCR (Image to Text)",
        es="OCR (Imagen a Texto)",
        pt="OCR (Imagem para Texto)",
        de="OCR (Bild zu Text)",
        zh="OCR（图像转文本）",
    )
    DESCRIPTION = MultilingualString(
        en="Reads the text in image items (GOT-OCR 2.0) as new text items.",
        es=(
            "Lee el texto de los elementos de imagen (GOT-OCR 2.0) como nuevos "
            "elementos de texto."
        ),
        pt="Lê o texto dos itens de imagem (GOT-OCR 2.0) como novos itens de texto.",
        de="Liest den Text in Bildelementen (GOT-OCR 2.0) als neue Textelemente.",
        zh="读取图像元素中的文本（GOT-OCR 2.0），生成新的文本元素。",
    )

    def __init__(
        self,
        keep_image: bool = True,
        max_tokens: int = 2048,
        device: str = DEVICE_PLACEHOLDER,
    ) -> None:
        """Store the OCR options.

        Parameters
        ----------
        keep_image : bool, optional
            Keep each image and insert its text after it. Default True.
        max_tokens : int, optional
            Most tokens read from one image. Default 2048.
        device : str, optional
            The device label the model runs on.
        """
        super().__init__()
        self.keep_source = keep_image
        self.max_tokens = max_tokens
        self.setup_device(device)

    def load_pretrained(self, source: str) -> Tuple[Any, Any]:
        """Load the GOT-OCR processor and model.

        Parameters
        ----------
        source : str
            A local directory or the Hub repo id.

        Returns
        -------
        Tuple[Any, Any]
            The processor and the model, in evaluation mode on the device.
        """
        from transformers import AutoModelForImageTextToText, AutoProcessor

        processor = AutoProcessor.from_pretrained(source)
        model = AutoModelForImageTextToText.from_pretrained(source)
        return processor, model.to(self.device).eval()

    def read_images(self, images: List[Any]) -> List[str]:
        """Read the text of a batch of images.

        Parameters
        ----------
        images : List[PIL.Image.Image]
            RGB images.

        Returns
        -------
        List[str]
            The text of each image.
        """
        import torch

        processor, model = self.pretrained()
        inputs = processor(images, return_tensors="pt").to(self.device)
        with torch.no_grad():
            output = model.generate(
                **inputs,
                do_sample=False,
                tokenizer=processor.tokenizer,
                stop_strings="<|im_end|>",
                max_new_tokens=self.max_tokens,
            )
        prompt_length = inputs["input_ids"].shape[1]
        return processor.batch_decode(
            output[:, prompt_length:], skip_special_tokens=True
        )
