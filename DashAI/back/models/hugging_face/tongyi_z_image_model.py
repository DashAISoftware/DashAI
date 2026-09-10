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


class TongyiZImageSchema(BaseSchema):
    """Configuration schema for Tongyi Z-Image text-to-image generation.

    Configures the checkpoint variant (``model_name``), prompt conditioning
    (``negative_prompt``), denoising schedule (``num_inference_steps``),
    classifier free guidance strength (``guidance_scale``), output dimensions
    (``width``, ``height``), reproducibility (``seed``), hardware target
    (``device``), and batch size (``num_images_per_prompt``) for
    ``TongyiZImageModel``.
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
                    "描述需从生成图像中排除内容的文本。"
                    "常用值：'模糊、低质量、失真、水印'。"
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
        placeholder=20,
        description=MultilingualString(
            en=(
                "Number of denoising steps. Tongyi Z-Image achieves high quality "
                "results with 20-30 steps. More steps refine detail at the cost "
                "of generation time."
            ),
            es=(
                "Número de pasos de eliminación de ruido. Tongyi Z-Image logra "
                "resultados de alta calidad con 20-30 pasos. Más pasos refinan "
                "el detalle a costa de tiempo de generación."
            ),
            pt=(
                "Número de etapas de inferência. Tongyi Z-Image atinge resultados "
                "de alta qualidade com 20-30 etapas. Mais etapas refinam o detalhe "
                "ao custo do tempo de geração."
            ),
            de=(
                "Anzahl der Entrauschungsschritte. Tongyi Z-Image erzielt mit "
                "20-30 Schritten hochwertige Ergebnisse. Mehr Schritte verfeinern "
                "Details auf Kosten der Generierungszeit."
            ),
            zh=(
                "去噪步数。Tongyi Z-Image 在 20-30 步时可达到高质量效果。"
                "步数越多细节越精细，但生成时间也越长。"
            ),
        ),
        alias=MultilingualString(
            en="Num inference steps",
            es="Número de pasos de inferencia",
            pt="Número de etapas de inferência",
            de="Anzahl Inferenzschritte",
            zh="推理步数",
        ),
    )  # type: ignore

    guidance_scale: schema_field(
        float_field(ge=0.0),
        placeholder=5.0,
        description=MultilingualString(
            en=(
                "Classifier-Free Guidance (CFG) scale. Controls how strictly the "
                "image follows the text prompt. Values 4-7 work well for "
                "Tongyi Z-Image."
            ),
            es=(
                "Escala de Classifier-Free Guidance (CFG). Controla qué tan "
                "estrictamente la imagen sigue el prompt. Valores 4-7 funcionan "
                "bien para Tongyi Z-Image."
            ),
            pt=(
                "Escala de Classifier-Free Guidance (CFG). Controla o quão "
                "estritamente a imagem segue o prompt. Valores entre 4-7 funcionam "
                "bem para o Tongyi Z-Image."
            ),
            de=(
                "Classifier-Free Guidance (CFG)-Skala. Steuert, wie streng das Bild "
                "dem Prompt folgt. Werte 4-7 funktionieren gut für Tongyi Z-Image."
            ),
            zh=(
                "无分类器引导（CFG）比例。控制图像与文本提示的匹配程度。"
                "对 Tongyi Z-Image 而言，4-7 的值效果较好。"
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
                "Hardware device for inference. GPU is strongly recommended for "
                "this 6B parameter model. CPU inference is possible but very slow."
            ),
            es=(
                "Dispositivo de hardware para inferencia. Se recomienda GPU para "
                "este modelo de 6B parámetros. La inferencia en CPU es posible "
                "pero muy lenta."
            ),
            pt=(
                "Dispositivo de hardware para inferência. GPU é fortemente "
                "recomendada para este modelo de 6B parâmetros. A inferência em "
                "CPU é possível, mas muito lenta."
            ),
            de=(
                "Hardware-Gerät für die Inferenz. GPU wird für dieses "
                "6B-Parameter-Modell "
                "dringend empfohlen. CPU-Inferenz ist möglich, aber sehr langsam."
            ),
            zh=(
                "推理所用的硬件设备。对于此 60 亿参数模型，强烈建议使用 GPU。"
                "CPU 推理可行，但速度极慢。"
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
                "always produces the same image. Use -1 for a random seed."
            ),
            es=(
                "Semilla aleatoria para generación reproducible. Un entero positivo "
                "fijo siempre produce la misma imagen. Use -1 para semilla aleatoria."
            ),
            pt=(
                "Semente aleatória para geração reproduzível. Um inteiro positivo "
                "fixo sempre produz a mesma imagem. Use -1 para uma semente aleatória."
            ),
            de=(
                "Zufalls-Seed für reproduzierbare Generierung. Ein fester positiver "
                "Integer erzeugt stets dasselbe Bild. Verwenden Sie -1 für einen "
                "zufälligen Seed."
            ),
            zh=(
                "用于可复现生成的随机种子。固定的正整数始终生成相同图像。"
                "使用 -1 表示随机种子。"
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
                "Tongyi Z-Image natively targets 1024x1024 px."
            ),
            es=(
                "Ancho de la imagen en píxeles. Debe ser múltiplo de 8. "
                "Tongyi Z-Image apunta nativamente a 1024x1024 px."
            ),
            pt=(
                "Largura da imagem em pixels. Deve ser múltiplo de 8. "
                "Tongyi Z-Image tem como alvo nativo 1024x1024 px."
            ),
            de=(
                "Breite des Ausgabebildes in Pixeln. Muss ein Vielfaches von 8 sein. "
                "Tongyi Z-Image zielt nativ auf 1024x1024 px ab."
            ),
            zh=(
                "输出图像的宽度（像素）。必须是 8 的倍数。"
                "Tongyi Z-Image 原生目标分辨率为 1024x1024 px。"
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
                "Tongyi Z-Image natively targets 1024x1024 px."
            ),
            es=(
                "Altura de la imagen en píxeles. Debe ser múltiplo de 8. "
                "Tongyi Z-Image apunta nativamente a 1024x1024 px."
            ),
            pt=(
                "Altura da imagem em pixels. Deve ser múltiplo de 8. "
                "Tongyi Z-Image tem como alvo nativo 1024x1024 px."
            ),
            de=(
                "Höhe des Ausgabebildes in Pixeln. Muss ein Vielfaches von 8 sein. "
                "Tongyi Z-Image zielt nativ auf 1024x1024 px ab."
            ),
            zh=(
                "输出图像的高度（像素）。必须是 8 的倍数。"
                "Tongyi Z-Image 原生目标分辨率为 1024x1024 px。"
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
                "Requires proportionally more GPU memory per additional image."
            ),
            es=(
                "Cuántas imágenes generar desde un solo prompt en un lote. "
                "Requiere proporcionalmente más memoria GPU por imagen adicional."
            ),
            pt=(
                "Quantas imagens gerar a partir de um único prompt em um lote. "
                "Requer proporcionalmente mais memória GPU por imagem adicional."
            ),
            de=(
                "Anzahl der Bilder, die aus einem einzelnen Prompt in einem Batch "
                "generiert werden. Erfordert proportional mehr GPU-Speicher pro "
                "zusätzlichem Bild."
            ),
            zh=(
                "每个提示词在一批次中生成的图像数量。"
                "每增加一张图像，所需 GPU 显存按比例增加。"
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


class TongyiZImageGenerationModel(
    HFPretrainedDownloadMixin, TextToImageGenerationTaskModel
):
    """Tongyi Z-Image S3-DiT model for high quality text-to-image generation.

    Wraps Alibaba's 6B parameter Tongyi Z-Image pipeline. The model uses a
    novel Sparse Spatial-Spectral Diffusion Transformer (S3-DiT) architecture
    that processes image tokens in both spatial and spectral domains for
    efficient high fidelity generation. It outperforms previous open source
    state of the art models while being more parameter efficient, and excels
    at photorealism, diverse artistic styles, and accurate text rendering.

    References
    ----------
    - [1] https://huggingface.co/Tongyi-MAI/Z-Image
    """

    SCHEMA = TongyiZImageSchema
    MODEL_NAME: str = ""
    COLOR: str = "#e65100"
    DISPLAY_NAME: str = MultilingualString(
        en="Tongyi Z-Image",
        es="Tongyi Z-Image",
        pt="Tongyi Z-Image",
        zh="通义 Z-Image",
        de="Tongyi Z-Image",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Tongyi Z-Image is Alibaba's 6B parameter text-to-image model using a "
            "novel S3-DiT (Sparse Spatial-Spectral Diffusion Transformer) "
            "architecture. It is currently one of the most downloaded models on "
            "Hugging Face and "
            "outperforms previous open source state of the art models at a fraction "
            "of their size. Excels at photorealistic image generation, diverse styles, "
            "and accurate text rendering. Model available at "
            "https://huggingface.co/Tongyi-AI/Tongyi-Z-Image."
        ),
        es=(
            "Tongyi Z-Image es el modelo de texto a imagen de 6B parámetros de "
            "Alibaba que utiliza una novedosa arquitectura S3-DiT (Sparse "
            "Spatial-Spectral Diffusion Transformer). Es actualmente uno de los "
            "modelos más descargados en Hugging Face y supera a modelos de última "
            "generación anteriores con una fracción de su tamaño. Destaca en "
            "generación fotorrealista, estilos diversos y renderizado preciso de "
            "texto. Modelo disponible en "
            "https://huggingface.co/Tongyi-AI/Tongyi-Z-Image."
        ),
        pt=(
            "Tongyi Z-Image é o modelo de texto para imagem de 6B parâmetros da "
            "Alibaba que utiliza uma nova arquitetura S3-DiT (Sparse "
            "Spatial-Spectral Diffusion Transformer). É atualmente um dos "
            "modelos mais baixados no Hugging Face e supera modelos anteriores "
            "de última geração com uma fração do seu tamanho. Destaca-se em "
            "geração fotorrealista de imagens, estilos diversos e renderização "
            "precisa de texto. Modelo disponível em "
            "https://huggingface.co/Tongyi-AI/Tongyi-Z-Image."
        ),
        zh=(
            "通义 Z-Image 是阿里巴巴的 60 亿参数文本到图像模型，"
            "采用创新的 S3-DiT 架构，擅长真实感图像生成、多样风格和精确文字渲染。"
        ),
        de=(
            "Tongyi Z-Image ist Alibabas 6B-Parameter-Text-zu-Bild-Modell mit "
            "einer neuartigen S3-DiT-Architektur (Sparse Spatial-Spectral "
            "Diffusion Transformer). Es ist derzeit eines der am häufigsten "
            "heruntergeladenen Modelle auf Hugging Face und übertrifft frühere "
            "Open-Source-Modelle auf dem neuesten Stand bei einem Bruchteil ihrer "
            "Größe. Hervorragend für fotorealistische Bildgenerierung, diverse "
            "Stile und genaues Text-Rendering. Modell verfügbar unter "
            "https://huggingface.co/Tongyi-AI/Tongyi-Z-Image."
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

        self.model = DiffusionPipeline.from_pretrained(
            self._pretrained_source(None),
            torch_dtype=torch.float16 if use_gpu else torch.float32,
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

        output = self.model(
            prompt=input,
            negative_prompt=self.negative_prompt,
            num_inference_steps=self.num_inference_steps,
            guidance_scale=self.guidance_scale,
            width=self.width,
            height=self.height,
            generator=generator,
            num_images_per_prompt=self.num_images_per_prompt,
        )
        return output.images


class TongyiZImage(TongyiZImageGenerationModel):
    """Tongyi Z-Image text-to-image checkpoint.

    Downloads its checkpoint into the component's own download folder.
    """

    MODEL_NAME: str = "Tongyi-MAI/Z-Image"
    DOWNLOAD_SIZE_BYTES: int = 20547479575
    DISPLAY_NAME = MultilingualString(
        en="Tongyi Z-Image",
        es="Tongyi Z-Image",
        pt="Tongyi Z-Image",
        de="Tongyi Z-Image",
        zh="Tongyi Z-Image",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Z-Image by Alibaba's Tongyi lab, a modern text-to-image diffusion model "
            "with strong prompt following and multilingual support. This is the "
            "standard, full-quality checkpoint. Weights are downloaded into the "
            "component's own folder. Model page: https://huggingface.co/Tongyi-MAI/Z-"
            "Image"
        ),
        es=(
            "Z-Image del laboratorio Tongyi de Alibaba, un modelo moderno de "
            "difusión de texto a imagen con buen seguimiento de prompts y soporte "
            "multilingüe. Este es el checkpoint estándar de máxima calidad. Los "
            "pesos se descargan en la carpeta propia del componente. Página del "
            "modelo: https://huggingface.co/Tongyi-MAI/Z-Image"
        ),
        pt=(
            "Z-Image do laboratório Tongyi da Alibaba, um modelo moderno de "
            "difusão de texto para imagem com bom seguimento de prompts e suporte "
            "multilíngue. Este é o checkpoint padrão de qualidade máxima. Os "
            "pesos são baixados na pasta própria do componente. Página do modelo: "
            "https://huggingface.co/Tongyi-MAI/Z-Image"
        ),
        de=(
            "Z-Image aus Alibabas Tongyi-Labor, ein modernes "
            "Text-zu-Bild-Diffusionsmodell mit guter Prompt-Befolgung und "
            "mehrsprachiger Unterstützung. Dies ist der standardmäßige Checkpoint "
            "in voller Qualität. Die Gewichte werden in den eigenen Ordner der "
            "Komponente heruntergeladen. Modellseite: "
            "https://huggingface.co/Tongyi-MAI/Z-Image"
        ),
        zh=(
            "阿里巴巴通义实验室推出的 Z-Image，是一种现代文本到图像扩散模型，具有出色"
            "的提示词遵循能力和多语言支持。这是标准的全质量检查点。权重会下载到该组件"
            "自己的文件夹中。 模型页面： https://huggingface.co/Tongyi-MAI/Z-Image"
        ),
    )


class TongyiZImageTurbo(TongyiZImageGenerationModel):
    """Tongyi Z-Image Turbo fast checkpoint.

    Downloads its checkpoint into the component's own download folder.
    """

    MODEL_NAME: str = "Tongyi-MAI/Z-Image-Turbo"
    DOWNLOAD_SIZE_BYTES: int = 32899667397
    DISPLAY_NAME = MultilingualString(
        en="Tongyi Z-Image Turbo",
        es="Tongyi Z-Image Turbo",
        pt="Tongyi Z-Image Turbo",
        de="Tongyi Z-Image Turbo",
        zh="Tongyi Z-Image Turbo",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Z-Image Turbo by Alibaba's Tongyi lab, a distilled variant of Z-Image "
            "that generates images in far fewer denoising steps. It trades a little "
            "quality for much faster generation. Weights are downloaded into the "
            "component's own folder. Model page: https://huggingface.co/Tongyi-MAI/Z-"
            "Image-Turbo"
        ),
        es=(
            "Z-Image Turbo del laboratorio Tongyi de Alibaba, una variante destilada "
            "de Z-Image que genera imágenes en muchos menos pasos de denoising. "
            "Sacrifica algo de calidad a cambio de una generación mucho más "
            "rápida. Los pesos se descargan en la carpeta propia del componente. "
            "Página del modelo: https://huggingface.co/Tongyi-MAI/Z-Image-Turbo"
        ),
        pt=(
            "Z-Image Turbo do laboratório Tongyi da Alibaba, uma variante destilada "
            "do Z-Image que gera imagens em muito menos passos de denoising. Troca "
            "um pouco de qualidade por uma geração muito mais rápida. Os pesos "
            "são baixados na pasta própria do componente. Página do modelo: "
            "https://huggingface.co/Tongyi-MAI/Z-Image-Turbo"
        ),
        de=(
            "Z-Image Turbo aus Alibabas Tongyi-Labor, eine destillierte Variante von "
            "Z-Image, die Bilder in weit weniger Entrauschungsschritten erzeugt. Sie "
            "opfert etwas Qualität für eine deutlich schnellere Generierung. Die "
            "Gewichte werden in den eigenen Ordner der Komponente heruntergeladen. "
            "Modellseite: https://huggingface.co/Tongyi-MAI/Z-Image-Turbo"
        ),
        zh=(
            "阿里巴巴通义实验室推出的 Z-Image Turbo，是 Z-Image "
            "的蒸馏变体，可用更少的去噪步骤生成图像。以少量质量换取快得多的生成速度。"
            "权重会下载到该组件自己的文件夹中。 模型页面： https://huggingface.co/Ton"
            "gyi-MAI/Z-Image-Turbo"
        ),
    )
