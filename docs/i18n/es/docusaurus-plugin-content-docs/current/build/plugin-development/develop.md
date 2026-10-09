---
title: Desarrollar un Plugin
sidebar_label: Desarrollar un Plugin
---

# Desarrollar un Plugin

## Requisitos Previos

Antes de desarrollar un plugin, asegúrate de entender:

1. **[¿Qué es un Plugin?](/build/plugin-development/overview)**: visión general de los conceptos y capacidades de los plugins
2. **[Estructura de un Plugin](/build/plugin-development/structure)**: cómo se organizan los plugins y qué requiere dashAI

---

## Configura tu Entorno de Desarrollo

Para crear un plugin, necesitas acceso a las clases Python de dashAI. Hay dos enfoques:

### Opción 1: dashAI como Biblioteca Instalada

Instala dashAI como paquete en tu entorno virtual de Python:

```bash
pip install dashai
```

**Nota:** Este enfoque es más sencillo pero limita tu capacidad de probar el plugin interactivamente dentro de dashAI.

### Opción 2: Clonar el Repositorio (Recomendado)

Clona el repositorio de dashAI para obtener capacidades completas de desarrollo y prueba:

```bash
git clone https://github.com/DashAISoftware/DashAI.git
cd DashAI
```

Crea una carpeta `plugins` en la raíz del repositorio para el desarrollo de tu plugin:

```text
DashAI/
├── DashAI/
├── plugins/                  ← Crea esta carpeta
├── tests/
├── ...
```

Este enfoque te permite probar tu plugin en tiempo real mientras lo desarrollas.

---

## Paso 1: Identifica Qué Quieres Construir

Los plugins pueden extender dashAI con:

- **Modelos de Machine Learning** (`TabularClassificationModel`, `RegressionModel`, `TextGenerationModel`, etc.)
- **Data Loaders** (soporte para formatos de dataset adicionales)
- **Data Converters** (preprocesamiento, ingeniería de características, transformaciones)
- **Explorers** (herramientas de visualización y análisis de datos)
- **Explainers** (herramientas de interpretabilidad de modelos)
- **Tareas Personalizadas** (nuevos tipos de problemas de ML)
- **Métricas Personalizadas** (métricas de evaluación)

Para garantizar la compatibilidad, las clases de tu plugin **deben extender la clase base apropiada de dashAI**:

```python
# Ejemplo: Crear un modelo de clasificación tabular
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class MyCustomModel(TabularClassificationModel):
    def train(self, X, y):
        # Tu lógica de entrenamiento
        pass
```

---

## Paso 2: Implementa tu Plugin

1. Crea la carpeta del plugin dentro del directorio `plugins` (si usas la Opción 2)
2. Escribe tus clases Python extendiendo las clases base apropiadas de dashAI
3. Crea los archivos de configuración JSON necesarios
4. Agrega el `pyproject.toml` con los entry points correctos (ver [Estructura de un Plugin](/build/plugin-development/structure))
5. Escribe un README describiendo tu plugin

---

## Recomendaciones

### Revisa Plugins Existentes

Estudia ejemplos funcionales para entender las mejores prácticas:

- **[Ejemplo real](/build/plugin-development/overview):** `dashai-phi-model-package` agrega los modelos Microsoft Phi
- **Plugins de la comunidad:** [pypi.org/search/?q=dashai](https://pypi.org/search/?q=dashai)

### Prueba tu Plugin Durante el Desarrollo

1. Crea los archivos Python y JSON localmente (Opción 2: clonar el repositorio)
2. Colócalos en la carpeta `/plugins`
3. Inicia dashAI y verifica que tus componentes aparecen y funcionan correctamente
4. Itera hasta estar seguro de la implementación

### Verifica Conflictos de Dependencias

Después de instalar nuevas dependencias, verifica que no existan conflictos:

```bash
pip check
```

**Sin conflictos:**

```text
No broken requirements found.
```

**Con conflictos:**

```text
fastapi 0.106.0 has requirement starlette<0.28.0,>=0.27.0, but you have starlette 0.20.0.
```

Resuelve cualquier conflicto antes de publicar tu plugin.

**Es importante que al instalar una nueva librería para un plugin o paquete, esta sea incluida entre las dependencias del plugin o paquete.**

5. **Usa prints en el flujo de los componentes agregados**

   Incluir prints en el flujo del componente que creaste puede ser muy útil para verificar el correcto funcionamiento del componente en el software.
