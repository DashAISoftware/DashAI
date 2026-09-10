---
title: "Guía del Módulo: Datasets"
sidebar_label: Datasets
sidebar_position: 1
---

# Guía del Módulo: Datasets

El módulo de Datasets es el punto de entrada para todos los datos en dashAI. Todos los demás módulos (Modelos, Notebooks, Generativo) dependen de que un dataset esté cargado aquí primero. Esta guía cubre qué hace el módulo, cómo funcionan sus componentes y cómo sacar el máximo provecho de cada funcionalidad.

---

## La Interfaz del Módulo de Datasets

La barra lateral izquierda lista todos los datasets y notebooks disponibles. Cada entrada de dataset muestra su nombre, cantidad de filas y cantidad de columnas de un vistazo. Al hacer clic en un dataset se abre su vista completa en el área principal.

El botón **Nuevo Dataset/Notebook** en la parte superior de la barra lateral es el punto de entrada tanto para cargar un nuevo dataset como para crear un nuevo notebook vinculado a uno existente.

---

## Carga de Datos

dashAI admite cuatro formatos de archivo. Cada uno tiene un cargador de datos dedicado que controla cómo se analiza el archivo.

### Formatos Admitidos y Cargadores de Datos

| Formato | Cargador de Datos | Extensiones     |
| ------- | ----------------- | --------------- |
| CSV     | `CSVDataLoader`   | `.csv`          |
| Excel   | `ExcelDataLoader` | `.xlsx`, `.xls` |
| JSON    | `JSONDataLoader`  | `.json`         |

El flujo de carga es en línea. Todo ocurre dentro de la página de Datasets sin navegar a otra página.

### Inferencia de Tipos

Después de cargar un archivo, dashAI lee una cantidad configurable de filas (**Filas de Inferencia**, por defecto 1000) y asigna automáticamente un tipo semántico a cada columna: `Categorical`, `Float` o `Integer`. Estos tipos se utilizan en toda la plataforma: en las pestañas del Explorador, en el módulo de Modelos para verificar la compatibilidad de columnas, y en los convertidores de Notebook para filtrar las operaciones aplicables.

Puedes sobrescribir cualquier tipo inferido directamente en la vista previa de carga haciendo clic en el menú desplegable del encabezado de cada columna. Corregir los tipos en el momento de la carga previene problemas posteriores en experimentos y transformaciones.

### Parámetros de CSVDataLoader

| Parámetro    | Por defecto        | Descripción                                                                                                                                                   |
| ------------ | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Nombre       | nombre del archivo | Nombre para mostrar del dataset dentro de dashAI                                                                                                              |
| Separador    | `,`                | Carácter que separa los valores de columna. Usa `;` para exportaciones de Excel con configuración regional europea                                            |
| Encabezado   | `infer`            | Fila que contiene los nombres de las columnas. `infer` detecta automáticamente; establece un número para archivos con filas de metadatos antes del encabezado |
| Nombres      | Null               | Sobrescribir los nombres de columnas manualmente                                                                                                              |
| Codificación | `utf-8`            | Codificación de caracteres del archivo. Usa `latin-1` o `ISO-8859-1` para archivos con caracteres acentuados                                                  |
| Valores NA   | Null               | Cadenas adicionales a tratar como valores faltantes (p. ej. `"?"`, `"N/A"`)                                                                                   |

### Parámetros de ExcelDataLoader

| Parámetro               | Por defecto | Descripción                                                     |
| ----------------------- | ----------- | --------------------------------------------------------------- |
| Hoja                    | `0`         | Índice basado en cero de la hoja a cargar                       |
| Encabezado              | `0`         | Índice de fila basado en cero del encabezado de columna         |
| Usar columnas           | Null        | Lista de columnas separadas por coma a cargar; Null carga todas |
| Omitir filas            | Null        | Filas a omitir al inicio de la hoja                             |
| N filas                 | Null        | Máximo de filas a cargar; Null carga todas                      |
| Nombres                 | Null        | Sobrescribir nombres de columnas                                |
| Valores NA              | Null        | Cadenas NA adicionales                                          |
| Mantener NA por defecto | Sí          | Reconocer cadenas NA integradas automáticamente                 |
| Valores verdaderos      | Null        | Cadenas a interpretar como `True` booleano                      |
| Valores falsos          | Null        | Cadenas a interpretar como `False` booleano                     |

### Parámetros de JSONDataLoader

| Parámetro      | Por defecto        | Descripción                                                       |
| -------------- | ------------------ | ----------------------------------------------------------------- |
| Nombre         | nombre del archivo | Nombre para mostrar                                               |
| Clave de datos | `data`             | Clave dentro del objeto JSON que contiene el arreglo de registros |

El JSONDataLoader espera una estructura como `{ "data": [{...}, {...}] }`. Cambia `Clave de datos` para que coincida con la clave real en tu archivo si difiere de `data`.

---

## Explorador de Datasets (EDA)

Al hacer clic en un dataset se abre su panel EDA integrado, un conjunto de análisis automáticos que se ejecutan de inmediato sin ninguna configuración. El panel está organizado en seis pestañas.

### Puntuación de Calidad

Un porcentaje que se muestra en la parte superior derecha de cada vista de dataset. Refleja la ausencia de problemas estructurales de calidad de datos. Una puntuación del 100% significa que no se detectaron columnas constantes, problemas de alta cardinalidad ni posibles columnas ID. Cualquier puntuación por debajo del 100% significa que la pestaña **Calidad de Datos** tiene hallazgos que vale la pena revisar antes del entrenamiento.

### Pestaña de Descripción General

Muestra una tabla de **Vista Previa del Dataset** con las filas de datos reales. Hay cuatro controles de barra de herramientas disponibles:

- **COLUMNAS**: mostrar/ocultar columnas específicas para enfocarse en lo que importa
- **FILTROS**: aplicar filtros a nivel de fila para inspeccionar subconjuntos
- **DENSIDAD**: alternar la altura de fila entre compacta y cómoda
- **EXPORTAR**: descargar la vista actual

Las cinco tarjetas de resumen en la parte superior de cada vista de dataset ofrecen un chequeo inmediato de salud: Total de Filas, Total de Columnas, Tamaño del Archivo (MB), Filas Duplicadas y Valores Faltantes. Los valores distintos de cero en Filas Duplicadas o Valores Faltantes indican que puede ser necesario trabajar en la calidad de datos antes del entrenamiento.

### Pestaña de Análisis Numérico

Para cada columna `Float` o `Integer`, dashAI calcula y muestra:

**Estadísticas descriptivas:** Media, Mediana, Desviación Estándar, Conteo de únicos

**Métricas de distribución:** Mínimo, Q1, Mediana, Q3, Máximo

**Indicadores de forma:** Asimetría, Curtosis, Conteo de valores atípicos, Rango

**Diagrama de caja:** Resumen visual de cinco números. Los valores atípicos aparecen como puntos más allá de los bigotes.

**Alertas inteligentes:** dashAI detecta patrones de distribución comunes y sugiere acciones automáticamente. Por ejemplo:

> ⚠️ Distribución sesgada a la derecha: Considera aplicar una transformación logarítmica.

Estas sugerencias son accionables: si ves una, el convertidor de Notebook correspondiente (p. ej., una transformación logarítmica) es el siguiente paso recomendado.

### Pestaña Categórica

Para cada columna `Categorical`:

- **Valores Únicos**: cuántas categorías distintas existen
- **Más Frecuente**: el valor de categoría dominante
- **Conteo del Valor Principal**: cuántas veces aparece el valor dominante
- **Distribución de Valores**: gráfico de barras de todos los conteos de categorías
- **Proporción**: gráfico circular que muestra la participación de cada categoría

Una distribución muy desequilibrada (donde una categoría domina) en tu columna objetivo es una señal para considerar convertidores de remuestreo (SMOTE, RandomUnderSampler) antes de entrenar modelos de clasificación.

### Pestaña de Texto

Activa solo cuando existen columnas de tipo texto. Muestra estadísticas basadas en longitud por columna: Longitud Promedio, Longitud Mediana, Promedio de Palabras, Valores Únicos, Longitud Mínima/Máxima, Rango.

Aparece una **advertencia de baja unicidad** cuando una columna de texto tiene muy pocos valores distintos. Esto generalmente significa que la columna fue clasificada incorrectamente como texto y debería ser `Categorical`. Corregir esto a nivel del dataset (volviendo a cargar el archivo) evita problemas posteriores.

### Pestaña de Calidad de Datos

Reporta tres categorías de problemas estructurales:

| Problema                 | Qué significa                                                                   | Qué hacer                                                                 |
| ------------------------ | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Columnas Constantes**  | Cada fila tiene el mismo valor, sin ninguna información predictiva              | Eliminar antes del entrenamiento                                          |
| **Alta Cardinalidad**    | Una columna categórica tiene un número inusualmente grande de valores distintos | Investigar; puede ser un campo de texto libre o una columna ID disfrazada |
| **Posibles Columnas ID** | La columna parece ser un identificador único de fila                            | Excluir de las columnas de entrada del modelo                             |

El panel de **Patrones de Datos Faltantes** muestra si los valores faltantes están distribuidos aleatoriamente o concentrados en columnas específicas. Los valores faltantes concentrados pueden indicar un problema sistemático de recolección de datos que vale la pena abordar antes del modelado.

### Pestaña de Correlaciones

Calcula correlaciones de Pearson por pares entre todas las columnas numéricas. El gráfico de barras interactivo muestra cada par de columnas con barras codificadas por color (verde = positivo, rojo/rosa = negativo). Al pasar el cursor se muestra el valor exacto de correlación.

Las **Correlaciones Fuertes (|r| > 0.5)** se listan por separado, ya que estas son las relaciones con mayor probabilidad de ser significativas. Una alta correlación entre dos características de entrada sugiere posible redundancia; una alta correlación entre una característica y la columna objetivo sugiere valor predictivo.

---

## Notebooks

Los Notebooks son espacios de trabajo no destructivos vinculados a un dataset. Permiten aplicar secuencias de **Exploradores** (visualizaciones) y **Convertidores** (transformaciones) a una copia de trabajo de los datos, previsualizar el efecto de cada operación en tiempo real y guardar el resultado como un nuevo dataset.

El dataset original nunca se modifica. Todos los cambios están aislados en la copia de trabajo del notebook hasta que guardes explícitamente.

### Herramientas de Explorador (pestaña EXPLORAR)

Los Exploradores generan visualizaciones y resúmenes estadísticos del estado actual de los datos. No modifican los datos. Los exploradores disponibles están organizados en cinco categorías:

| Categoría                      | Qué contiene                                                                                  |
| ------------------------------ | --------------------------------------------------------------------------------------------- |
| **Inspección de Vista Previa** | Describir Dataset (tabla de resumen estadístico), Mostrar Filas (vista paginada de registros) |
| **Análisis de Relaciones**     | Mapa de calor de densidad, Gráfico de dispersión múltiple, Gráfico de dispersión              |
| **Análisis Estadístico**       | Matriz de correlación, Matriz de covarianza                                                   |
| **Análisis de Distribución**   | Diagrama de caja, Distribución empírica acumulada, Histograma, Nube de palabras               |
| **Análisis Multidimensional**  | Gráfico de columnas múltiples, Categorías paralelas, Coordenadas paralelas                    |

Cada explorador tiene una configuración de dos pasos: primero seleccionar qué columnas incluir (alcance) y luego establecer los parámetros del explorador. Los resultados se renderizan en línea en la línea de tiempo del notebook debajo de la vista previa de datos.

### Herramientas de Convertidor (pestaña CONVERTIR)

Los Convertidores modifican los datos. Cada uno se aplica a un conjunto configurable de columnas y filas, y la vista previa del dataset se actualiza inmediatamente después de que cada convertidor se ejecuta. Los convertidores disponibles están organizados en ocho categorías:

**Preprocesamiento Básico**

| Convertidor          | Qué hace                                                                    |
| -------------------- | --------------------------------------------------------------------------- |
| `NaN Remover`        | Elimina filas que contienen al menos un valor faltante                      |
| `Simple Imputer`     | Rellena valores faltantes con media, mediana, más frecuente o una constante |
| `KNN Imputer`        | Rellena valores faltantes usando k vecinos más cercanos                     |
| `Missing Indicator`  | Agrega columnas binarias que marcan qué valores faltaban                    |
| `Column Remover`     | Elimina completamente las columnas seleccionadas del dataset                |
| `Character Replacer` | Reemplaza caracteres o cadenas específicas en columnas de texto             |

**Codificación**

| Convertidor       | Qué hace                                                             |
| ----------------- | -------------------------------------------------------------------- |
| `Binarizer`       | Mapea valores numéricos a 0 o 1 basándose en un umbral               |
| `Label Binarizer` | Binariza etiquetas en un esquema uno contra todos                    |
| `Label Encoder`   | Codifica etiquetas categóricas como enteros (para columnas objetivo) |
| `One-Hot Encoder` | Crea una columna binaria para cada valor de categoría                |
| `Ordinal Encoder` | Codifica categorías como enteros ordenados                           |

**Escalado y Normalización**

| Convertidor      | Qué hace                                                                |
| ---------------- | ----------------------------------------------------------------------- |
| `Max Abs Scaler` | Escala cada característica por su valor absoluto máximo (rango: -1 a 1) |
| `Min-Max Scaler` | Escala características a un rango especificado (por defecto: 0 a 1)     |
| `Normalizer`     | Escala cada fila (registro) a norma unitaria                            |

**Reducción de Dimensionalidad**

| Convertidor                    | Qué hace                                                                     |
| ------------------------------ | ---------------------------------------------------------------------------- |
| `Principal Component Analysis` | Reduce a n componentes explicando la máxima varianza                         |
| `Incremental PCA`              | PCA para datasets grandes procesados en lotes eficientes en memoria          |
| `Truncated SVD`                | Reducción basada en SVD, funciona con matrices dispersas                     |
| `Fast ICA`                     | Análisis de Componentes Independientes                                       |
| `Nystroem Approximation`       | Aproxima un mapa de características del kernel para representación no lineal |
| `Variance Threshold`           | Elimina características con varianza por debajo de un umbral                 |

**Selección de Características**

| Convertidor                 | Qué hace                                                                     |
| --------------------------- | ---------------------------------------------------------------------------- |
| `Select K Best`             | Mantiene las K características con las puntuaciones estadísticas más altas   |
| `Select Percentile`         | Mantiene el X% superior de características por puntuación                    |
| `Select FDR`                | Selecciona características controlando la tasa de falsos descubrimientos     |
| `Select FPR`                | Selecciona características por umbral de significancia del valor p           |
| `Select FWE`                | Selecciona características con corrección estricta de error por familia      |
| `Generic Univariate Filter` | Selector univariante configurable que combina puntuación y modo de selección |

**Métodos Polinomiales y de Kernel**

| Convertidor             | Qué hace                                                                                       |
| ----------------------- | ---------------------------------------------------------------------------------------------- |
| `Polynomial Features`   | Genera términos polinomiales y de interacción a partir de las características de entrada       |
| `RBF Sampler`           | Aproxima un mapa de características de kernel RBF usando características de Fourier aleatorias |
| `Additive Chi² Sampler` | Aproxima el kernel chi-cuadrado aditivo para datos no negativos                                |
| `Skewed Chi² Sampler`   | Variante de la aproximación del kernel chi-cuadrado con un parámetro de desplazamiento         |

**Remuestreo y Balanceo de Clases**

| Convertidor            | Qué hace                                                                           |
| ---------------------- | ---------------------------------------------------------------------------------- |
| `SMOTE`                | Genera registros sintéticos de la clase minoritaria por interpolación              |
| `SMOTE-ENN`            | SMOTE seguido de limpieza por Vecinos Editados más Cercanos                        |
| `Random Under-Sampler` | Elimina aleatoriamente registros de la clase mayoritaria para balancear el dataset |

**Preprocesamiento Avanzado**

| Convertidor    | Qué hace                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------ |
| `TF-IDF`       | Convierte texto en vectores de características TF-IDF (frecuencias de palabras ponderadas) |
| `Bag of Words` | Convierte texto en vectores de conteo de palabras sin procesar                             |
| `Tokenizer`    | Convierte texto en secuencias de índices de tokens enteros                                 |
| `Embedding`    | Mapea secuencias de tokens a representaciones vectoriales semánticas densas                |

### Guardar un Dataset Transformado

Cuando el notebook contiene las transformaciones que deseas, haz clic en **GUARDAR COMO NUEVO DATASET**. Esto crea un nuevo dataset independiente en dashAI con los datos en su estado actual. El nuevo dataset está disponible inmediatamente para experimentos sin afectar el dataset fuente.

---

## Consejos

- Usa la **Puntuación de Calidad** como verificación de salud de primera pasada antes de hacer cualquier análisis. Una puntuación por debajo del 100% siempre tiene una causa específica visible en la pestaña de Calidad de Datos.
- Las **Alertas Inteligentes** en el Análisis Numérico son sugerencias priorizadas. Abórdalas con el convertidor de Notebook correspondiente antes del entrenamiento para mejorar el rendimiento del modelo.
- Construye pipelines de transformación en Notebooks de forma incremental: agrega un convertidor a la vez y verifica la vista previa antes de agregar el siguiente.
- Los convertidores de remuestreo (SMOTE, RandomUnderSampler) solo deben aplicarse a la partición de entrenamiento, no al dataset completo. Ten esto en cuenta al guardar un dataset transformado para usar en experimentos.
- Para datos de texto, aplica **TF-IDF** o **Bag of Words** cuando trabajes con modelos de ML tradicionales (Regresión Logística, SVM, Random Forest). Los modelos neuronales que aceptan texto sin procesar (como DistilBERT) no requieren estos pasos de preprocesamiento.
