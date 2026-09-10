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


class SD15HEDControlNetSchema(BaseSchema):
    """Configuration schema for SD 1.5 HED ControlNet image generation.

    Configures the denoising schedule (``num_inference_steps``), soft-edge
    conditioning strength (``controlnet_conditioning_scale``), prompt adherence
    (``guidance_scale``), and hardware target (``device``) for
    ``SD15HEDControlNetModel``.
    """

    num_inference_steps: schema_field(
        int_field(ge=1),
        placeholder=20,
        description=MultilingualString(
            en=(
                "Number of denoising steps. Typical range: 20-30 for fast results, "
                "40-50 for higher quality."
            ),
            es=(
                "Número de pasos de eliminación de ruido. Rango típico: 20-30 para "
                "resultados rápidos, 40-50 para mayor calidad."
            ),
            pt=(
                "Número de passos de eliminação de ruído. Intervalo típico: 20-30 para "
                "resultados rápidos, 40-50 para maior qualidade."
            ),
            de=(
                "Anzahl der Entrauschungsschritte. Typischer Bereich: 20-30 für "
                "schnelle Ergebnisse, 40-50 für höhere Qualität."
            ),
            zh="去噪步数。典型范围：20-30 步获得快速结果，40-50 步获得更高质量。",
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
                "Weight of the ControlNet soft-edge conditioning (range 0.0-2.0). "
                "HED produces soft, sketch-like edge maps that are less strict than "
                "Canny. At 1.0 the output closely follows the input edges. "
                "Lower values give more creative freedom."
            ),
            es=(
                "Peso del condicionamiento de borde suave ControlNet (rango 0.0-2.0). "
                "HED produce mapas de bordes suaves tipo boceto, menos estrictos "
                "que Canny. "
                "En 1.0 la salida sigue de cerca los bordes de entrada. "
                "Valores menores dan más libertad creativa."
            ),
            pt=(
                "Peso do condicionamento de borda suave do ControlNet (intervalo "
                "0.0-2.0). HED produz mapas de bordas suaves estilo esboço, menos "
                "rígidos que o Canny. Em 1.0 a saída segue de perto as bordas de "
                "entrada. Valores menores oferecem mais liberdade criativa."
            ),
            de=(
                "Gewicht der weichen ControlNet-Kantenkonditionierung (Bereich "
                "0.0-2.0). "
                "HED erzeugt weiche, skizzenartige Kantenkarten, die weniger streng "
                "als Canny sind. Bei 1.0 folgt die Ausgabe den Eingabekanten eng. "
                "Niedrigere Werte bieten mehr kreative Freiheit."
            ),
            zh=(
                "ControlNet 软边缘条件权重（范围 0.0-2.0）。"
                "HED 生成类素描的柔和边缘图，比 Canny 更宽松。"
                "值为 1.0 时输出紧随输入边缘，较低值提供更多创意自由度。"
            ),
        ),
        alias=MultilingualString(
            en="ControlNet conditioning scale",
            es="Escala de condicionamiento ControlNet",
            pt="Escala de condicionamento ControlNet",
            de="ControlNet-Konditionierungsskala",
            zh="ControlNet 条件权重",
        ),
    )  # type: ignore

    guidance_scale: schema_field(
        float_field(ge=0.0),
        placeholder=7.5,
        description=MultilingualString(
            en=(
                "Classifier-Free Guidance (CFG) scale. Controls prompt adherence. "
                "Values 7-9 are typical for SD 1.5."
            ),
            es=(
                "Escala CFG. Controla la adherencia al prompt. "
                "Valores 7-9 son típicos para SD 1.5."
            ),
            pt=(
                "Escala CFG. Controla a aderência ao prompt. "
                "Valores 7-9 são típicos para SD 1.5."
            ),
            de=(
                "CFG-Skala. Steuert die Prompt-Treue. "
                "Werte 7-9 sind typisch für SD 1.5."
            ),
            zh=(
                "无分类器引导（CFG）比例。控制对提示词的遵循程度。"
                "SD 1.5 的典型值为 7-9。"
            ),
        ),
        alias=MultilingualString(
            en="Guidance scale",
            es="Escala de guía",
            pt="Escala de orientação",
            de="Führungsskala",
            zh="引导比例",
        ),
    )  # type: ignore

    device: schema_field(
        enum_field(enum=DEVICE_ENUM),
        placeholder=DEVICE_PLACEHOLDER,
        description=MultilingualString(
            en=(
                "Hardware device for inference. GPU is strongly recommended. "
                "CPU inference is possible but very slow."
            ),
            es=(
                "Dispositivo de hardware para inferencia. Se recomienda GPU. "
                "La inferencia en CPU es posible pero muy lenta."
            ),
            pt=(
                "Dispositivo de hardware para inferência. GPU é fortemente "
                "recomendada. A inferência em CPU é possível, mas muito lenta."
            ),
            de=(
                "Hardware-Gerät für die Inferenz. GPU wird dringend empfohlen. "
                "CPU-Inferenz ist möglich, aber sehr langsam."
            ),
            zh=("推理硬件设备。强烈建议使用 GPU。CPU 推理可行但速度非常慢。"),
        ),
        alias=MultilingualString(
            en="Device",
            es="Dispositivo",
            pt="Dispositivo",
            de="Gerät",
            zh="设备",
        ),
    )  # type: ignore


class SD15HEDControlNetModel(HFDownloadableMixin, BaseControlNetModel):
    """HED soft-edge-conditioned ControlNet pipeline built on Stable Diffusion 1.5.

    Takes an input image and a text prompt. Soft edge maps are extracted from
    the image using the Holistically-nested Edge Detection (HED) detector from
    ``lllyasviel/Annotators``, then fed as spatial conditioning into the
    ``lllyasviel/sd-controlnet-hed`` ControlNet backbone together with the
    ``runwayml/stable-diffusion-v1-5`` diffusion pipeline. HED produces
    sketch-like contours that preserve structural outlines while allowing more
    creative variation than hard-edge Canny maps, making this model well-suited
    for artistic reinterpretation of existing images.

    Requires the ``controlnet_aux`` package (``pip install controlnet_aux``).

    References
    ----------
    - [1] Zhang & Agrawala, "Adding Conditional Control to Text-to-Image
           Diffusion Models", ICCV 2023. https://arxiv.org/abs/2302.05543
    - [2] https://huggingface.co/lllyasviel/sd-controlnet-hed
    """

    SCHEMA = SD15HEDControlNetSchema
    HF_REPOS = [
        ("runwayml/stable-diffusion-v1-5", "model"),
        ("lllyasviel/sd-controlnet-hed", "model"),
        ("lllyasviel/Annotators", "model"),
    ]
    DOWNLOAD_SIZE_BYTES = 60738022767
    COLOR: str = "#006064"
    DISPLAY_NAME: str = MultilingualString(
        en="SD 1.5 HED ControlNet",
        es="SD 1.5 ControlNet HED",
        pt="SD 1.5 ControlNet HED",
        de="SD 1.5 HED ControlNet",
        zh="SD 1.5 HED ControlNet",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Combines ControlNet HED (Holistically-nested Edge Detection) soft-edge "
            "conditioning with Stable Diffusion 1.5 for edge-guided image generation. "
            "HED produces soft, sketch-like edge maps that preserve structural "
            "outlines "
            "while allowing more creative variation than hard-edge methods like Canny. "
            "Ideal for artistic reinterpretation of existing images while preserving "
            "overall composition. Uses lllyasviel/sd-controlnet-hed "
            "(https://huggingface.co/lllyasviel/sd-controlnet-hed) and "
            "runwayml/stable-diffusion-v1-5 "
            "(https://huggingface.co/runwayml/stable-diffusion-v1-5). "
            "Requires controlnet_aux: pip install controlnet_aux."
        ),
        es=(
            "Combina el condicionamiento de borde suave HED (Detección de Bordes "
            "Holísticamente Anidada) de ControlNet con Stable Diffusion 1.5 para "
            "generación de imágenes guiada por bordes. HED produce mapas de bordes "
            "suaves tipo boceto que preservan contornos estructurales permitiendo "
            "más variación creativa que métodos de borde duro como Canny. Ideal para "
            "reinterpretación artística de imágenes. Utiliza "
            "lllyasviel/sd-controlnet-hed "
            "(https://huggingface.co/lllyasviel/sd-controlnet-hed) y "
            "runwayml/stable-diffusion-v1-5 "
            "(https://huggingface.co/runwayml/stable-diffusion-v1-5). "
            "Requiere controlnet_aux: pip install controlnet_aux."
        ),
        pt=(
            "Combina o condicionamento de borda suave HED (Detecção de Bordas "
            "Holisticamente Aninhada) do ControlNet com o Stable Diffusion 1.5 para "
            "geração de imagens guiada por bordas. HED produz mapas de bordas suaves "
            "estilo esboço que preservam contornos estruturais permitindo mais "
            "variação criativa que métodos de borda dura como Canny. Ideal para "
            "reinterpretação artística de imagens. Utiliza "
            "lllyasviel/sd-controlnet-hed "
            "(https://huggingface.co/lllyasviel/sd-controlnet-hed) e "
            "runwayml/stable-diffusion-v1-5 "
            "(https://huggingface.co/runwayml/stable-diffusion-v1-5). "
            "Requer controlnet_aux: pip install controlnet_aux."
        ),
        de=(
            "Kombiniert die weiche HED-Kantenkonditionierung (Holistically-nested Edge "
            "Detection) von ControlNet mit Stable Diffusion 1.5 für kantengeführte "
            "Bildgenerierung. HED erzeugt weiche, skizzenartige Kantenkarten, die "
            "strukturelle Umrisse bewahren und mehr kreative Variation als harte "
            "Kantenmethoden wie Canny ermöglichen. Ideal für künstlerische "
            "Neuinterpretation vorhandener Bilder. Verwendet "
            "lllyasviel/sd-controlnet-hed "
            "(https://huggingface.co/lllyasviel/sd-controlnet-hed) und "
            "runwayml/stable-diffusion-v1-5 "
            "(https://huggingface.co/runwayml/stable-diffusion-v1-5). "
            "Erfordert controlnet_aux: pip install controlnet_aux."
        ),
        zh=(
            "结合 ControlNet HED 软边缘条件与 Stable Diffusion 1.5，"
            "实现边缘引导的图像生成，适用于保留结构轮廓的艺术再创作。"
            "需要 controlnet_aux。"
        ),
    )

    def __init__(self, **kwargs: Any):
        """Initialize the SD 1.5 HED ControlNet model and pipeline.

        Loads the HED soft-edge detector from ``lllyasviel/Annotators``, then
        loads ``lllyasviel/sd-controlnet-hed`` as the ControlNet backbone and
        ``runwayml/stable-diffusion-v1-5`` as the base diffusion pipeline, both
        moved to the requested device. CPU offloading is enabled automatically
        via ``pipe.enable_model_cpu_offload()`` to reduce VRAM pressure.

        Requires the ``controlnet_aux`` package
        (``pip install controlnet_aux``).

        Parameters
        ----------
        **kwargs : Any
            Keyword arguments validated against :class:`SD15HEDControlNetSchema`.
            Recognised keys are:

            device : str
                Target hardware (e.g. ``"GPU 0"`` or ``"CPU"``).
            num_inference_steps : int
                Number of denoising steps during generation.
            controlnet_conditioning_scale : float
                Strength of the HED soft-edge conditioning signal (0.0-2.0).
            guidance_scale : float
                Classifier-Free Guidance scale controlling prompt adherence.

        Raises
        ------
        RuntimeError
            If ``controlnet_aux`` is not installed.
        """
        try:
            from controlnet_aux import HEDdetector
        except ImportError as e:
            raise RuntimeError("controlnet_aux is not installed. ") from e

        import torch
        from diffusers import ControlNetModel, StableDiffusionControlNetPipeline

        kwargs = self.validate_and_transform(kwargs)
        use_gpu = DEVICE_TO_IDX.get(kwargs.get("device")) >= 0
        self.device = (
            f"cuda:{DEVICE_TO_IDX.get(kwargs.get('device'))}" if use_gpu else "cpu"
        )

        self.hed_detector = HEDdetector.from_pretrained(
            self._local_or_repo("lllyasviel/Annotators")
        )

        controlnet = ControlNetModel.from_pretrained(
            self._local_or_repo("lllyasviel/sd-controlnet-hed"),
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

        hed_image = self.hed_detector(image)
        output = self.pipe(
            prompt=prompt,
            image=hed_image,
            num_inference_steps=self.num_inference_steps,
            guidance_scale=self.guidance_scale,
            controlnet_conditioning_scale=self.controlnet_conditioning_scale,
        )
        return output.images
