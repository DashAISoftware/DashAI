"""Mixtral 8x7B Instruct GGUF checkpoint subclasses for DashAI.

Mixtral 8x7B is a single Sparse Mixture-of-Experts repo published in several
quantizations. Each quantization is exposed as its own downloadable component so
the user fetches only the one GGUF file they intend to run.
"""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.hugging_face.gguf_text_generation_base import (
    GGUFTextGenerationModel,
    GGUFTextGenerationSchema,
)

_MIXTRAL_REPO = "mradermacher/Mixtral-8x7B-Instruct-v0.1-GGUF"


class Mixtral8x7BInstructQ4KM(GGUFTextGenerationModel):
    """Mixtral 8x7B Instruct GGUF checkpoint (Q4_K_M quantization).

    A Sparse Mixture-of-Experts model (8 experts of 7B parameters, 2 active per
    token) from Mistral AI. The Q4_K_M quantization balances quality and size
    and requires roughly 26 GB of RAM. Weights are stored locally after a
    one-time download from HuggingFace.

    References
    ----------
    - Jiang et al. (2024) "Mixtral of Experts" https://arxiv.org/abs/2401.04088
    - https://huggingface.co/mradermacher/Mixtral-8x7B-Instruct-v0.1-GGUF
    """

    REPO_ID = _MIXTRAL_REPO
    GGUF_PATTERN = "*Q4_K_M.gguf"
    DOWNLOAD_SIZE_BYTES = 28448468384
    SCHEMA = GGUFTextGenerationSchema
    COLOR: str = "#4a148c"
    DISPLAY_NAME = MultilingualString(
        en="Mixtral 8x7B Instruct (Q4_K_M)",
        es="Mixtral 8x7B Instruct (Q4_K_M)",
        pt="Mixtral 8x7B Instruct (Q4_K_M)",
        de="Mixtral 8x7B Instruct (Q4_K_M)",
        zh="Mixtral 8x7B Instruct (Q4_K_M)",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Mixtral 8x7B Instruct is a Sparse Mixture-of-Experts model by Mistral "
            "AI (8 experts of 7B parameters, 2 active per token), loaded as a Q4_K_M "
            "GGUF for a balance of quality and size. It matches larger dense models "
            "on many tasks. Warning: requires ~26 GB of RAM; a GPU with >= 24 GB "
            "VRAM is recommended. Model available at "
            "https://huggingface.co/mradermacher/Mixtral-8x7B-Instruct-v0.1-GGUF."
        ),
        es=(
            "Mixtral 8x7B Instruct es un modelo de Mezcla Dispersa de Expertos de "
            "Mistral AI (8 expertos de 7B parametros, 2 activos por token), cargado "
            "como GGUF Q4_K_M para equilibrar calidad y tamano. Advertencia: "
            "requiere ~26 GB de RAM; se recomienda una GPU con >= 24 GB de VRAM."
        ),
        pt=(
            "Mixtral 8x7B Instruct e um modelo de Mistura Esparsa de Especialistas "
            "da Mistral AI (8 especialistas de 7B parametros, 2 ativos por token), "
            "carregado como GGUF Q4_K_M para equilibrar qualidade e tamanho. Aviso: "
            "requer ~26 GB de RAM; recomenda-se uma GPU com >= 24 GB de VRAM."
        ),
        de=(
            "Mixtral 8x7B Instruct ist ein Sparse-Mixture-of-Experts-Modell von "
            "Mistral AI (8 Experten mit 7B Parametern, 2 pro Token aktiv), als "
            "Q4_K_M-GGUF fuer ein Gleichgewicht aus Qualitaet und Groesse geladen. "
            "Warnung: benoetigt ~26 GB RAM; eine GPU mit >= 24 GB VRAM wird empfohlen."
        ),
        zh=(
            "Mixtral 8x7B Instruct 是 Mistral AI 的稀疏混合专家模型"
            "（8 个 70 亿参数专家，每 token 激活 2 个），"
            "以 Q4_K_M GGUF 格式加载，兼顾质量与体积。"
            "警告：需要约 26 GB 内存；建议使用显存不低于 24 GB 的 GPU。"
        ),
    )


class Mixtral8x7BInstructQ2K(GGUFTextGenerationModel):
    """Mixtral 8x7B Instruct GGUF checkpoint (Q2_K quantization).

    The smallest quantization of the Mixtral 8x7B Sparse Mixture-of-Experts
    model, trading some quality for a lower memory footprint (roughly 16 GB).
    Weights are stored locally after a one-time download from HuggingFace.

    References
    ----------
    - Jiang et al. (2024) "Mixtral of Experts" https://arxiv.org/abs/2401.04088
    - https://huggingface.co/mradermacher/Mixtral-8x7B-Instruct-v0.1-GGUF
    """

    REPO_ID = _MIXTRAL_REPO
    GGUF_PATTERN = "*Q2_K.gguf"
    DOWNLOAD_SIZE_BYTES = 17311231392
    SCHEMA = GGUFTextGenerationSchema
    COLOR: str = "#4a148c"
    DISPLAY_NAME = MultilingualString(
        en="Mixtral 8x7B Instruct (Q2_K)",
        es="Mixtral 8x7B Instruct (Q2_K)",
        pt="Mixtral 8x7B Instruct (Q2_K)",
        de="Mixtral 8x7B Instruct (Q2_K)",
        zh="Mixtral 8x7B Instruct (Q2_K)",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Mixtral 8x7B Instruct is a Sparse Mixture-of-Experts model by Mistral "
            "AI (8 experts of 7B parameters, 2 active per token). This Q2_K "
            "quantization is the smallest variant (~16 GB), trading some output "
            "quality for lower memory use. Model available at "
            "https://huggingface.co/mradermacher/Mixtral-8x7B-Instruct-v0.1-GGUF."
        ),
        es=(
            "Mixtral 8x7B Instruct es un modelo de Mezcla Dispersa de Expertos de "
            "Mistral AI. Esta cuantizacion Q2_K es la variante mas pequena (~16 GB), "
            "sacrificando algo de calidad por menor uso de memoria."
        ),
        pt=(
            "Mixtral 8x7B Instruct e um modelo de Mistura Esparsa de Especialistas "
            "da Mistral AI. Esta quantizacao Q2_K e a variante menor (~16 GB), "
            "trocando alguma qualidade por menor uso de memoria."
        ),
        de=(
            "Mixtral 8x7B Instruct ist ein Sparse-Mixture-of-Experts-Modell von "
            "Mistral AI. Diese Q2_K-Quantisierung ist die kleinste Variante "
            "(~16 GB) und tauscht etwas Qualitaet gegen geringeren Speicherbedarf."
        ),
        zh=(
            "Mixtral 8x7B Instruct 是 Mistral AI 的稀疏混合专家模型。"
            "此 Q2_K 量化是最小的变体（约 16 GB），"
            "以部分输出质量换取更低的内存占用。"
        ),
    )
