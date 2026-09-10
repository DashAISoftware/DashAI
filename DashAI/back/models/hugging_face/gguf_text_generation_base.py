"""Shared base for GGUF-backed text-generation models loaded via llama.cpp."""

from typing import List, Optional, Union

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from DashAI.back.models.utils import (
    LLAMA_DEVICE_ENUM,
    LLAMA_DEVICE_PLACEHOLDER,
    LLAMA_DEVICE_TO_IDX,
)


class GGUFTextGenerationSchema(BaseSchema):
    """Schema for GGUF-based text-generation model hyperparameters.

    All GGUF checkpoint subclasses share this schema. The schema controls
    generation length, sampling randomness, repetition penalty, context budget,
    and the hardware device used by llama.cpp.
    """

    max_tokens: schema_field(
        int_field(ge=1),
        placeholder=100,
        description=MultilingualString(
            en=(
                "Maximum number of new tokens the model will generate per response. "
                "Roughly 1 token ≈ 0.75 English words. Set to 100-200 for short "
                "answers, 500-1000 for detailed explanations or code. Must not "
                "exceed the context window minus the prompt length."
            ),
            es=(
                "Número máximo de tokens nuevos que el modelo generará por respuesta. "
                "Aproximadamente 1 token ≈ 0.75 palabras en español. Use 100-200 "
                "para respuestas cortas, 500-1000 para explicaciones detalladas o "
                "código. No debe superar la ventana de contexto menos la longitud "
                "del prompt."
            ),
            pt=(
                "Número máximo de tokens novos que o modelo gerará por resposta. "
                "Aproximadamente 1 token ≈ 0.75 palavras em português. Use 100-200 "
                "para respostas curtas, 500-1000 para explicações detalhadas ou "
                "código. Não deve exceder a janela de contexto menos o comprimento "
                "do prompt."
            ),
            de=(
                "Maximale Anzahl neuer Token, die das Modell pro Antwort erzeugt. "
                "Ungefähr 1 Token ≈ 0,75 englische Wörter. 100-200 für kurze "
                "Antworten, 500-1000 für ausführliche Erklärungen oder Code. "
                "Darf die Kontextfenstergröße abzüglich der Prompt-Länge nicht "
                "überschreiten."
            ),
            zh=(
                "模型每次响应生成的最大新 token 数量。"
                "大约 1 token 约等于 0.75 个英文单词。短答案设为 100-200，"
                "详细说明或代码设为 500-1000。不得超过上下文窗口减去提示词长度的值。"
            ),
        ),
        alias=MultilingualString(
            en="Max tokens",
            es="Tokens máximos",
            pt="Tokens máximos",
            de="Maximale neue Token",
            zh="最大 token 数",
        ),
    )  # type: ignore

    temperature: schema_field(
        float_field(ge=0.0, le=1.0),
        placeholder=0.7,
        description=MultilingualString(
            en=(
                "Sampling temperature controlling output randomness (range 0.0-1.0). "
                "At 0.0 the model always picks the most likely token (greedy, fully "
                "deterministic). Around 0.7 is a good balance for conversational "
                "tasks. At 1.0 outputs are maximally varied and unpredictable."
            ),
            es=(
                "Temperatura de muestreo que controla la aleatoriedad de la salida "
                "(rango 0.0-1.0). En 0.0 el modelo siempre elige el token más "
                "probable (greedy, totalmente determinista). Alrededor de 0.7 es "
                "un buen equilibrio para tareas conversacionales. En 1.0 las "
                "salidas son máximamente variadas e impredecibles."
            ),
            pt=(
                "Temperatura de amostragem que controla a aleatoriedade da saída "
                "(intervalo 0.0-1.0). Em 0.0 o modelo sempre escolhe o token mais "
                "provável (greedy, totalmente determinístico). Em torno de 0.7 é "
                "um bom equilíbrio para tarefas conversacionais. Em 1.0 as "
                "saídas são maximamente variadas e imprevisíveis."
            ),
            de=(
                "Stichprobentemperatur zur Steuerung der Ausgabezufälligkeit (0.0-1.0)."
                "Bei 0.0 wählt das Modell stets den wahrscheinlichsten Token (greedy, "
                "vollständig deterministisch). Um 0.7 ist ein gutes Gleichgewicht für "
                "Konversationsaufgaben. Bei 1.0 sind Ausgaben maximal variiert und "
                "unvorhersehbar."
            ),
            zh=(
                "控制输出随机性的采样温度（范围 0.0-1.0）。"
                "0.0 时模型始终选择最可能的 token（贪心，完全确定性）。"
                "0.7 左右是对话任务的良好平衡点。1.0 时输出变化最大，不可预测。"
            ),
        ),
        alias=MultilingualString(
            en="Temperature",
            es="Temperatura",
            pt="Temperatura",
            de="Temperatur",
            zh="温度",
        ),
    )  # type: ignore

    frequency_penalty: schema_field(
        float_field(ge=0.0, le=2.0),
        placeholder=0.1,
        description=MultilingualString(
            en=(
                "Penalizes tokens that have already appeared in the output based on "
                "how often they occur (range 0.0-2.0). At 0.0 there is no penalty "
                "and the model may repeat itself. Values around 0.1-0.3 gently "
                "discourage repetition. High values (1.5+) strongly prevent reuse "
                "of any word, which may produce less coherent text."
            ),
            es=(
                "Penaliza los tokens que ya aparecieron en la salida según su "
                "frecuencia (rango 0.0-2.0). En 0.0 no hay penalización y el modelo "
                "puede repetirse. Valores en torno a 0.1-0.3 desincentivan "
                "suavemente la repetición. Valores altos (1.5+) previenen "
                "fuertemente la reutilización de palabras, lo que puede producir "
                "texto menos coherente."
            ),
            pt=(
                "Penaliza os tokens que já apareceram na saída com base em "
                "sua frequência (intervalo 0.0-2.0). Em 0.0 não há penalização e o "
                "modelo pode se repetir. Valores em torno de 0.1-0.3 desestimulam "
                "suavemente a repetição. Valores altos (1.5+) impedem fortemente a "
                "reutilização de palavras, o que pode produzir texto menos coerente."
            ),
            de=(
                "Bestraft Token, die bereits in der Ausgabe erschienen sind, "
                "basierend auf ihrer Häufigkeit (0.0-2.0). Bei 0.0 gibt es keine "
                "Strafe und das Modell kann sich wiederholen. Werte um 0.1-0.3 "
                "hemmen Wiederholungen sanft. Hohe Werte (1.5+) verhindern die "
                "Wiederverwendung von Wörtern stark, was zu weniger kohärentem Text "
                "führen kann."
            ),
            zh=(
                "根据 token 在输出中出现的频率对其进行惩罚（范围 0.0-2.0）。"
                "0.0 时无惩罚，模型可能重复输出。0.1-0.3 左右可轻微抑制重复。"
                "高值（1.5+）会强烈阻止任何词的复用，可能导致文本连贯性下降。"
            ),
        ),
        alias=MultilingualString(
            en="Frequency penalty",
            es="Penalización de frecuencia",
            pt="Penalização de frequência",
            de="Häufigkeitsstrafe",
            zh="频率惩罚",
        ),
    )  # type: ignore

    context_window: schema_field(
        int_field(ge=1, le=131072),
        placeholder=512,
        description=MultilingualString(
            en=(
                "Total token budget for a single forward pass, including both the "
                "input prompt and the generated response. Larger values allow longer "
                "conversations but consume more RAM/VRAM. Llama 3.1 supports up to "
                "128K tokens natively; Llama 3.2 models support up to 128K tokens."
            ),
            es=(
                "Presupuesto total de tokens para una sola pasada, incluyendo tanto "
                "el prompt de entrada como la respuesta generada. Valores más altos "
                "permiten conversaciones más largas pero consumen más RAM/VRAM. "
                "Llama 3.1 soporta hasta 128K tokens de forma nativa; los modelos "
                "Llama 3.2 soportan hasta 128K tokens."
            ),
            pt=(
                "Orçamento total de tokens para uma única passagem, incluindo tanto "
                "o prompt de entrada quanto a resposta gerada. Valores maiores "
                "permitem conversas mais longas mas consomem mais RAM/VRAM. "
                "Llama 3.1 suporta até 128K tokens nativamente; os modelos "
                "Llama 3.2 suportam até 128K tokens."
            ),
            de=(
                "Gesamtes Token-Budget für einen einzelnen Vorwärtsdurchlauf, "
                "einschließlich Eingabe-Prompt und generierter Antwort. Größere Werte "
                "ermöglichen längere Gespräche, verbrauchen jedoch mehr RAM/VRAM. "
                "Llama 3.1 unterstützt nativ bis zu 128K Token; Llama-3.2-Modelle "
                "unterstützen ebenfalls bis zu 128K Token."
            ),
            zh=(
                "单次前向传播的总 token 预算，包含输入提示和生成响应。"
                "较大的值允许更长的对话，但会消耗更多 RAM/VRAM。"
                "Llama 3.1 原生支持最多 128K token；"
                "Llama 3.2 模型同样支持最多 128K token。"
            ),
        ),
        alias=MultilingualString(
            en="Context window",
            es="Ventana de contexto",
            pt="Janela de contexto",
            de="Kontextfenster",
            zh="上下文窗口",
        ),
    )  # type: ignore

    device: schema_field(
        enum_field(enum=LLAMA_DEVICE_ENUM),
        placeholder=LLAMA_DEVICE_PLACEHOLDER,
        description=MultilingualString(
            en=(
                "Hardware device for llama.cpp inference. 'CPU' runs the model "
                "fully in RAM with no GPU requirement. Selecting a GPU option "
                "offloads all layers for faster inference, setting n_gpu_layers=-1 "
                "so every transformer layer is GPU-accelerated."
            ),
            es=(
                "Dispositivo de hardware para la inferencia con llama.cpp. 'CPU' "
                "ejecuta el modelo completamente en RAM sin requisito de GPU. "
                "Seleccionar una opción de GPU descarga todas las capas para "
                "inferencia más rápida, estableciendo n_gpu_layers=-1 para que "
                "cada capa del transformer sea acelerada por GPU."
            ),
            pt=(
                "Dispositivo de hardware para inferência com llama.cpp. 'CPU' "
                "executa o modelo completamente na RAM sem requisito de GPU. "
                "Selecionar uma opção de GPU descarrega todas as camadas para "
                "inferência mais rápida, definindo n_gpu_layers=-1 para que "
                "cada camada do transformer seja acelerada por GPU."
            ),
            de=(
                "Hardware-Gerät für die llama.cpp-Inferenz. 'CPU' führt das Modell "
                "vollständig im RAM ohne GPU-Anforderung aus. Eine GPU-Option "
                "lagert alle Schichten für schnellere Inferenz aus und setzt "
                "n_gpu_layers=-1, damit jede Transformer-Schicht GPU-beschleunigt wird."
            ),
            zh=(
                "llama.cpp 推理所使用的硬件设备。'CPU' 完全在内存中运行模型，无需 GPU。"
                "选择 GPU 选项会将所有层卸载以加快推理速度，"
                "并设置 n_gpu_layers=-1 使每个 Transformer 层均由 GPU 加速。"
            ),
        ),
        alias=MultilingualString(
            en="Device",
            es="Dispositivo",
            pt="Dispositivo",
            de="Gerät",
            zh="设备",
        ),
    )  # type: ignore


class GGUFTextGenerationModel(HFDownloadableMixin, TextToTextGenerationTaskModel):
    """Base class for GGUF quantized text-generation models loaded via llama.cpp.

    Each concrete subclass represents one specific checkpoint and sets the class
    attributes ``REPO_ID``, ``GGUF_PATTERN``, and ``DOWNLOAD_SIZE_BYTES``. The
    base class provides the shared ``hf_repos`` classmethod, a helper that locates
    the downloaded GGUF file on disk, the ``__init__`` that loads the model, and
    the ``generate`` method.

    Subclasses must NOT override ``hf_repos`` or ``_local_gguf_path`` unless they
    need non-standard repo layout.
    """

    REPO_ID: str = ""
    GGUF_PATTERN: str = ""
    DOWNLOAD_SIZE_BYTES: Optional[int] = None
    COMPATIBLE_COMPONENTS = ["TextToTextGenerationTask"]
    SCHEMA = GGUFTextGenerationSchema

    @classmethod
    def hf_repos(
        cls,
    ) -> List[Union[tuple, tuple]]:
        """Return the single HuggingFace repo entry for this checkpoint.

        Returns
        -------
        list of tuple
            A list containing one 3-tuple ``(repo_id, "model", [gguf_pattern])``
            when ``REPO_ID`` is set, or an empty list otherwise.
        """
        if cls.REPO_ID:
            return [(cls.REPO_ID, "model", [cls.GGUF_PATTERN])]
        return []

    @classmethod
    def _local_gguf_path(cls):
        """Locate the downloaded GGUF file within this component's repo directory.

        Returns
        -------
        pathlib.Path
            Absolute path to the first ``*.gguf`` file found under the repo
            directory for ``REPO_ID``.

        Raises
        ------
        StopIteration
            If no ``*.gguf`` file exists inside the repo directory.
        """
        return next(iter(cls._repo_dir(cls.REPO_ID).glob("*.gguf")))

    def __init__(self, **kwargs):
        """Load a GGUF checkpoint from disk and initialise the llama.cpp model.

        Parameters
        ----------
        **kwargs : dict
            max_tokens : int, optional
                Maximum number of new tokens to generate per response. Default 100.
            temperature : float, optional
                Sampling temperature in [0.0, 1.0]. Default 0.7.
            frequency_penalty : float, optional
                Token-frequency penalty in [0.0, 2.0]. Default 0.1.
            context_window : int, optional
                Total token budget for a single forward pass. Default 512.
            device : str, optional
                Target device from ``LLAMA_DEVICE_ENUM``. CPU runs in RAM only;
                a GPU label enables full GPU offload via ``n_gpu_layers=-1``.

        Raises
        ------
        RuntimeError
            If ``llama-cpp-python`` is not installed.
        """
        try:
            from llama_cpp import Llama
        except ImportError as e:
            raise RuntimeError(
                "llama-cpp-python is not installed. "
                "Please install it to use this model."
            ) from e

        kwargs = self.validate_and_transform(kwargs)
        self.max_tokens = kwargs.pop("max_tokens", 100)
        self.temperature = kwargs.pop("temperature", 0.7)
        self.frequency_penalty = kwargs.pop("frequency_penalty", 0.1)
        self.n_ctx = kwargs.pop("context_window", 512)

        device_val = kwargs.get("device")
        use_gpu = LLAMA_DEVICE_TO_IDX.get(device_val, -1) >= 0
        main_gpu = LLAMA_DEVICE_TO_IDX.get(device_val, 0) if use_gpu else 0

        self.model = Llama(
            model_path=str(self._local_gguf_path()),
            verbose=True,
            n_ctx=self.n_ctx,
            n_gpu_layers=-1 if use_gpu else 0,
            main_gpu=main_gpu,
        )

    def generate(self, prompt: list) -> List[str]:
        """Generate a reply for the given chat prompt.

        Parameters
        ----------
        prompt : list of dict
            Conversation history in OpenAI chat format. Each dict must contain
            at least ``"role"`` (``"system"``, ``"user"``, or ``"assistant"``)
            and ``"content"`` (the message text).

        Returns
        -------
        list of str
            A single-element list containing the model's reply text, extracted
            from ``choices[0]["message"]["content"]``.
        """
        output = self.model.create_chat_completion(
            messages=prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            frequency_penalty=self.frequency_penalty,
        )
        return [output["choices"][0]["message"]["content"]]
