from typing import Any, List, Optional

from DashAI.back.core.schema_fields import (
    enum_field,
    int_field,
    schema_field,
    string_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.downloadable import (
    HFPretrainedDownloadMixin,
)
from DashAI.back.models.text_to_image_generation_model import (
    TextToImageGenerationTaskModel,
)
from DashAI.back.models.utils import DEVICE_ENUM, DEVICE_PLACEHOLDER, DEVICE_TO_IDX


class SDXLTurboSchema(BaseSchema):
    """Configuration schema for SDXL Turbo text-to-image generation.

    Configures the prompt conditioning (``negative_prompt``), number of
    denoising steps (``num_inference_steps``; 1-4 is optimal for this
    distilled model), output dimensions (``width``, ``height``),
    reproducibility (``seed``), hardware target (``device``), and batch size
    (``num_images_per_prompt``) for ``SDXLTurboModel``.

    Note: ``guidance_scale`` is not exposed because SDXL Turbo always runs
    with ``guidance_scale=0`` due to its Adversarial Diffusion Distillation
    (ADD) training.
    """

    negative_prompt: Optional[
        schema_field(
            string_field(),
            placeholder="",
            description=MultilingualString(
                en=(
                    "Text describing what to exclude from the generated image. "
                    "Note: SDXL Turbo uses distillation training and "
                    "guidance_scale=0, so negative prompts have minimal effect. "
                    "Leave empty for best results."
                ),
                es=(
                    "Texto que describe qué excluir de la imagen generada. "
                    "Nota: SDXL Turbo usa entrenamiento por destilación y "
                    "guidance_scale=0, por lo que los prompts negativos tienen "
                    "efecto mínimo. "
                    "Dejar vacío para mejores resultados."
                ),
                pt=(
                    "Texto descrevendo o que excluir da imagem gerada. "
                    "Nota: SDXL Turbo usa treinamento por destilação e "
                    "guidance_scale=0, portanto os prompts negativos têm "
                    "efeito mínimo. "
                    "Deixe vazio para melhores resultados."
                ),
                de=(
                    "Text, der beschreibt, was aus dem generierten Bild ausgeschlossen "
                    "werden soll. Hinweis: SDXL Turbo verwendet Destillationstraining "
                    "und guidance_scale=0, daher haben negative Prompts minimale "
                    "Wirkung. "
                    "Leer lassen für beste Ergebnisse."
                ),
                zh=(
                    "描述要从生成图像中排除的内容的文本。"
                    "注意：SDXL Turbo 使用蒸馏训练且 guidance_scale=0，"
                    "因此负向提示效果极小。"
                    "留空以获得最佳结果。"
                ),
            ),
            alias=MultilingualString(
                en="Negative prompt",
                es="Prompt negativo",
                pt="Prompt negativo",
                de="Negativer Prompt",
                zh="负向提示",
            ),
        )  # type: ignore
    ]

    num_inference_steps: schema_field(
        int_field(ge=1, le=10),
        placeholder=1,
        description=MultilingualString(
            en=(
                "Number of denoising steps. SDXL Turbo is a distilled model that "
                "generates high quality images in just 1-4 steps. Using 1 step is "
                "fastest; 2-4 steps improve quality slightly. Values above 4 provide "
                "diminishing returns for this model."
            ),
            es=(
                "Número de pasos de eliminación de ruido. SDXL Turbo es un modelo "
                "destilado que genera imágenes de alta calidad en solo 1-4 pasos. "
                "Usar 1 paso es lo más rápido; 2-4 pasos mejoran la calidad "
                "ligeramente. Valores superiores a 4 tienen rendimientos "
                "decrecientes para este modelo."
            ),
            pt=(
                "Número de etapas de inferência. SDXL Turbo é um modelo destilado "
                "que gera imagens de alta qualidade em apenas 1-4 etapas. Usar "
                "1 etapa é o mais rápido; 2-4 etapas melhoram ligeiramente a "
                "qualidade. Valores acima de 4 têm retornos decrescentes para "
                "este modelo."
            ),
            de=(
                "Anzahl der Inferenzschritte. SDXL Turbo ist ein destilliertes Modell, "
                "das hochwertige Bilder in nur 1-4 Schritten generiert. 1 Schritt ist "
                "am schnellsten; 2-4 Schritte verbessern die Qualität leicht. "
                "Werte über 4 bieten für dieses Modell abnehmende Erträge."
            ),
            zh=(
                "去噪步骤数。SDXL Turbo 是一个蒸馏模型，仅需 1-4 步即可生成高质量图像。"
                "1 步最快；2-4 步可略微提升质量。超过 4 步对此模型收益递减。"
            ),
        ),
        alias=MultilingualString(
            en="Num inference steps",
            es="Número de pasos de inferencia",
            pt="Número de etapas de inferência",
            de="Anzahl Inferenzschritte",
            zh="推理步骤数",
        ),
    )  # type: ignore

    device: schema_field(
        enum_field(enum=DEVICE_ENUM),
        placeholder=DEVICE_PLACEHOLDER,
        description=MultilingualString(
            en=(
                "Hardware device for inference. SDXL Turbo is fast enough that CPU "
                "inference is feasible (30-60 seconds per image). GPU is still "
                "recommended for real time or batch generation."
            ),
            es=(
                "Dispositivo de hardware para inferencia. SDXL Turbo es lo "
                "suficientemente rápido como para que la inferencia en CPU sea "
                "factible (30-60 segundos por imagen). La GPU sigue siendo "
                "recomendada para generación en tiempo real o por lotes."
            ),
            pt=(
                "Dispositivo de hardware para inferência. SDXL Turbo é rápido o "
                "suficiente para que a inferência em CPU seja viável (30-60 segundos "
                "por imagem). GPU ainda é recomendada para geração em tempo real "
                "ou em lote."
            ),
            de=(
                "Hardware-Gerät für die Inferenz. SDXL Turbo ist schnell genug, "
                "dass CPU-Inferenz machbar ist (30-60 Sekunden pro Bild). GPU wird "
                "für Echtzeit- oder Stapelgenerierung dennoch empfohlen."
            ),
            zh=(
                "推理硬件设备。SDXL Turbo 足够快，CPU 推理可行（每张图约 30-60 秒）。"
                "实时或批量生成仍推荐使用 GPU。"
            ),
        ),
        alias=MultilingualString(
            en="Device", es="Dispositivo", pt="Dispositivo", de="Gerät", zh="设备"
        ),
    )  # type: ignore

    seed: schema_field(
        int_field(),
        placeholder=-1,
        description=MultilingualString(
            en=(
                "Random seed for reproducible generation. A fixed positive integer "
                "will always produce the same image for identical settings. "
                "Use a negative value (e.g. -1) for a random seed on each run."
            ),
            es=(
                "Semilla aleatoria para generación reproducible. Un entero positivo "
                "fijo siempre producirá la misma imagen con configuraciones idénticas. "
                "Use un valor negativo (ej. -1) para una semilla aleatoria en "
                "cada ejecución."
            ),
            pt=(
                "Semente aleatória para geração reproduzível. Um inteiro positivo "
                "fixo sempre produzirá a mesma imagem com configurações idênticas. "
                "Use um valor negativo (ex.: -1) para uma semente aleatória a "
                "cada execução."
            ),
            de=(
                "Zufalls-Seed für reproduzierbare Generierung. Ein fester positiver "
                "Integer erzeugt stets dasselbe Bild bei identischen Einstellungen. "
                "Verwenden Sie einen negativen Wert (z.B. -1) für einen zufälligen "
                "Seed bei jedem Durchlauf."
            ),
            zh=(
                "用于可复现生成的随机种子。固定正整数在相同设置下始终产生相同图像。"
                "使用负值（如 -1）可在每次运行时随机取种。"
            ),
        ),
        alias=MultilingualString(
            en="Seed", es="Semilla", pt="Semente", de="Seed", zh="随机种子"
        ),
    )  # type: ignore

    width: schema_field(
        int_field(ge=64, le=2048, multiple_of=8),
        placeholder=512,
        description=MultilingualString(
            en=(
                "Width of the output image in pixels. Must be a multiple of 8. "
                "SDXL Turbo's optimal resolution is 512x512 px. Larger resolutions "
                "may reduce quality as the model was trained at 512 px."
            ),
            es=(
                "Ancho de la imagen de salida en píxeles. Debe ser múltiplo de 8. "
                "La resolución óptima de SDXL Turbo es 512x512 px. Resoluciones más "
                "grandes pueden reducir la calidad ya que el modelo fue entrenado "
                "a 512 px."
            ),
            pt=(
                "Largura da imagem de saída em pixels. Deve ser múltiplo de 8. "
                "A resolução ideal do SDXL Turbo é 512x512 px. Resoluções maiores "
                "podem reduzir a qualidade, pois o modelo foi treinado a 512 px."
            ),
            de=(
                "Breite des Ausgabebildes in Pixeln. Muss ein Vielfaches von 8 sein. "
                "Die optimale Auflösung von SDXL Turbo ist 512x512 px. Größere "
                "Auflösungen können die Qualität verringern, da das Modell bei "
                "512 px trainiert wurde."
            ),
            zh=(
                "输出图像宽度（像素），须为 8 的倍数。"
                "SDXL Turbo 最佳分辨率为 512x512 px，更高分辨率可能降低质量。"
            ),
        ),
        alias=MultilingualString(
            en="Width", es="Ancho", pt="Largura", de="Breite", zh="宽度"
        ),
    )  # type: ignore

    height: schema_field(
        int_field(ge=64, le=2048, multiple_of=8),
        placeholder=512,
        description=MultilingualString(
            en=(
                "Height of the output image in pixels. Must be a multiple of 8. "
                "SDXL Turbo's optimal resolution is 512x512 px."
            ),
            es=(
                "Altura de la imagen de salida en píxeles. Debe ser múltiplo de 8. "
                "La resolución óptima de SDXL Turbo es 512x512 px."
            ),
            pt=(
                "Altura da imagem de saída em pixels. Deve ser múltiplo de 8. "
                "A resolução ideal do SDXL Turbo é 512x512 px."
            ),
            de=(
                "Höhe des Ausgabebildes in Pixeln. Muss ein Vielfaches von 8 sein. "
                "Die optimale Auflösung von SDXL Turbo ist 512x512 px."
            ),
            zh=(
                "输出图像高度（像素），须为 8 的倍数。"
                "SDXL Turbo 最佳分辨率为 512x512 px。"
            ),
        ),
        alias=MultilingualString(
            en="Height", es="Altura", pt="Altura", de="Höhe", zh="高度"
        ),
    )  # type: ignore

    num_images_per_prompt: schema_field(
        int_field(ge=1),
        placeholder=1,
        description=MultilingualString(
            en=(
                "How many images to generate from a single prompt in one batch. "
                "Since SDXL Turbo is fast, generating multiple images per prompt "
                "is very efficient."
            ),
            es=(
                "Cuántas imágenes generar desde un solo prompt en un lote. "
                "Como SDXL Turbo es rápido, generar múltiples imágenes por prompt "
                "es muy eficiente."
            ),
            pt=(
                "Quantas imagens gerar a partir de um único prompt em um lote. "
                "Como o SDXL Turbo é rápido, gerar múltiplas imagens por prompt "
                "é muito eficiente."
            ),
            de=(
                "Wie viele Bilder aus einem einzelnen Prompt in einem Stapel generiert "
                "werden sollen. Da SDXL Turbo schnell ist, ist die Generierung mehrerer"
                "Bilder pro Prompt sehr effizient."
            ),
            zh=(
                "单次批量从一个提示词生成的图像数量。"
                "由于 SDXL Turbo 速度快，每个提示词生成多张图像非常高效。"
            ),
        ),
        alias=MultilingualString(
            en="Num images per prompt",
            es="Número de imágenes por prompt",
            pt="Número de imagens por prompt",
            de="Bilder pro Prompt",
            zh="每提示词图像数",
        ),
    )  # type: ignore


class SDXLTurboModel(HFPretrainedDownloadMixin, TextToImageGenerationTaskModel):
    """Distilled SDXL model for near real time text-to-image generation.

    Wraps ``stabilityai/sdxl-turbo``, a version of Stable Diffusion XL
    trained with Adversarial Diffusion Distillation (ADD) by Stability AI.
    ADD transfers knowledge from a large teacher model into a student that
    can produce photorealistic 512 px images in as few as one denoising step,
    up to 30x faster than standard SDXL.

    Because ADD bakes guidance directly into the model weights, classifier free
    guidance is disabled (``guidance_scale=0`` is enforced internally) and
    negative prompts have minimal effect.

    Ideal for interactive and real time applications where latency matters
    more than absolute peak quality.

    References
    ----------
    - [1] Sauer et al., "Adversarial Diffusion Distillation", 2023.
           https://arxiv.org/abs/2311.17042
    - [2] https://huggingface.co/stabilityai/sdxl-turbo
    """

    SCHEMA = SDXLTurboSchema
    MODEL_NAME: str = "stabilityai/sdxl-turbo"
    # SDXL-Turbo diffusers pipeline is ~7 GB.
    DOWNLOAD_SIZE_BYTES: int = 41631892171
    COLOR: str = "#b71c1c"
    DISPLAY_NAME: str = MultilingualString(
        en="SDXL Turbo",
        es="SDXL Turbo",
        pt="SDXL Turbo",
        de="SDXL Turbo",
        zh="SDXL Turbo",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "SDXL Turbo is a distilled version of Stable Diffusion XL by Stability AI "
            "that generates high quality images in a single denoising step using "
            "Adversarial Diffusion Distillation (ADD). It produces photorealistic "
            "images at 512x512 px resolution up to 30x faster than standard SDXL. "
            "Ideal for interactive and real time applications. Note: does not use "
            "classifier free guidance (guidance_scale=0 internally). Model available "
            "at https://huggingface.co/stabilityai/sdxl-turbo."
        ),
        es=(
            "SDXL Turbo es una versión destilada de Stable Diffusion XL por "
            "Stability AI que genera imágenes de alta calidad en un solo paso "
            "de eliminación de ruido "
            "usando Destilación de Difusión Adversarial (ADD). Produce imágenes "
            "fotorrealistas a 512x512 px hasta 30x más rápido que el SDXL estándar. "
            "Ideal para aplicaciones interactivas y en tiempo real. Nota: no usa guía "
            "libre de clasificador (guidance_scale=0 internamente). Modelo "
            "disponible en "
            "https://huggingface.co/stabilityai/sdxl-turbo."
        ),
        pt=(
            "SDXL Turbo é uma versão destilada do Stable Diffusion XL pela "
            "Stability AI que gera imagens de alta qualidade em uma única etapa "
            "de remoção de ruído "
            "usando Destilação por Difusão Adversarial (ADD). Produz imagens "
            "fotorrealistas a 512x512 px até 30x mais rápido que o SDXL padrão. "
            "Ideal para aplicações interativas e em tempo real. Nota: não usa "
            "orientação livre de classificador (guidance_scale=0 internamente). "
            "Modelo disponível em "
            "https://huggingface.co/stabilityai/sdxl-turbo."
        ),
        de=(
            "SDXL Turbo ist eine destillierte Version von Stable Diffusion XL von "
            "Stability AI, die hochwertige Bilder in einem einzigen "
            "Entrauschungsschritt "
            "mithilfe von Adversarial Diffusion Distillation (ADD) generiert. Erzeugt "
            "fotorealistische Bilder bei 512x512 px bis zu 30x schneller als "
            "Standard-SDXL. "
            "Ideal für interaktive und Echtzeit-Anwendungen. Hinweis: verwendet keine "
            "classifier-free guidance (guidance_scale=0 intern). Modell verfügbar unter"
            "https://huggingface.co/stabilityai/sdxl-turbo."
        ),
        zh=(
            "SDXL Turbo 是 Stability AI 的 Stable Diffusion XL 蒸馏版本，"
            "利用对抗扩散蒸馏（ADD）在单步降噪中生成高质量图像，比标准 SDXL 快 30 倍。"
        ),
    )

    def __init__(self, **kwargs):
        """Download and initialise the SDXL Turbo pipeline.

        Downloads ``stabilityai/sdxl-turbo`` from HuggingFace Hub via
        ``StableDiffusionXLPipeline.from_pretrained`` and moves the pipeline
        to the requested device.  When a GPU is available, the ``fp16``
        variant is loaded to halve memory usage; CPU inference uses
        ``float32``.

        Parameters
        ----------
        **kwargs : dict
            negative_prompt : str or None, optional
                Text describing content to suppress.  Has minimal effect
                because SDXL Turbo uses ADD training with ``guidance_scale=0``.
            num_inference_steps : int, optional
                Number of denoising steps (1-4 recommended).  Defaults to
                ``1``.  Values above 4 provide diminishing returns.
            device : str
                Target device string from ``DEVICE_ENUM``.  Mapped to a
                ``cuda:<index>`` string or ``"cpu"`` via ``DEVICE_TO_IDX``.
            seed : int
                Fixed seed for reproducible outputs.  Values ≤ 0 disable
                seeding.
            width : int
                Output image width in pixels (multiple of 8).  Optimal is
                512 px.
            height : int
                Output image height in pixels (multiple of 8).  Optimal is
                512 px.
            num_images_per_prompt : int
                Number of images to generate per prompt call.
        """
        import torch
        from diffusers import StableDiffusionXLPipeline

        kwargs = self.validate_and_transform(kwargs)
        use_gpu = DEVICE_TO_IDX.get(kwargs.get("device")) >= 0
        self.device = (
            f"cuda:{DEVICE_TO_IDX.get(kwargs.get('device'))}" if use_gpu else "cpu"
        )

        self.model = StableDiffusionXLPipeline.from_pretrained(
            self._pretrained_source(None),
            torch_dtype=torch.float16 if use_gpu else torch.float32,
            variant="fp16" if use_gpu else None,
        ).to(self.device)

        self.negative_prompt = kwargs.get("negative_prompt")
        self.num_inference_steps = kwargs.get("num_inference_steps", 1)
        self.seed = kwargs.get("seed")
        self.width = kwargs.get("width")
        self.height = kwargs.get("height")
        self.num_images_per_prompt = kwargs.get("num_images_per_prompt")

    def generate(self, input: str) -> List[Any]:
        """Generate images from a text prompt using single step distillation.

        Parameters
        ----------
        input : str
            Text prompt to generate an image from.

        Returns
        -------
        List[Any]
            Generated output images in a list.
        """
        import torch

        generator = None
        if self.seed is not None and self.seed > 0:
            generator = torch.Generator(device=self.device).manual_seed(self.seed)

        output = self.model(
            prompt=input,
            negative_prompt=self.negative_prompt,
            num_inference_steps=self.num_inference_steps,
            guidance_scale=0.0,
            width=self.width,
            height=self.height,
            generator=generator,
            num_images_per_prompt=self.num_images_per_prompt,
        )
        return output.images
