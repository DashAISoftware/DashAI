from typing import Any, List, Optional

from DashAI.back.core.schema_fields import (
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
)
from DashAI.back.models.text_to_image_generation_model import (
    TextToImageGenerationTaskModel,
)
from DashAI.back.models.utils import DEVICE_ENUM, DEVICE_PLACEHOLDER, DEVICE_TO_IDX


class StableDiffusionXLSchema(BaseSchema):
    """Configuration schema for Stable Diffusion XL text-to-image generation.

    Configures the checkpoint variant (``model_name``), prompt conditioning
    (``negative_prompt``), denoising schedule (``num_inference_steps``),
    classifier-free guidance strength (``guidance_scale``), output dimensions
    (``width``, ``height``), reproducibility (``seed``), hardware target
    (``device``), and batch size (``num_images_per_prompt``) for
    ``StableDiffusionXLModel``.
    """

    negative_prompt: Optional[
        schema_field(
            string_field(),
            placeholder="",
            description=MultilingualString(
                en=(
                    "Text describing what to exclude from the generated image. "
                    "Common values: 'blurry, low quality, distorted, watermark'. "
                    "Leave empty to skip negative conditioning."
                ),
                es=(
                    "Texto que describe qué excluir de la imagen generada. "
                    "Valores comunes: 'borroso, baja calidad, distorsionado, "
                    "marca de agua'. "
                    "Dejar vacío para omitir el condicionamiento negativo."
                ),
                pt=(
                    "Texto descrevendo o que excluir da imagem gerada. "
                    "Valores comuns: 'borrado, baixa qualidade, distorcido, "
                    "marca d'água'. "
                    "Deixe vazio para omitir o condicionamento negativo."
                ),
                de=(
                    "Text, der beschreibt, was aus dem generierten Bild ausgeschlossen "
                    "werden soll. Häufige Werte: 'unscharf, geringe Qualität, verzerrt,"
                    "Wasserzeichen'. Leer lassen, um die negative Konditionierung zu "
                    "überspringen."
                ),
                zh=(
                    "描述要从生成图像中排除内容的文本。"
                    "常用值：'模糊、低质量、失真、水印'。"
                    "留空以跳过负面条件引导。"
                ),
            ),
            alias=MultilingualString(
                en="Negative prompt",
                es="Prompt negativo",
                pt="Prompt negativo",
                de="Negativer Prompt",
                zh="负面提示词",
            ),
        )  # type: ignore
    ]

    num_inference_steps: schema_field(
        int_field(ge=1),
        placeholder=25,
        description=MultilingualString(
            en=(
                "Number of denoising steps to run. More steps refine the image but "
                "increase generation time. Typical range: 20-30 for fast results, "
                "40-50 for higher quality. SDXL achieves good results with 25-40 steps."
            ),
            es=(
                "Número de pasos de eliminación de ruido a ejecutar. Más pasos refinan "
                "la imagen pero aumentan el tiempo de generación. Rango típico: 20-30 "
                "para resultados rápidos, 40-50 para mayor calidad. SDXL logra buenos "
                "resultados con 25-40 pasos."
            ),
            pt=(
                "Número de passos de remoção de ruído a executar. Mais passos refinam "
                "a imagem mas aumentam o tempo de geração. Intervalo típico: 20-30 "
                "para resultados rápidos, 40-50 para maior qualidade. SDXL alcança "
                "bons resultados com 25-40 passos."
            ),
            de=(
                "Anzahl der auszuführenden Entrauschungsschritte. Mehr Schritte "
                "refinieren "
                "das Bild, erhöhen aber die Generierungszeit. Typischer Bereich: 20-30 "
                "für schnelle Ergebnisse, 40-50 für höhere Qualität. SDXL erzielt "
                "gute Ergebnisse mit 25-40 Schritten."
            ),
            zh=(
                "去噪步数。步数越多图像越精细，但生成时间越长。"
                "典型范围：20-30 步快速生成，40-50 步更高质量。"
                "SDXL 在 25-40 步时效果良好。"
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

    guidance_scale: schema_field(
        float_field(ge=0.0),
        placeholder=7.0,
        description=MultilingualString(
            en=(
                "Classifier-Free Guidance (CFG) scale. Controls how strictly the "
                "image follows the text prompt. Low values (1-4) allow creative "
                "freedom; medium values (5-9) balance quality and adherence; "
                "high values (10+) enforce the prompt but may produce artifacts. "
                "SDXL works well with values between 5-9."
            ),
            es=(
                "Escala de Classifier-Free Guidance (CFG). Controla qué tan "
                "estrictamente la imagen sigue el prompt. Valores bajos (1-4) permiten "
                "libertad creativa; valores medios (5-9) equilibran calidad y "
                "adherencia; valores altos (10+) refuerzan el prompt pero pueden "
                "producir artefactos. "
                "SDXL funciona bien con valores entre 5-9."
            ),
            pt=(
                "Escala de Classifier-Free Guidance (CFG). Controla quão "
                "estritamente a imagem segue o prompt. Valores baixos (1-4) permitem "
                "liberdade criativa; valores médios (5-9) equilibram qualidade e "
                "aderência; valores altos (10+) reforçam o prompt mas podem "
                "produzir artefatos. "
                "SDXL funciona bem com valores entre 5-9."
            ),
            de=(
                "Classifier-Free Guidance (CFG)-Skala. Steuert, wie streng das Bild "
                "dem Prompt folgt. Niedrige Werte (1-4) erlauben kreative Freiheit; "
                "mittlere Werte (5-9) balancieren Qualität und Treue; hohe Werte (10+) "
                "erzwingen den Prompt, können aber Artefakte erzeugen. "
                "SDXL funktioniert gut mit Werten zwischen 5-9."
            ),
            zh=(
                "无分类器引导（CFG）比例。控制图像对文本提示的遵循程度。"
                "低值（1-4）允许创意自由；中值（5-9）平衡质量与忠实度；"
                "高值（10+）强制执行提示但可能产生伪影。SDXL 在 5-9 之间效果最佳。"
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
                "Hardware device for inference. Select a GPU option for hardware "
                "acceleration, strongly recommended for SDXL. CPU inference is very "
                "slow for this large model; expect 10-30 minutes per image on CPU."
            ),
            es=(
                "Dispositivo de hardware para la inferencia. Seleccione GPU para "
                "aceleración por hardware, muy recomendado para SDXL. La inferencia "
                "en CPU es muy lenta para este modelo grande; espere 10-30 minutos "
                "por imagen en CPU."
            ),
            pt=(
                "Dispositivo de hardware para inferência. Selecione GPU para "
                "aceleração por hardware, altamente recomendado para SDXL. A "
                "inferência em CPU é muito lenta para este modelo grande; espere "
                "10-30 minutos por imagem em CPU."
            ),
            de=(
                "Hardware-Gerät für die Inferenz. Wählen Sie GPU für "
                "Hardwarebeschleunigung, "
                "für SDXL dringend empfohlen. CPU-Inferenz ist für dieses große Modell "
                "sehr langsam; rechnen Sie mit 10-30 Minuten pro Bild auf CPU."
            ),
            zh=(
                "推理硬件设备。强烈建议 SDXL 使用 GPU 加速。"
                "CPU 推理对此大模型非常缓慢，每张图像预计需要 10-30 分钟。"
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
                "Use um valor negativo (ex. -1) para uma semente aleatória em "
                "cada execução."
            ),
            de=(
                "Zufalls-Seed für reproduzierbare Generierung. Ein fester positiver "
                "Integer erzeugt stets dasselbe Bild bei identischen Einstellungen. "
                "Verwenden Sie einen negativen Wert (z.B. -1) für einen zufälligen "
                "Seed bei jedem Durchlauf."
            ),
            zh=(
                "用于可复现生成的随机种子。固定正整数在相同设置下始终生成相同图像。"
                "使用负值（如 -1）表示每次运行使用随机种子。"
            ),
        ),
        alias=MultilingualString(
            en="Seed", es="Semilla", pt="Semente", de="Seed", zh="随机种子"
        ),
    )  # type: ignore

    width: schema_field(
        int_field(ge=64, le=2048, multiple_of=8),
        placeholder=1024,
        description=MultilingualString(
            en=(
                "Width of the output image in pixels. Must be a multiple of 8. "
                "SDXL's native resolution is 1024x1024 px. Using non-native "
                "resolutions may reduce quality."
            ),
            es=(
                "Ancho de la imagen de salida en píxeles. Debe ser múltiplo de 8. "
                "La resolución nativa de SDXL es 1024x1024 px. Usar resoluciones no "
                "nativas puede reducir la calidad."
            ),
            pt=(
                "Largura da imagem de saída em pixels. Deve ser múltiplo de 8. "
                "A resolução nativa do SDXL é 1024x1024 px. Usar resoluções não "
                "nativas pode reduzir a qualidade."
            ),
            de=(
                "Breite des Ausgabebildes in Pixeln. Muss ein Vielfaches von 8 sein. "
                "Die native Auflösung von SDXL ist 1024x1024 px. Die Verwendung "
                "nicht-nativer Auflösungen kann die Qualität verringern."
            ),
            zh=(
                "输出图像的宽度（像素），必须是 8 的倍数。"
                "SDXL 原生分辨率为 1024x1024px，使用非原生分辨率可能降低质量。"
            ),
        ),
        alias=MultilingualString(
            en="Width", es="Ancho", pt="Largura", de="Breite", zh="宽度"
        ),
    )  # type: ignore

    height: schema_field(
        int_field(ge=64, le=2048, multiple_of=8),
        placeholder=1024,
        description=MultilingualString(
            en=(
                "Height of the output image in pixels. Must be a multiple of 8. "
                "SDXL's native resolution is 1024x1024 px."
            ),
            es=(
                "Altura de la imagen de salida en píxeles. Debe ser múltiplo de 8. "
                "La resolución nativa de SDXL es 1024x1024 px."
            ),
            pt=(
                "Altura da imagem de saída em pixels. Deve ser múltiplo de 8. "
                "A resolução nativa do SDXL é 1024x1024 px."
            ),
            de=(
                "Höhe des Ausgabebildes in Pixeln. Muss ein Vielfaches von 8 sein. "
                "Die native Auflösung von SDXL ist 1024x1024 px."
            ),
            zh=(
                "输出图像的高度（像素），必须是 8 的倍数。"
                "SDXL 原生分辨率为 1024x1024px。"
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
                "Increasing this value is more efficient than running multiple "
                "sessions, but requires proportionally more GPU memory."
            ),
            es=(
                "Cuántas imágenes generar desde un solo prompt en un lote. "
                "Aumentar este valor es más eficiente que ejecutar varias sesiones, "
                "pero requiere proporcionalmente más memoria GPU."
            ),
            pt=(
                "Quantas imagens gerar a partir de um único prompt em um lote. "
                "Aumentar este valor é mais eficiente do que executar várias sessões, "
                "mas requer proporcionalmente mais memória GPU."
            ),
            de=(
                "Wie viele Bilder aus einem einzelnen Prompt in einem Stapel generiert "
                "werden sollen. Diesen Wert zu erhöhen ist effizienter als mehrere "
                "Sitzungen zu starten, erfordert aber proportional mehr GPU-Speicher."
            ),
            zh=(
                "每个提示词在单批次中生成的图像数量。"
                "增大此值比多次运行更高效，但需要等比例更多的 GPU 显存。"
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


class StableDiffusionXLGenerationModel(
    HFPretrainedDownloadMixin, TextToImageGenerationTaskModel
):
    """Latent diffusion model for high-resolution 1024 px text-to-image generation.

    Wraps Stable Diffusion XL (SDXL) checkpoints. SDXL scales the standard
    SD architecture with a larger U-Net backbone and a two-text-encoder
    conditioning stack (OpenCLIP-ViT/G + CLIP-ViT/L), enabling significantly
    better prompt following and photorealism at 1024 x 1024 px compared to
    SD 1.x/2.x.

    Two checkpoints are supported: the official
    ``stabilityai/stable-diffusion-xl-base-1.0`` and
    ``SG161222/RealVisXL_V4.0``, a popular community fine-tune optimised for
    realistic portraits and photography.

    References
    ----------
    - [1] Podell et al., "SDXL: Improving Latent Diffusion Models for
           High-Resolution Image Synthesis", 2023. https://arxiv.org/abs/2307.01952
    - [2] https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
    """

    SCHEMA = StableDiffusionXLSchema
    MODEL_NAME: str = ""
    COLOR: str = "#0d47a1"
    DISPLAY_NAME: str = MultilingualString(
        en="Stable Diffusion XL",
        es="Stable Diffusion XL",
        pt="Stable Diffusion XL",
        de="Stable Diffusion XL",
        zh="Stable Diffusion XL",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Stable Diffusion XL (SDXL) is a latent diffusion model by Stability AI "
            "for high-resolution text-to-image generation at 1024x1024 px. It features "
            "a larger U-Net backbone and a second text encoder (OpenCLIP ViT-bigG) "
            "that significantly improves image quality, text rendering, and "
            "compositional accuracy compared to earlier SD versions. Also includes "
            "RealVisXL V4.0, a community fine-tune optimized for photorealistic "
            "portraits and photography. Base model at "
            "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0."
        ),
        es=(
            "Stable Diffusion XL (SDXL) es un modelo de difusión latente de "
            "Stability AI para generación de imágenes de alta resolución a "
            "1024x1024 px. Presenta una arquitectura U-Net más grande y un segundo "
            "codificador de texto (OpenCLIP ViT-bigG) que mejora significativamente "
            "la calidad de imagen, el renderizado de texto y la precisión "
            "composicional respecto a versiones anteriores de SD. También incluye "
            "RealVisXL V4.0, un fine-tune comunitario optimizado para retratos "
            "fotorrealistas y fotografía. Modelo base en "
            "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0."
        ),
        pt=(
            "Stable Diffusion XL (SDXL) é um modelo de difusão latente da "
            "Stability AI para geração de imagens de alta resolução a "
            "1024x1024 px. Apresenta uma arquitetura U-Net maior e um segundo "
            "codificador de texto (OpenCLIP ViT-bigG) que melhora significativamente "
            "a qualidade de imagem, a renderização de texto e a precisão "
            "composicional em relação a versões anteriores do SD. Também inclui "
            "RealVisXL V4.0, um fine-tune comunitário otimizado para retratos "
            "fotorrealistas e fotografia. Modelo base em "
            "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0."
        ),
        de=(
            "Stable Diffusion XL (SDXL) ist ein latentes Diffusionsmodell von "
            "Stability AI zur hochauflösenden Text-zu-Bild-Generierung bei "
            "1024x1024 px. Es verfügt über eine größere U-Net-Architektur und einen "
            "zweiten Textcodierer (OpenCLIP ViT-bigG), der Bildqualität, "
            "Textdarstellung und kompositorische Genauigkeit gegenüber früheren "
            "SD-Versionen deutlich verbessert. Enthält auch RealVisXL V4.0, einen "
            "Community-Fine-Tune optimiert für fotorealistische Porträts und "
            "Fotografie. Basismodell unter "
            "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0."
        ),
        zh=(
            "Stable Diffusion XL（SDXL）是 Stability AI 的潜扩散模型，"
            "用于 1024x1024px 高分辨率文本到图像生成，图像质量和排版精度显著提升。"
        ),
    )

    def __init__(self, **kwargs):
        """Initialize the model."""
        import torch
        from diffusers import StableDiffusionXLPipeline

        kwargs = self.validate_and_transform(kwargs)
        use_gpu = DEVICE_TO_IDX.get(kwargs.get("device")) >= 0
        self.device = (
            f"cuda:{DEVICE_TO_IDX.get(kwargs.get('device'))}" if use_gpu else "cpu"
        )
        self.model_name = self._pretrained_source(None)

        self.model = StableDiffusionXLPipeline.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if use_gpu else torch.float32,
            use_safetensors=True,
            variant="fp16" if use_gpu else None,
        ).to(self.device)

        self.negative_prompt = kwargs.get("negative_prompt")
        self.num_inference_steps = kwargs.get("num_inference_steps")
        self.guidance_scale = kwargs.get("guidance_scale")
        self.seed = kwargs.get("seed")
        self.width = kwargs.get("width")
        self.height = kwargs.get("height")
        self.num_images_per_prompt = kwargs.get("num_images_per_prompt")

    def generate(self, input: str) -> List[Any]:
        """Generate images from a text prompt.

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

        params = {
            "prompt": input,
            "negative_prompt": self.negative_prompt,
            "num_inference_steps": self.num_inference_steps,
            "guidance_scale": self.guidance_scale,
            "width": self.width,
            "height": self.height,
            "generator": generator,
            "num_images_per_prompt": self.num_images_per_prompt,
        }

        output = self.model(**params)
        return output.images


class StableDiffusionXL(StableDiffusionXLGenerationModel):
    """Stable Diffusion XL base 1.0 checkpoint.

    Downloads its checkpoint into the component's own download folder.
    """

    MODEL_NAME: str = "stabilityai/stable-diffusion-xl-base-1.0"
    # SDXL diffusers pipeline (base + refiner-less) is ~7 GB.
    DOWNLOAD_SIZE_BYTES: int = 35249410067
    DISPLAY_NAME = MultilingualString(
        en="Stable Diffusion XL",
        es="Stable Diffusion XL",
        pt="Stable Diffusion XL",
        de="Stable Diffusion XL",
        zh="Stable Diffusion XL",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Stable Diffusion XL base 1.0 by Stability AI, a large latent diffusion "
            "model that uses two text encoders and a 1024x1024 px native resolution "
            "for high fidelity results. It is well suited to detailed, "
            "photorealistic and artistic prompts. Weights are downloaded into the "
            "component's own folder. Model page: https://huggingface.co/stabilityai/s"
            "table-diffusion-xl-base-1.0"
        ),
        es=(
            "Stable Diffusion XL base 1.0 de Stability AI, un modelo de difusión "
            "latente grande que usa dos codificadores de texto y una resolución "
            "nativa de 1024x1024 px para resultados de alta fidelidad. Es adecuado "
            "para prompts detallados, fotorrealistas y artísticos. Los pesos se "
            "descargan en la carpeta propia del componente. Página del modelo: "
            "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"
        ),
        pt=(
            "Stable Diffusion XL base 1.0 da Stability AI, um grande modelo de "
            "difusão latente que usa dois codificadores de texto e resolução "
            "nativa de 1024x1024 px para resultados de alta fidelidade. É adequado "
            "para prompts detalhados, fotorrealistas e artísticos. Os pesos são "
            "baixados na pasta própria do componente. Página do modelo: "
            "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"
        ),
        de=(
            "Stable Diffusion XL Basis 1.0 von Stability AI, ein großes latentes "
            "Diffusionsmodell mit zwei Textencodern und einer nativen Auflösung von "
            "1024x1024 px für Ergebnisse mit hoher Detailtreue. Es eignet sich gut "
            "für detaillierte, fotorealistische und künstlerische Prompts. Die "
            "Gewichte werden in den eigenen Ordner der Komponente heruntergeladen. "
            "Modellseite: https://huggingface.co/stabilityai/stable-diffusion-xl-base"
            "-1.0"
        ),
        zh=(
            "Stability AI 推出的 Stable Diffusion XL base "
            "1.0，是一种大型潜在扩散模型，使用两个文本编码器和 1024x1024 "
            "像素的原生分辨率以获得高保真结果。非常适合细致、写实和艺术性的提示词。权"
            "重会下载到该组件自己的文件夹中。 模型页面： https://huggingface.co/stabi"
            "lityai/stable-diffusion-xl-base-1.0"
        ),
    )


class RealVisXLV4(StableDiffusionXLGenerationModel):
    """RealVisXL V4.0 photorealistic SDXL checkpoint.

    Downloads its checkpoint into the component's own download folder.
    """

    MODEL_NAME: str = "SG161222/RealVisXL_V4.0"
    # SDXL diffusers pipeline (base + refiner-less) is ~7 GB.
    DOWNLOAD_SIZE_BYTES: int = 27754923233
    DISPLAY_NAME = MultilingualString(
        en="RealVisXL V4.0",
        es="RealVisXL V4.0",
        pt="RealVisXL V4.0",
        de="RealVisXL V4.0",
        zh="RealVisXL V4.0",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "RealVisXL V4.0 by SG161222, a community fine-tune of Stable Diffusion "
            "XL focused on photorealism. It excels at lifelike portraits, lighting "
            "and textures while remaining compatible with the SDXL pipeline. Weights "
            "are downloaded into the component's own folder. Model page: "
            "https://huggingface.co/SG161222/RealVisXL_V4.0"
        ),
        es=(
            "RealVisXL V4.0 de SG161222, un ajuste comunitario de Stable Diffusion "
            "XL enfocado en el fotorrealismo. Destaca en retratos, iluminación y "
            "texturas realistas, manteniéndose compatible con el pipeline de SDXL. "
            "Los pesos se descargan en la carpeta propia del componente. Página del "
            "modelo: https://huggingface.co/SG161222/RealVisXL_V4.0"
        ),
        pt=(
            "RealVisXL V4.0 de SG161222, um ajuste comunitário do Stable Diffusion "
            "XL focado em fotorrealismo. Destaca-se em retratos, iluminação e "
            "texturas realistas, mantendo compatibilidade com o pipeline do SDXL. Os "
            "pesos são baixados na pasta própria do componente. Página do modelo: "
            "https://huggingface.co/SG161222/RealVisXL_V4.0"
        ),
        de=(
            "RealVisXL V4.0 von SG161222, eine Community-Feinabstimmung von Stable "
            "Diffusion XL mit Fokus auf Fotorealismus. Es glänzt bei lebensechten "
            "Porträts, Beleuchtung und Texturen und bleibt mit der SDXL-Pipeline "
            "kompatibel. Die Gewichte werden in den eigenen Ordner der Komponente "
            "heruntergeladen. Modellseite: https://huggingface.co/SG161222/RealVisXL_"
            "V4.0"
        ),
        zh=(
            "SG161222 推出的 RealVisXL V4.0，是 Stable Diffusion XL "
            "的社区微调版本，专注于照片级真实感。擅长逼真的人像、光照和纹理，同时保持"
            "与 SDXL 流水线的兼容。权重会下载到该组件自己的文件夹中。 模型页面： "
            "https://huggingface.co/SG161222/RealVisXL_V4.0"
        ),
    )
