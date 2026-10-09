"""SmolLM2 Instruct GGUF checkpoint subclasses for DashAI."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.gguf_text_generation_base import (
    GGUFTextGenerationModel,
    GGUFTextGenerationSchema,
)


class SmolLM2_360MInstruct(GGUFTextGenerationModel):  # noqa: N801
    """SmolLM2 360M Instruct GGUF checkpoint (Q8_0 quantization).

    A very small 360M-parameter instruction-tuned model from HuggingFace,
    designed for fast on-device inference. Weights are stored locally after a
    one-time download from HuggingFace.

    References
    ----------
    - https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct-GGUF
    """

    REPO_ID = "HuggingFaceTB/SmolLM2-360M-Instruct-GGUF"
    GGUF_PATTERN = "*q8_0.gguf"
    DOWNLOAD_SIZE_BYTES = 386404992
    SCHEMA = GGUFTextGenerationSchema
    COLOR: str = "#00695c"
    DISPLAY_NAME = MultilingualString(
        en="SmolLM2 360M Instruct",
        es="SmolLM2 360M Instruct",
        pt="SmolLM2 360M Instruct",
        de="SmolLM2 360M Instruct",
        zh="SmolLM2 360M Instruct",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "SmolLM2 360M Instruct is a compact 360M-parameter instruction-tuned "
            "language model from HuggingFace, loaded as a Q8_0 GGUF for very fast "
            "CPU inference. It is the lightest text-generation model in DashAI, "
            "ideal for constrained devices. Model available at "
            "https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct-GGUF."
        ),
        es=(
            "SmolLM2 360M Instruct es un modelo de lenguaje compacto de 360M "
            "parametros ajustado para instrucciones por HuggingFace, cargado como "
            "GGUF Q8_0 para inferencia muy rapida en CPU. Es el modelo de generacion "
            "de texto mas ligero de DashAI, ideal para dispositivos limitados."
        ),
        pt=(
            "SmolLM2 360M Instruct e um modelo de linguagem compacto de 360M "
            "parametros ajustado para instrucoes pela HuggingFace, carregado como "
            "GGUF Q8_0 para inferencia muito rapida em CPU. E o modelo de geracao de "
            "texto mais leve do DashAI, ideal para dispositivos limitados."
        ),
        de=(
            "SmolLM2 360M Instruct ist ein kompaktes 360M-Parameter-Instruktionsmodell "
            "von HuggingFace, als Q8_0-GGUF fuer sehr schnelle CPU-Inferenz geladen. "
            "Es ist das leichteste Textgenerierungsmodell in DashAI, ideal fuer "
            "eingeschraenkte Geraete."
        ),
        zh=(
            "SmolLM2 360M Instruct 是 HuggingFace 推出的 3.6 亿参数指令微调语言模型，"
            "以 Q8_0 GGUF 格式加载，支持极快的 CPU 推理。"
            "这是 DashAI 中最轻量的文本生成模型，非常适合资源受限的设备。"
        ),
    )


class SmolLM2_17BInstruct(GGUFTextGenerationModel):  # noqa: N801
    """SmolLM2 1.7B Instruct GGUF checkpoint (Q4_K_M quantization).

    A 1.7B-parameter instruction-tuned model from HuggingFace offering stronger
    generation quality than the 360M variant. Weights are stored locally after a
    one-time download from HuggingFace.

    References
    ----------
    - https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF
    """

    REPO_ID = "HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF"
    GGUF_PATTERN = "*q4_k_m.gguf"
    DOWNLOAD_SIZE_BYTES = 1055609536
    SCHEMA = GGUFTextGenerationSchema
    COLOR: str = "#00695c"
    DISPLAY_NAME = MultilingualString(
        en="SmolLM2 1.7B Instruct",
        es="SmolLM2 1.7B Instruct",
        pt="SmolLM2 1.7B Instruct",
        de="SmolLM2 1.7B Instruct",
        zh="SmolLM2 1.7B Instruct",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "SmolLM2 1.7B Instruct is a 1.7B-parameter instruction-tuned language "
            "model from HuggingFace, loaded as a Q4_K_M GGUF for efficient CPU "
            "inference. It provides better reasoning and generation quality than the "
            "360M variant. Model available at "
            "https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF."
        ),
        es=(
            "SmolLM2 1.7B Instruct es un modelo de lenguaje de 1.7B parametros "
            "ajustado para instrucciones por HuggingFace, cargado como GGUF Q4_K_M "
            "para inferencia eficiente en CPU. Ofrece mejor razonamiento y calidad de "
            "generacion que la variante de 360M."
        ),
        pt=(
            "SmolLM2 1.7B Instruct e um modelo de linguagem de 1.7B parametros "
            "ajustado para instrucoes pela HuggingFace, carregado como GGUF Q4_K_M "
            "para inferencia eficiente em CPU. Oferece melhor raciocinio e qualidade "
            "de geracao do que a variante de 360M."
        ),
        de=(
            "SmolLM2 1.7B Instruct ist ein 1,7B-Parameter-Instruktionsmodell von "
            "HuggingFace, als Q4_K_M-GGUF fuer effiziente CPU-Inferenz geladen. "
            "Es bietet besseres Schlussfolgern und Generierungsqualitaet als die "
            "360M-Variante."
        ),
        zh=(
            "SmolLM2 1.7B Instruct 是 HuggingFace 推出的 17 亿参数指令微调语言模型，"
            "以 Q4_K_M GGUF 格式加载，支持高效 CPU 推理。"
            "与 360M 变体相比，它具有更强的推理能力和生成质量。"
        ),
    )
