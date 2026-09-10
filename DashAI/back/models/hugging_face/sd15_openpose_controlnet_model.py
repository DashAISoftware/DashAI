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


class SD15OpenPoseControlNetSchema(BaseSchema):
    """Configuration schema for SD 1.5 OpenPose ControlNet image generation.

    Configures the denoising schedule (``num_inference_steps``), pose
    conditioning strength (``controlnet_conditioning_scale``), prompt adherence
    (``guidance_scale``), and hardware target (``device``) for
    ``SD15OpenPoseControlNetModel``.
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
            zh=("去噪步数。典型范围：20-30 步获得快速结果，40-50 步获得更高质量。"),
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
                "Weight of the ControlNet pose conditioning (range 0.0-2.0). "
                "At 1.0 the output closely follows the input pose. Lower values "
                "allow more creative freedom while preserving the general pose."
            ),
            es=(
                "Peso del condicionamiento de pose ControlNet (rango 0.0-2.0). "
                "En 1.0 la salida sigue de cerca la pose de entrada. Valores menores "
                "permiten más libertad creativa manteniendo la pose general."
            ),
            pt=(
                "Peso do condicionamento de pose do ControlNet (intervalo 0.0-2.0). "
                "Em 1.0 a saída segue de perto a pose de entrada. Valores menores "
                "permitem mais liberdade criativa mantendo a pose geral."
            ),
            de=(
                "Gewicht der ControlNet-Posenkonditionierung (Bereich 0.0-2.0). "
                "Bei 1.0 folgt die Ausgabe der Eingabepose eng. Niedrigere Werte "
                "erlauben mehr kreative Freiheit bei Beibehaltung der allgemeinen Pose."
            ),
            zh=(
                "ControlNet 姿态条件权重（范围 0.0-2.0）。"
                "1.0 时输出紧随输入姿态；较低值在保持整体姿态的同时允许更多创意自由度。"
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
                "无分类器引导（CFG）缩放。控制提示词的遵循程度。SD 1.5 的典型值为 7-9。"
            ),
        ),
        alias=MultilingualString(
            en="Guidance scale",
            es="Escala de guía",
            pt="Escala de orientação",
            de="Führungsskala",
            zh="引导缩放",
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
                "Dispositivo de hardware para inferencia. Se recomienda GPU. "
                "La inferencia en CPU es posible pero muy lenta."
            ),
            pt=(
                "Dispositivo de hardware para inferência. GPU é fortemente "
                "recomendada para modelos de difusão. A inferência em CPU é "
                "possível, mas muito lenta."
            ),
            de=(
                "Hardware-Gerät für die Inferenz. GPU wird für Diffusionsmodelle "
                "dringend empfohlen. CPU-Inferenz ist möglich, aber sehr langsam."
            ),
            zh=(
                "推理所用硬件设备。强烈建议使用 GPU 运行扩散模型。"
                "CPU 推理可行，但速度极慢。"
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


class SD15OpenPoseControlNetModel(HFDownloadableMixin, BaseControlNetModel):
    """OpenPose-conditioned ControlNet pipeline built on Stable Diffusion 1.5.

    Takes an input image and a text prompt. Human body keypoints and skeleton
    structures are detected from the image using ``OpenposeDetector`` from
    ``lllyasviel/Annotators``, then fed as spatial conditioning into the
    ``lllyasviel/sd-controlnet-openpose`` ControlNet backbone together with the
    ``runwayml/stable-diffusion-v1-5`` diffusion pipeline. This model is ideal
    for generating images with specific human poses or body positions while
    retaining full control over appearance via the text prompt.

    Requires the ``controlnet_aux`` package (``pip install controlnet_aux``).

    References
    ----------
    - [1] Zhang & Agrawala, "Adding Conditional Control to Text-to-Image
           Diffusion Models", ICCV 2023. https://arxiv.org/abs/2302.05543
    - [2] https://huggingface.co/lllyasviel/sd-controlnet-openpose
    """

    SCHEMA = SD15OpenPoseControlNetSchema
    HF_REPOS = [
        ("runwayml/stable-diffusion-v1-5", "model"),
        ("lllyasviel/sd-controlnet-openpose", "model"),
        ("lllyasviel/Annotators", "model"),
    ]
    DOWNLOAD_SIZE_BYTES = 60737694276
    COLOR: str = "#880e4f"
    DISPLAY_NAME: str = MultilingualString(
        en="SD 1.5 OpenPose ControlNet",
        es="SD 1.5 ControlNet OpenPose",
        pt="SD 1.5 ControlNet OpenPose",
        de="SD 1.5 OpenPose ControlNet",
        zh="SD 1.5 OpenPose ControlNet",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Combines ControlNet pose conditioning with Stable Diffusion 1.5 for "
            "pose-guided image generation. Takes an input image and a text prompt: "
            "human poses are detected using OpenposeDetector from controlnet_aux, "
            "then used as spatial conditions for image synthesis. Ideal for "
            "generating images with specific human poses or body positions. Uses "
            "lllyasviel/sd-controlnet-openpose "
            "(https://huggingface.co/lllyasviel/sd-controlnet-openpose) and "
            "runwayml/stable-diffusion-v1-5 "
            "(https://huggingface.co/runwayml/stable-diffusion-v1-5). "
            "Requires the controlnet_aux library: pip install controlnet_aux."
        ),
        es=(
            "Combina el condicionamiento de pose de ControlNet con Stable "
            "Diffusion 1.5 para generación de imágenes guiada por pose. "
            "Recibe una imagen y un prompt: las poses humanas se detectan "
            "usando OpenposeDetector de controlnet_aux y se usan como "
            "condiciones espaciales. Ideal para generar imágenes con poses "
            "humanas específicas. Utiliza lllyasviel/sd-controlnet-openpose "
            "(https://huggingface.co/lllyasviel/sd-controlnet-openpose) y "
            "runwayml/stable-diffusion-v1-5 "
            "(https://huggingface.co/runwayml/stable-diffusion-v1-5). "
            "Requiere la librería controlnet_aux: pip install controlnet_aux."
        ),
        pt=(
            "Combina o condicionamento de pose do ControlNet com o Stable "
            "Diffusion 1.5 para geração de imagens guiada por pose. Recebe uma "
            "imagem de entrada e um prompt: poses humanas são detectadas usando "
            "OpenposeDetector do controlnet_aux e usadas como condições espaciais "
            "para a síntese de imagens. "
            "Ideal para gerar imagens com poses humanas específicas. Utiliza "
            "lllyasviel/sd-controlnet-openpose "
            "(https://huggingface.co/lllyasviel/sd-controlnet-openpose) e "
            "runwayml/stable-diffusion-v1-5 "
            "(https://huggingface.co/runwayml/stable-diffusion-v1-5). "
            "Requer a biblioteca controlnet_aux: pip install controlnet_aux."
        ),
        de=(
            "Kombiniert die ControlNet-Posenkonditionierung mit Stable Diffusion 1.5 "
            "für posengeführte Bildgenerierung. Nimmt ein Eingabebild und einen "
            "Textprompt: Menschliche Posen werden mit OpenposeDetector aus "
            "controlnet_aux erkannt und als räumliche Bedingungen für die "
            "Bildsynthese verwendet. Ideal für die Generierung von Bildern mit "
            "spezifischen menschlichen Körperposen. Verwendet "
            "lllyasviel/sd-controlnet-openpose "
            "(https://huggingface.co/lllyasviel/sd-controlnet-openpose) und "
            "runwayml/stable-diffusion-v1-5 "
            "(https://huggingface.co/runwayml/stable-diffusion-v1-5). "
            "Erfordert die controlnet_aux-Bibliothek: pip install controlnet_aux."
        ),
        zh=(
            "结合 ControlNet 姿态条件与 Stable Diffusion 1.5，"
            "实现姿态引导的图像生成，适用于特定人体姿态的图像合成。"
            "需要 controlnet_aux。"
        ),
    )

    def __init__(self, **kwargs: Any):
        """Initialize the SD 1.5 OpenPose ControlNet model and pipeline.

        Loads the OpenPose detector from ``lllyasviel/Annotators``, then loads
        ``lllyasviel/sd-controlnet-openpose`` as the ControlNet backbone and
        ``runwayml/stable-diffusion-v1-5`` as the base diffusion pipeline, both
        moved to the requested device. CPU offloading is enabled automatically
        via ``pipe.enable_model_cpu_offload()`` to reduce VRAM pressure.

        Requires the ``controlnet_aux`` package
        (``pip install controlnet_aux``).

        Parameters
        ----------
        **kwargs : Any
            Keyword arguments validated against
            :class:`SD15OpenPoseControlNetSchema`. Recognised keys are:

            device : str
                Target hardware (e.g. ``"GPU 0"`` or ``"CPU"``).
            num_inference_steps : int
                Number of denoising steps during generation.
            controlnet_conditioning_scale : float
                Strength of the pose conditioning signal (0.0-2.0).
            guidance_scale : float
                Classifier-Free Guidance scale controlling prompt adherence.

        Raises
        ------
        RuntimeError
            If ``controlnet_aux`` is not installed.
        """
        try:
            from controlnet_aux import OpenposeDetector
        except ImportError as e:
            raise RuntimeError("controlnet_aux is not installed. ") from e

        import torch
        from diffusers import ControlNetModel, StableDiffusionControlNetPipeline

        kwargs = self.validate_and_transform(kwargs)
        use_gpu = DEVICE_TO_IDX.get(kwargs.get("device")) >= 0
        self.device = (
            f"cuda:{DEVICE_TO_IDX.get(kwargs.get('device'))}" if use_gpu else "cpu"
        )

        self.pose_detector = OpenposeDetector.from_pretrained(
            self._local_or_repo("lllyasviel/Annotators")
        )

        controlnet = ControlNetModel.from_pretrained(
            self._local_or_repo("lllyasviel/sd-controlnet-openpose"),
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

        pose_image = self.pose_detector(image)
        output = self.pipe(
            prompt=prompt,
            image=pose_image,
            num_inference_steps=self.num_inference_steps,
            guidance_scale=self.guidance_scale,
            controlnet_conditioning_scale=self.controlnet_conditioning_scale,
        )
        return output.images
