"""Llama 3.x Instruct GGUF checkpoint subclasses for DashAI."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.gguf_text_generation_base import (
    GGUFTextGenerationModel,
    GGUFTextGenerationSchema,
)


class Llama31_8BInstruct(GGUFTextGenerationModel):  # noqa: N801
    """Meta Llama 3.1 8B Instruct GGUF checkpoint (Q4_K_M quantization).

    An 8B-parameter instruction-tuned model from Meta with strong general
    reasoning and multilingual ability. Weights are stored locally after a
    one-time download from HuggingFace.

    References
    ----------
    - https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF
    """

    REPO_ID = "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"
    GGUF_PATTERN = "*Q4_K_M.gguf"
    DOWNLOAD_SIZE_BYTES = 4920739232
    SCHEMA = GGUFTextGenerationSchema
    COLOR: str = "#1a237e"
    DISPLAY_NAME = MultilingualString(
        en="Llama 3.1 8B Instruct",
        es="Llama 3.1 8B Instruct",
        pt="Llama 3.1 8B Instruct",
        de="Llama 3.1 8B Instruct",
        zh="Llama 3.1 8B Instruct",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Meta Llama 3.1 8B Instruct is an 8B-parameter instruction-tuned language "
            "model, loaded as a Q4_K_M GGUF for efficient CPU or GPU inference. It "
            "offers strong reasoning, coding, and multilingual capabilities. This is "
            "the largest text-generation model in DashAI and benefits from a GPU. "
            "Model available at "
            "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF."
        ),
        es=(
            "Meta Llama 3.1 8B Instruct es un modelo de lenguaje de 8B parametros "
            "ajustado para instrucciones, cargado como GGUF Q4_K_M para inferencia "
            "eficiente en CPU o GPU. Ofrece solida capacidad de razonamiento, "
            "programacion y multilingue. Es el modelo de generacion de texto mas "
            "grande de DashAI y se beneficia de una GPU."
        ),
        pt=(
            "Meta Llama 3.1 8B Instruct e um modelo de linguagem de 8B parametros "
            "ajustado para instrucoes, carregado como GGUF Q4_K_M para inferencia "
            "eficiente em CPU ou GPU. Oferece solida capacidade de raciocinio, "
            "programacao e multilingue. E o maior modelo de geracao de texto do "
            "DashAI e se beneficia de uma GPU."
        ),
        de=(
            "Meta Llama 3.1 8B Instruct ist ein 8B-Parameter-Instruktionsmodell, "
            "als Q4_K_M-GGUF fuer effiziente CPU- oder GPU-Inferenz geladen. Es "
            "bietet starke Faehigkeiten in Schlussfolgern, Programmierung und "
            "Mehrsprachigkeit. Es ist das groesste Textgenerierungsmodell in DashAI "
            "und profitiert von einer GPU."
        ),
        zh=(
            "Meta Llama 3.1 8B Instruct 是 80 亿参数的指令微调语言模型，"
            "以 Q4_K_M GGUF 格式加载，支持高效的 CPU 或 GPU 推理。"
            "它具备强大的推理、编程和多语言能力。"
            "这是 DashAI 中最大的文本生成模型，使用 GPU 效果更佳。"
        ),
    )


class Llama32_1BInstruct(GGUFTextGenerationModel):  # noqa: N801
    """Meta Llama 3.2 1B Instruct GGUF checkpoint (Q4_K_M quantization).

    A lightweight 1B-parameter instruction-tuned model from Meta suitable for
    CPU inference. Weights are stored locally after a one-time download from
    HuggingFace.

    References
    ----------
    - https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF
    """

    REPO_ID = "bartowski/Llama-3.2-1B-Instruct-GGUF"
    GGUF_PATTERN = "*Q4_K_M.gguf"
    DOWNLOAD_SIZE_BYTES = 807694464
    SCHEMA = GGUFTextGenerationSchema
    COLOR: str = "#1a237e"
    DISPLAY_NAME = MultilingualString(
        en="Llama 3.2 1B Instruct",
        es="Llama 3.2 1B Instruct",
        pt="Llama 3.2 1B Instruct",
        de="Llama 3.2 1B Instruct",
        zh="Llama 3.2 1B Instruct",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Meta Llama 3.2 1B Instruct is a lightweight 1B-parameter "
            "instruction-tuned language model, loaded as a Q4_K_M GGUF for fast CPU "
            "inference. It is a good balance of speed and quality for everyday tasks. "
            "Model available at "
            "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF."
        ),
        es=(
            "Meta Llama 3.2 1B Instruct es un modelo de lenguaje ligero de 1B "
            "parametros ajustado para instrucciones, cargado como GGUF Q4_K_M para "
            "inferencia rapida en CPU. Ofrece un buen equilibrio entre velocidad y "
            "calidad para tareas cotidianas."
        ),
        pt=(
            "Meta Llama 3.2 1B Instruct e um modelo de linguagem leve de 1B "
            "parametros ajustado para instrucoes, carregado como GGUF Q4_K_M para "
            "inferencia rapida em CPU. Oferece um bom equilibrio entre velocidade e "
            "qualidade para tarefas cotidianas."
        ),
        de=(
            "Meta Llama 3.2 1B Instruct ist ein leichtes 1B-Parameter-"
            "Instruktionsmodell, als Q4_K_M-GGUF fuer schnelle CPU-Inferenz geladen. "
            "Es bietet ein gutes Gleichgewicht aus Geschwindigkeit und Qualitaet fuer "
            "alltaegliche Aufgaben."
        ),
        zh=(
            "Meta Llama 3.2 1B Instruct 是轻量级的 10 亿参数指令微调语言模型，"
            "以 Q4_K_M GGUF 格式加载，支持快速 CPU 推理。"
            "在日常任务中兼顾速度与质量。"
        ),
    )


class Llama32_3BInstruct(GGUFTextGenerationModel):  # noqa: N801
    """Meta Llama 3.2 3B Instruct GGUF checkpoint (Q4_K_M quantization).

    A 3B-parameter instruction-tuned model from Meta offering higher quality
    than the 1B variant while remaining CPU-friendly. Weights are stored locally
    after a one-time download from HuggingFace.

    References
    ----------
    - https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF
    """

    REPO_ID = "bartowski/Llama-3.2-3B-Instruct-GGUF"
    GGUF_PATTERN = "*Q4_K_M.gguf"
    DOWNLOAD_SIZE_BYTES = 2019377696
    SCHEMA = GGUFTextGenerationSchema
    COLOR: str = "#1a237e"
    DISPLAY_NAME = MultilingualString(
        en="Llama 3.2 3B Instruct",
        es="Llama 3.2 3B Instruct",
        pt="Llama 3.2 3B Instruct",
        de="Llama 3.2 3B Instruct",
        zh="Llama 3.2 3B Instruct",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Meta Llama 3.2 3B Instruct is a 3B-parameter instruction-tuned language "
            "model, loaded as a Q4_K_M GGUF for efficient CPU or GPU inference. It "
            "offers stronger reasoning and generation quality than the 1B variant. "
            "Model available at "
            "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF."
        ),
        es=(
            "Meta Llama 3.2 3B Instruct es un modelo de lenguaje de 3B parametros "
            "ajustado para instrucciones, cargado como GGUF Q4_K_M para inferencia "
            "eficiente en CPU o GPU. Ofrece mejor razonamiento y calidad de "
            "generacion que la variante de 1B."
        ),
        pt=(
            "Meta Llama 3.2 3B Instruct e um modelo de linguagem de 3B parametros "
            "ajustado para instrucoes, carregado como GGUF Q4_K_M para inferencia "
            "eficiente em CPU ou GPU. Oferece melhor raciocinio e qualidade de "
            "geracao do que a variante de 1B."
        ),
        de=(
            "Meta Llama 3.2 3B Instruct ist ein 3B-Parameter-Instruktionsmodell, "
            "als Q4_K_M-GGUF fuer effiziente CPU- oder GPU-Inferenz geladen. Es "
            "bietet besseres Schlussfolgern und Generierungsqualitaet als die "
            "1B-Variante."
        ),
        zh=(
            "Meta Llama 3.2 3B Instruct 是 30 亿参数的指令微调语言模型，"
            "以 Q4_K_M GGUF 格式加载，支持高效的 CPU 或 GPU 推理。"
            "与 1B 变体相比，它具有更强的推理能力和生成质量。"
        ),
    )
