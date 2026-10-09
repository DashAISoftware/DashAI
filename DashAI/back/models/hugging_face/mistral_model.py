"""Mistral Instruct GGUF checkpoint subclasses for DashAI."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.gguf_text_generation_base import (
    GGUFTextGenerationModel,
    GGUFTextGenerationSchema,
)


class Mistral7BInstructV03(GGUFTextGenerationModel):
    """Mistral 7B Instruct v0.3 GGUF checkpoint (Q4_K_M quantization).

    A 7B-parameter instruction-tuned model from Mistral AI with strong general
    performance. Weights are stored locally after a one-time download from
    HuggingFace.

    References
    ----------
    - https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF
    """

    REPO_ID = "bartowski/Mistral-7B-Instruct-v0.3-GGUF"
    GGUF_PATTERN = "*Q4_K_M.gguf"
    DOWNLOAD_SIZE_BYTES = 4372812000
    SCHEMA = GGUFTextGenerationSchema
    COLOR: str = "#ff6f00"
    DISPLAY_NAME = MultilingualString(
        en="Mistral 7B Instruct v0.3",
        es="Mistral 7B Instruct v0.3",
        pt="Mistral 7B Instruct v0.3",
        de="Mistral 7B Instruct v0.3",
        zh="Mistral 7B Instruct v0.3",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Mistral 7B Instruct v0.3 is a 7B-parameter instruction-tuned language "
            "model from Mistral AI, loaded as a Q4_K_M GGUF for efficient CPU or GPU "
            "inference. It offers strong general reasoning and generation quality. "
            "Model available at "
            "https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF."
        ),
        es=(
            "Mistral 7B Instruct v0.3 es un modelo de lenguaje de 7B parametros "
            "ajustado para instrucciones por Mistral AI, cargado como GGUF Q4_K_M "
            "para inferencia eficiente en CPU o GPU. Ofrece solida capacidad de "
            "razonamiento y calidad de generacion."
        ),
        pt=(
            "Mistral 7B Instruct v0.3 e um modelo de linguagem de 7B parametros "
            "ajustado para instrucoes pela Mistral AI, carregado como GGUF Q4_K_M "
            "para inferencia eficiente em CPU ou GPU. Oferece solida capacidade de "
            "raciocinio e qualidade de geracao."
        ),
        de=(
            "Mistral 7B Instruct v0.3 ist ein 7B-Parameter-Instruktionsmodell von "
            "Mistral AI, als Q4_K_M-GGUF fuer effiziente CPU- oder GPU-Inferenz "
            "geladen. Es bietet starke allgemeine Schlussfolgerungs- und "
            "Generierungsqualitaet."
        ),
        zh=(
            "Mistral 7B Instruct v0.3 是 Mistral AI 推出的 70 亿参数指令微调语言模型，"
            "以 Q4_K_M GGUF 格式加载，支持高效的 CPU 或 GPU 推理。"
            "它具备强大的通用推理和生成质量。"
        ),
    )


class MistralNemoInstruct2407(GGUFTextGenerationModel):
    """Mistral Nemo Instruct 2407 GGUF checkpoint (Q4_K_M quantization).

    A 12B-parameter instruction-tuned model from Mistral AI and NVIDIA with a
    large context window. This is a heavy model that benefits from a GPU.
    Weights are stored locally after a one-time download from HuggingFace.

    References
    ----------
    - https://huggingface.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF
    """

    REPO_ID = "bartowski/Mistral-Nemo-Instruct-2407-GGUF"
    GGUF_PATTERN = "*Q4_K_M.gguf"
    DOWNLOAD_SIZE_BYTES = 7477208192
    SCHEMA = GGUFTextGenerationSchema
    COLOR: str = "#ff6f00"
    DISPLAY_NAME = MultilingualString(
        en="Mistral Nemo Instruct 2407",
        es="Mistral Nemo Instruct 2407",
        pt="Mistral Nemo Instruct 2407",
        de="Mistral Nemo Instruct 2407",
        zh="Mistral Nemo Instruct 2407",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Mistral Nemo Instruct 2407 is a 12B-parameter instruction-tuned language "
            "model built by Mistral AI and NVIDIA, loaded as a Q4_K_M GGUF. It offers "
            "high generation quality and a large context window, and is the heaviest "
            "text-generation model in DashAI; a GPU is recommended. Model available at "
            "https://huggingface.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF."
        ),
        es=(
            "Mistral Nemo Instruct 2407 es un modelo de lenguaje de 12B parametros "
            "ajustado para instrucciones, creado por Mistral AI y NVIDIA, cargado como "
            "GGUF Q4_K_M. Ofrece alta calidad de generacion y una gran ventana de "
            "contexto; es el modelo mas pesado de DashAI y se recomienda una GPU."
        ),
        pt=(
            "Mistral Nemo Instruct 2407 e um modelo de linguagem de 12B parametros "
            "ajustado para instrucoes, criado pela Mistral AI e NVIDIA, carregado como "
            "GGUF Q4_K_M. Oferece alta qualidade de geracao e uma grande janela de "
            "contexto; e o modelo mais pesado do DashAI e uma GPU e recomendada."
        ),
        de=(
            "Mistral Nemo Instruct 2407 ist ein 12B-Parameter-Instruktionsmodell von "
            "Mistral AI und NVIDIA, als Q4_K_M-GGUF geladen. Es bietet hohe "
            "Generierungsqualitaet und ein grosses Kontextfenster und ist das "
            "schwerste Textgenerierungsmodell in DashAI; eine GPU wird empfohlen."
        ),
        zh=(
            "Mistral Nemo Instruct 2407 是 Mistral AI 与 NVIDIA 共同打造的 "
            "120 亿参数指令微调语言模型，以 Q4_K_M GGUF 格式加载。"
            "它具有高生成质量和大上下文窗口，是 DashAI 中最重的文本生成模型，"
            "建议使用 GPU。"
        ),
    )
