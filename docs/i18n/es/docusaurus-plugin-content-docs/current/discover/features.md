---
title: Características principales
sidebar_label: Características principales
sidebar_position: 2
---

# Características principales

## Gestión de datasets

Carga y gestiona datasets en múltiples formatos: CSV, Excel y JSON. Cada dataset muestra un resumen de filas, columnas, tipos de datos y distribuciones. Desde la vista del dataset puedes iniciar exploraciones de EDA y aplicar converters de datos directamente.

**Formatos compatibles:** `.csv`, `.xlsx` / `.xls`, `.json`

## Exploración de datos (EDA)

Analiza tus datos visualmente con exploradores integrados antes de comprometerte con un modelo. Los exploradores disponibles incluyen:

| Explorador                | Propósito                                                             |
| ------------------------- | --------------------------------------------------------------------- |
| BoxPlotExplorer           | Distribución de valores por columna                                   |
| CorrelationMatrixExplorer | Correlación entre variables (Pearson, Kendall, Spearman)              |
| DescribeExplorer          | Estadísticas descriptivas (media, mediana, desviación estándar, etc.) |
| ScatterPlotExplorer       | Relación visual entre pares de variables                              |
| HistogramPlotExplorer     | Distribuciones de frecuencia                                          |
| WordcloudExplorer         | Frecuencia de palabras para columnas de texto                         |

## Entrenamiento de modelos

Crea experimentos que asocian un dataset con una tarea, luego entrena uno o más modelos en paralelo. Configura los hiperparámetros mediante formularios generados automáticamente, sin necesidad de escribir archivos de esquema. Tareas compatibles:

- **Clasificación tabular**: predice una categoría a partir de datos estructurados
- **Regresión**: predice un valor continuo
- **Clasificación de texto**: asigna categorías a texto
- **Traducción**: traducción de lenguaje secuencia a secuencia
- **Generación de texto a imagen**: síntesis generativa de imágenes
- **Generación de texto a texto**: modelos conversacionales y de resumen

## Converters de datos

Transforma tus datos con una biblioteca de más de 30 converters antes del entrenamiento: normalización, codificación, reducción de dimensionalidad, imputación y más. Los converters son componibles en cadenas y están impulsados por Scikit-learn e imbalanced-learn.

## Predicciones

Una vez entrenado un modelo, ejecuta predicciones sobre nuevos datos y descarga los resultados. La interfaz de predicción funciona para todas las tareas compatibles.

## Explicabilidad

Comprende las decisiones del modelo con herramientas de explicabilidad integradas:

- **Kernel SHAP**: contribuciones de características por instancia
- **Permutation Feature Importance**: ranking global de características mediante permutación
- **Partial Dependence Plots**: relación entre una característica y la salida del modelo

## Optimización de hiperparámetros

Busca automáticamente la mejor configuración de hiperparámetros usando los optimizadores Optuna o HyperOpt. Se generan gráficos del historial de optimización, coordenadas paralelas e importancia de características por cada ejecución.

## Sistema de plugins

Extiende dashAI con plugins de terceros distribuidos como paquetes de PyPI. Instálalos directamente desde la interfaz, y los nuevos componentes aparecen automáticamente en sus secciones correspondientes.
