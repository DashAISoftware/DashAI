---
title: Conceptos clave
sidebar_label: Conceptos clave
sidebar_position: 2
---

# Conceptos clave

Estos son los conceptos fundamentales que encontrarás a lo largo de dashAI. Cada término corresponde a algo que puedes ver e interactuar directamente en la interfaz.

---

## Dataset

Un dataset es la colección de datos con la que trabajas. Generalmente es una tabla estructurada (CSV, Excel, JSON). Todo flujo de trabajo en dashAI comienza cargando un dataset en el módulo **Datasets**.

Una vez cargado, el dataset es persistente: permanece en dashAI hasta que lo elimines, y puede utilizarse en múltiples notebooks y sesiones.

:::note
dashAI incluye cargadores de datos para los formatos más comunes (CSV, Excel, JSON). Puedes [crear cargadores de datos personalizados](/build/plugin-development/overview) para admitir fuentes de datos adicionales e instalarlos mediante el módulo **Plugins**.
:::

---

## Notebook

Un notebook es un espacio de trabajo no destructivo vinculado a un dataset. Te permite aplicar una secuencia de **Exploradores** y **Converters** sobre una copia de trabajo de los datos, mientras el dataset original permanece sin cambios.

Cada operación que agregas aparece en la línea de tiempo del notebook, por lo que tu proceso de transformación siempre es visible y auditable. Cuando el resultado esté listo, puedes guardarlo como un nuevo dataset con **Save as New Dataset**.

---

## Explorador

Un explorador es una herramienta de visualización o análisis en la pestaña **EXPLORE** del notebook. Los exploradores leen el estado actual de los datos y producen un resultado, como un gráfico, una tabla estadística o un mapa de calor, sin modificar los datos.

dashAI incluye exploradores organizados en cinco categorías: Inspección previa, Análisis de relaciones, Análisis estadístico, Análisis de distribuciones y Análisis multidimensional.

:::note
También puedes [desarrollar exploradores personalizados](/build/plugin-development/overview) e instalar adicionales a través del módulo **Plugins**.
:::

---

## Converter

Un converter es una herramienta de transformación de datos en la pestaña **CONVERT** del notebook. Los converters modifican los datos codificando categorías, escalando valores numéricos, eliminando valores faltantes, reduciendo dimensionalidad y más. Cada converter se aplica a un conjunto específico de columnas y filas, y el efecto es inmediatamente visible en la vista previa del dataset.

dashAI incluye más de 30 converters organizados en ocho categorías: Preprocesamiento básico, Codificación, Escalado y normalización, Reducción de dimensionalidad, Selección de características, Métodos polinomiales y de kernel, Remuestreo y balanceo de clases, y Preprocesamiento avanzado.

:::note
Puedes [crear converters personalizados](/build/plugin-development/overview) e instalar adicionales desde el módulo **Plugins**.
:::

---

## Tarea

Una tarea define el tipo de problema de ML que deseas resolver. La tarea determina qué modelos están disponibles, qué tipos de columnas son válidos como entradas y salidas, y qué métricas se utilizan para evaluar los resultados.

El módulo **Models** de dashAI admite cuatro tareas principales:

| Tarea                      | Qué predice                                                |
| -------------------------- | ---------------------------------------------------------- |
| **Clasificación tabular**  | Una categoría a partir de datos de tabla estructurados     |
| **Regresión**              | Un valor numérico continuo a partir de datos estructurados |
| **Clasificación de texto** | Una categoría asignada a un documento de texto             |
| **Traducción**             | Texto convertido de un idioma a otro                       |

El módulo **Generative** admite tareas separadas para generación de texto e imágenes. Consulta [IA Generativa](/learn/tutorials/generative) para más detalles.

:::note
Puedes extender dashAI [desarrollando nuevas tareas](/build/plugin-development/overview) e instalándolas mediante el módulo **Plugins**.
:::

---

## Sesión

Una sesión es la unidad central de trabajo en el módulo Models. Vincula un dataset, una tarea, una configuración de columnas (cuáles son entradas y cuál es el objetivo) y una estrategia de división de datos. Todos los modelos que entrenas para ese problema viven dentro de la misma sesión, lo que facilita su comparación.

Las sesiones se agrupan por tipo de tarea en la barra lateral izquierda. Puedes tener múltiples sesiones para el mismo dataset, por ejemplo para explorar distintas combinaciones de columnas de entrada o estrategias de división.

---

## Modelo

Un modelo es un algoritmo específico añadido a una sesión. Cada modelo tiene su propio nombre, configuración de hiperparámetros y estado de entrenamiento. Puedes agregar múltiples modelos del mismo tipo o de tipos distintos a la misma sesión y entrenarlos de forma independiente o todos a la vez con **Run All**.

dashAI incluye una biblioteca creciente de modelos impulsados por scikit-learn, Hugging Face, PyTorch y TensorFlow.

:::note
Puedes [desarrollar nuevas integraciones de modelos](/build/plugin-development/overview) y descubrir modelos adicionales mediante el módulo **Plugins**.
:::

---

## Estado de entrenamiento

Cada modelo en una sesión tiene uno de cinco estados posibles:

| Estado          | Significado                                           |
| --------------- | ----------------------------------------------------- |
| **Not Started** | El modelo fue añadido pero nunca entrenado            |
| **Delivered**   | El modelo ha sido encolado                            |
| **Started**     | El proceso de entrenamiento ha comenzado              |
| **Finished**    | El entrenamiento se completó con éxito                |
| **Error**       | El entrenamiento falló; revisa los parámetros o datos |

---

## Métrica

Las métricas miden qué tan bien se desempeña un modelo entrenado en cada división de datos. dashAI calcula automáticamente las métricas apropiadas para el tipo de tarea que estás resolviendo, lo que te permite comprender la efectividad de tu modelo en las distintas divisiones.

Para **tareas de clasificación**, puedes revisar métricas como Accuracy (porcentaje de predicciones correctas), F1 (balance entre precisión y exhaustividad), Precision y Recall (verdaderos positivos en relación al total de positivos y al total de positivos reales), o ROCAUC (capacidad del modelo para distinguir entre clases). Las métricas adicionales incluyen LogLoss, HammingDistance y CohenKappa para un análisis más profundo.

Para **tareas de regresión**, las métricas se centran en el error de predicción: RMSE (raíz del error cuadrático medio) penaliza los errores más grandes, mientras que MAE (error absoluto medio) proporciona una magnitud de error promedio.

Para **tareas de traducción**, las métricas incluyen BLEU (similitud con traducciones de referencia) y TER (número de ediciones necesarias para coincidir con una referencia).

:::note
dashAI incluye un conjunto básico de métricas apropiadas para cada tarea. Si necesitas métricas adicionales para casos de uso especializados, puedes [desarrollar métricas personalizadas](/build/plugin-development/overview) y añadirlas mediante el módulo **Plugins**.
:::

---

## Predicción

Una predicción es la salida de un modelo entrenado aplicado a nuevos datos. dashAI admite dos modos de predicción: **Predicciones por dataset** (ejecuta el modelo sobre un dataset completo cargado) y **Predicciones manuales** (ingresa valores específicos fila por fila en la interfaz).

---

## Explicador

Un explicador es una herramienta para interpretar el comportamiento de un modelo entrenado. Los **explicadores globales** analizan el comportamiento del modelo sobre el dataset completo (p. ej., qué características son más importantes en general). Los **explicadores locales** analizan una predicción específica (p. ej., por qué el modelo produjo este resultado para este registro en particular).

dashAI proporciona explicadores integrados como Kernel SHAP, Permutation Feature Importance y Partial Dependence Plots.

:::note
Puedes [crear explicadores personalizados](/build/plugin-development/overview) e instalar herramientas de interpretabilidad adicionales desde el módulo **Plugins**.
:::

---

## Trabajo

Las operaciones de larga duración, como entrenar un modelo, ejecutar un explorador o generar una predicción, se ejecutan como **trabajos** en segundo plano. La Cola de trabajos en la parte inferior derecha de la pantalla muestra los trabajos activos y completados para que puedas continuar trabajando mientras se ejecuta una operación.
