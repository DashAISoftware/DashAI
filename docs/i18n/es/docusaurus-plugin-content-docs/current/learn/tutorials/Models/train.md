---
title: Entrenar un Modelo
sidebar_label: Entrenar un Modelo
---

# Entrenar un Modelo

Esta página te guía para crear una sesión, añadir modelos, configurar hiperparámetros y ejecutar el entrenamiento en dashAI.

## Requisitos Previos

- Al menos un dataset cargado en dashAI.
- El dataset debe tener columnas compatibles con la tarea que deseas ejecutar (p. ej., una columna de salida categórica para tareas de clasificación).

---

## Paso 1: Seleccionar una Tarea

En la página principal del módulo de Modelos, haz clic en la tarea que coincida con tu problema. Cada tarjeta de tarea muestra una descripción para ayudarte a elegir la correcta.

Si tienes una sesión existente, también puedes hacer clic directamente en ella en la barra lateral izquierda para saltarte este paso y retomar el trabajo.

---

## Paso 2: Crear una Sesión

Después de seleccionar una tarea, comienza un flujo de creación de sesión en dos pasos.

### 2a: Seleccionar Dataset y Nombrar la Sesión

- Usa el desplegable **Select a dataset** para elegir entre tus datasets disponibles. Una vez seleccionado, una tarjeta resumen muestra el nombre del dataset, la fecha de creación, el conteo de filas y el conteo de columnas.
- Ingresa un nombre en el campo **Session Name**. Se rellena previamente un nombre por defecto basado en el tipo de tarea (p. ej., `Session_Tabular Classification_1`), pero puedes cambiarlo por algo más descriptivo.

Haz clic en **NEXT** para continuar.

### 2b: Preparar el Dataset

Este paso tiene dos partes: definir columnas y definir la división de datos.

**Columnas de Entrada y Salida**

dashAI valida si el dataset seleccionado es compatible con la tarea elegida. Un banner en la parte superior del paso confirma la compatibilidad y muestra los tipos de columnas requeridos para entradas y salidas.

- **Input Columns**: Selecciona las características que el modelo usará para aprender. Cada columna se muestra como una etiqueta con su insignia de tipo (Float, Integer, Categorical). Haz clic dentro del campo y selecciona columnas del desplegable. Elimina cualquier columna haciendo clic en la `×` de su etiqueta.
- **Output Columns**: Selecciona la columna objetivo que el modelo predecirá. La salida debe coincidir con el tipo requerido por la tarea (p. ej., Categorical para tareas de clasificación).

:::tip Requisitos de tipo de columna
Cada tarea impone requisitos de tipo específicos. Para Clasificación Tabular, las entradas pueden ser Float, Integer o Categorical, mientras que la salida debe ser Categorical con cardinalidad 1. Si el banner de compatibilidad muestra una advertencia, revisa los tipos de columnas en el Explorador de Datasets antes de crear la sesión.
:::

**División de Datos**

Define cómo dashAI divide el dataset en subconjuntos de entrenamiento, validación y prueba. Hay tres opciones disponibles:

| Opción                          | Descripción                                                                                                                                             |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Use predefined splits**       | Usa divisiones train/validación/test ya definidas en el archivo del dataset. Solo disponible si el dataset fue cargado con estructura predividida.      |
| **Random split by proportion**  | Asigna filas aleatoriamente a cada subconjunto según las proporciones que especifiques. El valor por defecto es Train: 0.6, Validation: 0.2, Test: 0.2. |
| **Manual split by row indices** | Especifica manualmente los índices de fila de inicio y fin para cada subconjunto.                                                                       |

Al usar **Random split**, hay tres opciones adicionales disponibles:

| Opción       | Descripción                                                                                                                                                            |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Shuffle**  | Mezcla aleatoriamente las filas antes de dividir. Recomendado para evitar sesgo de orden en los datos. Habilitado por defecto.                                         |
| **Stratify** | Asegura que cada división preserve las mismas proporciones de clases que el dataset completo. Útil para datasets desbalanceados.                                       |
| **Seed**     | Una semilla aleatoria fija para reproducibilidad. El valor por defecto es `42`. Establece un valor específico para asegurar que siempre se produzca la misma división. |

Haz clic en **CREATE SESSION** para finalizar la configuración. La sesión se abre inmediatamente.

---

## Paso 3: Añadir Modelos

Una vez abierta la sesión, el área principal muestra el panel de **Comparación de Modelos** y el panel derecho lista los **Modelos Disponibles** para tu tarea.

Para añadir un modelo:

1. Haz clic en un modelo en el panel derecho. Al pasar el cursor aparece un popup de descripción. Léelo para entender qué hace el algoritmo antes de añadirlo.
2. Hacer clic en el modelo abre el modal **Add Model to Session**.

### Configurar el Modelo

El modal tiene un paso: **Configure Model**.

- **Model Name**: Un nombre único para esta instancia del modelo dentro de la sesión. Rellenado previamente con un valor por defecto (p. ej., `SVC_1`). Cámbialo por algo significativo si planeas añadir múltiples instancias del mismo tipo de modelo.
- **Model**: Muestra el tipo de algoritmo (solo lectura, establecido por tu selección).

**Hiperparámetros**

Debajo del nombre, cada hiperparámetro configurable se lista con su valor actual y un icono de ayuda **?**. Los parámetros varían según el modelo. Por ejemplo:

- Un SVM (SVC) tiene parámetros como `C`, `coef0`, `degree`, `gamma`, `kernel`, `max_iter`, `shrinking`, `tolerance`.
- Un Decision Tree tiene `max_depth`, `min_samples_split`, `criterion` y otros.
- Un KNN tiene `n_neighbors`, `weights`, `metric` y otros.

**Optimización de Hiperparámetros**

Cada hiperparámetro numérico tiene un interruptor: **Optimize hyperparameter [nombre]**. Cuando está habilitado, dashAI buscará automáticamente el mejor valor para ese parámetro durante el entrenamiento en lugar de usar el valor fijo que ingresaste. Puedes habilitar la optimización para cualquier combinación de parámetros.

Haz clic en **ADD MODEL** para añadirlo a la sesión. Haz clic en **CANCEL** para descartar.

Puedes añadir tantos modelos como necesites, incluyendo múltiples instancias del mismo algoritmo con diferentes configuraciones. Cada uno aparece como una fila independiente en la tabla de comparación.

---

## Paso 4: Entrenar Modelos

Una vez añadidos los modelos, aparecen en dos lugares:

**Tabla de Comparación (arriba)**

Una tabla resumen que muestra todos los modelos en la sesión con columnas:

- **Model Name**: el nombre que asignaste.
- **Model**: el tipo de algoritmo.
- **Actions**: tres botones por fila: ▶ ejecutar, 👁 ver detalles, 🗑 eliminar.

**Tarjetas de Modelo (debajo de la tabla)**

Cada modelo tiene una tarjeta expandible que muestra su nombre, algoritmo, insignia de estado actual y botones de acción:

| Botón                  | Descripción                                                                                    |
| ---------------------- | ---------------------------------------------------------------------------------------------- |
| **EDIT**               | Reabre el modal de configuración para cambiar el nombre del modelo o los hiperparámetros.      |
| **TRAIN**              | Inicia el entrenamiento de este modelo. Cambia a **RE-TRAIN** después de la primera ejecución. |
| **Insignia de estado** | Muestra el estado actual: **Not Started**, **Finalizado** o **Error**.                         |
| 🗑                      | Elimina el modelo de la sesión.                                                                |

**Para entrenar un modelo individual:** haz clic en **TRAIN** en su tarjeta.

**Para entrenar todos los modelos a la vez:** haz clic en **RUN ALL** en la parte superior derecha del encabezado de la tabla de comparación. Esto pone en cola todos los modelos no entrenados para ejecución secuencial.

El entrenamiento se ejecuta como un trabajo en segundo plano, por lo que puedes monitorear el progreso en la **Job Queue** en la parte inferior derecha de la pantalla.

---

## Paso 5: Revisar Resultados

Después de que el entrenamiento se completa, cada tarjeta de modelo muestra una insignia **Finalizado** y se expande para mostrar cuatro pestañas:

### LIVE METRICS

Muestra las métricas de rendimiento del modelo organizadas en tres subpestañas: **TRAINING**, **VALIDATION** y **TEST**.

Un desplegable **Metrics** te permite seleccionar qué métrica mostrar. Las métricas disponibles dependen de la tarea. Para clasificación incluyen Accuracy, F1, Precision, Recall, ROCAUC, LogLoss, HammingDistance, CohenKappa. Para regresión incluyen RMSE, MAE y otras.

:::note
Las métricas solo están disponibles después de que el entrenamiento está completo. Si un modelo muestra "No metrics available for this view", aún no ha sido entrenado.
:::

### EXPLAINABILITY

Muestra los explicadores globales y locales adjuntos a este modelo. Consulta la página [Explicabilidad](/learn/tutorials/Models/explainability) para más detalles.

### PREDICTIONS

Muestra las predicciones de dataset y las predicciones manuales generadas desde este modelo. Consulta la página [Predicciones](/learn/tutorials/Models/predictions) para más detalles.

### HYPERPARAMETERS

Muestra los valores exactos de hiperparámetros usados en la última ejecución de entrenamiento. Útil para verificar qué valores fueron seleccionados cuando la optimización de hiperparámetros estaba habilitada.

---

## Consejos

- Añade un **Dummy Classifier** (o modelo de referencia equivalente para tu tarea) junto a tus modelos principales. Te da una referencia de rendimiento para comparar: cualquier modelo que no supere al dummy necesita más ajustes.
- Habilita **Stratify** al trabajar con datasets desbalanceados para asegurar que cada división tenga una muestra representativa de todas las clases.
- Usa una **Seed** fija al comparar múltiples modelos para asegurar que todos entrenen y evalúen exactamente con la misma división de datos.
- Puedes añadir múltiples instancias del mismo tipo de modelo con diferentes configuraciones de hiperparámetros para explorar cómo los parámetros afectan el rendimiento.

## Solución de Problemas

| Síntoma                                                        | Causa probable                                                    | Solución                                                                                        |
| -------------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| El banner de compatibilidad muestra una advertencia            | Los tipos de columnas no coinciden con los requisitos de la tarea | Revisa los tipos de columnas en el Explorador de Datasets y vuelve a cargar si es necesario     |
| El botón NEXT no está activo en la configuración de sesión     | Los campos requeridos están vacíos                                | Asegúrate de que se seleccionó un dataset y se ingresó un nombre de sesión                      |
| El modelo muestra insignia **Error** después del entrenamiento | Valores de hiperparámetros inválidos o problema con los datos     | Haz clic en **EDIT** para revisar los parámetros, o revisa la Job Queue para detalles del error |
| No hay métricas disponibles después del entrenamiento          | Modelo entrenado con datos incompatibles                          | Revisa la selección de columnas de entrada/salida y vuelve a entrenar                           |
| RUN ALL no es visible                                          | No se han añadido modelos todavía                                 | Añade al menos un modelo antes de usar RUN ALL                                                  |
