---
title: Tipos Semánticos
sidebar_label: Tipos Semánticos
sidebar_position: 4
---

# Tipos Semánticos

## ¿Qué Son los Tipos Semánticos?

Cuando se carga un dataset, dashAI asigna un **tipo semántico** a cada columna. Los tipos semánticos van más allá de los formatos de almacenamiento en bruto (p. ej., `int32` o `string` de PyArrow) para expresar la naturaleza significativa de los datos para el ML: ¿es esta columna una medida continua, una etiqueta discreta, un texto libre, una fecha?

Esta clasificación impulsa tres comportamientos críticos en toda la plataforma:

- **Compatibilidad de tareas**: solo las columnas cuyos tipos coinciden con los requisitos de una tarea pueden seleccionarse como entradas o salidas.
- **Encadenamiento de converters**: los converters declaran el tipo que aceptan y el tipo que producen, habilitando pipelines de preprocesamiento seguras.
- **Codificación de etiquetas**: las columnas de salida categóricas se codifican automáticamente como enteros antes del entrenamiento y se decodifican de vuelta a etiquetas de cadena tras la predicción.

---

## Jerarquía de Tipos

Todos los tipos semánticos heredan de una clase base abstracta común, `DashAIDataType`.

```
DashAIDataType
├── DashAIValue          # padre abstracto para todos los tipos de valor
│   ├── Integer          # int8, int16, int32, int64 (con o sin signo)
│   ├── Float            # float16, float32, float64
│   ├── Text             # cadena con codificación (por defecto: UTF-8)
│   ├── Date             # fecha de calendario (formato por defecto: YYYY-MM-DD)
│   ├── Time             # hora del día (formato por defecto: HH:mm:ss)
│   ├── Timestamp        # fecha y hora con zona horaria (por defecto: YYYY-MM-DD HH:mm:ss)
│   ├── Duration         # tiempo transcurrido con unidad (s, ms, us, ns)
│   ├── Decimal          # decimal preciso (128 o 256 bits, con precisión y escala)
│   └── Binary           # datos binarios en bruto
└── Categorical          # etiquetas discretas con mapa de codificación str ↔ int
```

Los tipos `DashAIValue` representan medidas continuas u ordenadas. `Categorical` es una rama separada porque lleva estructura adicional: la lista completa de categorías únicas y un mapeo de codificación biyectivo.

---

## Tipos Concretos

### Tipos de Valor

| Tipo        | Atributos clave                     | Uso típico                                                    |
| ----------- | ----------------------------------- | ------------------------------------------------------------- |
| `Integer`   | `dtype` (p. ej. `int64`), `signed`  | Características de conteo, etiquetas con codificación ordinal |
| `Float`     | `dtype` (p. ej. `float64`)          | Medidas continuas, objetivos de regresión                     |
| `Text`      | `dtype` (`string`), `encoding`      | Texto libre, tareas de NLP                                    |
| `Date`      | `format` (por defecto `YYYY-MM-DD`) | Fechas de calendario                                          |
| `Time`      | `format` (por defecto `HH:mm:ss`)   | Valores de hora del día                                       |
| `Timestamp` | `format`, `timezone`                | Fecha y hora con zona horaria                                 |
| `Duration`  | `unit` (`s`, `ms`, `us`, `ns`)      | Intervalos de tiempo                                          |
| `Decimal`   | `precision`, `scale`, `bit_width`   | Numéricos de alta precisión                                   |
| `Binary`    | -                                   | Cargas útiles de bytes en bruto                               |

### Categorical

`Categorical` es el tipo estructuralmente más rico. Almacena:

- `categories`: lista ordenada de valores de cadena únicos (`["cat", "dog", "bird"]`)
- `dtype`: tipo de almacenamiento subyacente de PyArrow (`string`, `int64`, etc.)
- `encoding` / `str2int`: diccionario que mapea cada categoría a un entero (`{"cat": 0, "dog": 1, "bird": 2}`)
- `decoding` / `int2str`: mapeo inverso (`{0: "cat", 1: "dog", 2: "bird"}`)
- `converted`: indicador de si la columna ya ha sido codificada como entero

`Categorical` se usa para todas las columnas de destino de clasificación y para cualquier columna de característica que contenga un conjunto discreto de etiquetas (p. ej., país, categoría de producto).

---

## Inferencia de Tipos

Los tipos se asignan automáticamente cuando se carga un dataset. dashAI soporta dos métodos de inferencia, seleccionables al momento de la carga.

### Primario: `DashAIPtype`

Usa el modelo de inferencia de tipos probabilístico **ptype**, que analiza los valores de cada columna para estimar el tipo semántico más probable. Salidas de ptype soportadas y sus mapeos en dashAI:

| Salida ptype    | Tipo dashAI                                   |
| --------------- | --------------------------------------------- |
| `integer`       | `Integer` (`int64`)                           |
| `float`         | `Float` (`float64`)                           |
| `string`        | `Text` (`string`, UTF-8)                      |
| `boolean`       | `Categorical` (`string`)                      |
| `categorical`   | `Categorical` (`string`)                      |
| `date-iso-8601` | `Text` (análisis de fechas aún no automático) |
| `date-eu`       | `Text`                                        |
| `float_comma`   | `Float` (coma decimal normalizada)            |

Después de la clasificación con ptype, cualquier columna cuyo conteo y proporción de valores únicos estén dentro de los umbrales configurables se promueve adicionalmente a `Categorical`, independientemente de la salida original de ptype.

### Alternativa: `DummyCategoricalInference`

Una heurística ligera utilizada cuando ptype no está disponible:

- Columnas de cadena con menos de 10 valores únicos → `Categorical`
- Columnas enteras con menos de 10 valores únicos → `Categorical`
- Todas las demás columnas enteras → `Integer`
- Todas las demás columnas de cadena → `Text`
- Columnas flotantes → `Float`

### Casos Especiales

- Las columnas PyArrow `bool` siempre se mapean a `Categorical` (dos categorías: `True`/`False`).
- Las columnas codificadas como diccionario de PyArrow se mapean a `Categorical` con una lista de categorías inicialmente vacía.

---

## Persistencia de Tipos

Los tipos semánticos se serializan en los **metadatos de la tabla Apache Arrow** bajo la clave `dashai_types` y se almacenan junto al archivo Arrow IPC del dataset. Esto significa:

- Los tipos sobreviven a ciclos de guardado/carga sin necesidad de reinferencia.
- Los Notebooks heredan los tipos de su dataset fuente.
- Los converters que cambian el tipo de una columna actualizan los metadatos en el lugar.

Las utilidades relevantes son `save_types_in_arrow_metadata()` y `get_types_from_arrow_metadata()` en `DashAI/back/types/utils.py`.

---

## Cómo Se Usan los Tipos

### Compatibilidad de Tareas

Cada clase de tarea declara los tipos semánticos que acepta para las columnas de entrada y salida mediante un diccionario `metadata`:

```python
metadata = {
    "inputs_types": [
        Float,
        Integer,
        Categorical,
    ],  # tipos de columnas de entrada permitidos
    "outputs_types": [Categorical],  # tipo de columna de salida requerido
    "inputs_cardinality": "n",  # cualquier número de entradas
    "outputs_cardinality": 1,  # exactamente una salida
}
```

Antes del entrenamiento, `validate_dataset_for_task()` verifica que el tipo semántico de cada columna seleccionada esté en el conjunto permitido. Las columnas que no coinciden se rechazan con un error descriptivo.

**Requisitos de tipos por tarea:**

| Tarea                       | Tipos de entrada permitidos       | Tipo de salida requerido              |
| --------------------------- | --------------------------------- | ------------------------------------- |
| `TabularClassificationTask` | `Float`, `Integer`, `Categorical` | `Categorical`                         |
| `RegressionTask`            | `Float`, `Integer`, `Categorical` | `Float` o `Integer`                   |
| `TextClassificationTask`    | `Text` (exactamente 1 columna)    | `Categorical` (exactamente 1 columna) |
| `TranslationTask`           | `Text` (exactamente 1 columna)    | `Text` (exactamente 1 columna)        |

### Contratos de Tipos de Converters

Cada converter implementa `get_output_type(column_name)` para declarar el tipo semántico de cada columna de salida. Esto permite a dashAI rastrear el tipo de cada columna a través de una pipeline de preprocesamiento de múltiples pasos.

**Contratos de converters comunes:**

| Converter                        | Tipo de entrada    | Tipo de salida                                |
| -------------------------------- | ------------------ | --------------------------------------------- |
| `OneHotEncoder`                  | `Categorical`      | `Integer` (una columna binaria por categoría) |
| `OrdinalEncoder`                 | `Categorical`      | `Integer`                                     |
| `LabelEncoder`                   | `Categorical`      | `Integer`                                     |
| `LabelBinarizer`                 | `Categorical`      | `Integer`                                     |
| `StandardScaler`                 | `Integer`, `Float` | `Float`                                       |
| `MinMaxScaler`                   | `Integer`, `Float` | `Float`                                       |
| `Normalizer`                     | `Integer`, `Float` | `Float`                                       |
| `Binarizer`                      | `Integer`, `Float` | `Integer`                                     |
| `TFIDFConverter`                 | `Text`             | `Float`                                       |
| `BagOfWordsConverter`            | `Text`             | `Float`                                       |
| `TokenizerConverter`             | `Text`             | `Integer`                                     |
| `PCA`, `TruncatedSVD`, `FastICA` | `Integer`, `Float` | `Float`                                       |

### Codificación de Etiquetas

Las tareas de clasificación requieren una columna de salida `Categorical`, pero la mayoría de los modelos de ML requieren objetivos numéricos. dashAI maneja esto automáticamente:

1. **Antes del entrenamiento**: `categorical_label_encoder()` convierte cada columna de salida `Categorical` a `Integer` usando el mapa `str2int` del tipo `Categorical`. El mapeo se guarda para poder revertirlo.
2. **Después de la predicción**: `process_predictions()` aplica el mapa inverso `int2str` para convertir las predicciones enteras de vuelta a sus etiquetas de cadena originales antes de mostrar los resultados o guardarlos en disco.

No se necesita ningún paso de codificación manual por parte del usuario.

### Validación de Tipos

Cuando un usuario cambia manualmente el tipo semántico de una columna en la UI, `validate_type_change()` verifica si la conversión es segura y factible:

| De \ A        |        `Integer`        |      `Float`       | `Text` |       `Categorical`       | `Date` | `Time` | `Timestamp` |
| ------------- | :---------------------: | :----------------: | :----: | :-----------------------: | :----: | :----: | :---------: |
| `Integer`     |            -            |         Sí         |   Sí   | Sí (si baja cardinalidad) |   -    |   -    |      -      |
| `Float`       | Sí (si números enteros) |         -          |   Sí   | Sí (si baja cardinalidad) |   -    |   -    |      -      |
| `Text`        |   Sí (si analizable)    | Sí (si analizable) |   -    | Sí (si baja cardinalidad) |   Sí   |   Sí   |     Sí      |
| `Categorical` |           Sí            |         Sí         |   Sí   |             -             |   -    |   -    |      -      |
| `Date`        |            -            |         -          |   Sí   |             -             |   -    |   -    |      -      |
| `Time`        |            -            |         -          |   Sí   |             -             |   -    |   -    |      -      |
| `Timestamp`   |            -            |         -          |   Sí   |             -             |   -    |   -    |      -      |

Si la conversión no es segura (p. ej., promover una columna de texto de alta cardinalidad a `Categorical`), el validador devuelve un error descriptivo antes de que se modifique ningún dato.

---

## Archivos Fuente

| Archivo                                      | Rol                                                    |
| -------------------------------------------- | ------------------------------------------------------ |
| `DashAI/back/types/dashai_data_type.py`      | Clase base abstracta `DashAIDataType`                  |
| `DashAI/back/types/dashai_value.py`          | Clase intermedia abstracta `DashAIValue`               |
| `DashAI/back/types/value_types.py`           | Clases de tipos de valor concretos                     |
| `DashAI/back/types/categorical.py`           | Tipo `Categorical` con lógica de codificación          |
| `DashAI/back/types/utils.py`                 | Conversión de tipos Arrow ↔ dashAI, E/S de metadatos   |
| `DashAI/back/types/type_validation.py`       | `validate_type_change()` y verificaciones de idoneidad |
| `DashAI/back/types/inf/inference_methods.py` | `DashAIPtype` y `DummyCategoricalInference`            |
| `DashAI/back/types/inf/type_inference.py`    | Punto de entrada `infer_types()`                       |
