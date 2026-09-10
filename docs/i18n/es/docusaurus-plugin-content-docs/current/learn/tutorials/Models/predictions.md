---
title: Predicciones
sidebar_label: Predicciones
---

# Predicciones

Una vez que un modelo ha sido entrenado, puedes usarlo para generar predicciones sobre nuevos datos. dashAI admite dos modos de predicción: **Predicciones de Dataset** y **Predicciones Manuales**. Ambas se acceden desde la pestaña **PREDICTIONS** dentro de cada tarjeta de modelo.

---

## Acceder a las Predicciones

1. Abre una sesión desde la barra lateral izquierda.
2. Expande una tarjeta de modelo que tenga estado **Finalizado**.
3. Haz clic en la pestaña **PREDICTIONS**.

La pestaña está dividida en dos secciones:

| Sección                 | Descripción                                                                       |
| ----------------------- | --------------------------------------------------------------------------------- |
| **Dataset Predictions** | Ejecuta el modelo contra un dataset completo cargado en dashAI.                   |
| **Manual Predictions**  | Ingresa una o más filas de datos manualmente y obtén una predicción de inmediato. |

Cada sección muestra una insignia de conteo con el número de predicciones ya creadas, y un botón para añadir una nueva.

---

## Predicciones de Dataset

Usa este modo cuando deseas aplicar el modelo a un dataset completo, por ejemplo para generar predicciones para un conjunto de prueba o un nuevo lote de registros.

### Crear una Predicción de Dataset

Haz clic en **NEW DATASET PREDICTION** para abrir el modal **Create New Prediction**. El modal tiene dos pasos.

**Paso 1: Configurar Entrada**

- **Select a dataset**: Elige entre los datasets disponibles en dashAI. El desplegable muestra el nombre del dataset y el conteo de filas (p. ej., `Dataset_1 (45000 Rows)`).
- Una vez seleccionado un dataset, un panel **Prediction Information** muestra:
  - **Input Columns**: las columnas de características que el modelo espera, mostradas como etiquetas.
  - **Target Column**: la columna que el modelo predecirá, resaltada en teal.
- Una tabla de vista previa muestra las primeras filas del dataset seleccionado para que puedas verificar que tiene la estructura correcta antes de continuar.

Haz clic en **NEXT** para continuar.

**Paso 2: Confirmar**

Una tarjeta resumen muestra la configuración de la predicción:

- **Model**: el tipo de algoritmo.
- **Run**: el nombre específico de la instancia del modelo.
- **Input Type**: `Dataset`.
- **Dataset**: el dataset seleccionado en el Paso 1.

Revisa el resumen y haz clic en **SEND** para poner en cola el trabajo de predicción. Haz clic en **BACK** para volver al Paso 1, o en **CANCEL** para descartar.

### Resultado de la Predicción

Una vez completada, la predicción aparece como una tarjeta bajo **Dataset Predictions** con:

- **Prediction #N**: número secuencial.
- **Timestamp**: fecha y hora en que se ejecutó la predicción.
- **Dataset name**: el dataset fuente utilizado.
- Insignia **Finalizado** cuando el procesamiento está completo.
- Una **tabla de vista previa** que muestra las primeras 100 filas de resultados.
- Una nota: _"Preview of first 100 rows. Download the CSV for complete results."_
- Un botón de **descarga** (↓) para exportar los resultados completos como archivo CSV.
- Un botón de **eliminación** (🗑) para eliminar la predicción.

:::tip
La vista previa muestra 100 filas. Siempre descarga el CSV completo cuando trabajes con datasets grandes para acceder a todos los resultados de predicción.
:::

---

## Predicciones Manuales

Usa este modo cuando deseas probar el modelo con valores de entrada específicos creados manualmente. Por ejemplo, para entender cómo responde el modelo a una combinación particular de características, o para demostrar el comportamiento del modelo en un contexto de aula o presentación.

### Crear una Predicción Manual

Haz clic en **NEW MANUAL PREDICTION** para abrir el modal **Create New Prediction**.

**Paso 1: Configurar Entrada (Ingreso Manual de Datos)**

El modal muestra una tabla con una fila por instancia de predicción. Cada columna corresponde a una característica de entrada que el modelo espera.

- Las **columnas categóricas** aparecen como desplegables con los valores de categoría válidos.
- Las **columnas numéricas** aparecen como campos de texto editables.

Rellena los valores para cada columna en la fila. Haz clic en **Add Row** (el botón `+`) para añadir filas adicionales si deseas predecir múltiples instancias a la vez.

Haz clic en **NEXT** para continuar.

**Paso 2: Confirmar**

Una tarjeta resumen muestra:

- **Model**: el tipo de algoritmo.
- **Run**: el nombre específico de la instancia del modelo.
- **Input Type**: `Manual Input`.
- **Manual Rows**: el número de filas que ingresaste.

Haz clic en **SEND** para enviar. Haz clic en **BACK** para volver y editar los datos.

### Resultado de la Predicción

El resultado aparece bajo **Manual Predictions** con la misma estructura que las predicciones de dataset: una tarjeta numerada con una marca de tiempo, insignia **Finalizado**, y una tabla de vista previa que muestra los valores de entrada junto al resultado predicho.

Un botón de descarga (↓) y un botón de eliminación (🗑) están disponibles en cada tarjeta de resultado.

---

## Consejos

- Para **Predicciones de Dataset**, el dataset seleccionado debe tener las mismas columnas de entrada (mismos nombres y tipos) que el dataset con el que se entrenó el modelo. Si los nombres de las columnas difieren, la predicción fallará.
- Usa **Predicciones Manuales** para validar rápidamente que el comportamiento del modelo tenga sentido intuitivo en ejemplos específicos antes de ejecutarlo sobre un dataset completo.
- Puedes crear múltiples predicciones del mismo modelo entrenado. Cada una se almacena de forma independiente y puede descargarse por separado.
- Las predicciones persisten en la sesión incluso después de cerrar y volver a abrir dashAI.

## Solución de Problemas

| Síntoma                                                     | Causa probable                                                                    | Solución                                                                                               |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| La pestaña PREDICTIONS está vacía o deshabilitada           | El modelo no ha sido entrenado                                                    | Entrena el modelo primero; la pestaña se activa después de una ejecución exitosa                       |
| La predicción de dataset falla                              | Incompatibilidad de columnas entre el dataset de entrenamiento y el de predicción | Asegúrate de que el dataset de predicción tenga las mismas columnas de entrada que el de entrenamiento |
| El formulario de predicción manual tiene columnas faltantes | La configuración del modelo ha cambiado desde el entrenamiento                    | Reabre el modelo y verifica las columnas de entrada en la configuración de sesión                      |
| El botón de descarga produce un archivo vacío               | El trabajo de predicción no se completó exitosamente                              | Revisa la Job Queue para errores y vuelve a ejecutar la predicción                                     |
