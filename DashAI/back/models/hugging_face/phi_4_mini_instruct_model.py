from typing import List

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from DashAI.back.models.utils import (
    LLAMA_DEVICE_ENUM,
    LLAMA_DEVICE_PLACEHOLDER,
    LLAMA_DEVICE_TO_IDX,
)


class Phi4MiniInstructSchema(BaseSchema):
    """Schema for Phi 4 Mini Instruct model hyperparameters"""

    model_name: schema_field(
        enum_field(
            enum=[
                "unsloth/Phi-4-mini-instruct-GGUF",
            ]
        ),
        placeholder="unsloth/Phi-4-mini-instruct-GGUF",
        description=MultilingualString(
            en=(
                "Phi-4-mini-instruct is a lightweight open model built upon"
                " synthetic data and filtered publicly available websites -"
                " with a focus on high-quality, reasoning dense data. The"
                " model belongs to the Phi-4 model family and supports"
                " 128K token context length. The model underwent an"
                " enhancement process, incorporating both supervised"
                " fine-tuning and direct preference optimization to support"
                " precise instruction adherence and robust safety measures."
            ),
            es=(
                "Phi-4-mini-instruct es un modelo abierto ligero construido"
                " sobre datos sintéticos y sitios web disponibles"
                " públicamente filtrados, con un enfoque en datos de alta"
                " calidad y densos en razonamiento. El modelo pertenece a la"
                " familia de modelos Phi-4 y soporta un contexto de longitud"
                " de 128K tokens. El modelo se sometió a un proceso de"
                " mejora, incorporando tanto ajuste fino (fine-tuning)"
                " supervisado como optimización directa de preferencias para"
                " soportar una adherencia precisa a las instrucciones y"
                " medidas de seguridad."
            ),
            pt=(
                "Phi-4-mini-instruct é um modelo aberto e leve construído"
                " sobre dados sintéticos e sites públicos filtrados, com foco"
                " em dados de alta qualidade e densos em raciocínio. O modelo"
                " pertence à família de modelos Phi-4 e suporta comprimento"
                " de contexto de 128K tokens. O modelo passou por um processo"
                " de aprimoramento, incorporando tanto ajuste fino"
                " (fine-tuning) supervisionado quanto otimização direta de"
                " preferências, para suportar adesão precisa às instruções e"
                " medidas robustas de segurança."
            ),
            de=(
                "Phi-4-mini-instruct ist ein leichtgewichtiges offenes Modell,"
                " das auf synthetischen Daten und gefilterten, öffentlich"
                " verfügbaren Websites aufbaut, mit Schwerpunkt auf"
                " hochwertigen, reasoning-intensiven Daten. Das Modell gehört zur"
                " Phi-4-Modellfamilie und unterstützt eine Kontextlänge von"
                " 128K Token. Das Modell durchlief einen Verbesserungsprozess,"
                " der sowohl überwachtes Fine-Tuning als auch direkte"
                " Präferenzoptimierung umfasst, um präzise Befolgung von"
                " Anweisungen und robuste Sicherheitsmaßnahmen zu unterstützen."
            ),
            zh=(
                "Phi-4-mini-instruct 是一个轻量级开源模型，"
                "基于合成数据和经过筛选的公开网站构建，侧重于高质量、推理密集的数据。"
                "该模型属于 Phi-4 模型系列，支持 128K token 的上下文长度。"
                "该模型经过了增强处理，融合了监督微调和直接偏好优化，"
                "以支持精确遵循指令和稳健的安全措施。"
            ),
        ),
        alias=MultilingualString(
            en="Model Name",
            es="Nombre del Modelo",
            pt="Nome do Modelo",
            de="Modellname",
            zh="模型名称",
        ),
    )  # type: ignore

    quantization: schema_field(
        enum_field(
            enum=[
                # "unsloth/Phi-4-mini-instruct-GGUF",
                "Phi-4-mini-instruct-Q2_K.gguf",
                "Phi-4-mini-instruct-Q2_K_L.gguf",
                "Phi-4-mini-instruct-Q3_K_M.gguf",
                "Phi-4-mini-instruct-Q4_K_M.gguf",
                "Phi-4-mini-instruct-Q5_K_M.gguf",
                "Phi-4-mini-instruct-Q6_K.gguf",
                "Phi-4-mini-instruct.BF16.gguf",
                "Phi-4-mini-instruct.Q8_0.gguf",
            ]
        ),
        placeholder="Phi-4-mini-instruct.Q8_0.gguf",
        description=MultilingualString(
            en=(
                "The specific Phi 4 Mini Instruct model quantization to use. Options "
                "include various quantization sizes and the BF16 format. The choice of "
                "quantization can affect the model's performance and resource usage, "
                "with smaller quantizations typically requiring less memory but "
                "potentially sacrificing some accuracy."
            ),
            es=(
                "La cuantización específica del modelo Phi 4 Mini Instruct a"
                " utilizar. Las opciones incluyen varios tamaños de"
                " cuantización y el formato BF16. La elección de la"
                " cuantización puede afectar el rendimiento y el uso de"
                " recursos del modelo, generalmente con cuantizaciones más"
                " pequeñas requieren menos memoria pero potencialmente"
                " sacrifican algo de precisión."
            ),
            pt=(
                "A quantização específica do modelo Phi 4 Mini Instruct a"
                " utilizar. As opções incluem vários tamanhos de quantização"
                " e o formato BF16. A escolha da quantização pode afetar o"
                " desempenho e o uso de recursos do modelo, com quantizações"
                " menores geralmente exigindo menos memória, mas"
                " potencialmente sacrificando um pouco de precisão."
            ),
            de=(
                "Die spezifische Phi-4-Mini-Instruct-Modellquantisierung, die"
                " verwendet werden soll. Die Optionen umfassen verschiedene"
                " Quantisierungsgrößen und das BF16-Format. Die Wahl der"
                " Quantisierung kann die Leistung und Ressourcennutzung des"
                " Modells beeinflussen, wobei kleinere Quantisierungen in der"
                " Regel weniger Speicher benötigen, aber möglicherweise etwas"
                " Genauigkeit opfern."
            ),
            zh=(
                "要使用的特定 Phi 4 Mini Instruct 模型量化。"
                "选项包括各种量化大小和 BF16 格式。"
                "量化的选择会影响模型的性能和资源使用，"
                "较小的量化通常需要更少的内存，但可能会牺牲一些准确性。"
            ),
        ),
        alias=MultilingualString(
            en="Quantization",
            es="Cuantización",
            pt="Quantização",
            de="Quantisierung",
            zh="量化",
        ),
    )  # type: ignore

    max_tokens: schema_field(
        int_field(ge=1),
        placeholder=100,
        description=MultilingualString(
            en=(
                "Maximum number of new tokens the model will generate per response. "
                "Roughly 1 token ≈ 0.75 English words. Set to 100-200 for short "
                "answers, 500-1000 for detailed explanations or code."
            ),
            es=(
                "Número máximo de tokens nuevos que el modelo generará por respuesta. "
                "Aproximadamente 1 token ≈ 0.75 palabras en español. Use 100-200 "
                "para respuestas cortas, 500-1000 para explicaciones detalladas "
                "o código."
            ),
            pt=(
                "Número máximo de tokens novos que o modelo gerará por resposta. "
                "Aproximadamente 1 token ≈ 0.75 palavras em português. Use 100-200 "
                "para respostas curtas, 500-1000 para explicações detalhadas ou "
                "código."
            ),
            de=(
                "Maximale Anzahl neuer Token, die das Modell pro Antwort erzeugt. "
                "Ungefähr 1 Token ≈ 0,75 englische Wörter. 100-200 für kurze "
                "Antworten, 500-1000 für ausführliche Erklärungen oder Code."
            ),
            zh=(
                "模型每次响应生成的最大新 token 数量。"
                "大约 1 token 约等于 0.75 个英文单词。短答案设为 100-200，"
                "详细说明或代码设为 500-1000。"
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
                "At 0.0 the model picks the most likely token (deterministic). "
                "Around 0.7 balances quality and creativity. At 1.0 outputs are "
                "maximally varied."
            ),
            es=(
                "Temperatura de muestreo que controla la aleatoriedad (rango 0.0-1.0). "
                "En 0.0 el modelo elige el token más probable (determinista). "
                "Alrededor de 0.7 equilibra calidad y creatividad. En 1.0 las salidas "
                "son máximamente variadas."
            ),
            pt=(
                "Temperatura de amostragem que controla a aleatoriedade da saída "
                "(intervalo 0.0-1.0). Em 0.0 o modelo escolhe o token mais "
                "provável (determinístico). Em torno de 0.7 equilibra qualidade "
                "e criatividade. Em 1.0 as saídas são maximamente variadas."
            ),
            de=(
                "Stichprobentemperatur zur Steuerung der Ausgabezufälligkeit "
                "(Bereich 0.0-1.0). Bei 0.0 wählt das Modell den wahrscheinlichsten "
                "Token (deterministisch). Um 0.7 werden Qualität und Kreativität "
                "ausbalanciert. Bei 1.0 sind die Ausgaben maximal variiert."
            ),
            zh=(
                "控制输出随机性的采样温度（范围 0.0-1.0）。"
                "0.0 时模型选择最可能的 token（确定性）。"
                "0.7 左右可平衡质量与创造力。1.0 时输出变化最大。"
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
                "frequency (range 0.0-2.0). Higher values discourage repetition."
            ),
            es=(
                "Penaliza los tokens que ya aparecieron en la salida según su "
                "frecuencia (rango 0.0-2.0). Valores más altos desincentivan "
                "la repetición."
            ),
            pt=(
                "Penaliza os tokens que já apareceram na saída com base em sua "
                "frequência (intervalo 0.0-2.0). Valores mais altos desestimulam "
                "a repetição."
            ),
            de=(
                "Bestraft Token, die bereits in der Ausgabe erschienen sind, "
                "basierend auf ihrer Häufigkeit (Bereich 0.0-2.0). Höhere Werte "
                "verhindern Wiederholungen."
            ),
            zh=(
                "根据 token 在输出中出现的频率对其进行惩罚（范围 0.0-2.0）。"
                "更高的值可抑制重复。"
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
                "Total token budget for a single forward pass, including prompt and "
                "response. Mistral-7B supports up to 32K tokens; Mistral-Nemo "
                "supports up to 128K tokens."
            ),
            es=(
                "Presupuesto total de tokens por pasada, incluyendo prompt y "
                "respuesta. Mistral-7B soporta hasta 32K tokens; Mistral-Nemo "
                "soporta hasta 128K tokens."
            ),
            pt=(
                "Orçamento total de tokens para uma única passagem, incluindo "
                "prompt e resposta. Mistral-7B suporta até 32K tokens; "
                "Mistral-Nemo suporta até 128K tokens."
            ),
            de=(
                "Gesamtes Token-Budget für einen einzelnen Vorwärtsdurchlauf, "
                "einschließlich Prompt und Antwort. Mistral-7B unterstützt bis "
                "zu 32K Token; Mistral-Nemo unterstützt bis zu 128K Token."
            ),
            zh=(
                "单次前向传播的总 token 预算，包括提示词和响应。"
                "Mistral-7B 最多支持 32K token；Mistral-Nemo 最多支持 128K token。"
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
                "fully in RAM. A GPU option offloads all layers for faster inference."
            ),
            es=(
                "Dispositivo de hardware para inferencia con llama.cpp. 'CPU' ejecuta "
                "el modelo en RAM. Una opción de GPU descarga todas las capas para "
                "inferencia más rápida."
            ),
            pt=(
                "Dispositivo de hardware para inferência com llama.cpp. 'CPU' "
                "executa o modelo completamente na RAM. Uma opção de GPU "
                "descarrega todas as camadas para inferência mais rápida."
            ),
            de=(
                "Hardware-Gerät für die llama.cpp-Inferenz. 'CPU' führt das "
                "Modell vollständig im RAM aus. Eine GPU-Option lagert alle "
                "Schichten für schnellere Inferenz aus."
            ),
            zh=(
                "llama.cpp 推理所使用的硬件设备。'CPU' 完全在内存中运行模型。"
                "选择 GPU 选项会将所有层卸载以加快推理速度。"
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


class Phi4MiniInstructModel(TextToTextGenerationTaskModel):
    """Phi 4 Mini Instruct model for text generation using llama.cpp library."""

    SCHEMA = Phi4MiniInstructSchema
    COLOR: str = "#FF5733"
    DISPLAY_NAME: str = MultilingualString(
        en="Phi 4 Mini Instruct",
        es="Phi 4 Mini Instruct",
        pt="Phi 4 Mini Instruct",
        de="Phi 4 Mini Instruct",
        zh="Phi 4 Mini Instruct",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Phi-4-mini-instruct is a lightweight open model built upon"
            " synthetic data and filtered publicly available websites -"
            " with a focus on high-quality, reasoning dense data. The"
            " model belongs to the Phi-4 model family and supports"
            " 128K token context length. The model underwent an"
            " enhancement process, incorporating both supervised"
            " fine-tuning and direct preference optimization to support"
            " precise instruction adherence and robust safety measures."
        ),
        es=(
            "Phi-4-mini-instruct es un modelo abierto ligero construido"
            " sobre datos sintéticos y sitios web disponibles públicamente"
            " filtrados, con un enfoque en datos de alta calidad y densos"
            " en razonamiento. El modelo pertenece a la familia de modelos"
            " Phi-4 y soporta un contexto de longitud de 128K tokens. El"
            " modelo se sometió a un proceso de mejora, incorporando tanto"
            " ajuste fino (fine-tuning) supervisado como optimización"
            " directa de preferencias para soportar una adherencia precisa"
            " a las instrucciones y medidas de seguridad."
        ),
        pt=(
            "Phi-4-mini-instruct é um modelo aberto e leve construído"
            " sobre dados sintéticos e sites públicos filtrados, com foco"
            " em dados de alta qualidade e densos em raciocínio. O modelo"
            " pertence à família de modelos Phi-4 e suporta comprimento"
            " de contexto de 128K tokens. O modelo passou por um processo"
            " de aprimoramento, incorporando tanto ajuste fino"
            " (fine-tuning) supervisionado quanto otimização direta de"
            " preferências, para suportar adesão precisa às instruções e"
            " medidas robustas de segurança."
        ),
        de=(
            "Phi-4-mini-instruct ist ein leichtgewichtiges offenes Modell,"
            " das auf synthetischen Daten und gefilterten, öffentlich"
            " verfügbaren Websites aufbaut, mit Schwerpunkt auf"
            " hochwertigen, reasoning-intensiven Daten. Das Modell gehört zur"
            " Phi-4-Modellfamilie und unterstützt eine Kontextlänge von"
            " 128K Token. Das Modell durchlief einen Verbesserungsprozess,"
            " der sowohl überwachtes Fine-Tuning als auch direkte"
            " Präferenzoptimierung umfasst, um präzise Befolgung von"
            " Anweisungen und robuste Sicherheitsmaßnahmen zu unterstützen."
        ),
        zh=(
            "Phi-4-mini-instruct 是一个轻量级开源模型，"
            "基于合成数据和经过筛选的公开网站构建，侧重于高质量、推理密集的数据。"
            "该模型属于 Phi-4 模型系列，支持 128K token 的上下文长度。"
            "该模型经过了增强处理，融合了监督微调和直接偏好优化，"
            "以支持精确遵循指令和稳健的安全措施。"
        ),
    )

    def __init__(self, **kwargs):
        try:
            from llama_cpp import Llama
        except ImportError as e:
            raise RuntimeError(
                "llama-cpp-python is not installed. Please install it to use QwenModel."
            ) from e

        kwargs = self.validate_and_transform(kwargs)
        self.model_name = kwargs.pop("model_name")
        self.quantization = kwargs.pop("quantization", "Phi-4-mini-instruct.Q8_0.gguf")
        self.max_tokens = kwargs.pop("max_tokens", 100)
        self.temperature = kwargs.pop("temperature", 0.7)
        self.frequency_penalty = kwargs.pop("frequency_penalty", 0.1)
        self.n_ctx = kwargs.pop("context_window", 512)

        use_gpu = LLAMA_DEVICE_TO_IDX.get(kwargs.get("device")) >= 0

        self.model = Llama.from_pretrained(
            repo_id=self.model_name,
            filename=self.quantization,
            verbose=True,
            n_ctx=self.n_ctx,
            n_gpu_layers=-1 if use_gpu else 0,
            main_gpu=LLAMA_DEVICE_TO_IDX.get(kwargs.get("device")) if use_gpu else 0,
        )

    def generate(self, prompt: list[dict[str, str]]) -> List[str]:
        output = self.model.create_chat_completion(
            messages=prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            frequency_penalty=self.frequency_penalty,
        )
        return [output["choices"][0]["message"]["content"]]
