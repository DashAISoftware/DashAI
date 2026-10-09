---
title: Notebooks
sidebar_label: Notebooks
---

# Notebooks

Un Notebook es el espacio de trabajo interactivo de dashAI para explorar y transformar un dataset.
Proporciona un entorno en vivo y temporal donde puedes aplicar herramientas de análisis y
transformaciones de datos, observar su efecto en los datos en tiempo real, y registrar cada operación
como una línea de tiempo secuencial, todo sin modificar el dataset original hasta que decidas guardar.

Cuando estés satisfecho con el resultado, puedes guardar todo el proceso como un nuevo dataset,
preservando los datos originales intactos.

---

## Conceptos clave

- **No destructivo por defecto.** Todas las operaciones en un notebook se ejecutan en una copia de trabajo del
  dataset. El dataset original nunca se modifica.
- **Vista previa en vivo.** Cada vez que agregas un Explorer o un Converter, la vista previa del dataset
  se actualiza inmediatamente para reflejar el estado actual de los datos.
- **Línea de tiempo.** Cada operación se agrega en línea debajo de la vista previa de datos, formando un
  registro secuencial de cada transformación aplicada.
- **Guardar cuando estés listo.** Una vez que tus transformaciones estén completas, puedes guardar el estado
  actual del notebook como un nuevo dataset independiente.

---

## Acceder a los Notebooks

Los Notebooks están vinculados a un dataset específico. Hay dos formas de abrir uno:

- **Desde el Dataset Explorer:** haz clic en el botón **NEW NOTEBOOK** en la esquina superior derecha
  de cualquier vista de dataset. Esto crea un nuevo notebook asociado con ese dataset.
- **Desde la barra lateral izquierda:** en la sección **Notebooks**, haz clic en cualquier notebook existente
  para volver a abrirlo. Cada entrada de notebook muestra el nombre del dataset al que pertenece.

La barra lateral agrupa los notebooks bajo su dataset padre, por lo que puedes mantener múltiples
sesiones de trabajo independientes para el mismo dataset.

---

## La interfaz del Notebook

Cuando un notebook está abierto, la pantalla se divide en dos áreas:

### Área principal: Vista previa del dataset y línea de tiempo

El área central muestra:

- **Título del notebook**: se muestra como `Notebook: [Nombre del dataset]` en la parte superior.
- **Barra de herramientas**: dos controles disponibles en todo momento:
  - **FILTERS**: aplica filtros a nivel de fila para enfocar la vista previa en un subconjunto de los datos.
  - **EXPORT**: descarga el estado actual de la vista previa del dataset.
- **Tabla de vista previa del dataset**: una vista paginada y desplazable del dataset en su estado
  actual. Los nombres de columna y sus tipos se muestran como subencabezados. A medida que agregas Converters,
  los valores de esta tabla se actualizan para reflejar cada transformación.
- **Línea de tiempo de operaciones**: cada Explorer o Converter que agregues aparece como un bloque debajo
  de la tabla de vista previa, en el orden en que fueron aplicados. Cada bloque muestra:
  - El nombre y tipo de la herramienta.
  - Una tabla resumen de su configuración (columna objetivo, alcance, parámetros).
  - Una insignia de estado: **Finalizado** (completado) o un estado de error si algo salió mal.
  - Un botón de **Información/Editar** para revisar o modificar su configuración.
  - Un botón de eliminar para quitar la operación de la línea de tiempo.

### Panel derecho: Herramientas de análisis

El panel derecho es la biblioteca de herramientas. Tiene dos pestañas:

| Pestaña     | Propósito                                                                                                                           |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **EXPLORE** | Herramientas de análisis que generan visualizaciones o resúmenes estadísticos de los datos, sin modificarlos.                       |
| **CONVERT** | Herramientas de transformación que modifican los datos: codificación, escalado, imputación y otras operaciones de preprocesamiento. |

Ambas pestañas comparten el mismo patrón de interacción: una lista de herramientas con búsqueda y categorías,
con una vista previa en miniatura y descripción al pasar el cursor.

**Explorar herramientas**

Las herramientas están agrupadas por categoría. Cada categoría muestra un conteo de herramientas disponibles y puede expandirse o contraerse.

Categorías de la pestaña EXPLORE: **Preview Inspection**, **Relationship Analysis**, **Statistical Analysis**, **Distribution Analysis**, **Multidimensional Analysis**.

Categorías de la pestaña CONVERT: **Basic Preprocessing**, **Encoding**, **Scaling and Normalization**, **Dimensionality Reduction**, **Feature Selection**, **Polynomial & Kernel Methods**, **Resampling & Class Balancing**, **Advanced Preprocessing**.

Al pasar el cursor sobre cualquier tarjeta de herramienta aparece un popup con:

- Una imagen de vista previa del resultado de la herramienta.
- Una breve descripción de lo que hace.
- Una etiqueta de categoría.

**Modo de vista**

El panel admite dos modos de visualización (lista y cuadrícula), que se alternan con los iconos junto a
**View Mode** en la parte superior del panel.

**Búsqueda**

Usa la barra de búsqueda en la parte superior del panel para filtrar herramientas por nombre en todas las categorías.

---

## Explorers

Los Explorers son herramientas de análisis. Leen el estado actual del dataset y generan
una visualización o un resumen estadístico en línea en la línea de tiempo del notebook. No
modifican los datos.

Usa los Explorers para entender la estructura de tus datos en cualquier punto del proceso de transformación:
antes de aplicar converters, entre pasos o después de completar todas las transformaciones.

### Agregar un Explorer

1. En el panel derecho, haz clic en la pestaña **EXPLORE**.
2. Busca o navega hasta el Explorer que quieras usar. Pasa el cursor sobre él para leer su descripción.
3. Haz clic en la tarjeta del Explorer para abrir el modal de configuración.

### Configurar un Explorer

El modal de configuración tiene dos pasos, mostrados como un indicador de progreso en la parte superior:
**1. Configure Scope → 2. Configure Parameters**.

El modal también tiene dos pestañas internas: **DESCRIPTION** y **DATASET**.

- **DESCRIPTION** muestra qué hace la herramienta y su configuración de alcance.
- **DATASET** muestra una vista previa del dataset como referencia durante la configuración.

**Paso 1: Configurar el alcance**

Selecciona qué columnas usará el Explorer.

La tabla de selector de columnas muestra:

| Columna        | Descripción                                                             |
| -------------- | ----------------------------------------------------------------------- |
| Index          | La posición de la columna en el dataset (basada en cero).               |
| Column Name    | El nombre de la columna.                                                |
| Value Type     | El tipo semántico asignado en dashAI (Categorical, Float, Integer).     |
| Data Type      | El tipo de datos subyacente (float64, string, int64, etc.).             |
| Selected Order | El orden en que las columnas seleccionadas se pasarán a la herramienta. |

Un contador en la parte superior de la tabla muestra cuántas columnas están seleccionadas y cuántas
son requeridas (p. ej., `Columns required: at least 2`). El contador se vuelve verde cuando se cumple el
requisito mínimo.

Usa la barra de búsqueda para filtrar columnas por nombre. Selecciona todas con la casilla del encabezado,
o selecciona individualmente haciendo clic en cada fila.

Haz clic en **NEXT** una vez que se satisfaga el requisito de columnas.

**Paso 2: Configurar los parámetros**

Cada Explorer tiene su propio conjunto de parámetros. Estos varían según la herramienta.
Los tipos de parámetros comunes incluyen menús desplegables (p. ej., método de correlación: `pearson`),
entradas numéricas (p. ej., períodos mínimos) y casillas de verificación (p. ej., solo numérico, mostrar resultado).

Cada parámetro tiene un icono de ayuda **?** que muestra una descripción al pasar el cursor.

Haz clic en **CREATE EXPLORER** para ejecutar la herramienta y agregarla a la línea de tiempo del notebook.
Haz clic en **BACK** para volver al Paso 1.

### Resultado del Explorer

Una vez creado, el Explorer aparece como un bloque en la línea de tiempo debajo de la vista previa de datos.
El resultado se renderiza en línea. Por ejemplo, una matriz de correlación se muestra como un
mapa de calor interactivo directamente en el notebook.

El encabezado del bloque muestra:

- El nombre e icono del Explorer.
- Una insignia **Finalizado** cuando el procesamiento está completo.
- Un botón de **Información/Editar** que abre el modal de configuración para revisar la configuración
  o modificar el alcance y los parámetros.
- Un botón de eliminar para quitar el Explorer de la línea de tiempo.

---

## Converters

Los Converters son herramientas de transformación. Modifican los datos en la copia de trabajo del notebook,
y su efecto se refleja inmediatamente en la tabla de vista previa del dataset arriba.

Usa los Converters para preparar tus datos para el entrenamiento de modelos: codifica variables categóricas,
escala columnas numéricas, maneja valores faltantes y más.

### Agregar un Converter

1. En el panel derecho, haz clic en la pestaña **CONVERT**.
2. Busca o navega hasta el Converter que quieras usar. Pasa el cursor sobre él para leer su descripción.
3. Haz clic en la tarjeta del Converter para abrir el modal de configuración.

### Configurar un Converter

El modal de configuración sigue la misma estructura de dos pasos que los Explorers:
**1. Configure Scope → 2. Configure Parameters**.

**Paso 1: Configurar el alcance**

A diferencia de los Explorers, los Converters te permiten definir el alcance tanto para **columnas** como para **filas**.

_Alcance de columnas_

El selector de columnas funciona de manera idéntica a la configuración del Explorer:
selecciona las columnas a las que se aplicará el Converter. El contador muestra
cuántas columnas están seleccionadas. Usa la barra de búsqueda para filtrar, o usa la
casilla del encabezado para seleccionar todas.

_Alcance de filas_

Debajo del selector de columnas, una sección de **Selection Mode** define qué filas
procesará el Converter:

| Opción         | Descripción                                                                                                                  |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **By Range**   | Selecciona filas especificando un índice de inicio y un índice de fin. El converter procesará todas las filas en ese rango.  |
| **By Indices** | Selecciona índices de filas específicos para procesar.                                                                       |
| **SELECT ALL** | Botón que selecciona todas las filas del dataset. El pie de página muestra el conteo: `Rows selected: all \| Total rows: N`. |

Haz clic en **NEXT** una vez que el alcance esté configurado.

**Paso 2: Configurar los parámetros**

Cada Converter expone sus propios parámetros. Estos varían según la herramienta. Por ejemplo:

- Un **Binarizer** tiene un parámetro `Threshold` y una casilla `copy`.
- Un **Min-Max Scaler** tiene parámetros `feature_range_min` y `feature_range_max`.
- Un **One-Hot Encoder** tiene parámetros para manejar categorías desconocidas.

Cada parámetro tiene un icono de ayuda **?**. Haz clic en **BACK** para volver al Paso 1,
o en **CREATE CONVERTER** para aplicar la transformación.

### Resultado del Converter

Una vez creado, el Converter aparece como un bloque en la línea de tiempo y la tabla de vista previa del
dataset se actualiza inmediatamente para reflejar la transformación.

El bloque muestra una tabla resumen con:

| Campo               | Descripción                                                |
| ------------------- | ---------------------------------------------------------- |
| **Target Column**   | La columna designada como objetivo/salida, si corresponde. |
| **Scope (Columns)** | Las columnas a las que se aplicó el Converter.             |
| **Scope (Rows)**    | La selección de filas utilizada (p. ej., `All`).           |

La misma insignia **Finalizado**, el botón de **Información/Editar** y el botón de eliminar
están disponibles al igual que con los Explorers.

:::note El orden de las operaciones importa
Los Converters se aplican en el orden en que aparecen en la línea de tiempo. Si aplicas un
scaler antes de un encoder, el scaler se ejecuta primero sobre los valores originales. Reordenar
o eliminar operaciones cambiará el estado final de los datos.
:::

---

## Categorías de Explorers disponibles

La pestaña EXPLORE organiza las herramientas en cinco categorías:

| Categoría                     | Qué contiene                                                                                                                      |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Preview Inspection**        | Vistas directas de los datos en bruto: Describe Dataset (tabla de resumen estadístico) y Show Rows (vista de registros paginada). |
| **Relationship Analysis**     | Herramientas para analizar cómo se relacionan pares de variables: Density Heatmap, Multiple Scatter Plot, Scatter Plot.           |
| **Statistical Analysis**      | Medidas cuantitativas formales de estructura: Correlation Matrix, Covariance Matrix.                                              |
| **Distribution Analysis**     | Forma y dispersión de variables individuales: Box Plot, Empirical Cumulative Distribution, Histogram Plot, Word Cloud.            |
| **Multidimensional Analysis** | Patrones a través de múltiples variables simultáneamente: Multiple Column Chart, Parallel Categories, Parallel Coordinates.       |

---

## Categorías de Converters disponibles

La pestaña CONVERT organiza las herramientas en ocho categorías:

| Categoría                        | Qué contiene                                                                                                                                       |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Basic Preprocessing**          | Limpieza fundamental de datos: NaN Remover, Simple Imputer, KNN Imputer, Missing Indicator, Column Remover, Character Replacer.                    |
| **Encoding**                     | Conversión categórica a numérica: Binarizer, Label Binarizer, Label Encoder, One-Hot Encoder, Ordinal Encoder.                                     |
| **Scaling and Normalization**    | Ajuste de rangos numéricos: Max Abs Scaler, Min-Max Scaler, Normalizer.                                                                            |
| **Dimensionality Reduction**     | Compresión de variables: PCA, Incremental PCA, Truncated SVD, Fast ICA, Nystroem Approximation, Variance Threshold.                                |
| **Feature Selection**            | Eliminación de variables guiada estadísticamente: Select K Best, Select Percentile, Select FDR, Select FPR, Select FWE, Generic Univariate Filter. |
| **Polynomial & Kernel Methods**  | Expansión no lineal de características: Polynomial Features, RBF Sampler, Additive Chi² Sampler, Skewed Chi² Sampler.                              |
| **Resampling & Class Balancing** | Corrección de desequilibrio de clases: SMOTE, SMOTE-ENN, Random Under-Sampler.                                                                     |
| **Advanced Preprocessing**       | Transformación de texto a numérico: TF-IDF, Bag of Words, Tokenizer, Embedding.                                                                    |

---

## Guardar el resultado

Cuando estés satisfecho con las transformaciones aplicadas en el notebook, haz clic en
**SAVE AS NEW DATASET** en la esquina superior derecha del notebook.

Esto crea un nuevo dataset independiente en dashAI que contiene los datos en su
estado transformado actual. El nuevo dataset aparece en la lista de **Available Datasets**
en la barra lateral izquierda y puede usarse para experimentos igual que cualquier dataset cargado.

El dataset original en el que se basó el notebook permanece sin cambios.

:::tip Cuándo guardar
Guarda un nuevo dataset cuando tengas un pipeline de transformación estable y reproducible
que quieras usar para el entrenamiento. Puedes crear múltiples datasets desde el mismo
notebook guardando en diferentes puntos de la línea de tiempo.
:::

---

## Consejos

- Agrega un Explorer **antes y después** de un Converter para confirmar visualmente que la
  transformación tuvo el efecto esperado en tus datos.
- Usa el control de barra de herramientas **FILTERS** para inspeccionar subconjuntos específicos de los datos
  después de aplicar una transformación.
- Si un Converter produce resultados inesperados, haz clic en **Información/Editar** en su
  bloque de la línea de tiempo para revisar el alcance y los parámetros, o elimínalo y vuelve a configurarlo.
- El **Selected Order** de columnas en el selector de alcance importa para algunas herramientas,
  por ejemplo herramientas que tratan la primera columna seleccionada como referencia.

## Solución de problemas

| Síntoma                                                              | Causa probable                             | Solución                                                                                                     |
| -------------------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| El botón NEXT no está activo en el Paso 1                            | No hay suficientes columnas seleccionadas  | Verifica el contador de columnas requeridas y selecciona el mínimo requerido                                 |
| El resultado del Explorer no aparece                                 | Error de procesamiento                     | Verifica el bloque de la línea de tiempo para ver el estado de error y revisa la configuración de parámetros |
| El Converter no cambió los datos como se esperaba                    | Columnas o filas incorrectas en el alcance | Haz clic en **Información/Editar** en el bloque y revisa la configuración del alcance                        |
| La vista previa del dataset se ve incorrecta después de un Converter | Operaciones aplicadas en orden incorrecto  | Revisa el orden de la línea de tiempo; elimina y vuelve a agregar operaciones si es necesario                |
| SAVE AS NEW DATASET no está disponible                               | Aún no se han agregado operaciones         | Agrega al menos un Explorer o Converter antes de guardar                                                     |
