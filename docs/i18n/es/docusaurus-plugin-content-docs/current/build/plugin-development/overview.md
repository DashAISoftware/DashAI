---
title: Visión General de Plugins
sidebar_label: Visión General de Plugins
---

# ¿Qué es un Plugin?

Un **plugin** es un paquete de extensión que agrega nueva funcionalidad a dashAI sin modificar la aplicación central. Los plugins te permiten:

- Agregar nuevos **modelos de Machine Learning** (clasificación, regresión, generación, etc.)
- Crear **data loaders** personalizados para soportar formatos de dataset adicionales
- Implementar nuevos **data converters** para preprocesamiento y transformación
- Agregar **explorers** especializados para análisis de datos
- Desarrollar **explainers** personalizados para la interpretabilidad de modelos
- Extender **tareas** para soportar nuevos tipos de problemas de ML
- Definir **métricas** personalizadas para evaluación

Los plugins se distribuyen como paquetes Python en [PyPI](https://pypi.org) y son descubiertos e instalados automáticamente por dashAI cuando usas el módulo **Plugins**. Esto facilita que la comunidad extienda dashAI con funcionalidades específicas de dominio y experimentales sin esperar lanzamientos oficiales.

:::tip Convención de Nombres para Plugins
Todos los plugins de dashAI **deben** usar el prefijo `dashai-` en el nombre de su paquete (ej. `dashai-my-model-package`) para que la aplicación pueda descubrirlos y cargarlos automáticamente. Ver más plugins de la comunidad: [pypi.org/search/?q=dashai](https://pypi.org/search/?q=dashai).
:::

---

## Ejemplo Real: Modelos Microsoft Phi

Aquí hay un ejemplo concreto de un plugin de dashAI en acción.

**dashai-phi-model-package** agrega los modelos de lenguaje Microsoft Phi para generación de texto a dashAI.

**Disponible en PyPI:** [dashai-phi-model-package](https://pypi.org/project/dashai-phi-model-package/)

### Estructura del Paquete

```bash
dashai_phi_model_package/
├── dashai_phi_model_package/
│   ├── __init__.py
│   └── phi_model.py
├── pyproject.toml
└── README.md
```

<details>
<summary>pyproject.toml</summary>

```toml
[project]
name = "dashai_phi_model_package"
version = "0.0.2"

dependencies = ['llama-cpp-python>=0.2.90', 'huggingface-hub>=0.29.1']

authors = [{ name = "DashAI team" }, { email = "dashaisoftware@gmail.com" }]

keywords = ["DashAI", "Model"]

description = "Phi Model for DashAI"
readme = "README.md"
requires-python = ">=3.8"

[project.entry-points.'dashai.plugins']
PhiModel = 'dashai_phi_model_package.phi_model:PhiModel'

[project.urls]
Homepage = "https://github.com/DashAISoftware/DashAI"
Issues = "https://github.com/DashAISoftware/DashAI/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

</details>

La sección `[project.entry-points.'dashai.plugins']` es clave: le indica a dashAI qué clases registrar cuando el plugin está instalado. Cada entrada mapea un nombre arbitrario a una ruta de importación `module:ClassName`.

<details>
<summary>phi_model.py</summary>

```python
from typing import List

from llama_cpp import Llama

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.models.hugging_face.llama_utils import is_gpu_available_for_llama_cpp
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)

if is_gpu_available_for_llama_cpp():
    DEVICE_ENUM = ["gpu", "cpu"]
    DEVICE_PLACEHOLDER = "gpu"
else:
    DEVICE_ENUM = ["cpu"]
    DEVICE_PLACEHOLDER = "cpu"


class PhiSchema(BaseSchema):
    """Schema for Phi model."""

    model_name: schema_field(
        enum_field(
            enum=[
                "microsoft/Phi-3-mini-4k-instruct-gguf",
                "microsoft/phi-4-gguf",
            ]
        ),
        placeholder="microsoft/Phi-3-mini-4k-instruct-gguf",
        description="The specific Phi model version to use.",
    )  # type: ignore

    max_tokens: schema_field(
        int_field(ge=1),
        placeholder=100,
        description="Maximum number of tokens to generate.",
    )  # type: ignore

    temperature: schema_field(
        float_field(ge=0.0, le=1.0),
        placeholder=0.7,
        description=(
            "Sampling temperature. Higher values make the output more random, while "
            "lower values make it more focused and deterministic."
        ),
    )  # type: ignore

    frequency_penalty: schema_field(
        float_field(ge=0.0, le=2.0),
        placeholder=0.1,
        description=(
            "Penalty for repeated tokens in the output. Higher values reduce the "
            "likelihood of repetition, encouraging more diverse text generation."
        ),
    )  # type: ignore

    context_window: schema_field(
        int_field(ge=1),
        placeholder=512,
        description=(
            "Maximum number of tokens the model can process in a single forward pass "
            "(context window size)."
        ),
    )  # type: ignore

    device: schema_field(
        enum_field(enum=DEVICE_ENUM),
        placeholder=DEVICE_PLACEHOLDER,
        description="The device to use for model inference.",
    )  # type: ignore


class PhiModel(TextToTextGenerationTaskModel):
    """Phi model for text generation using llama.cpp library."""

    SCHEMA = PhiSchema

    def __init__(self, **kwargs):
        kwargs = self.validate_and_transform(kwargs)
        self.model_name = kwargs.get(
            "model_name", "microsoft/Phi-3-mini-4k-instruct-gguf"
        )
        self.max_tokens = kwargs.pop("max_tokens", 100)
        self.temperature = kwargs.pop("temperature", 0.7)
        self.frequency_penalty = kwargs.pop("frequency_penalty", 0.1)
        self.n_ctx = kwargs.pop("context_window", 512)

        model_filenames = {
            "microsoft/Phi-3-mini-4k-instruct-gguf": "*4.gguf",
            "microsoft/phi-4-gguf": "phi-4-IQ3_M.gguf",
        }

        self.filename = model_filenames.get(
            self.model_name, "Phi-3-mini-4k-instruct-q4.gguf"
        )

        self.model = Llama.from_pretrained(
            repo_id=self.model_name,
            filename=self.filename,
            verbose=True,
            n_ctx=self.n_ctx,
            n_gpu_layers=-1 if kwargs.get("device", "gpu") == "gpu" else 0,
        )

    def generate(self, prompt: list[dict[str, str]]) -> List[str]:
        output = self.model.create_chat_completion(
            messages=prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            frequency_penalty=self.frequency_penalty,
        )

        generated_text = output["choices"][0]["message"]["content"]
        return [generated_text]
```

</details>

## Conceptos Clave Ilustrados

| Concepto                          | Dónde buscar                                                 |
| --------------------------------- | ------------------------------------------------------------ |
| Registro de entry points          | `pyproject.toml` → `[project.entry-points.'dashai.plugins']` |
| Extender una clase base de dashAI | `PhiModel(TextToTextGenerationTaskModel)`                    |
| Definir parámetros                | `PhiSchema` con `schema_field()`                             |
| Carga del modelo                  | `__init__` con `validate_and_transform`                      |
| Generar salida                    | `generate()` retornando `List[str]`                          |
