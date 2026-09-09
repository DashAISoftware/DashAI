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


class StableDiffusionSchema(BaseSchema):
    """Configuration schema for Stable Diffusion V2 text-to-image generation.

    Configures the checkpoint variant (``model_name``), prompt conditioning
    (``negative_prompt``), denoising schedule (``num_inference_steps``),
    classifier free guidance strength (``guidance_scale``), output dimensions
    (``width``, ``height``), reproducibility (``seed``), hardware target
    (``device``), and batch size (``num_images_per_prompt``) for
    ``StableDiffusionV2Model``.
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
                    "marca de agua'. Dejar vacío para omitir "
                    "el condicionamiento negativo."
                ),
                pt=(
                    "Texto descrevendo o que excluir da imagem gerada. "
                    "Valores comuns: 'borrado, baixa qualidade, distorcido, "
                    "marca d'água'. Deixe vazio para omitir "
                    "o condicionamento negativo."
                ),
                de=(
                    "Text, der beschreibt, was aus dem generierten Bild ausgeschlossen "
                    "werden soll. Häufige Werte: 'unscharf, geringe Qualität, verzerrt,"
                    "Wasserzeichen'. Leer lassen, um die negative Konditionierung zu "
                    "überspringen."
                ),
                zh=(
                    "描述要从生成图像中排除内容的文本。"
                    "常用值：'模糊, 低质量, 失真, 水印'。"
                    "留空以跳过负向条件约束。"
                ),
            ),
            alias=MultilingualString(
                en="Negative prompt",
                es="Prompt negativo",
                pt="Prompt negativo",
                de="Negativer Prompt",
                zh="负向提示词",
            ),
        )  # type: ignore
    ]

    num_inference_steps: schema_field(
        int_field(ge=1),
        placeholder=15,
        description=MultilingualString(
            en=(
                "Number of denoising steps to run. More steps refine the image but "
                "increase generation time. Typical range: 15-30 for fast results, "
                "40-50 for higher quality. Values above 100 rarely improve output."
            ),
            es=(
                "Número de pasos de eliminación de ruido a ejecutar. Más pasos refinan "
                "la imagen pero aumentan el tiempo de generación. Rango típico: 15-30 "
                "para resultados rápidos, 40-50 para mayor calidad. Valores superiores "
                "a 100 raramente mejoran el resultado."
            ),
            pt=(
                "Número de passos de remoção de ruído a executar. Mais passos refinam "
                "a imagem mas aumentam o tempo de geração. Intervalo típico: 15-30 "
                "para resultados rápidos, 40-50 para maior qualidade. Valores acima "
                "de 100 raramente melhoram o resultado."
            ),
            de=(
                "Anzahl der auszuführenden Entrauschungsschritte. Mehr Schritte "
                "verfeinern "
                "das Bild, erhöhen aber die Generierungszeit. Typischer Bereich: 15-30 "
                "für schnelle Ergebnisse, 40-50 für höhere Qualität. Werte über 100 "
                "verbessern das Ergebnis selten."
            ),
            zh=(
                "去噪步骤数。步骤越多图像越精细，但生成时间越长。"
                "典型范围：15-30 步可快速出图，40-50 步质量更高。"
                "超过 100 步时效果提升通常不明显。"
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
        placeholder=3.5,
        description=MultilingualString(
            en=(
                "Classifier-Free Guidance (CFG) scale. Controls how strictly the "
                "image follows the text prompt. Low values (1-4) allow creative "
                "freedom; medium values (5-9) balance quality and adherence; "
                "high values (10+) enforce the prompt but may produce artifacts."
            ),
            es=(
                "Escala de Classifier-Free Guidance (CFG). Controla qué tan "
                "estrictamente la imagen sigue el prompt de texto. Valores bajos "
                "(1-4) permiten libertad creativa; valores medios (5-9) equilibran "
                "calidad y adherencia; valores altos (10+) refuerzan el prompt pero "
                "pueden producir artefactos."
            ),
            pt=(
                "Escala de Classifier-Free Guidance (CFG). Controla quão "
                "estritamente a imagem segue o prompt de texto. Valores baixos "
                "(1-4) permitem liberdade criativa; valores médios (5-9) equilibram "
                "qualidade e aderência; valores altos (10+) reforçam o prompt mas "
                "podem produzir artefatos."
            ),
            de=(
                "Classifier-Free Guidance (CFG)-Skala. Steuert, wie streng das Bild "
                "dem Textprompt folgt. Niedrige Werte (1-4) erlauben kreative Freiheit;"
                "mittlere Werte (5-9) balancieren Qualität und Treue; hohe Werte (10+) "
                "erzwingen den Prompt, können aber Artefakte erzeugen."
            ),
            zh=(
                "无分类器引导（CFG）比例。控制图像遵循文本提示的严格程度。"
                "低值（1-4）允许创意自由；中值（5-9）平衡质量与贴合度；"
                "高值（10+）严格执行提示，但可能产生伪影。"
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
                "acceleration, which is strongly recommended for diffusion models. "
                "Select 'CPU' on systems without a compatible GPU, but expect "
                "significantly longer generation times."
            ),
            es=(
                "Dispositivo de hardware para la inferencia. Seleccione una opción "
                "de GPU para aceleración por hardware, muy recomendado para modelos "
                "de difusión. Seleccione 'CPU' en sistemas sin GPU compatible, pero "
                "espere tiempos de generación significativamente más largos."
            ),
            pt=(
                "Dispositivo de hardware para inferência. Selecione uma opção de GPU "
                "para aceleração por hardware, altamente recomendado para modelos de "
                "difusão. Selecione 'CPU' em sistemas sem GPU compatível, mas espere "
                "tempos de geração significativamente mais longos."
            ),
            de=(
                "Hardware-Gerät für die Inferenz. Wählen Sie eine GPU-Option für "
                "Hardwarebeschleunigung, die für Diffusionsmodelle dringend empfohlen "
                "wird. Wählen Sie 'CPU' auf Systemen ohne kompatible GPU, aber erwarten"
                "Sie deutlich längere Generierungszeiten."
            ),
            zh=(
                "推理硬件设备。建议选择 GPU 选项以加速扩散模型推理。"
                "在没有兼容 GPU 的系统上可选择 CPU，但生成时间将显著增加。"
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
                "Use un valor negativo (ej. -1) para una semilla aleatoria en cada "
                "ejecución."
            ),
            pt=(
                "Semente aleatória para geração reproduzível. Um inteiro positivo "
                "fixo sempre produzirá a mesma imagem com configurações idênticas. "
                "Use um valor negativo (ex. -1) para uma semente aleatória em cada "
                "execução."
            ),
            de=(
                "Zufalls-Seed für reproduzierbare Generierung. Ein fester positiver "
                "Integer erzeugt stets dasselbe Bild bei identischen Einstellungen. "
                "Verwenden Sie einen negativen Wert (z.B. -1) für einen zufälligen "
                "Seed bei jedem Durchlauf."
            ),
            zh=(
                "用于可复现生成的随机种子。固定正整数在相同设置下始终生成相同图像。"
                "使用负值（如 -1）可在每次运行时使用随机种子。"
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
                "Native resolution is 512 for '-base' variants and 768 for others. "
                "Using the native resolution produces the best quality results."
            ),
            es=(
                "Ancho de la imagen de salida en píxeles. Debe ser múltiplo de 8. "
                "La resolución nativa es 512 para variantes '-base' y 768 para las "
                "demás. Usar la resolución nativa produce los mejores resultados."
            ),
            pt=(
                "Largura da imagem de saída em pixels. Deve ser múltiplo de 8. "
                "A resolução nativa é 512 para variantes '-base' e 768 para as "
                "demais. Usar a resolução nativa produz os melhores resultados."
            ),
            de=(
                "Breite des Ausgabebildes in Pixeln. Muss ein Vielfaches von 8 sein. "
                "Die native Auflösung beträgt 512 für '-base'-Varianten und 768 für "
                "andere. "
                "Die native Auflösung liefert die besten Qualitätsergebnisse."
            ),
            zh=(
                "输出图像的宽度（像素）。必须是 8 的倍数。"
                "'-base' 变体原生分辨率为 512，其他变体为 768。"
                "使用原生分辨率可获得最佳质量。"
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
                "Native resolution is 512 for '-base' variants and 768 for others. "
                "Using the native resolution produces the best quality results."
            ),
            es=(
                "Altura de la imagen de salida en píxeles. Debe ser múltiplo de 8. "
                "La resolución nativa es 512 para variantes '-base' y 768 para las "
                "demás. Usar la resolución nativa produce los mejores resultados."
            ),
            pt=(
                "Altura da imagem de saída em pixels. Deve ser múltiplo de 8. "
                "A resolução nativa é 512 para variantes '-base' e 768 para as "
                "demais. Usar a resolução nativa produz os melhores resultados."
            ),
            de=(
                "Höhe des Ausgabebildes in Pixeln. Muss ein Vielfaches von 8 sein. "
                "Die native Auflösung beträgt 512 für '-base'-Varianten und 768 für "
                "andere. "
                "Die native Auflösung liefert die besten Qualitätsergebnisse."
            ),
            zh=(
                "输出图像的高度（像素）。必须是 8 的倍数。"
                "'-base' 变体原生分辨率为 512，其他变体为 768。"
                "使用原生分辨率可获得最佳质量。"
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
                "单次批处理中从一个提示词生成的图像数量。"
                "增大此值比多次运行更高效，但需要相应更多的 GPU 显存。"
            ),
        ),
        alias=MultilingualString(
            en="Num images per prompt",
            es="Número de imágenes por prompt",
            pt="Número de imagens por prompt",
            de="Bilder pro Prompt",
            zh="每提示词生成图像数",
        ),
    )  # type: ignore


class StableDiffusion2GenerationModel(
    HFPretrainedDownloadMixin, TextToImageGenerationTaskModel
):
    """Latent diffusion model for high resolution text-to-image generation.

    Wraps the Stable Diffusion 2.x family of checkpoints released by
    Stability AI. The pipeline uses a U-Net denoiser conditioned on OpenCLIP
    text embeddings (ViT-H/14) and a variational autoencoder (VAE) to
    iteratively denoise a latent representation into a high resolution image.

    Four checkpoints are supported:

    * ``stable-diffusion-2`` / ``stable-diffusion-2-1``: trained at 768 px,
      produce sharper detail; '2-1' is further fine-tuned and generally
      outperforms '2'.
    * ``stable-diffusion-2-base`` / ``stable-diffusion-2-1-base``: trained at
      512 px, faster and lower memory; best for rapid prototyping.

    Models are served from the ``sd2-community`` HuggingFace organisation,
    a community mirror of the original Stability AI weights (deprecated at
    ``stabilityai``).

    References
    ----------
    - [1] Rombach et al., "High-Resolution Image Synthesis with Latent
           Diffusion Models", CVPR 2022. https://arxiv.org/abs/2112.10752
    - [2] https://huggingface.co/sd2-community
    """

    SCHEMA = StableDiffusionSchema
    MODEL_NAME: str = ""
    COLOR: str = "#1565c0"
    DISPLAY_NAME: str = MultilingualString(
        en="Stable Diffusion V2",
        es="Stable Diffusion V2",
        pt="Stable Diffusion V2",
        de="Stable Diffusion V2",
        zh="Stable Diffusion V2",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Stable Diffusion 2.x is a latent diffusion model by Stability AI for "
            "high resolution text-to-image generation. It uses a U-Net denoiser "
            "conditioned on CLIP text embeddings and a variational autoencoder (VAE) "
            "to produce detailed images from text prompts. "
            "Supports stable-diffusion-2, "
            "stable-diffusion-2-base, stable-diffusion-2-1, and "
            "stable-diffusion-2-1-base variants. Models are served from the "
            "sd2-community organization (https://huggingface.co/sd2-community), "
            "a community mirror of the original Stability AI weights which have been "
            "deprecated and removed from https://huggingface.co/stabilityai."
        ),
        es=(
            "Stable Diffusion 2.x es un modelo de difusión latente de Stability AI "
            "para generación de imágenes de alta resolución a partir de texto. Utiliza "
            "un denoiser U-Net condicionado en embeddings de texto CLIP y un "
            "autoencoder variacional (VAE) para producir imágenes detalladas. Soporta "
            "las variantes stable-diffusion-2, stable-diffusion-2-base, "
            "stable-diffusion-2-1 y stable-diffusion-2-1-base. Los modelos se sirven "
            "desde la organización sd2-community "
            "(https://huggingface.co/sd2-community), un espejo comunitario de los "
            "pesos originales de Stability AI que han sido deprecados y eliminados de "
            "https://huggingface.co/stabilityai."
        ),
        pt=(
            "Stable Diffusion 2.x é um modelo de difusão latente da Stability AI para "
            "geração de imagens de alta resolução a partir de texto. Utiliza um "
            "denoiser U-Net condicionado em embeddings de texto CLIP e um autoencoder "
            "variacional (VAE) para produzir imagens detalhadas. Suporta as variantes "
            "stable-diffusion-2, stable-diffusion-2-base, stable-diffusion-2-1 e "
            "stable-diffusion-2-1-base. Os modelos são servidos pela organização "
            "sd2-community (https://huggingface.co/sd2-community), um espelho "
            "comunitário dos pesos originais da Stability AI que foram depreciados e "
            "removidos de https://huggingface.co/stabilityai."
        ),
        de=(
            "Stable Diffusion 2.x ist ein latentes Diffusionsmodell von Stability AI "
            "zur hochauflösenden Text-zu-Bild-Generierung. Es verwendet einen U-Net-"
            "Entrauscher konditioniert auf CLIP-Texteinbettungen und einen "
            "variationalen "
            "Autoencoder (VAE) zur Erzeugung detaillierter Bilder. Unterstützt die "
            "Varianten stable-diffusion-2, stable-diffusion-2-base, "
            "stable-diffusion-2-1 "
            "und stable-diffusion-2-1-base. Modelle werden von der Organisation "
            "sd2-community (https://huggingface.co/sd2-community) bereitgestellt, einem"
            "Community-Spiegel der originalen Stability AI-Gewichte, die von "
            "https://huggingface.co/stabilityai veraltet und entfernt wurden."
        ),
        zh=(
            "Stable Diffusion 2.x 是 Stability AI 的潜扩散模型，"
            "用于高分辨率文本到图像生成。"
            "支持 stable-diffusion-2、stable-diffusion-2-1 等变体。"
        ),
    )

    def __init__(self, **kwargs):
        """Download and initialise the Stable Diffusion V2 pipeline.

        Downloads the selected checkpoint from HuggingFace Hub via
        ``DiffusionPipeline.from_pretrained`` and moves the pipeline to the
        requested device.

        Parameters
        ----------
        **kwargs : dict
            model_name : str, optional
                HuggingFace model ID to load.  Must be one of the four
                ``sd2-community`` checkpoints defined in ``StableDiffusionSchema``.
                Defaults to ``"sd2-community/stable-diffusion-2"``.
            negative_prompt : str or None, optional
                Text describing content to suppress in the output image.
            num_inference_steps : int
                Number of denoising steps.  Higher values improve quality at
                the cost of generation time.
            guidance_scale : float
                Classifier-Free Guidance (CFG) scale controlling prompt
                adherence.
            device : str
                Target device string from ``DEVICE_ENUM``.  Mapped to a
                ``cuda:<index>`` string or ``"cpu"`` via ``DEVICE_TO_IDX``.
            seed : int
                Fixed seed for reproducible outputs.  Values ≤ 0 disable
                seeding.
            width : int
                Output image width in pixels (multiple of 8).
            height : int
                Output image height in pixels (multiple of 8).
            num_images_per_prompt : int
                Number of images to generate per prompt call.
        """
        import torch
        from diffusers import DiffusionPipeline

        kwargs = self.validate_and_transform(kwargs)
        use_gpu = DEVICE_TO_IDX.get(kwargs.get("device")) >= 0
        self.device = (
            f"cuda:{DEVICE_TO_IDX.get(kwargs.get('device'))}" if use_gpu else "cpu"
        )
        self.model_name = self._pretrained_source(None)

        self.model = DiffusionPipeline.from_pretrained(
            self.model_name,
            torch_dtype=torch.float32,
        ).to(self.device)

        self.negative_prompt = kwargs.get("negative_prompt")
        self.num_inference_steps = kwargs.get("num_inference_steps")
        self.guidance_scale = kwargs.get("guidance_scale")
        self.seed = kwargs.get("seed")
        self.width = kwargs.get("width")
        self.height = kwargs.get("height")
        self.num_images_per_prompt = kwargs.get("num_images_per_prompt")

    def generate(self, input: str) -> List[Any]:
        """Generate output from a generative model.

        Parameters
        ----------
        input : str
            Input data to be generated

        Returns
        -------
        List[Any]
            Generated output images in a list

        """
        import torch

        generator = None
        if self.seed is not None and self.seed > 0:
            generator = torch.Generator(device=self.device).manual_seed(self.seed)

        # Base parameters for all models
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

        # Generate images
        output = self.model(**params)

        return output.images


class StableDiffusion2(StableDiffusion2GenerationModel):
    """768px Stable Diffusion 2 checkpoint.

    Downloads its checkpoint into the component's own download folder.
    """

    MODEL_NAME: str = "sd2-community/stable-diffusion-2"
    # Full fp32 diffusers pipeline (text encoder + U-Net + VAE) is ~5 GB.
    DOWNLOAD_SIZE_BYTES: int = 25911933905
    DISPLAY_NAME = MultilingualString(
        en="Stable Diffusion 2",
        es="Stable Diffusion 2",
        pt="Stable Diffusion 2",
        de="Stable Diffusion 2",
        zh="Stable Diffusion 2",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Stable Diffusion 2 by Stability AI, a latent text-to-image diffusion "
            "model conditioned on OpenCLIP text embeddings. This checkpoint is "
            "trained at 768x768 px and produces sharp, high-detail images. Weights "
            "are downloaded into the component's own folder from the sd2-community "
            "mirror. Model page: https://huggingface.co/sd2-community/stable-diffusio"
            "n-2"
        ),
        es=(
            "Stable Diffusion 2 de Stability AI, un modelo de difusión latente de "
            "texto a imagen condicionado en embeddings de texto OpenCLIP. Este "
            "checkpoint se entrena a 768x768 px y produce imágenes nítidas y muy "
            "detalladas. Los pesos se descargan en la carpeta propia del componente "
            "desde el espejo sd2-community. Página del modelo: "
            "https://huggingface.co/sd2-community/stable-diffusion-2"
        ),
        pt=(
            "Stable Diffusion 2 da Stability AI, um modelo de difusão latente de "
            "texto para imagem condicionado em embeddings de texto OpenCLIP. Este "
            "checkpoint é treinado a 768x768 px e produz imagens nítidas e com "
            "muitos detalhes. Os pesos são baixados na pasta própria do componente "
            "a partir do espelho sd2-community. Página do modelo: "
            "https://huggingface.co/sd2-community/stable-diffusion-2"
        ),
        de=(
            "Stable Diffusion 2 von Stability AI, ein latentes "
            "Text-zu-Bild-Diffusionsmodell, das auf OpenCLIP-Texteinbettungen "
            "konditioniert ist. Dieser Checkpoint wird bei 768x768 px trainiert und "
            "erzeugt scharfe, detailreiche Bilder. Die Gewichte werden aus dem "
            "sd2-community-Spiegel in den eigenen Ordner der Komponente "
            "heruntergeladen. Modellseite: https://huggingface.co/sd2-community/stabl"
            "e-diffusion-2"
        ),
        zh=(
            "Stability AI 推出的 Stable Diffusion 2，是一种以 OpenCLIP "
            "文本嵌入为条件的潜在文本到图像扩散模型。该检查点在 768x768 "
            "像素下训练，可生成清晰且细节丰富的图像。权重会从 sd2-community "
            "镜像下载到该组件自己的文件夹中。 模型页面： https://huggingface.co/sd2-c"
            "ommunity/stable-diffusion-2"
        ),
    )


class StableDiffusion2_512(StableDiffusion2GenerationModel):  # noqa: N801
    """512px base Stable Diffusion 2 checkpoint (faster).

    Downloads its checkpoint into the component's own download folder.
    """

    MODEL_NAME: str = "sd2-community/stable-diffusion-2-base"
    # Full fp32 diffusers pipeline (text encoder + U-Net + VAE) is ~5 GB.
    DOWNLOAD_SIZE_BYTES: int = 25911843836
    DISPLAY_NAME = MultilingualString(
        en="Stable Diffusion 2 (512px)",
        es="Stable Diffusion 2 (512px)",
        pt="Stable Diffusion 2 (512px)",
        de="Stable Diffusion 2 (512px)",
        zh="Stable Diffusion 2 (512px)",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Stable Diffusion 2 base checkpoint by Stability AI, trained at 512x512 "
            "px. It is faster and uses less memory than the 768 px variant, making "
            "it a good choice for rapid prototyping. Weights are downloaded into the "
            "component's own folder from the sd2-community mirror. Model page: "
            "https://huggingface.co/sd2-community/stable-diffusion-2-base"
        ),
        es=(
            "Checkpoint base de Stable Diffusion 2 de Stability AI, entrenado a "
            "512x512 px. Es más rápido y usa menos memoria que la variante de 768 "
            "px, ideal para prototipado rápido. Los pesos se descargan en la "
            "carpeta propia del componente desde el espejo sd2-community. Página "
            "del modelo: https://huggingface.co/sd2-community/stable-diffusion-2-base"
        ),
        pt=(
            "Checkpoint base do Stable Diffusion 2 da Stability AI, treinado a "
            "512x512 px. É mais rápido e usa menos memória que a variante de 768 "
            "px, ideal para prototipagem rápida. Os pesos são baixados na pasta "
            "própria do componente a partir do espelho sd2-community. Página do "
            "modelo: https://huggingface.co/sd2-community/stable-diffusion-2-base"
        ),
        de=(
            "Stable Diffusion 2 Basis-Checkpoint von Stability AI, trainiert bei "
            "512x512 px. Er ist schneller und benötigt weniger Speicher als die "
            "768-px-Variante und eignet sich gut für schnelles Prototyping. Die "
            "Gewichte werden aus dem sd2-community-Spiegel in den eigenen Ordner der "
            "Komponente heruntergeladen. Modellseite: "
            "https://huggingface.co/sd2-community/stable-diffusion-2-base"
        ),
        zh=(
            "Stability AI 推出的 Stable Diffusion 2 基础检查点，在 512x512 "
            "像素下训练。相比 768 像素变体速度更快、显存占用更低，非常适合快速原型设"
            "计。权重会从 sd2-community 镜像下载到该组件自己的文件夹中。 模型页面： "
            "https://huggingface.co/sd2-community/stable-diffusion-2-base"
        ),
    )


class StableDiffusion21(StableDiffusion2GenerationModel):
    """768px Stable Diffusion 2.1 checkpoint (further fine-tuned).

    Downloads its checkpoint into the component's own download folder.
    """

    MODEL_NAME: str = "sd2-community/stable-diffusion-2-1"
    # Full fp32 diffusers pipeline (text encoder + U-Net + VAE) is ~5 GB.
    DOWNLOAD_SIZE_BYTES: int = 36341303572
    DISPLAY_NAME = MultilingualString(
        en="Stable Diffusion 2.1",
        es="Stable Diffusion 2.1",
        pt="Stable Diffusion 2.1",
        de="Stable Diffusion 2.1",
        zh="Stable Diffusion 2.1",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Stable Diffusion 2.1 by Stability AI, a further fine-tuned revision of "
            "the 2.x family trained at 768x768 px. It generally produces cleaner, "
            "more coherent images than the original 2.0. Weights are downloaded into "
            "the component's own folder from the sd2-community mirror. Model page: "
            "https://huggingface.co/sd2-community/stable-diffusion-2-1"
        ),
        es=(
            "Stable Diffusion 2.1 de Stability AI, una revisión más ajustada de la "
            "familia 2.x entrenada a 768x768 px. Suele producir imágenes más "
            "limpias y coherentes que la 2.0 original. Los pesos se descargan en la "
            "carpeta propia del componente desde el espejo sd2-community. Página "
            "del modelo: https://huggingface.co/sd2-community/stable-diffusion-2-1"
        ),
        pt=(
            "Stable Diffusion 2.1 da Stability AI, uma revisão mais ajustada da "
            "família 2.x treinada a 768x768 px. Costuma produzir imagens mais "
            "limpas e coerentes que a 2.0 original. Os pesos são baixados na pasta "
            "própria do componente a partir do espelho sd2-community. Página do "
            "modelo: https://huggingface.co/sd2-community/stable-diffusion-2-1"
        ),
        de=(
            "Stable Diffusion 2.1 von Stability AI, eine weiter feinabgestimmte "
            "Überarbeitung der 2.x-Familie, trainiert bei 768x768 px. Sie erzeugt "
            "in der Regel sauberere, kohärentere Bilder als die ursprüngliche 2.0. "
            "Die Gewichte werden aus dem sd2-community-Spiegel in den eigenen Ordner "
            "der Komponente heruntergeladen. Modellseite: "
            "https://huggingface.co/sd2-community/stable-diffusion-2-1"
        ),
        zh=(
            "Stability AI 推出的 Stable Diffusion 2.1，是 2.x "
            "系列的进一步微调版本，在 768x768 像素下训练。通常比原始的 2.0 "
            "生成更干净、更连贯的图像。权重会从 sd2-community "
            "镜像下载到该组件自己的文件夹中。 模型页面： https://huggingface.co/sd2-c"
            "ommunity/stable-diffusion-2-1"
        ),
    )


class StableDiffusion21_512(StableDiffusion2GenerationModel):  # noqa: N801
    """512px base Stable Diffusion 2.1 checkpoint.

    Downloads its checkpoint into the component's own download folder.
    """

    MODEL_NAME: str = "sd2-community/stable-diffusion-2-1-base"
    # Full fp32 diffusers pipeline (text encoder + U-Net + VAE) is ~5 GB.
    DOWNLOAD_SIZE_BYTES: int = 36341275775
    DISPLAY_NAME = MultilingualString(
        en="Stable Diffusion 2.1 (512px)",
        es="Stable Diffusion 2.1 (512px)",
        pt="Stable Diffusion 2.1 (512px)",
        de="Stable Diffusion 2.1 (512px)",
        zh="Stable Diffusion 2.1 (512px)",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Stable Diffusion 2.1 base checkpoint by Stability AI, trained at "
            "512x512 px. It combines the 2.1 fine-tuning improvements with the lower "
            "memory footprint and faster generation of the 512 px base models. "
            "Weights are downloaded into the component's own folder from the "
            "sd2-community mirror. Model page: https://huggingface.co/sd2-community/s"
            "table-diffusion-2-1-base"
        ),
        es=(
            "Checkpoint base de Stable Diffusion 2.1 de Stability AI, entrenado a "
            "512x512 px. Combina las mejoras de ajuste de la 2.1 con el menor "
            "consumo de memoria y la generación más rápida de los modelos base de "
            "512 px. Los pesos se descargan en la carpeta propia del componente "
            "desde el espejo sd2-community. Página del modelo: "
            "https://huggingface.co/sd2-community/stable-diffusion-2-1-base"
        ),
        pt=(
            "Checkpoint base do Stable Diffusion 2.1 da Stability AI, treinado a "
            "512x512 px. Combina as melhorias de ajuste da 2.1 com o menor uso de "
            "memória e a geração mais rápida dos modelos base de 512 px. Os "
            "pesos são baixados na pasta própria do componente a partir do espelho "
            "sd2-community. Página do modelo: https://huggingface.co/sd2-community/s"
            "table-diffusion-2-1-base"
        ),
        de=(
            "Stable Diffusion 2.1 Basis-Checkpoint von Stability AI, trainiert bei "
            "512x512 px. Er verbindet die Feinabstimmungs-Verbesserungen von 2.1 mit "
            "dem geringeren Speicherbedarf und der schnelleren Generierung der "
            "512-px-Basismodelle. Die Gewichte werden aus dem sd2-community-Spiegel "
            "in den eigenen Ordner der Komponente heruntergeladen. Modellseite: "
            "https://huggingface.co/sd2-community/stable-diffusion-2-1-base"
        ),
        zh=(
            "Stability AI 推出的 Stable Diffusion 2.1 基础检查点，在 512x512 "
            "像素下训练。它将 2.1 的微调改进与 512 "
            "像素基础模型更低的显存占用和更快的生成速度相结合。权重会从 "
            "sd2-community 镜像下载到该组件自己的文件夹中。 模型页面： "
            "https://huggingface.co/sd2-community/stable-diffusion-2-1-base"
        ),
    )
