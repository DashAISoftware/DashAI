from typing import TYPE_CHECKING, Any, List, Tuple

from DashAI.back.core.schema_fields import (
    Check,
    Lt,
    enum_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.downloadable import (
    HFDownloadableMixin,
)
from DashAI.back.models.controlnet_model import ControlNetModel as BaseControlNetModel
from DashAI.back.models.utils import DEVICE_ENUM, DEVICE_PLACEHOLDER, DEVICE_TO_IDX

if TYPE_CHECKING:
    from PIL import Image


class SDXLCannyControlNetSchema(BaseSchema):
    """Configuration schema for SDXL Canny ControlNet image generation.

    Configures Canny edge detection thresholds (``canny_low_threshold``,
    ``canny_high_threshold``), the denoising schedule
    (``num_inference_steps``), edge conditioning strength
    (``controlnet_conditioning_scale``), and hardware target (``device``) for
    ``SDXLCannyControlNetModel``.
    """

    canny_low_threshold: schema_field(
        int_field(ge=0, le=255),
        placeholder=100,
        description=MultilingualString(
            en=(
                "Lower threshold for Canny edge detection (range 0-255). "
                "Edges with gradient below this value are discarded. "
                "Lower values detect more edges, including weaker ones. "
                "Typical range: 50-150."
            ),
            es=(
                "Umbral inferior para la detección de bordes Canny (rango 0-255). "
                "Los bordes con gradiente inferior a este valor se descartan. "
                "Valores menores detectan más bordes, incluyendo los más débiles. "
                "Rango típico: 50-150."
            ),
            pt=(
                "Limiar inferior para detecção de bordas Canny (intervalo 0-255). "
                "Bordas com gradiente abaixo deste valor são descartadas. "
                "Valores menores detectam mais bordas, incluindo as mais fracas. "
                "Intervalo típico: 50-150."
            ),
            de=(
                "Unterer Schwellenwert für die Canny-Kantenerkennung (Bereich 0-255). "
                "Kanten mit Gradientwert unterhalb dieses Werts werden verworfen. "
                "Niedrigere Werte erkennen mehr Kanten, einschließlich schwächerer. "
                "Typischer Bereich: 50-150."
            ),
            zh=(
                "Canny 边缘检测的下限阈值（范围 0-255）。"
                "梯度低于此值的边缘将被丢弃。"
                "较低的值会检测到更多边缘，包括较弱的边缘。"
                "典型范围：50-150。"
            ),
        ),
        alias=MultilingualString(
            en="Canny low threshold",
            es="Umbral bajo Canny",
            pt="Limiar inferior Canny",
            de="Canny unterer Schwellenwert",
            zh="Canny 下限阈值",
        ),
    )  # type: ignore

    canny_high_threshold: schema_field(
        int_field(ge=0, le=255),
        placeholder=200,
        description=MultilingualString(
            en=(
                "Upper threshold for Canny edge detection (range 0-255). "
                "Edges with gradient above this value are detected. "
                "Higher values produce fewer but stronger edges. "
                "Typical range: 150-250. Must be greater than low_threshold."
            ),
            es=(
                "Umbral superior para la detección de bordes Canny (rango 0-255). "
                "Los bordes con gradiente superior a este valor se detectan. "
                "Valores mayores producen menos bordes pero más fuertes. "
                "Rango típico: 150-250. Debe ser mayor que low_threshold."
            ),
            pt=(
                "Limiar superior para detecção de bordas Canny (intervalo 0-255). "
                "Bordas com gradiente acima deste valor são detectadas. "
                "Valores maiores produzem menos bordas, porém mais fortes. "
                "Intervalo típico: 150-250. Deve ser maior que low_threshold."
            ),
            de=(
                "Oberer Schwellenwert für die Canny-Kantenerkennung (Bereich 0-255). "
                "Kanten mit Gradientwert oberhalb dieses Werts werden erkannt. "
                "Höhere Werte erzeugen weniger, aber stärkere Kanten. "
                "Typischer Bereich: 150-250. Muss größer als low_threshold sein."
            ),
            zh=(
                "Canny 边缘检测的上限阈值（范围 0-255）。"
                "梯度高于此值的边缘将被检测。"
                "较高的值产生更少但更强的边缘。"
                "典型范围：150-250。必须大于 low_threshold。"
            ),
        ),
        alias=MultilingualString(
            en="Canny high threshold",
            es="Umbral alto Canny",
            pt="Limiar superior Canny",
            de="Canny oberer Schwellenwert",
            zh="Canny 上限阈值",
        ),
    )  # type: ignore

    num_inference_steps: schema_field(
        int_field(ge=1),
        placeholder=20,
        description=MultilingualString(
            en=(
                "Number of denoising steps. SDXL Canny achieves good quality with "
                "20-30 steps. More steps improve quality at the cost of "
                "generation time."
            ),
            es=(
                "Número de pasos de eliminación de ruido. SDXL Canny logra buena "
                "calidad con 20-30 pasos. Más pasos mejoran la calidad a costa de "
                "tiempo de generación."
            ),
            pt=(
                "Número de passos de eliminação de ruído. SDXL Canny alcança boa "
                "qualidade com 20-30 passos. Mais passos melhoram a qualidade ao "
                "custo do tempo de geração."
            ),
            de=(
                "Anzahl der Entrauschungsschritte. SDXL Canny erreicht gute "
                "Qualität mit 20-30 Schritten. Mehr Schritte verbessern die "
                "Qualität auf Kosten der Generierungszeit."
            ),
            zh=(
                "去噪步数。SDXL Canny 在 20-30 步时可达到良好质量。"
                "更多步数可提升质量，但会增加生成时间。"
            ),
        ),
        alias=MultilingualString(
            en="Num inference steps",
            es="Número de pasos de inferencia",
            pt="Número de passos de inferência",
            de="Anzahl Inferenzschritte",
            zh="推理步数",
        ),
    )  # type: ignore

    controlnet_conditioning_scale: schema_field(
        float_field(ge=0.0),
        placeholder=0.5,
        description=MultilingualString(
            en=(
                "Weight of the Canny edge conditioning (range 0.0-2.0). "
                "At 0.5 the edges guide the composition loosely. "
                "At 1.0 the output closely follows the input edges. "
                "Higher values produce more rigid edge adherence."
            ),
            es=(
                "Peso del condicionamiento de bordes Canny (rango 0.0-2.0). "
                "En 0.5 los bordes guían la composición ligeramente. "
                "En 1.0 la salida sigue de cerca los bordes de entrada. "
                "Valores más altos producen mayor adherencia a los bordes."
            ),
            pt=(
                "Peso do condicionamento de bordas Canny (intervalo 0.0-2.0). "
                "Em 0.5 as bordas guiam a composição levemente. "
                "Em 1.0 a saída segue de perto as bordas de entrada. "
                "Valores mais altos produzem maior aderência às bordas."
            ),
            de=(
                "Gewicht der Canny-Kantenkonditionierung (Bereich 0.0-2.0). "
                "Bei 0.5 führen die Kanten die Komposition lose. "
                "Bei 1.0 folgt die Ausgabe den Eingabekanten genau. "
                "Höhere Werte erzeugen stärkere Kantentreue."
            ),
            zh=(
                "Canny 边缘条件权重（范围 0.0-2.0）。"
                "0.5 时边缘对构图的引导较为宽松；"
                "1.0 时输出与输入边缘高度吻合。"
                "更高的值产生更严格的边缘约束。"
            ),
        ),
        alias=MultilingualString(
            en="ControlNet conditioning scale",
            es="Escala de condicionamiento ControlNet",
            pt="Escala de condicionamento ControlNet",
            de="ControlNet-Konditionierungsskala",
            zh="ControlNet 条件缩放",
        ),
    )  # type: ignore

    device: schema_field(
        enum_field(enum=DEVICE_ENUM),
        placeholder=DEVICE_PLACEHOLDER,
        description=MultilingualString(
            en=(
                "Hardware device for inference. GPU is strongly recommended for SDXL. "
                "CPU inference is very slow for this large model."
            ),
            es=(
                "Dispositivo de hardware para inferencia. Se recomienda "
                "encarecidamente GPU para SDXL. La inferencia en CPU es muy lenta "
                "para este modelo grande."
            ),
            pt=(
                "Dispositivo de hardware para inferência. GPU é fortemente recomendada "
                "para SDXL. A inferência em CPU é muito lenta para este modelo grande."
            ),
            de=(
                "Hardware-Gerät für die Inferenz. GPU wird für SDXL dringend empfohlen."
                "CPU-Inferenz ist für dieses große Modell sehr langsam."
            ),
            zh=(
                "推理使用的硬件设备。SDXL 强烈建议使用 GPU。"
                "对于此大型模型，CPU 推理非常缓慢。"
            ),
        ),
        alias=MultilingualString(
            en="Device",
            es="Dispositivo",
            pt="Dispositivo",
            de="Gerät",
            zh="设备",
        ),
    )  # type: ignore

    # A range the underlying library takes as one tuple, which the schema
    # cannot express, so it is split into two fields. OpenCV does not complain and
    # produces the same edges either way, so an inverted pair is silently wrong rather
    # than an error.
    rules = [
        Check(
            Lt("canny_low_threshold", "canny_high_threshold"),
            id="canny.thresholds_are_ordered",
            targets=["canny_low_threshold", "canny_high_threshold"],
            message=MultilingualString(
                en="The low threshold must be smaller than the high threshold.",
                es="El umbral bajo debe ser menor que el umbral alto.",
                pt="O limiar baixo deve ser menor que o limiar alto.",
                de=(
                    "Der untere Schwellwert muss kleiner als der obere Schwellwert "
                    "sein."
                ),
                zh="低阈值必须小于高阈值。",
            ),
        ),
    ]


def get_canny_image(
    image: "Image.Image", low_threshold: int, high_threshold: int
) -> "Image.Image":
    """Apply Canny edge detection to an image and return a three-channel edge map.

    Converts the image to a NumPy array, runs OpenCV's Canny detector with the
    supplied thresholds, then stacks the single-channel result into an RGB image
    suitable for use as a ControlNet conditioning signal.

    Parameters
    ----------
    image : PIL.Image.Image
        The source image to extract edges from.
    low_threshold : int
        Lower hysteresis threshold for the Canny algorithm (0-255). Gradient
        magnitudes below this value are discarded.
    high_threshold : int
        Upper hysteresis threshold for the Canny algorithm (0-255). Gradient
        magnitudes above this value are retained as strong edges.

    Returns
    -------
    PIL.Image.Image
        An RGB image of the same spatial dimensions as ``image`` where each
        channel contains the binary Canny edge map (0 or 255).
    """
    import cv2
    import numpy as np
    from PIL import Image

    image_array = np.array(image)
    edges = cv2.Canny(image_array, low_threshold, high_threshold)
    edges_rgb = np.stack([edges] * 3, axis=-1)
    return Image.fromarray(edges_rgb)


class SDXLCannyControlNetModel(HFDownloadableMixin, BaseControlNetModel):
    """Canny-edge-conditioned ControlNet pipeline built on Stable Diffusion XL 1.0.

    Takes an input image and a text prompt. Canny edge maps are extracted using
    OpenCV with configurable hysteresis thresholds, then fed as spatial
    conditioning into the ``diffusers/controlnet-canny-sdxl-1.0`` ControlNet
    backbone together with the ``stabilityai/stable-diffusion-xl-base-1.0``
    diffusion pipeline and the ``madebyollin/sdxl-vae-fp16-fix`` VAE. The result
    is a high-resolution image (up to 1024 x 1024 px) that closely follows the
    structural edges of the original while adhering to the text prompt.

    Requires ``opencv-python`` (``pip install opencv-python``).

    References
    ----------
    - [1] Zhang & Agrawala, "Adding Conditional Control to Text-to-Image
           Diffusion Models", ICCV 2023. https://arxiv.org/abs/2302.05543
    - [2] https://huggingface.co/diffusers/controlnet-canny-sdxl-1.0
    """

    SCHEMA = SDXLCannyControlNetSchema
    HF_REPOS = [
        ("stabilityai/stable-diffusion-xl-base-1.0", "model"),
        ("diffusers/controlnet-canny-sdxl-1.0", "model"),
        ("madebyollin/sdxl-vae-fp16-fix", "model"),
    ]
    DOWNLOAD_SIZE_BYTES = 51644917846
    COLOR: str = "#1a237e"
    DISPLAY_NAME: str = MultilingualString(
        en="SDXL Canny ControlNet",
        es="SDXL ControlNet Canny",
        pt="SDXL ControlNet Canny",
        de="SDXL Canny ControlNet",
        zh="SDXL Canny ControlNet",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Combines ControlNet Canny edge conditioning with the Stable Diffusion XL "
            "1.0 pipeline for edge-guided high-resolution image generation. Takes an "
            "input image and a text prompt: Canny edge detection (via OpenCV) extracts "
            "sharp structural edges, which are used as spatial conditions to guide "
            "image synthesis at 1024x1024 px. Uses diffusers/controlnet-canny-sdxl-1.0 "
            "(https://huggingface.co/diffusers/controlnet-canny-sdxl-1.0), "
            "madebyollin/sdxl-vae-fp16-fix "
            "(https://huggingface.co/madebyollin/sdxl-vae-fp16-fix), and "
            "stabilityai/stable-diffusion-xl-base-1.0 "
            "(https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0). "
            "Requires opencv-python: pip install opencv-python."
        ),
        es=(
            "Combina el condicionamiento de bordes Canny de ControlNet con el pipeline "
            "de Stable Diffusion XL 1.0 para generación de imágenes de alta resolución "
            "guiada por bordes. Recibe una imagen y un prompt: la detección de bordes "
            "Canny (vía OpenCV) extrae bordes estructurales nítidos usados como "
            "condiciones espaciales a 1024x1024 px. Utiliza "
            "diffusers/controlnet-canny-sdxl-1.0 "
            "(https://huggingface.co/diffusers/controlnet-canny-sdxl-1.0), "
            "madebyollin/sdxl-vae-fp16-fix "
            "(https://huggingface.co/madebyollin/sdxl-vae-fp16-fix) y "
            "stabilityai/stable-diffusion-xl-base-1.0 "
            "(https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0). "
            "Requiere opencv-python: pip install opencv-python."
        ),
        pt=(
            "Combina o condicionamento de bordas Canny do ControlNet com o pipeline "
            "do Stable Diffusion XL 1.0 para geração de imagens de alta resolução "
            "guiada por bordas. Recebe uma imagem de entrada e um prompt: a detecção "
            "de bordas Canny (via OpenCV) extrai bordas estruturais nítidas usadas "
            "como condições espaciais a 1024x1024 px. Utiliza "
            "diffusers/controlnet-canny-sdxl-1.0 "
            "(https://huggingface.co/diffusers/controlnet-canny-sdxl-1.0), "
            "madebyollin/sdxl-vae-fp16-fix "
            "(https://huggingface.co/madebyollin/sdxl-vae-fp16-fix) e "
            "stabilityai/stable-diffusion-xl-base-1.0 "
            "(https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0). "
            "Requer opencv-python: pip install opencv-python."
        ),
        de=(
            "Kombiniert die Canny-Kantenkonditionierung von ControlNet mit der Stable "
            "Diffusion XL 1.0-Pipeline für kantengeführte hochauflösende "
            "Bildgenerierung. "
            "Nimmt ein Eingabebild und einen Textprompt: Die Canny-Kantenerkennung "
            "(über "
            "OpenCV) extrahiert scharfe Strukturkanten, die als räumliche Bedingungen "
            "bei 1024x1024 px dienen. Verwendet diffusers/controlnet-canny-sdxl-1.0 "
            "(https://huggingface.co/diffusers/controlnet-canny-sdxl-1.0), "
            "madebyollin/sdxl-vae-fp16-fix "
            "(https://huggingface.co/madebyollin/sdxl-vae-fp16-fix) und "
            "stabilityai/stable-diffusion-xl-base-1.0 "
            "(https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0). "
            "Erfordert opencv-python: pip install opencv-python."
        ),
        zh=(
            "结合 ControlNet Canny 边缘条件与 Stable Diffusion XL 1.0，"
            "实现边缘引导的 1024x1024px 高分辨率图像生成。需要 opencv-python。"
        ),
    )

    def __init__(self, **kwargs: Any):
        """Initialize the SDXL Canny ControlNet model and pipeline.

        Loads ``diffusers/controlnet-canny-sdxl-1.0`` as the ControlNet
        backbone, ``madebyollin/sdxl-vae-fp16-fix`` as the VAE, and
        ``stabilityai/stable-diffusion-xl-base-1.0`` as the base diffusion
        pipeline, all moved to the requested device. CPU offloading is enabled
        automatically via ``pipe.enable_model_cpu_offload()`` to reduce VRAM
        pressure.

        Requires ``opencv-python`` (``pip install opencv-python``).

        Parameters
        ----------
        **kwargs : Any
            Keyword arguments validated against :class:`SDXLCannyControlNetSchema`.
            Recognised keys are:

            device : str
                Target hardware (e.g. ``"GPU 0"`` or ``"CPU"``).
            num_inference_steps : int
                Number of denoising steps during generation.
            controlnet_conditioning_scale : float
                Strength of the Canny edge conditioning signal (0.0-2.0).
            canny_low_threshold : int
                Lower Canny hysteresis threshold (0-255).
            canny_high_threshold : int
                Upper Canny hysteresis threshold (0-255).
        """
        import torch
        from diffusers import (
            AutoencoderKL,
            ControlNetModel,
            StableDiffusionXLControlNetPipeline,
        )

        kwargs = self.validate_and_transform(kwargs)
        use_gpu = DEVICE_TO_IDX.get(kwargs.get("device")) >= 0
        self.device = (
            f"cuda:{DEVICE_TO_IDX.get(kwargs.get('device'))}" if use_gpu else "cpu"
        )

        controlnet = ControlNetModel.from_pretrained(
            self._local_or_repo("diffusers/controlnet-canny-sdxl-1.0"),
            torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
        ).to(self.device)

        vae = AutoencoderKL.from_pretrained(
            self._local_or_repo("madebyollin/sdxl-vae-fp16-fix"),
            torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
        ).to(self.device)

        self.pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
            self._local_or_repo("stabilityai/stable-diffusion-xl-base-1.0"),
            controlnet=controlnet,
            vae=vae,
            torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
        ).to(self.device)

        self.canny_low_threshold = kwargs.get("canny_low_threshold", 100)
        self.canny_high_threshold = kwargs.get("canny_high_threshold", 200)
        self.controlnet_conditioning_scale = kwargs.get("controlnet_conditioning_scale")
        self.num_inference_steps = kwargs.get("num_inference_steps")

        if self.device != "cpu":
            self.pipe.enable_model_cpu_offload()

    def generate(self, input: Tuple["Image.Image", str]) -> List[Any]:
        """Generate output from a generative model.

        Parameters
        ----------
        input : Tuple[Image.Image, str]
            Input image and text prompt.

        Returns
        -------
        List[Any]
            Generated output images in a list.
        """
        image = input[0]
        prompt = input[1]

        canny_image = get_canny_image(
            image, self.canny_low_threshold, self.canny_high_threshold
        )
        output = self.pipe(
            prompt=prompt,
            image=canny_image,
            num_inference_steps=self.num_inference_steps,
            controlnet_conditioning_scale=float(self.controlnet_conditioning_scale),
            height=image.size[1],
            width=image.size[0],
        )
        return output.images
