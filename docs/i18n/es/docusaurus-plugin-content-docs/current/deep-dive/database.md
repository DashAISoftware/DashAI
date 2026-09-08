---
title: Base de Datos
sidebar_label: Base de Datos
---

dashAI usa **SQLite** como base de datos (almacenada en `~/.DashAI/db.sqlite`) con **SQLAlchemy** como ORM y **Alembic** para las migraciones de esquema.

## Tablas Principales

| Tabla                               | Propósito                                                                                                                                                                                                                                                                                      |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Dataset`                           | Dataset cargado: nombre, ruta del archivo Arrow, estado de carga y marcas de tiempo.                                                                                                                                                                                                           |
| `ModelSession`                      | Configuración del experimento: dataset, nombre de la tarea, columnas de entrada/salida, proporciones de división train/validación/test y métricas seleccionadas por división.                                                                                                                  |
| `Run`                               | Ejecución individual de entrenamiento dentro de una ModelSession: nombre del modelo, parámetros, configuración del optimizador, métrica objetivo, artefactos de la ejecución, estado y tiempos de ejecución, y rutas a los gráficos de optimización (historial, slice, contorno, importancia). |
| `Metric`                            | Medición de una única métrica: nombre, valor, división (`TRAIN`/`VALIDATION`/`TEST`), nivel (`LAST`/`STEP`/`BATCH`/`TRIAL`) e índice de paso. Vinculada a una ejecución.                                                                                                                       |
| `Prediction`                        | Trabajo de predicción que vincula una ejecución entrenada a un Dataset de entrada, rastrea el estado y tiempos de ejecución, y almacena la ruta a los resultados de salida.                                                                                                                    |
| `GenerativeSession`                 | Sesión de modelo generativo: tipo de tarea, nombre del modelo, parámetros actuales, y un nombre y descripción legibles. Posee un historial de instantáneas de parámetros y todos los registros de GenerativeProcess asociados.                                                                 |
| `GenerativeProcess`                 | Una invocación individual de una GenerativeSession que rastrea el estado y tiempos de ejecución. Vinculado a registros ProcessData que contienen las cargas útiles de entrada y salida.                                                                                                        |
| `ProcessData`                       | Carga útil de entrada o salida para un GenerativeProcess: valor de datos serializado, tipo de datos (texto, imagen, etc.) y un indicador `is_input` para distinguir entradas de salidas.                                                                                                       |
| `GenerativeSessionParameterHistory` | Instantánea inmutable de los parámetros de una GenerativeSession capturada en cada cambio, proporcionando un registro completo de la evolución de los parámetros a lo largo del tiempo.                                                                                                        |
| `Notebook`                          | Sesión de trabajo con un dataset: una copia mutable de un Dataset fuente sobre la que se pueden aplicar Exploradores y Converters. Los cambios pueden revertirse; el resultado puede guardarse como un nuevo Dataset para el entrenamiento de modelos.                                         |
| `Explorer`                          | Registro de visualización dentro de un Notebook: tipo de explorador, columnas seleccionadas, parámetros, ruta a los resultados guardados y estado de ejecución.                                                                                                                                |
| `Converter`                         | Paso individual de converter aplicado al dataset mutable de un Notebook: tipo de converter, parámetros, estado de ejecución y tiempos. Múltiples registros forman una pipeline de transformación ordenada sobre el Notebook.                                                                   |
| `Plugin`                            | Plugin instalado: nombre, autor, versiones instalada y más reciente, estado, resumen y descripción completa. Posee registros Tag para clasificación.                                                                                                                                           |
| `Tag`                               | Etiqueta de clasificación para un Plugin (p. ej., `Model`, `Task`, `Metric`), utilizada para filtrado y descubrimiento.                                                                                                                                                                        |
| `GlobalExplainer`                   | Explicación global del modelo: tipo de explicador, ejecución vinculada, parámetros, rutas a los datos de explicación y al gráfico, y estado de ejecución. Cubre el modelo en su totalidad.                                                                                                     |
| `LocalExplainer`                    | Explicación local (por instancia): tipo de explicador, ejecución y Dataset vinculados, parámetros, parámetros de ajuste, alcance, rutas de resultados y estado de ejecución.                                                                                                                   |

## Enumeraciones Importantes

- **`RunStatus`**: `NOT_STARTED` → `DELIVERED` → `STARTED` → `FINISHED` | `ERROR`
- **`SplitEnum`**: `TRAIN`, `VALIDATION`, `TEST`
- **`LevelEnum`**: `LAST` (valor final), `STEP`, `BATCH`, `TRIAL` (para optimización)

## Almacenamiento de Datos

- Los **datasets** se almacenan en formato Apache Arrow IPC (columnar, eficiente para cargas de trabajo de ML).
- Los **modelos entrenados** se guardan como archivos pickle/joblib en `~/.DashAI/runs/{run_id}/`.
- Los **gráficos** generados durante la optimización de hiperparámetros se almacenan como objetos Plotly serializados.
- Las **series temporales de métricas** (por paso, lote o prueba) se almacenan en la tabla `Metric` para rastrear el progreso del entrenamiento.
