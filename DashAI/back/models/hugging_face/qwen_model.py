"""Qwen 2.5 Instruct GGUF checkpoint subclasses for DashAI."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.gguf_text_generation_base import (
    GGUFTextGenerationModel,
    GGUFTextGenerationSchema,
)


class Qwen25_05BInstruct(GGUFTextGenerationModel):  # noqa: N801
    """Qwen 2.5 0.5B Instruct GGUF checkpoint (Q8_0 quantization).

    A compact 500M-parameter instruction-tuned model from Alibaba Cloud,
    well suited for lightweight CPU inference. Weights are stored locally
    after a one-time download from HuggingFace.

    References
    ----------
    - Qwen Team (2024). "Qwen2.5 Technical Report."
      https://arxiv.org/abs/2412.15115
    - https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF
    """

    REPO_ID = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
    GGUF_PATTERN = "*8_0.gguf"
    DOWNLOAD_SIZE_BYTES = 675710816
    SCHEMA = GGUFTextGenerationSchema
    COLOR: str = "#2e7d32"
    DISPLAY_NAME = MultilingualString(
        en="Qwen2.5 0.5B Instruct",
        es="Qwen2.5 0.5B Instruct",
        pt="Qwen2.5 0.5B Instruct",
        de="Qwen2.5 0.5B Instruct",
        zh="Qwen2.5 0.5B Instruct",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Qwen 2.5 0.5B Instruct is a 500M-parameter instruction-tuned "
            "language model by Alibaba Cloud, loaded as a Q8_0 GGUF for "
            "efficient CPU inference. It is the fastest and most "
            "memory-efficient Qwen 2.5 variant in DashAI, ideal for rapid "
            "prototyping or devices with limited RAM. Model available at "
            "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF."
        ),
        es=(
            "Qwen 2.5 0.5B Instruct es un modelo de 500M parámetros ajustado "
            "para instrucciones por Alibaba Cloud, cargado como GGUF Q8_0 "
            "para inferencia eficiente en CPU. Es la variante Qwen 2.5 más "
            "rápida y con menor uso de memoria en DashAI, ideal para "
            "prototipado rápido o dispositivos con RAM limitada."
        ),
        pt=(
            "Qwen 2.5 0.5B Instruct é um modelo de 500M parâmetros ajustado "
            "para instruções pela Alibaba Cloud, carregado como GGUF Q8_0 "
            "para inferência eficiente em CPU. É a variante Qwen 2.5 mais "
            "rápida e com menor uso de memória no DashAI, ideal para "
            "prototipagem rápida ou dispositivos com RAM limitada."
        ),
        de=(
            "Qwen 2.5 0.5B Instruct ist ein 500M-Parameter-Instruktionsmodell "
            "von Alibaba Cloud, als Q8_0-GGUF für effiziente CPU-Inferenz "
            "geladen. Es ist die schnellste und speichereffizienteste "
            "Qwen-2.5-Variante in DashAI, ideal für schnelles Prototyping "
            "oder Geräte mit begrenztem RAM."
        ),
        zh=(
            "Qwen 2.5 0.5B Instruct 是阿里云推出的 5 亿参数指令微调语言模型，"
            "以 Q8_0 GGUF 格式加载，支持高效 CPU 推理。"
            "这是 DashAI 中速度最快、内存占用最低的 Qwen 2.5 变体，"
            "非常适合快速原型开发或内存受限的设备。"
        ),
    )


class Qwen25_15BInstruct(GGUFTextGenerationModel):  # noqa: N801
    """Qwen 2.5 1.5B Instruct GGUF checkpoint (Q8_0 quantization).

    A 1.5B-parameter instruction-tuned model from Alibaba Cloud that offers
    higher response quality than the 0.5B variant while still running on CPU.
    Weights are stored locally after a one-time download from HuggingFace.

    References
    ----------
    - Qwen Team (2024). "Qwen2.5 Technical Report."
      https://arxiv.org/abs/2412.15115
    - https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF
    """

    REPO_ID = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
    GGUF_PATTERN = "*8_0.gguf"
    DOWNLOAD_SIZE_BYTES = 1894532128
    SCHEMA = GGUFTextGenerationSchema
    COLOR: str = "#2e7d32"
    DISPLAY_NAME = MultilingualString(
        en="Qwen2.5 1.5B Instruct",
        es="Qwen2.5 1.5B Instruct",
        pt="Qwen2.5 1.5B Instruct",
        de="Qwen2.5 1.5B Instruct",
        zh="Qwen2.5 1.5B Instruct",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Qwen 2.5 1.5B Instruct is a 1.5B-parameter instruction-tuned "
            "language model by Alibaba Cloud, loaded as a Q8_0 GGUF for "
            "efficient CPU inference. It provides stronger reasoning and "
            "generation quality than the 0.5B variant at the cost of slightly "
            "more memory. Model available at "
            "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF."
        ),
        es=(
            "Qwen 2.5 1.5B Instruct es un modelo de 1.5B parámetros ajustado "
            "para instrucciones por Alibaba Cloud, cargado como GGUF Q8_0 "
            "para inferencia eficiente en CPU. Ofrece mayor capacidad de "
            "razonamiento y calidad de generación que la variante de 0.5B a "
            "costa de un poco más de memoria."
        ),
        pt=(
            "Qwen 2.5 1.5B Instruct é um modelo de 1.5B parâmetros ajustado "
            "para instruções pela Alibaba Cloud, carregado como GGUF Q8_0 "
            "para inferência eficiente em CPU. Oferece melhor raciocínio e "
            "qualidade de geração que a variante de 0.5B ao custo de um pouco "
            "mais de memória."
        ),
        de=(
            "Qwen 2.5 1.5B Instruct ist ein 1,5B-Parameter-Instruktionsmodell "
            "von Alibaba Cloud, als Q8_0-GGUF für effiziente CPU-Inferenz "
            "geladen. Es bietet besseres Schlussfolgern und "
            "Generierungsqualität als die 0,5B-Variante, benötigt jedoch "
            "etwas mehr Speicher."
        ),
        zh=(
            "Qwen 2.5 1.5B Instruct 是阿里云推出的 15 亿参数指令微调语言模型，"
            "以 Q8_0 GGUF 格式加载，支持高效 CPU 推理。"
            "与 0.5B 变体相比，它具有更强的推理能力和生成质量，但需要稍多的内存。"
        ),
    )
