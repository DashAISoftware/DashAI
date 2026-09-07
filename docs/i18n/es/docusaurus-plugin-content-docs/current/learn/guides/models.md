---
title: "Guía del Módulo: Modelos"
sidebar_label: Modelos
sidebar_position: 2
---

# Guía del Módulo: Modelos

El módulo de Modelos gestiona el ciclo completo de experimentación de ML: definir tareas, entrenar modelos, optimizar hiperparámetros, evaluar resultados, generar predicciones e interpretar el comportamiento del modelo mediante herramientas de explicabilidad. Todo está organizado alrededor de **Sesiones**, experimentos autocontenidos que agrupan modelos, métricas, predicciones y resultados de explicabilidad en un solo lugar.

---

## Conceptos Fundamentales

### Tareas

Una tarea define el tipo de problema de aprendizaje automático. Determina qué modelos están disponibles, qué tipos de columnas son válidos como entradas y salidas, y qué métricas de evaluación se calculan.

| Tarea                      | Tipos de entrada            | Tipo de salida              | Caso de uso                                            |
| -------------------------- | --------------------------- | --------------------------- | ------------------------------------------------------ |
| **Clasificación Tabular**  | Float, Integer, Categorical | Categorical (1 columna)     | Predecir una categoría a partir de datos estructurados |
| **Clasificación de Texto** | Texto                       | Categorical                 | Clasificar documentos, reseñas, mensajes               |
| **Regresión**              | Float, Integer, Categorical | Float o Integer (1 columna) | Predecir un valor continuo                             |
| **Traducción**             | Texto                       | Texto                       | Convertir texto entre idiomas                          |

### Sesiones

Una sesión une un dataset, una configuración de tarea (columnas de entrada/salida, división de datos) y todos los modelos entrenados dentro de ese contexto. Las sesiones son persistentes, por lo que cerrar dashAI y volver a abrirlo te regresa al mismo estado.

La barra lateral izquierda organiza las sesiones por tipo de tarea. Cada entrada de sesión muestra su nombre y el dataset desde el que fue creada. Puedes mantener múltiples sesiones para el mismo dataset y tarea para explorar diferentes configuraciones de columnas o estrategias de división.

### Divisiones de Datos

dashAI admite tres estrategias de división:

| Estrategia                      | Cuándo usarla                                                               |
| ------------------------------- | --------------------------------------------------------------------------- |
| **Predefinida**                 | El dataset ya contiene la estructura tren/prueba/validación desde el origen |
| **Aleatoria por proporción**    | División estándar usando proporciones configurables (por defecto: 60/20/20) |
| **Manual por índices de filas** | Control total sobre qué filas van a cada subconjunto                        |

Para divisiones aleatorias, tres opciones adicionales refinan el comportamiento:

- **Mezclar**: aleatoriza el orden de las filas antes de dividir. Habilitado por defecto. Desactívalo solo cuando el orden de las filas sea significativo (p. ej., series de tiempo).
- **Estratificar**: preserva la distribución de clases de la columna de salida en cada división. Crítico para datasets desequilibrados donde las clases minoritarias podrían estar subrepresentadas en divisiones más pequeñas.
- **Semilla**: semilla aleatoria fija para reproducibilidad. El valor por defecto es 42. Establece un valor específico cuando necesitas comparar modelos entrenados en divisiones idénticas.

---

## Modelos Disponibles

### Clasificación Tabular (Scikit-learn)

| Modelo                           | Notas                                                                                                                          |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `SVC`                            | Clasificador de Vectores de Soporte. Efectivo en espacios de alta dimensionalidad. Opciones de kernel: lineal, rbf, polinomial |
| `LogisticRegression`             | Modelo lineal para clasificación binaria y multiclase. Rápido e interpretable                                                  |
| `RandomForestClassifier`         | Conjunto de árboles de decisión. Robusto ante el sobreajuste, maneja tipos de características mixtas                           |
| `DecisionTreeClassifier`         | Modelo de árbol único. Totalmente interpretable, propenso al sobreajuste sin límites de profundidad                            |
| `KNeighborsClassifier`           | Aprendizaje basado en instancias usando la distancia a los k vecinos más cercanos                                              |
| `HistGradientBoostingClassifier` | Gradient boosting basado en histogramas. Maneja grandes datasets eficientemente, admite valores NA nativos                     |
| `DummyClassifier`                | Modelo de línea base usando reglas simples (más frecuente, estratificado, etc.). Úsalo como piso de rendimiento                |

### Regresión (Scikit-learn)

| Modelo                      | Notas                                                               |
| --------------------------- | ------------------------------------------------------------------- |
| `LinearRegression`          | Mínimos cuadrados ordinarios. Simple, rápido, interpretable         |
| `LinearSVR`                 | Regresión de Vectores de Soporte con kernel lineal                  |
| `RidgeRegression`           | Regresión lineal con regularización L2. Maneja la multicolinealidad |
| `RandomForestRegressor`     | Regresión por conjuntos. Maneja relaciones no lineales              |
| `GradientBoostingRegressor` | Conjunto secuencial. Alta precisión, más lento de entrenar          |
| `MLPRegressor`              | Perceptrón multicapa. Modelo no lineal flexible                     |

### Clasificación de Texto (Hugging Face)

| Modelo                              | Notas                                                                                                           |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `DistilBertTransformer`             | BERT destilado, un transformador rápido y preciso para clasificación de texto. Requiere GPU para uso práctico   |
| `BagOfWordsTextClassificationModel` | Enfoque tradicional de vectores dispersos con un clasificador lineal. Rápido, interpretable, compatible con CPU |

### Traducción (Hugging Face)

| Modelo                  | Notas                                                                    |
| ----------------------- | ------------------------------------------------------------------------ |
| `OpusMtEnESTransformer` | Traducción del inglés al español usando los modelos Helsinki-NLP Opus-MT |

---

## Configuración de Hiperparámetros

Cada modelo expone sus hiperparámetros configurables en el modal **Agregar Modelo**. Los parámetros varían según el algoritmo, y cada parámetro tiene un ícono de ayuda **?** con una descripción.

### Configuración Manual

Establece un valor fijo para cada parámetro. Este es el modo predeterminado, adecuado cuando tienes conocimiento previo sobre buenos valores o quieres probar configuraciones específicas.

### Optimización de Hiperparámetros

Cada parámetro numérico tiene un interruptor **Optimizar**. Habilitarlo le indica a dashAI que busque automáticamente el mejor valor para ese parámetro en lugar de usar el valor fijo. Puedes habilitar la optimización en cualquier subconjunto de parámetros simultáneamente.

Hay dos optimizadores disponibles:

| Optimizador           | Estrategia                                                                                                                                          |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **OptunaOptimizer**   | Optimización bayesiana usando el muestreador TPE de Optuna. Eficiente, ya que enfoca los ensayos en regiones prometedoras del espacio de parámetros |
| **HyperOptOptimizer** | Estimador de Parzen estructurado en árbol (TPE) a través de HyperOpt. Estrategia similar a Optuna                                                   |

Durante la optimización, dashAI registra métricas por ensayo y genera gráficos de visualización:

- **Gráfico de historial**: valor de la métrica a través de todos los ensayos
- **Coordenadas paralelas**: relación entre combinaciones de parámetros y valores de métricas
- **Gráfico de corte**: efecto de parámetros individuales en la métrica
- **Gráfico de importancia**: qué parámetros tienen mayor influencia en el resultado

---

## Entrenamiento y Estado

Cada modelo en una sesión tiene un estado que refleja su estado actual:

| Estado          | Significado                                           |
| --------------- | ----------------------------------------------------- |
| **Not Started** | El modelo ha sido agregado pero nunca entrenado       |
| **Finalizado**  | El entrenamiento se completó exitosamente             |
| **Error**       | El entrenamiento falló; revisa los parámetros o datos |

Botones de acción por modelo:

- **ENTRENAR / RE-ENTRENAR**: iniciar o reiniciar el entrenamiento. Reentrenar sobreescribe los resultados de la ejecución anterior.
- **EDITAR**: modificar el nombre del modelo o los hiperparámetros antes de reentrenar.
- **EJECUTAR TODOS**: encola todos los modelos no entrenados en la sesión para ejecución secuencial.

El entrenamiento se ejecuta como un trabajo en segundo plano rastreado en la **Cola de Trabajos** (parte inferior derecha de la pantalla). Puedes monitorear el progreso y ver los detalles de errores ahí.

---

## Métricas de Evaluación

Las métricas se muestran en la pestaña **MÉTRICAS EN VIVO** de cada tarjeta de modelo, divididas en tres subpestañas: Entrenamiento, Validación y Prueba.

### Métricas de Clasificación

| Métrica             | Qué mide                                                                             |
| ------------------- | ------------------------------------------------------------------------------------ |
| **Accuracy**        | Proporción de predicciones correctas en general                                      |
| **F1**              | Media armónica de Precisión y Recall. Mejor que Accuracy para clases desequilibradas |
| **Precision**       | De todos los positivos predichos, cuántos eran realmente positivos                   |
| **Recall**          | De todos los positivos reales, cuántos fueron correctamente predichos                |
| **ROCAUC**          | Área bajo la curva ROC. Mide la separabilidad en todos los umbrales de clasificación |
| **LogLoss**         | Penaliza las predicciones incorrectas con alta confianza. Menor es mejor             |
| **HammingDistance** | Fracción de etiquetas que son incorrectamente predichas                              |
| **CohenKappa**      | Acuerdo entre predicciones y etiquetas verdaderas, corrigiendo por azar              |

### Métricas de Regresión

| Métrica  | Qué mide                                                         |
| -------- | ---------------------------------------------------------------- |
| **RMSE** | Error Cuadrático Medio, penaliza los errores grandes más que MAE |
| **MAE**  | Error Absoluto Medio, la magnitud promedio de los errores        |

### Métricas de Traducción

| Métrica  | Qué mide                                                                             |
| -------- | ------------------------------------------------------------------------------------ |
| **BLEU** | Superposición de n-gramas entre traducciones generadas y de referencia               |
| **TER**  | Tasa de Edición de Traducción, ediciones necesarias para coincidir con la referencia |

---

## Comparación de Modelos

El panel de **Comparación de Modelos** en la parte superior de cada sesión proporciona una vista unificada de todos los modelos y su rendimiento.

### Vista de Tabla

Todos los modelos de la sesión aparecen como filas con sus valores de métricas lado a lado. Cambia entre las divisiones de **ENTRENAMIENTO**, **VALIDACIÓN** y **PRUEBA** usando los botones en la parte superior. Los modelos que no han sido entrenados muestran `-` en las columnas de métricas.

Evalúa siempre la selección final del modelo en la división de **PRUEBA**, porque las métricas de entrenamiento y validación pueden no reflejar el verdadero rendimiento de generalización.

### Vista de Gráficos

Dos tipos de gráficos apoyan la comparación visual:

**Gráfico de barras**: agrupa métricas en el eje x con una barra por modelo por métrica. El mejor para comparar modelos en una sola métrica de un vistazo.

**Gráfico de radar**: cada eje es una métrica; cada modelo es un polígono. Un polígono más grande y regular indica un rendimiento consistentemente sólido en todas las métricas. Los polígonos irregulares revelan compensaciones. Un modelo fuerte en Accuracy pero débil en Recall, por ejemplo, crea una forma visiblemente irregular.

El panel de **Métricas** te permite seleccionar qué métricas aparecen en el gráfico. Usa **TODAS** / **NINGUNA** para alternar rápidamente.

---

## Predicciones

Después del entrenamiento, cada modelo puede generar predicciones en dos modos, a los que se accede desde la pestaña **PREDICCIONES** de la tarjeta del modelo.

### Predicciones sobre Dataset

Ejecuta el modelo contra un dataset completo cargado en dashAI. Útil para puntuación por lotes, como aplicar el modelo a un conjunto de validación, un conjunto de retención o nuevos datos entrantes.

El modal muestra una vista previa del dataset seleccionado con sus columnas de entrada y columna objetivo resaltadas, para que puedas verificar la compatibilidad antes de enviar. Los resultados están disponibles como vista previa en línea (primeras 100 filas) y como descarga CSV completa.

### Predicciones Manuales

Ingresa una o más filas de datos directamente, sin necesidad de ningún archivo. Las columnas categóricas aparecen como menús desplegables con valores válidos; las columnas numéricas son texto libre. Se pueden agregar múltiples filas con **Agregar Fila**.

Este modo es particularmente útil para:

- Demostrar el comportamiento del modelo en ejemplos específicos
- Probar casos límite y condiciones de frontera
- Contextos de aula o presentación donde quieres mostrar cómo las entradas individuales afectan las predicciones

---

## Explicabilidad

La pestaña **EXPLICABILIDAD** de cada modelo entrenado proporciona herramientas para comprender las decisiones del modelo. Hay dos tipos disponibles.

### Explicadores Globales

Analizan el comportamiento del modelo en todo el dataset: qué características importan más en general y cómo se relacionan con la salida del modelo.

| Explicador                         | Qué produce                                                                                                                        |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Kernel SHAP**                    | Valores SHAP para cada característica, cuantificando su contribución a las predicciones en todo el dataset                         |
| **Permutation Feature Importance** | Clasifica las características según cuánto disminuye el rendimiento del modelo cuando cada característica se mezcla aleatoriamente |
| **Partial Dependence**             | Muestra el efecto marginal de una o dos características en el resultado predicho                                                   |

### Explicadores Locales

Analizan el comportamiento del modelo para una predicción específica: por qué el modelo produjo esta salida para esta entrada particular.

Los explicadores locales ayudan a identificar comportamientos inesperados en instancias específicas, lo que es valioso tanto para depurar modelos como para explicar decisiones individuales a las partes interesadas.

---

## Consejos

- Incluye siempre un **DummyClassifier** (o equivalente de línea base) en cada sesión. Cualquier modelo que no supere al dummy necesita más ajuste.
- Habilita **Estratificar** siempre que tu columna objetivo tenga desequilibrio de clases, porque evita divisiones donde la clase minoritaria esté ausente o subrepresentada en validación o prueba.
- Usa una **Semilla** fija entre sesiones cuando compares enfoques, ya que las divisiones idénticas eliminan la variabilidad de datos como factor de confusión.
- Las métricas de la división de **PRUEBA** son la medida autorizada de generalización. Buenas métricas de entrenamiento con malas métricas de prueba indican sobreajuste.
- Ejecuta **Permutation Feature Importance** antes de finalizar un modelo. A menudo revela que algunas columnas de entrada agregan ruido en lugar de señal y pueden eliminarse para simplificar el modelo.
- Cuando uses **DistilBertTransformer** para clasificación de texto, asegúrate de que tus columnas de texto sin procesar se pasen directamente. No apliques convertidores TF-IDF o BagOfWords antes, ya que el transformador maneja su propia tokenización.
