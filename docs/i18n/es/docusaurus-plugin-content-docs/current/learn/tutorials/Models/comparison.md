---
title: Comparación de Modelos
sidebar_label: Comparación de Modelos
---

# Comparación de Modelos

El panel de Comparación de Modelos se encuentra en la parte superior de cada sesión y te proporciona una vista unificada de todos los modelos en la sesión y sus métricas de rendimiento. Se actualiza automáticamente a medida que los modelos terminan de entrenarse.

---

## La Tabla de Comparación

Por defecto el panel muestra una vista de **TABLE** con una fila por modelo. Las columnas incluyen:

| Columna                  | Descripción                                                                                                                                                                                         |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Model Name**           | El nombre asignado cuando se añadió el modelo.                                                                                                                                                      |
| **Model**                | El tipo de algoritmo (p. ej., Support Vector Machine, Decision Tree).                                                                                                                               |
| **Columnas de métricas** | Una columna por métrica de evaluación. Para clasificación: Accuracy, F1, Precision, Recall, ROCAUC, LogLoss y más. Para regresión: RMSE, MAE y otras. Las métricas mostradas varían según la tarea. |
| **Actions**              | ▶ ejecutar, 👁 ver detalles, 🗑 eliminar.                                                                                                                                                             |

Los modelos que aún no han sido entrenados muestran `-` en las columnas de métricas.

### Cambiar Entre Divisiones

Tres botones sobre la tabla te permiten elegir qué división de datos reflejan las métricas:

| Botón          | Descripción                                                                                                                |
| -------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **TRAINING**   | Métricas calculadas sobre el subconjunto de entrenamiento.                                                                 |
| **VALIDATION** | Métricas calculadas sobre el subconjunto de validación. Usadas durante el desarrollo para ajustar hiperparámetros.         |
| **TEST**       | Métricas calculadas sobre el subconjunto de prueba reservado. El indicador más confiable del rendimiento en el mundo real. |

Cambia entre divisiones para entender si un modelo está sobreajustando (métricas de entrenamiento altas pero métricas de prueba bajas) o generalizando bien.

---

## Vista de Gráficos

Haz clic en **CHARTS** en la parte superior derecha del panel de comparación para cambiar a una vista visual.

### Tipos de Gráficos

Hay dos tipos de gráficos disponibles, seleccionables con los interruptores **BARRA** (Barra) y **RADAR**:

**Gráfico de Barras**

Muestra un gráfico de barras agrupadas donde cada grupo representa una métrica y cada barra dentro del grupo representa un modelo. Esto facilita comparar modelos en cualquier métrica individual de un vistazo.

**Gráfico Radar**

Muestra un gráfico de araña/radar donde cada eje representa una métrica. Cada modelo se dibuja como un polígono. Un modelo con un rendimiento uniformemente bueno en todas las métricas aparece como un polígono más grande y equilibrado. Útil para identificar compensaciones: un modelo puede obtener puntuaciones altas en Accuracy pero bajas en Recall, lo que se ve como una forma irregular.

### Selección de Métricas

En el lado izquierdo de la vista de gráficos, un panel **Metrics** lista todas las métricas disponibles con casillas de verificación. Hay dos botones de selección rápida disponibles:

- **ALL** habilita todas las métricas.
- **NONE** limpia todas las selecciones.

Selecciona solo las métricas relevantes para tu análisis para reducir el desorden visual. El gráfico se actualiza de inmediato al marcar o desmarcar métricas.

---

## Consejos

- Siempre compara modelos en la división **TEST** para la evaluación final, ya que las métricas de entrenamiento y validación pueden ser engañosas si el modelo sobreajustó.
- Usa el **Gráfico Radar** para identificar rápidamente modelos con rendimiento equilibrado en todas las métricas frente a modelos que sobresalen en un área pero tienen bajo rendimiento en otras.
- Añade un modelo de referencia (p. ej., Dummy Classifier para tareas de clasificación) a la sesión antes de entrenar otros modelos. Establece un umbral mínimo de rendimiento que todos los demás modelos deben superar.
- La tabla de comparación se puede desplazar horizontalmente cuando se muestran muchas métricas. Desplázate hacia la derecha para ver todas las columnas.

## Solución de Problemas

| Síntoma                                                      | Causa probable                          | Solución                                                                              |
| ------------------------------------------------------------ | --------------------------------------- | ------------------------------------------------------------------------------------- |
| Todas las columnas de métricas muestran `-`                  | Ningún modelo ha sido entrenado todavía | Entrena al menos un modelo usando el botón **TRAIN** en su tarjeta                    |
| Algunos modelos muestran `-` mientras otros muestran valores | Esos modelos no han sido entrenados     | Haz clic en **TRAIN** en cada tarjeta de modelo no entrenado, o usa **RUN ALL**       |
| La vista de gráficos está vacía                              | No hay modelos entrenados en la sesión  | Entrena al menos un modelo antes de cambiar a la vista de gráficos                    |
| El gráfico radar es difícil de leer                          | Demasiadas métricas seleccionadas       | Deselecciona las métricas menos relevantes usando el panel **Metrics** a la izquierda |
