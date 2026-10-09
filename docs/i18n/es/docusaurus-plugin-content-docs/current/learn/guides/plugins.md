---
title: "Guía de Módulo: Plugins"
sidebar_label: Plugins
sidebar_position: 4
---

# Guía de Módulo: Plugins

El sistema de plugins es el mecanismo de extensibilidad de dashAI. Permite añadir nuevas capacidades (modelos, tareas, formatos de datos, transformaciones, explicadores y métricas) a la plataforma sin modificar su código base. Los plugins se distribuyen como paquetes Python estándar en PyPI y se instalan directamente desde la interfaz de dashAI.

---

## Cómo Funciona el Sistema de Plugins

dashAI descubre plugins a través del mecanismo de **entry points** de Python. Cuando un paquete Python declara un entry point `dashai.plugins` en su `pyproject.toml`, el registro de componentes de dashAI lo detecta automáticamente al iniciar y pone sus componentes disponibles en las secciones correspondientes de la interfaz.

Esto significa que:

- Un plugin que añade un nuevo modelo aparecerá en la lista de modelos disponibles del módulo de Modelos para la tarea que soporta.
- Un plugin que añade un nuevo converter aparecerá en el panel CONVERT del Notebook.
- Un plugin que añade un nuevo cargador de datos aparecerá en la selección de formato de carga.

No se requiere registro ni configuración manual, ya que la declaración del entry point es suficiente.

---

## Qué Pueden Aportar los Plugins

Un único paquete plugin puede aportar cualquier combinación de los siguientes tipos de componentes:

| Tipo de Componente      | Dónde aparece en dashAI                                                       |
| ----------------------- | ----------------------------------------------------------------------------- |
| **Modelos**             | Módulo de Modelos, lista de modelos disponibles para la tarea correspondiente |
| **Tareas**              | Módulo de Modelos, página de selección de tareas                              |
| **Cargadores de datos** | Módulo de Datasets, selector de formato de carga                              |
| **Converters**          | Módulo Notebook, pestaña CONVERT                                              |
| **Explicadores**        | Módulo de Modelos, pestaña EXPLAINABILITY                                     |
| **Métricas**            | Módulo de Modelos, métricas de evaluación para la tarea correspondiente       |

---

## Instalación de Plugins

Navega a la sección **PLUGINS** en la barra de navegación superior. Desde allí puedes:

1. Buscar plugins publicados en PyPI por nombre o palabra clave.
2. Ver descripciones de plugins, tipos de componentes soportados e información de versión.
3. Instalar con un solo clic, y dashAI gestiona la instalación con pip y el registro de componentes automáticamente.
4. Reiniciar dashAI si se solicita, ya que algunos plugins requieren reinicio para registrar completamente sus componentes.

Una vez instalados, los nuevos componentes aparecen de inmediato (o después del reinicio) en sus secciones correspondientes sin ninguna configuración adicional.

---

## Estructura de un Plugin

Un plugin de dashAI es un paquete Python estándar con una estructura específica:

```
plugin_name/
├── LICENSE
├── pyproject.toml
├── README.md
└── src/
    └── plugin_name/
        ├── my_model.py
        └── MyModel.json
```

Cada componente se implementa como una clase Python que extiende la clase base apropiada de dashAI, acompañada de un archivo de esquema JSON que describe sus parámetros para la interfaz.

El `pyproject.toml` debe declarar un entry point por clase de componente:

```toml
[project.entry-points.'dashai.plugins']
MyModel = 'plugin_name.my_model:MyModel'
```

Y debe incluir las palabras clave apropiadas para que dashAI pueda categorizar el plugin:

```toml
[project]
keywords = ["DashAI", "Package", "Model", "Task"]
```

Palabras clave válidas: `DashAI`, `Package`, `Task`, `Model`, `Dataloader`, `Converter`, `Explainer`

---

## Plugins Publicados Destacados

Las capacidades de generación de imágenes de dashAI se distribuyen ellas mismas como plugins:

| Plugin                                           | Qué añade                                                   |
| ------------------------------------------------ | ----------------------------------------------------------- |
| `dashai-stable-diffusion-v1-model-package`       | Stable Diffusion v1 para generación de imágenes desde texto |
| `dashai-flux-model-package`                      | Modelo Flux para generación de imágenes desde texto         |
| `dashai-stable-diffusion-controlnet-canny-model` | ControlNet con condicionamiento de bordes Canny             |

Esta arquitectura, en la que incluso las capacidades de primera parte son plugins, significa que la plataforma central se mantiene liviana y cada característica es opcional según tu hardware y caso de uso.

---

## Desarrollar tus Propios Plugins

Crear un plugin requiere:

1. Crear una clase Python que extienda la clase base correcta de dashAI para tu tipo de componente (p. ej., `TabularClassificationModel` para un modelo de clasificación tabular).
2. Crear un archivo de esquema JSON que describa los parámetros del componente. Esto es lo que dashAI usa para generar la interfaz de configuración automáticamente.
3. Empaquetar el código con los entry points correctos en `pyproject.toml`.
4. Probar localmente colocando el plugin en una carpeta `plugins/` dentro de tu directorio de desarrollo de dashAI.
5. Publicar en PyPI cuando esté listo.

Para una guía de desarrollo completa con ejemplos de código, referencias de clases base y un recorrido de publicación, consulta la sección [Desarrollo de Plugins](/build/plugin-development/overview).

:::info
El mecanismo de entry points significa que cualquier paquete en PyPI con la estructura correcta funcionará. No hay proceso de aprobación ni registro central más allá del propio PyPI. También puedes instalar plugins desde rutas locales durante el desarrollo.
:::
