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
    """Configuration schema for Stable Diffusion V3 text-to-image generation.

    Configures the checkpoint variant (``model_name``),
    prompt conditioning (``negative_prompt``),
    denoising schedule (``num_inference_steps``), prompt adherence
    (``guidance_scale``), output dimensions (``width``, ``height``),
    reproducibility (``seed``), hardware target (``device``), and batch size
    (``num_images_per_prompt``) for ``StableDiffusionV3Model``.
    """

    model_name: schema_field(
        enum_field(
            enum=[
                "stabilityai/stable-diffusion-3-medium-diffusers",
                "stabilityai/stable-diffusion-3.5-medium",
                "stabilityai/stable-diffusion-3.5-large",
                "stabilityai/stable-diffusion-3.5-large-turbo",
            ]
        ),
        placeholder="stabilityai/stable-diffusion-3-medium-diffusers",
        description=MultilingualString(
            en=(
                "The SD3/SD3.5 checkpoint to load. 'sd-3-medium' is the baseline "
                "2B-parameter model. 'sd-3.5-medium' improves quality at similar "
                "speed. 'sd-3.5-large' (8B) delivers the highest quality but needs "
                "more VRAM. 'sd-3.5-large-turbo' is a distilled large model that "
                "requires far fewer steps (4-8) for fast high-quality generation. "
                "All variants target 1024x1024 px natively."
            ),
            es=(
                "El checkpoint SD3/SD3.5 a cargar. 'sd-3-medium' es el modelo base "
                "de 2B parámetros. 'sd-3.5-medium' mejora la calidad a velocidad "
                "similar. 'sd-3.5-large' (8B) ofrece la mayor calidad pero necesita "
                "más VRAM. 'sd-3.5-large-turbo' es un modelo large destilado que "
                "requiere muchos menos pasos (4-8) para generación rápida de alta "
                "calidad. Todas las variantes apuntan a 1024x1024 px de forma nativa."
            ),
            pt=(
                "O checkpoint SD3/SD3.5 a carregar. 'sd-3-medium' é o modelo base "
                "de 2B parâmetros. 'sd-3.5-medium' melhora a qualidade a velocidade "
                "similar. 'sd-3.5-large' (8B) oferece a maior qualidade mas precisa "
                "de mais VRAM. 'sd-3.5-large-turbo' é um modelo large destilado que "
                "requer muito menos passos (4-8) para geração rápida de alta "
                "qualidade. "
                "Todas as variantes visam 1024x1024 px nativamente."
            ),
            de=(
                "Der zu ladende SD3/SD3.5-Checkpoint. 'sd-3-medium' ist das "
                "2B-Parameter-Basismodell. 'sd-3.5-medium' verbessert die Qualität "
                "bei ähnlicher Geschwindigkeit. 'sd-3.5-large' (8B) liefert die höchste"
                "Qualität, benötigt aber mehr VRAM. 'sd-3.5-large-turbo' ist ein "
                "destilliertes Large-Modell, das deutlich weniger Schritte (4-8) für "
                "schnelle hochwertige Generierung benötigt. "
                "Alle Varianten zielen nativ auf 1024x1024 px ab."
            ),
            zh=(
                "要加载的 SD3/SD3.5 检查点。'sd-3-medium' 是 2B 参数基准模型。"
                "'sd-3.5-medium' 以相近速度提升质量。'sd-3.5-large'（8B）质量最高但"
                "需要更多显存。'sd-3.5-large-turbo' 是蒸馏版大模型，仅需 4-8 步即可"
                "快速生成高质量图像。所有变体原生目标分辨率为 1024x1024 像素。"
            ),
        ),
        alias=MultilingualString(
            en="Model name",
            es="Nombre del modelo",
            pt="Nome do modelo",
            de="Modellname",
            zh="模型名称",
        ),
    )  # type: ignore

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
                    "描述生成图像中需排除内容的文本。"
                    "常用值：'模糊、低质量、扭曲、水印'。"
                    "留空以跳过负向条件引导。"
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
                "increase generation time. Typical range: 20-40 for standard models; "
                "use only 4-8 steps with 'large-turbo'. Values above 50 rarely "
                "improve output for SD3/SD3.5."
            ),
            es=(
                "Número de pasos de eliminación de ruido a ejecutar. Más pasos "
                "refinan la imagen pero aumentan el tiempo de generación. Rango "
                "típico: 20-40 para modelos estándar; use solo 4-8 pasos con "
                "'large-turbo'. Valores superiores a 50 raramente mejoran el "
                "resultado en SD3/SD3.5."
            ),
            pt=(
                "Número de passos de remoção de ruído a executar. Mais passos "
                "refinam a imagem mas aumentam o tempo de geração. Intervalo "
                "típico: 20-40 para modelos padrão; use apenas 4-8 passos com "
                "'large-turbo'. Valores acima de 50 raramente melhoram o "
                "resultado para SD3/SD3.5."
            ),
            de=(
                "Anzahl der auszuführenden Entrauschungsschritte. Mehr Schritte "
                "verfeinern das Bild, erhöhen aber die Generierungszeit. Typischer "
                "Bereich: 20-40 für Standardmodelle; verwenden Sie nur 4-8 Schritte "
                "mit 'large-turbo'. Werte über 50 verbessern das Ergebnis für "
                "SD3/SD3.5 selten."
            ),
            zh=(
                "去噪步数。更多步数可细化图像但会增加生成时间。标准模型典型范围：20-40；"
                "'large-turbo' 变体仅需 4-8 步。SD3/SD3.5 超过 50 步很少改善输出质量。"
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
                "image follows the text prompt. SD3.5 works well at 3.5-4.5. "
                "The 'large-turbo' variant is designed for guidance_scale=1 "
                "(no CFG). Higher values enforce the prompt but may introduce "
                "oversaturation or artifacts."
            ),
            es=(
                "Escala de Classifier-Free Guidance (CFG). Controla qué tan "
                "estrictamente la imagen sigue el prompt. SD3.5 funciona bien con "
                "3.5-4.5. La variante 'large-turbo' está diseñada para "
                "guidance_scale=1 (sin CFG). Valores más altos refuerzan el prompt "
                "pero pueden introducir sobresaturación o artefactos."
            ),
            pt=(
                "Escala de Classifier-Free Guidance (CFG). Controla quão "
                "estritamente a imagem segue o prompt. SD3.5 funciona bem com "
                "3.5-4.5. A variante 'large-turbo' é projetada para "
                "guidance_scale=1 (sem CFG). Valores mais altos reforçam o prompt "
                "mas podem introduzir supersaturação ou artefatos."
            ),
            de=(
                "Classifier-Free Guidance (CFG)-Skala. Steuert, wie streng das Bild "
                "dem Prompt folgt. SD3.5 funktioniert gut bei 3,5-4,5. Die "
                "'large-turbo'-"
                "Variante ist für guidance_scale=1 (kein CFG) ausgelegt. Höhere Werte "
                "erzwingen den Prompt, können aber Übersättigung oder Artefakte "
                "einführen."
            ),
            zh=(
                "无分类器引导（CFG）比例。控制图像对文本提示的遵循程度。"
                "SD3.5 在 3.5-4.5 效果良好。'large-turbo' 变体设计用于 "
                "guidance_scale=1（无 CFG）。较高值强化提示但可能引入过饱和或伪影。"
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
                "推理硬件设备。扩散模型强烈推荐选择 GPU 选项以硬件加速。"
                "无兼容 GPU 的系统可选 'CPU'，但生成时间会显著增加。"
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
                "可复现生成的随机种子。固定正整数在相同设置下始终产生相同图像。"
                "使用负值（如 -1）则每次运行使用随机种子。"
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
                "SD3/SD3.5 models are natively trained at 1024x1024 px; using "
                "that resolution yields the best quality."
            ),
            es=(
                "Ancho de la imagen de salida en píxeles. Debe ser múltiplo de 8. "
                "Los modelos SD3/SD3.5 se entrenan de forma nativa a 1024x1024 px; "
                "usar esa resolución produce la mejor calidad."
            ),
            pt=(
                "Largura da imagem de saída em pixels. Deve ser múltiplo de 8. "
                "Os modelos SD3/SD3.5 são nativamente treinados a 1024x1024 px; "
                "usar essa resolução produz a melhor qualidade."
            ),
            de=(
                "Breite des Ausgabebildes in Pixeln. Muss ein Vielfaches von 8 sein. "
                "SD3/SD3.5-Modelle werden nativ bei 1024x1024 px trainiert; "
                "diese Auflösung liefert die beste Qualität."
            ),
            zh=(
                "输出图像宽度（像素），必须是 8 的倍数。"
                "SD3/SD3.5 模型原生训练分辨率为 1024x1024 像素，"
                "使用该分辨率可获得最佳质量。"
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
                "SD3/SD3.5 models are natively trained at 1024x1024 px; using "
                "that resolution yields the best quality."
            ),
            es=(
                "Altura de la imagen de salida en píxeles. Debe ser múltiplo de 8. "
                "Los modelos SD3/SD3.5 se entrenan de forma nativa a 1024x1024 px; "
                "usar esa resolución produce la mejor calidad."
            ),
            pt=(
                "Altura da imagem de saída em pixels. Deve ser múltiplo de 8. "
                "Os modelos SD3/SD3.5 são nativamente treinados a 1024x1024 px; "
                "usar essa resolução produz a melhor qualidade."
            ),
            de=(
                "Höhe des Ausgabebildes in Pixeln. Muss ein Vielfaches von 8 sein. "
                "SD3/SD3.5-Modelle werden nativ bei 1024x1024 px trainiert; "
                "diese Auflösung liefert die beste Qualität."
            ),
            zh=(
                "输出图像高度（像素），必须是 8 的倍数。"
                "SD3/SD3.5 模型原生训练分辨率为 1024x1024 像素，"
                "使用该分辨率可获得最佳质量。"
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
                "单次批量从一个提示词生成的图像数量。"
                "增大此值比多次运行更高效，但需要成比例的更多 GPU 显存。"
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


class StableDiffusion3GenerationModel(
    HFPretrainedDownloadMixin, TextToImageGenerationTaskModel
):
    """Multimodal Diffusion Transformer model for high-quality text-to-image generation.

    Wraps the Stable Diffusion 3 and 3.5 family of checkpoints from
    Stability AI. These models use a Multimodal Diffusion Transformer (MMDiT)
    architecture that jointly processes text and image tokens, delivering
    significantly improved prompt adherence, typography, and overall image
    quality compared to U-Net-based predecessors.

    Four variants are supported: SD3 Medium (2B), SD3.5 Medium (2B, improved),
    SD3.5 Large (8B, best quality), and SD3.5 Large Turbo (distilled, 4-8
    steps). All produce images natively at 1024 x 1024 px. Access to these
    gated models requires a HuggingFace API key.

    References
    ----------
    - [1] Esser et al., "Scaling Rectified Flow Transformers for
           High-Resolution Image Synthesis", 2024.
           https://arxiv.org/abs/2403.03206
    - [2] https://huggingface.co/stabilityai/stable-diffusion-3-medium-diffusers
    """

    SCHEMA = StableDiffusionSchema
    REQUIRED_CREDENTIALS = ["HuggingFaceCredential"]
    MODEL_NAME: str = ""
    COLOR: str = "#6a1b9a"
    DISPLAY_NAME: str = MultilingualString(
        en="Stable Diffusion V3",
        es="Stable Diffusion V3",
        pt="Stable Diffusion V3",
        de="Stable Diffusion V3",
        zh="Stable Diffusion V3",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Stable Diffusion 3 and 3.5 are next-generation text-to-image models by "
            "Stability AI using a Multimodal Diffusion Transformer (MMDiT) "
            "architecture, offering improved prompt adherence, typography, and image "
            "quality over previous versions. Supports SD3 Medium, SD3.5 Medium, "
            "SD3.5 Large, and SD3.5 Large Turbo variants. A Hugging Face API key is "
            "required to access these gated models. Models are available at "
            "https://huggingface.co/stabilityai."
        ),
        es=(
            "Stable Diffusion 3 y 3.5 son modelos de texto a imagen de nueva "
            "generación de Stability AI que utilizan una arquitectura Multimodal "
            "Diffusion Transformer (MMDiT), ofreciendo mayor fidelidad al prompt, "
            "tipografía y calidad de imagen respecto a versiones anteriores. Soporta "
            "las variantes SD3 Medium, SD3.5 Medium, SD3.5 Large y SD3.5 Large "
            "Turbo. Se requiere una clave API de Hugging Face para acceder a estos "
            "modelos protegidos. Los modelos están disponibles en "
            "https://huggingface.co/stabilityai."
        ),
        pt=(
            "Stable Diffusion 3 e 3.5 são modelos de texto para imagem de nova "
            "geração da Stability AI que utilizam uma arquitetura Multimodal "
            "Diffusion Transformer (MMDiT), oferecendo maior fidelidade ao prompt, "
            "tipografia e qualidade de imagem em relação a versões anteriores. Suporta "
            "as variantes SD3 Medium, SD3.5 Medium, SD3.5 Large e SD3.5 Large "
            "Turbo. Uma chave de API do Hugging Face é necessária para acessar esses "
            "modelos protegidos. Os modelos estão disponíveis em "
            "https://huggingface.co/stabilityai."
        ),
        de=(
            "Stable Diffusion 3 und 3.5 sind Text-zu-Bild-Modelle der nächsten "
            "Generation von Stability AI, die eine Multimodal Diffusion Transformer "
            "(MMDiT)-Architektur verwenden und verbesserte Prompt-Treue, Typografie "
            "und Bildqualität gegenüber früheren Versionen bieten. Unterstützt die "
            "Varianten SD3 Medium, SD3.5 Medium, SD3.5 Large und SD3.5 Large Turbo. "
            "Ein Hugging Face API-Schlüssel ist erforderlich, um auf diese geschützten "
            "Modelle zuzugreifen. Modelle verfügbar unter "
            "https://huggingface.co/stabilityai."
        ),
        zh=(
            "Stable Diffusion 3 和 3.5 是 Stability AI 的新一代文本到图像模型，"
            "采用多模态扩散 Transformer（MMDiT）架构，提升了提示遵循度和图像质量。"
            "需要 Hugging Face API 密钥访问受限模型。"
        ),
    )

    def __init__(self, **kwargs):
        """Initialize the model."""

        import torch
        from diffusers import DiffusionPipeline

        kwargs = self.validate_and_transform(kwargs)
        use_gpu = DEVICE_TO_IDX.get(kwargs.get("device")) >= 0
        self.device = (
            f"cuda:{DEVICE_TO_IDX.get(kwargs.get('device'))}" if use_gpu else "cpu"
        )
        # Log in to HuggingFace using the stored credential so the gated
        # checkpoints can be downloaded.
        self.get_credential("HuggingFaceCredential").apply()

        self.model_name = self._pretrained_source(None)

        try:
            self.model = DiffusionPipeline.from_pretrained(
                self.model_name,
            ).to(self.device)
        except Exception as e:
            raise ValueError(f"Failed to load model {self.model_name}. {e}") from e

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


class StableDiffusion3Medium(StableDiffusion3GenerationModel):
    """Stable Diffusion 3 Medium checkpoint (gated).

    Downloads its checkpoint into the component's own download folder. This is
    a gated Hugging Face repo; downloading requires prior authentication
    (an HF token in the environment).
    """

    MODEL_NAME: str = "stabilityai/stable-diffusion-3-medium-diffusers"
    DOWNLOAD_SIZE_BYTES: int = 31012147557
    DISPLAY_NAME = MultilingualString(
        en="Stable Diffusion 3 Medium",
        es="Stable Diffusion 3 Medium",
        pt="Stable Diffusion 3 Medium",
        de="Stable Diffusion 3 Medium",
        zh="Stable Diffusion 3 Medium",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Stable Diffusion 3 Medium by Stability AI, built on the Multimodal "
            "Diffusion Transformer (MMDiT) architecture with markedly improved text "
            "rendering and prompt adherence over SD2. This is a gated Hugging Face "
            "repo, so downloading requires prior authentication with an access "
            "token. Weights are downloaded into the component's own folder. Model "
            "page: https://huggingface.co/stabilityai/stable-diffusion-3-medium-diffu"
            "sers"
        ),
        es=(
            "Stable Diffusion 3 Medium de Stability AI, construido sobre la "
            "arquitectura Multimodal Diffusion Transformer (MMDiT) con una "
            "representación de texto y adherencia al prompt notablemente mejores "
            "que SD2. Es un repositorio restringido de Hugging Face, por lo que la "
            "descarga requiere autenticación previa con un token de acceso. Los "
            "pesos se descargan en la carpeta propia del componente. Página del "
            "modelo: https://huggingface.co/stabilityai/stable-diffusion-3-medium-dif"
            "fusers"
        ),
        pt=(
            "Stable Diffusion 3 Medium da Stability AI, construído sobre a "
            "arquitetura Multimodal Diffusion Transformer (MMDiT) com renderização "
            "de texto e aderência ao prompt bem melhores que o SD2. É um "
            "repositório restrito do Hugging Face, portanto o download requer "
            "autenticação prévia com um token de acesso. Os pesos são baixados "
            "na pasta própria do componente. Página do modelo: "
            "https://huggingface.co/stabilityai/stable-diffusion-3-medium-diffusers"
        ),
        de=(
            "Stable Diffusion 3 Medium von Stability AI, basierend auf der "
            "Multimodal-Diffusion-Transformer-Architektur (MMDiT) mit deutlich "
            "verbesserter Textwiedergabe und Prompt-Treue gegenüber SD2. Dies ist "
            "ein zugangsbeschränktes Hugging-Face-Repository, daher erfordert der "
            "Download eine vorherige Authentifizierung mit einem Zugriffstoken. Die "
            "Gewichte werden in den eigenen Ordner der Komponente heruntergeladen. "
            "Modellseite: https://huggingface.co/stabilityai/stable-diffusion-3-mediu"
            "m-diffusers"
        ),
        zh=(
            "Stability AI 推出的 Stable Diffusion 3 Medium，基于多模态扩散 "
            "Transformer（MMDiT）架构，相比 SD2 "
            "在文本渲染和提示词遵循方面有显著提升。这是一个受限的 Hugging Face "
            "仓库，因此下载前需要使用访问令牌进行身份验证。权重会下载到该组件自己的文"
            "件夹中。 模型页面： https://huggingface.co/stabilityai/stable-diffusion-"
            "3-medium-diffusers"
        ),
    )


class StableDiffusion35Medium(StableDiffusion3GenerationModel):
    """Stable Diffusion 3.5 Medium checkpoint (gated).

    Downloads its checkpoint into the component's own download folder. This is
    a gated Hugging Face repo; downloading requires prior authentication
    (an HF token in the environment).
    """

    MODEL_NAME: str = "stabilityai/stable-diffusion-3.5-medium"
    DOWNLOAD_SIZE_BYTES: int = 48861581303
    DISPLAY_NAME = MultilingualString(
        en="Stable Diffusion 3.5 Medium",
        es="Stable Diffusion 3.5 Medium",
        pt="Stable Diffusion 3.5 Medium",
        de="Stable Diffusion 3.5 Medium",
        zh="Stable Diffusion 3.5 Medium",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Stable Diffusion 3.5 Medium by Stability AI, an updated MMDiT model "
            "that balances image quality against hardware requirements, running "
            "comfortably on consumer GPUs. This is a gated Hugging Face repo, so "
            "downloading requires prior authentication with an access token. Weights "
            "are downloaded into the component's own folder. Model page: "
            "https://huggingface.co/stabilityai/stable-diffusion-3.5-medium"
        ),
        es=(
            "Stable Diffusion 3.5 Medium de Stability AI, un modelo MMDiT "
            "actualizado que equilibra la calidad de imagen con los requisitos de "
            "hardware y funciona bien en GPUs de consumo. Es un repositorio "
            "restringido de Hugging Face, por lo que la descarga requiere "
            "autenticación previa con un token de acceso. Los pesos se descargan en "
            "la carpeta propia del componente. Página del modelo: "
            "https://huggingface.co/stabilityai/stable-diffusion-3.5-medium"
        ),
        pt=(
            "Stable Diffusion 3.5 Medium da Stability AI, um modelo MMDiT atualizado "
            "que equilibra a qualidade da imagem com os requisitos de hardware e "
            "roda bem em GPUs de consumo. É um repositório restrito do Hugging "
            "Face, portanto o download requer autenticação prévia com um token de "
            "acesso. Os pesos são baixados na pasta própria do componente. Página "
            "do modelo: https://huggingface.co/stabilityai/stable-diffusion-3.5-mediu"
            "m"
        ),
        de=(
            "Stable Diffusion 3.5 Medium von Stability AI, ein aktualisiertes "
            "MMDiT-Modell, das Bildqualität und Hardwareanforderungen ausbalanciert "
            "und komfortabel auf Consumer-GPUs läuft. Dies ist ein "
            "zugangsbeschränktes Hugging-Face-Repository, daher erfordert der "
            "Download eine vorherige Authentifizierung mit einem Zugriffstoken. Die "
            "Gewichte werden in den eigenen Ordner der Komponente heruntergeladen. "
            "Modellseite: https://huggingface.co/stabilityai/stable-diffusion-3.5-med"
            "ium"
        ),
        zh=(
            "Stability AI 推出的 Stable Diffusion 3.5 Medium，是更新的 MMDiT "
            "模型，在图像质量与硬件需求之间取得平衡，可在消费级 GPU "
            "上流畅运行。这是一个受限的 Hugging Face "
            "仓库，因此下载前需要使用访问令牌进行身份验证。权重会下载到该组件自己的文"
            "件夹中。 模型页面： https://huggingface.co/stabilityai/stable-diffusion-"
            "3.5-medium"
        ),
    )


class StableDiffusion35Large(StableDiffusion3GenerationModel):
    """Stable Diffusion 3.5 Large checkpoint (gated).

    Downloads its checkpoint into the component's own download folder. This is
    a gated Hugging Face repo; downloading requires prior authentication
    (an HF token in the environment).
    """

    MODEL_NAME: str = "stabilityai/stable-diffusion-3.5-large"
    DOWNLOAD_SIZE_BYTES: int = 71585723216
    DISPLAY_NAME = MultilingualString(
        en="Stable Diffusion 3.5 Large",
        es="Stable Diffusion 3.5 Large",
        pt="Stable Diffusion 3.5 Large",
        de="Stable Diffusion 3.5 Large",
        zh="Stable Diffusion 3.5 Large",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Stable Diffusion 3.5 Large by Stability AI, the highest quality MMDiT "
            "model in the 3.5 family, offering the strongest detail and prompt "
            "adherence at the cost of more memory and slower generation. This is a "
            "gated Hugging Face repo, so downloading requires prior authentication "
            "with an access token. Weights are downloaded into the component's own "
            "folder. Model page: https://huggingface.co/stabilityai/stable-diffusion-"
            "3.5-large"
        ),
        es=(
            "Stable Diffusion 3.5 Large de Stability AI, el modelo MMDiT de mayor "
            "calidad de la familia 3.5, con el mejor detalle y adherencia al prompt "
            "a costa de más memoria y una generación más lenta. Es un repositorio "
            "restringido de Hugging Face, por lo que la descarga requiere "
            "autenticación previa con un token de acceso. Los pesos se descargan en "
            "la carpeta propia del componente. Página del modelo: "
            "https://huggingface.co/stabilityai/stable-diffusion-3.5-large"
        ),
        pt=(
            "Stable Diffusion 3.5 Large da Stability AI, o modelo MMDiT de maior "
            "qualidade da família 3.5, oferecendo o melhor detalhe e aderência ao "
            "prompt ao custo de mais memória e geração mais lenta. É um "
            "repositório restrito do Hugging Face, portanto o download requer "
            "autenticação prévia com um token de acesso. Os pesos são baixados "
            "na pasta própria do componente. Página do modelo: "
            "https://huggingface.co/stabilityai/stable-diffusion-3.5-large"
        ),
        de=(
            "Stable Diffusion 3.5 Large von Stability AI, das qualitativ "
            "hochwertigste MMDiT-Modell der 3.5-Familie, das beste Detailtreue und "
            "Prompt-Treue bietet, allerdings auf Kosten von mehr Speicher und "
            "langsamerer Generierung. Dies ist ein zugangsbeschränktes "
            "Hugging-Face-Repository, daher erfordert der Download eine vorherige "
            "Authentifizierung mit einem Zugriffstoken. Die Gewichte werden in den "
            "eigenen Ordner der Komponente heruntergeladen. Modellseite: "
            "https://huggingface.co/stabilityai/stable-diffusion-3.5-large"
        ),
        zh=(
            "Stability AI 推出的 Stable Diffusion 3.5 Large，是 3.5 系列中质量最高的 "
            "MMDiT 模型，提供最强的细节和提示词遵循能力，代价是更高的显存占用和更慢的"
            "生成速度。这是一个受限的 Hugging Face "
            "仓库，因此下载前需要使用访问令牌进行身份验证。权重会下载到该组件自己的文"
            "件夹中。 模型页面： https://huggingface.co/stabilityai/stable-diffusion-"
            "3.5-large"
        ),
    )


class StableDiffusion35LargeTurbo(StableDiffusion3GenerationModel):
    """Stable Diffusion 3.5 Large Turbo checkpoint (gated).

    Downloads its checkpoint into the component's own download folder. This is
    a gated Hugging Face repo; downloading requires prior authentication
    (an HF token in the environment).
    """

    MODEL_NAME: str = "stabilityai/stable-diffusion-3.5-large-turbo"
    DOWNLOAD_SIZE_BYTES: int = 71582971259
    DISPLAY_NAME = MultilingualString(
        en="Stable Diffusion 3.5 Large Turbo",
        es="Stable Diffusion 3.5 Large Turbo",
        pt="Stable Diffusion 3.5 Large Turbo",
        de="Stable Diffusion 3.5 Large Turbo",
        zh="Stable Diffusion 3.5 Large Turbo",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Stable Diffusion 3.5 Large Turbo by Stability AI, a distilled version "
            "of 3.5 Large that produces high quality images in only a handful of "
            "denoising steps for much faster generation. This is a gated Hugging "
            "Face repo, so downloading requires prior authentication with an access "
            "token. Weights are downloaded into the component's own folder. Model "
            "page: https://huggingface.co/stabilityai/stable-diffusion-3.5-large-turb"
            "o"
        ),
        es=(
            "Stable Diffusion 3.5 Large Turbo de Stability AI, una versión "
            "destilada de 3.5 Large que produce imágenes de alta calidad en apenas "
            "unos pocos pasos de denoising para una generación mucho más rápida. "
            "Es un repositorio restringido de Hugging Face, por lo que la descarga "
            "requiere autenticación previa con un token de acceso. Los pesos se "
            "descargan en la carpeta propia del componente. Página del modelo: "
            "https://huggingface.co/stabilityai/stable-diffusion-3.5-large-turbo"
        ),
        pt=(
            "Stable Diffusion 3.5 Large Turbo da Stability AI, uma versão destilada "
            "do 3.5 Large que produz imagens de alta qualidade em apenas alguns "
            "passos de denoising para uma geração muito mais rápida. É um "
            "repositório restrito do Hugging Face, portanto o download requer "
            "autenticação prévia com um token de acesso. Os pesos são baixados "
            "na pasta própria do componente. Página do modelo: "
            "https://huggingface.co/stabilityai/stable-diffusion-3.5-large-turbo"
        ),
        de=(
            "Stable Diffusion 3.5 Large Turbo von Stability AI, eine destillierte "
            "Version von 3.5 Large, die hochwertige Bilder in nur wenigen "
            "Entrauschungsschritten für eine deutlich schnellere Generierung "
            "erzeugt. Dies ist ein zugangsbeschränktes Hugging-Face-Repository, "
            "daher erfordert der Download eine vorherige Authentifizierung mit einem "
            "Zugriffstoken. Die Gewichte werden in den eigenen Ordner der Komponente "
            "heruntergeladen. Modellseite: https://huggingface.co/stabilityai/stable-"
            "diffusion-3.5-large-turbo"
        ),
        zh=(
            "Stability AI 推出的 Stable Diffusion 3.5 Large Turbo，是 3.5 Large "
            "的蒸馏版本，仅需少数几个去噪步骤即可生成高质量图像，从而大幅加快生成速度"
            "。这是一个受限的 Hugging Face "
            "仓库，因此下载前需要使用访问令牌进行身份验证。权重会下载到该组件自己的文"
            "件夹中。 模型页面： https://huggingface.co/stabilityai/stable-diffusion-"
            "3.5-large-turbo"
        ),
    )
