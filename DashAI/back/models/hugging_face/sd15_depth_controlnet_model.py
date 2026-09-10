from typing import TYPE_CHECKING, Any, List, Tuple

from DashAI.back.core.schema_fields import (
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


class SD15DepthControlNetSchema(BaseSchema):
    """Configuration schema for SD 1.5 Depth ControlNet image generation.

    Configures the denoising schedule (``num_inference_steps``), depth-map
    conditioning strength (``controlnet_conditioning_scale``), prompt adherence
    (``guidance_scale``), and hardware target (``device``) for
    ``SD15DepthControlNetModel``.
    """

    num_inference_steps: schema_field(
        int_field(ge=1),
        placeholder=20,
        description=MultilingualString(
            en=(
                "Number of denoising steps to run. More steps refine the image but "
                "increase generation time. Typical range: 20-30 for fast results, "
                "40-50 for higher quality."
            ),
            es=(
                "Número de pasos de eliminación de ruido. Más pasos refinan la imagen "
                "pero aumentan el tiempo de generación. Rango típico: 20-30 para "
                "resultados rápidos, 40-50 para mayor calidad."
            ),
            pt=(
                "Número de passos de eliminação de ruído. Mais passos refinam a imagem "
                "mas aumentam o tempo de geração. Intervalo típico: 20-30 para "
                "resultados rápidos, 40-50 para maior qualidade."
            ),
            de=(
                "Anzahl der Entrauschungsschritte. Mehr Schritte verfeinern das Bild, "
                "erhöhen aber die Generierungszeit. Typischer Bereich: 20-30 für "
                "schnelle Ergebnisse, 40-50 für höhere Qualität."
            ),
            zh=(
                "去噪步数。步数越多图像越精细，但生成时间也越长。"
                "典型范围：20-30 步适合快速生成，40-50 步适合更高质量。"
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
        placeholder=1.0,
        description=MultilingualString(
            en=(
                "Weight of the ControlNet depth conditioning relative to the base "
                "diffusion pipeline (range 0.0-2.0). At 0.0 the depth map has no "
                "effect; at 1.0 the output closely follows the input structure; "
                "above 1.5 depth dominates and may produce rigid results."
            ),
            es=(
                "Peso del condicionamiento de profundidad ControlNet (rango 0.0-2.0). "
                "En 0.0 el mapa de profundidad no tiene efecto; en 1.0 la salida sigue "
                "la estructura de la entrada; por encima de 1.5 domina la profundidad "
                "y puede producir resultados rígidos."
            ),
            pt=(
                "Peso do condicionamento de profundidade do ControlNet (intervalo "
                "0.0-2.0). Em 0.0 o mapa de profundidade não tem efeito; em 1.0 a "
                "saída segue de perto a estrutura da entrada; acima de 1.5 a "
                "profundidade domina e pode produzir resultados rígidos."
            ),
            de=(
                "Gewichtung des ControlNet-Tiefenkonditionierens (Bereich 0.0-2.0). "
                "Bei 0.0 hat die Tiefenkarte keinen Effekt; bei 1.0 folgt die Ausgabe "
                "eng der Eingangsstruktur; über 1.5 dominiert die Tiefe und kann zu "
                "starren Ergebnissen führen."
            ),
            zh=(
                "ControlNet 深度条件权重（范围 0.0-2.0）。"
                "0.0 时深度图无效果；1.0 时输出紧随输入结构；"
                "超过 1.5 时深度主导，可能产生僵硬结果。"
            ),
        ),
        alias=MultilingualString(
            en="ControlNet conditioning scale",
            es="Escala de condicionamiento ControlNet",
            pt="Escala de condicionamento ControlNet",
            de="ControlNet-Konditionierungsskala",
            zh="ControlNet 条件缩放系数",
        ),
    )  # type: ignore

    guidance_scale: schema_field(
        float_field(ge=0.0),
        placeholder=7.5,
        description=MultilingualString(
            en=(
                "Classifier-Free Guidance (CFG) scale. Controls how strictly the "
                "image follows the text prompt. Values 7-9 are typical for SD 1.5."
            ),
            es=(
                "Escala de Classifier-Free Guidance (CFG). Controla qué tan "
                "estrictamente la imagen sigue el prompt. Valores 7-9 son típicos "
                "para SD 1.5."
            ),
            pt=(
                "Escala de Orientação Livre de Classificador (CFG). Controla com que "
                "rigor a imagem segue o prompt. Valores 7-9 são típicos para SD 1.5."
            ),
            de=(
                "Classifier-Free Guidance (CFG)-Skala. Steuert, wie streng das Bild "
                "dem Text-Prompt folgt. Werte 7-9 sind typisch für SD 1.5."
            ),
            zh=(
                "无分类器引导（CFG）缩放系数。控制图像对文本提示的遵从程度。"
                "SD 1.5 典型值为 7-9。"
            ),
        ),
        alias=MultilingualString(
            en="Guidance scale",
            es="Escala de guía",
            pt="Escala de orientação",
            de="Führungsskala",
            zh="引导缩放系数",
        ),
    )  # type: ignore

    device: schema_field(
        enum_field(enum=DEVICE_ENUM),
        placeholder=DEVICE_PLACEHOLDER,
        description=MultilingualString(
            en=(
                "Hardware device for inference. GPU is strongly recommended for "
                "diffusion models. CPU inference is possible but very slow."
            ),
            es=(
                "Dispositivo de hardware para inferencia. Se recomienda GPU para "
                "modelos de difusión. La inferencia en CPU es posible pero muy lenta."
            ),
            pt=(
                "Dispositivo de hardware para inferência. GPU é fortemente "
                "recomendada para modelos de difusão. A inferência em CPU é "
                "possível, mas muito lenta."
            ),
            de=(
                "Hardware-Gerät für die Inferenz. GPU wird dringend für "
                "Diffusionsmodelle empfohlen. CPU-Inferenz ist möglich, "
                "aber sehr langsam."
            ),
            zh=(
                "推理硬件设备。强烈推荐使用 GPU 运行扩散模型，"
                "CPU 推理虽可行但速度极慢。"
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


def get_depth_map_sd15(image, device, model_source="Intel/dpt-hybrid-midas"):
    """Convert an input image to a normalised depth map for SD 1.5 ControlNet.

    Uses Intel's DPT-Hybrid-MiDaS model to estimate per-pixel depth, then
    interpolates the result back to the source image resolution (rounded down
    to a multiple of 8) and normalises values to the [0, 1] range before
    returning a three-channel PIL image.

    Parameters
    ----------
    image : PIL.Image.Image
        The source image to estimate depth from.
    device : str
        Torch device string (e.g. ``"cpu"`` or ``"cuda:0"``) on which the
        depth estimator will run.

    Returns
    -------
    PIL.Image.Image
        An RGB image at the source resolution (each side rounded down to a
        multiple of 8) where each channel encodes the normalised depth value,
        ready to be used as a ControlNet conditioning signal.
    """
    import numpy as np
    import torch
    from PIL import Image
    from transformers import DPTForDepthEstimation, DPTImageProcessor

    depth_estimator = DPTForDepthEstimation.from_pretrained(model_source).to(device)
    feature_extractor = DPTImageProcessor.from_pretrained(model_source)

    pixel_values = feature_extractor(images=image, return_tensors="pt").pixel_values.to(
        device
    )

    with torch.no_grad(), torch.autocast(device, dtype=torch.float16):
        depth_map = depth_estimator(pixel_values).predicted_depth

    # Preserve the source resolution. SD 1.5's UNet downsamples by 8 in latent
    # space, so both dimensions must be divisible by 8; round down to the
    # nearest multiple to avoid a pipeline shape error.
    width, height = image.size
    width = max(8, (width // 8) * 8)
    height = max(8, (height // 8) * 8)

    depth_map = torch.nn.functional.interpolate(
        depth_map.unsqueeze(1),
        size=(height, width),
        mode="bicubic",
        align_corners=False,
    )
    depth_min = torch.amin(depth_map, dim=[1, 2, 3], keepdim=True)
    depth_max = torch.amax(depth_map, dim=[1, 2, 3], keepdim=True)
    depth_map = (depth_map - depth_min) / (depth_max - depth_min)
    image = torch.cat([depth_map] * 3, dim=1)
    image = image.permute(0, 2, 3, 1).cpu().numpy()[0]
    image = Image.fromarray((image * 255.0).clip(0, 255).astype(np.uint8))
    return image


class SD15DepthControlNetModel(HFDownloadableMixin, BaseControlNetModel):
    """Depth-conditioned ControlNet pipeline built on Stable Diffusion 1.5.

    Takes an input image and a text prompt. A depth map is estimated from the
    image using Intel's DPT-Hybrid-MiDaS model, then fed as a spatial
    conditioning signal into the ``lllyasviel/sd-controlnet-depth`` ControlNet
    backbone together with the ``runwayml/stable-diffusion-v1-5`` diffusion
    pipeline. The result is a 512 x 512 image that respects both the text
    description and the 3-D structure of the original scene.

    References
    ----------
    - [1] Zhang & Agrawala, "Adding Conditional Control to Text-to-Image
           Diffusion Models", ICCV 2023. https://arxiv.org/abs/2302.05543
    - [2] https://huggingface.co/lllyasviel/sd-controlnet-depth
    """

    SCHEMA = SD15DepthControlNetSchema
    HF_REPOS = [
        ("runwayml/stable-diffusion-v1-5", "model"),
        ("lllyasviel/sd-controlnet-depth", "model"),
        ("Intel/dpt-hybrid-midas", "model"),
    ]
    DOWNLOAD_SIZE_BYTES = 50640633273
    COLOR: str = "#4e342e"
    DISPLAY_NAME: str = MultilingualString(
        en="SD 1.5 Depth ControlNet",
        es="SD 1.5 ControlNet de Profundidad",
        pt="SD 1.5 ControlNet de Profundidade",
        zh="SD 1.5 深度 ControlNet",
        de="SD 1.5 Tiefen-ControlNet",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Combines ControlNet depth conditioning with Stable Diffusion 1.5 for "
            "structure-aware image generation. Takes an input image and a text prompt: "
            "a depth map is extracted using Intel's DPT-Hybrid-MiDaS model, then used "
            "as a spatial condition to guide image synthesis at 512x512 px. Uses "
            "lllyasviel/sd-controlnet-depth "
            "(https://huggingface.co/lllyasviel/sd-controlnet-depth) and "
            "runwayml/stable-diffusion-v1-5 "
            "(https://huggingface.co/runwayml/stable-diffusion-v1-5)."
        ),
        es=(
            "Combina el condicionamiento de profundidad de ControlNet con Stable "
            "Diffusion 1.5 para generación de imágenes con conciencia de estructura. "
            "Recibe una imagen y un prompt de texto: se extrae un mapa de profundidad "
            "usando DPT-Hybrid-MiDaS de Intel y se usa como condición espacial a "
            "512x512 px. Utiliza lllyasviel/sd-controlnet-depth "
            "(https://huggingface.co/lllyasviel/sd-controlnet-depth) y "
            "runwayml/stable-diffusion-v1-5 "
            "(https://huggingface.co/runwayml/stable-diffusion-v1-5)."
        ),
        pt=(
            "Combina o condicionamento de profundidade do ControlNet com o Stable "
            "Diffusion 1.5 para geração de imagens com reconhecimento de estrutura. "
            "Recebe uma imagem de entrada e um prompt de texto: um mapa de "
            "profundidade é extraído usando o modelo DPT-Hybrid-MiDaS da Intel "
            "e usado como condição espacial para guiar a síntese de imagens a "
            "512x512 px. Utiliza "
            "lllyasviel/sd-controlnet-depth "
            "(https://huggingface.co/lllyasviel/sd-controlnet-depth) e "
            "runwayml/stable-diffusion-v1-5 "
            "(https://huggingface.co/runwayml/stable-diffusion-v1-5)."
        ),
        zh=(
            "结合 ControlNet 深度条件与 Stable Diffusion 1.5，"
            "使用 Intel DPT-Hybrid-MiDaS 模型提取深度图，"
            "实现结构感知的 512x512px 图像生成。"
        ),
        de=(
            "Kombiniert die ControlNet-Tiefenkonditionierung mit Stable Diffusion 1.5 "
            "für strukturbewusste Bildgenerierung. Nimmt ein Eingabebild und einen "
            "Text-Prompt: Eine Tiefenkarte wird mit dem DPT-Hybrid-MiDaS-Modell von "
            "Intel extrahiert und als räumliche Bedingung zur Steuerung der "
            "Bildsynthese bei 512x512 px verwendet. Verwendet "
            "lllyasviel/sd-controlnet-depth "
            "(https://huggingface.co/lllyasviel/sd-controlnet-depth) und "
            "runwayml/stable-diffusion-v1-5 "
            "(https://huggingface.co/runwayml/stable-diffusion-v1-5)."
        ),
    )

    def __init__(self, **kwargs: Any):
        """Initialize the SD 1.5 Depth ControlNet model and pipeline.

        Loads ``lllyasviel/sd-controlnet-depth`` as the ControlNet backbone and
        ``runwayml/stable-diffusion-v1-5`` as the base diffusion pipeline, both
        moved to the requested device. CPU offloading is enabled automatically
        via ``pipe.enable_model_cpu_offload()`` to reduce VRAM pressure.

        Parameters
        ----------
        **kwargs : Any
            Keyword arguments validated against :class:`SD15DepthControlNetSchema`.
            Recognised keys are:

            device : str
                Target hardware (e.g. ``"GPU 0"`` or ``"CPU"``).
            num_inference_steps : int
                Number of denoising steps during generation.
            controlnet_conditioning_scale : float
                Strength of the depth-map conditioning signal (0.0-2.0).
            guidance_scale : float
                Classifier-Free Guidance scale controlling prompt adherence.
        """
        import torch
        from diffusers import ControlNetModel, StableDiffusionControlNetPipeline

        kwargs = self.validate_and_transform(kwargs)
        use_gpu = DEVICE_TO_IDX.get(kwargs.get("device")) >= 0
        self.device = (
            f"cuda:{DEVICE_TO_IDX.get(kwargs.get('device'))}" if use_gpu else "cpu"
        )

        controlnet = ControlNetModel.from_pretrained(
            self._local_or_repo("lllyasviel/sd-controlnet-depth"),
            torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
        ).to(self.device)

        self.pipe = StableDiffusionControlNetPipeline.from_pretrained(
            self._local_or_repo("runwayml/stable-diffusion-v1-5"),
            controlnet=controlnet,
            torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
        ).to(self.device)

        self.controlnet_conditioning_scale = kwargs.get("controlnet_conditioning_scale")
        self.num_inference_steps = kwargs.get("num_inference_steps")
        self.guidance_scale = kwargs.get("guidance_scale")

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

        depth_map = get_depth_map_sd15(
            image, self.device, self._local_or_repo("Intel/dpt-hybrid-midas")
        )
        output = self.pipe(
            prompt=prompt,
            image=depth_map,
            num_inference_steps=self.num_inference_steps,
            guidance_scale=self.guidance_scale,
            controlnet_conditioning_scale=self.controlnet_conditioning_scale,
        )
        return output.images
