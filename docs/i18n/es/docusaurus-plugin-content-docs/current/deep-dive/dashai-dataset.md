---
title: DashAIDataset
sidebar_label: DashAIDataset
sidebar_position: 9
---

# DashAIDataset

## ¿Qué Es DashAIDataset?

`DashAIDataset` es el primitivo central de datos de dashAI. Extiende la clase `Dataset` de HuggingFace con dos responsabilidades adicionales:

- **Metadatos de tipo semántico**: un diccionario `_types` (`Dict[str, DashAIDataType]`) que mapea cada nombre de columna a su tipo semántico dashAI (ver [Tipos Semánticos](/deep-dive/semantic-types)). Estos metadatos se persisten dentro del esquema Apache Arrow para sobrevivir ciclos de guardado/carga.
- **Metadatos de splits**: un diccionario `splits` que registra qué índices de fila pertenecen a qué split (`train`, `test`, `validation`), junto con estadísticas agregadas calculadas durante la carga del dataset.

Cada pieza de datos que fluye por dashAI (carga, transformaciones en el notebook, entrenamiento de modelos, predicciones) se representa como un `DashAIDataset`.

---

## Estructura Interna

### Atributos de Instancia

| Atributo | Tipo                        | Descripción                                                              |
| -------- | --------------------------- | ------------------------------------------------------------------------ |
| `_table` | `pyarrow.Table`             | La tabla Arrow subyacente. Todos los datos de columnas residen aquí.     |
| `_types` | `Dict[str, DashAIDataType]` | Tipo semántico de cada columna. Sincronizado con los metadatos de Arrow. |
| `splits` | `dict`                      | Índices de splits y estadísticas calculadas (ver abajo).                 |

### El Diccionario `splits`

`splits` es un dict Python plano. Sus claves se van poblando de forma progresiva:

| Clave               | Establecido por                           | Contenido                                                                           |
| ------------------- | ----------------------------------------- | ----------------------------------------------------------------------------------- |
| `split_indices`     | `split_dataset` / `update_dataset_splits` | `{"train": [...], "test": [...], "validation": [...]}` (listas de índices de fila)  |
| `column_names`      | `compute_base_metadata` / `save_dataset`  | Lista de nombres de columnas                                                        |
| `total_rows`        | `compute_base_metadata` / `save_dataset`  | Número total de filas                                                               |
| `nan`               | `compute_base_metadata`                   | Conteo de NaN por columna                                                           |
| `general_info`      | `compute_metadata`                        | Conteo de filas/columnas, memoria, duplicados, mapa de dtypes                       |
| `numeric_stats`     | `compute_metadata`                        | Estadísticas descriptivas por columna numérica                                      |
| `categorical_stats` | `compute_metadata`                        | Conteos de valores y top-5 por columna categórica                                   |
| `text_stats`        | `compute_metadata`                        | Estadísticas de longitud y conteo de palabras para columnas de texto                |
| `quality_info`      | `compute_metadata`                        | Completitud, columnas constantes, columnas de alta cardinalidad, puntaje de calidad |
| `correlations`      | `compute_metadata`                        | Matriz de correlación de Pearson para columnas numéricas                            |

### Metadatos de Arrow

Los tipos semánticos se serializan en los metadatos del esquema de la tabla Arrow bajo la clave `dashai_types`:

```python
table.schema.metadata[b"dashai_types"]  # mapa de tipos serializado en JSON
```

Las utilidades `save_types_in_arrow_metadata()` y `get_types_from_arrow_metadata()` en `DashAI/back/types/utils.py` gestionan esta serialización. Cuando `DashAIDataset` se construye con `types=None`, lee el mapa de tipos directamente de los metadatos de Arrow.

---

## Formato en Disco

`save_dataset` escribe dos archivos en un directorio:

```
<dataset_path>/
├── data.arrow    # Archivo IPC de PyArrow - tabla + metadatos de tipos en el esquema
└── splits.json   # JSON - índices de splits, conteos de filas, mapa de NaN, estadísticas calculadas
```

`load_dataset` lee ambos archivos y reconstruye el `DashAIDataset`. Los tipos se recuperan de los metadatos del esquema Arrow, por lo que no se necesita un archivo de tipos separado.

---

## Métodos de Instancia Clave

### `get_split(split_name)`

Devuelve un nuevo `DashAIDataset` que contiene solo las filas del split solicitado.

```python
train_ds = dataset.get_split("train")  # usa split_indices["train"]
```

`split_name` debe existir en `splits["split_indices"]`. Los metadatos `splits` del dataset devuelto contienen únicamente la lista de índices de ese split.

### `select_columns(column_names)`

Devuelve un nuevo `DashAIDataset` con solo las columnas especificadas, copiando los tipos correspondientes.

```python
features_ds = dataset.select_columns(["age", "income", "city"])
```

### `sample(n, method, seed)`

Devuelve `n` filas como un `dict` Python plano. `method` controla la selección:

| Método     | Comportamiento                                 |
| ---------- | ---------------------------------------------- |
| `"head"`   | Primeras `n` filas                             |
| `"tail"`   | Últimas `n` filas                              |
| `"random"` | `n` filas aleatorias (reproducible con `seed`) |

### `compute_metadata()`

Ejecuta todos los cálculos de EDA y almacena los resultados en `self.splits`. Se llama una vez tras la carga. Requiere que `_types` esté definido. Devuelve `self`.

### `compute_base_metadata()`

Subconjunto ligero de `compute_metadata()` que solo establece `column_names`, `total_rows` y `nan`. Se usa cuando no se necesitan estadísticas completas.

### `keys()`

Devuelve la lista de nombres de splits disponibles en `splits["split_indices"]`. Refleja la interfaz `DatasetDict.keys()` para que `DashAIDataset` pueda usarse de forma intercambiable en algunos contextos.

---

## Funciones del Ciclo de Vida del Dato

Estas funciones a nivel de módulo cubren el recorrido completo desde la entrada en bruto hasta los splits listos para entrenamiento.

### Carga y Conversión

**`to_dashai_dataset(dataset, types=None)`**

Conversor universal. Acepta `DashAIDataset` (pass through), `Dataset` de HuggingFace, `DatasetDict` de HuggingFace, o `pandas.DataFrame`. Los `DatasetDict` con múltiples splits se fusionan mediante `merge_splits_with_metadata`.

```python
from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

ds = to_dashai_dataset(my_hf_dataset, types=my_type_map)
```

**`merge_splits_with_metadata(dataset_dict)`**

Concatena todos los splits de un `DatasetDict` en un único `DashAIDataset` y registra los rangos de índices de fila en `splits["split_indices"]`. Los splits se fusionan en orden de clave alfabético.

### Persistencia

**`save_dataset(dataset, path, schema=None)`**

Escribe `data.arrow` y `splits.json` en `path`. Si se proporciona `schema`, se aplica `transform_dataset_with_schema` primero.

**`load_dataset(dataset_path)`**

Lee `data.arrow` y `splits.json` desde `dataset_path` y devuelve un `DashAIDataset`. Los tipos se recuperan de los metadatos de Arrow.

**`get_columns_spec(dataset_path)`**

Lee solo el esquema Arrow (sin datos de filas) y devuelve un `Dict[str, Dict]` que describe el tipo, dtype y (para columnas `Categorical`) la lista de categorías de cada columna. Es usado por la API para retornar metadatos de columnas sin cargar el dataset completo.

### Transformación de Tipos

**`transform_dataset_with_schema(dataset, schema)`**

Aplica un esquema de tipos al dataset, convirtiendo las columnas a sus tipos Arrow destino y actualizando `_types`. El formato del `schema` es:

```python
schema = {
    "age": {"type": "Integer", "dtype": "int64"},
    "income": {"type": "Float", "dtype": "float64"},
    "city": {"type": "Categorical", "dtype": "string", "converted": False},
}
```

Las columnas `Categorical` tienen su lista de categorías inferida a partir de los datos reales en este punto, garantizando que ningún valor sea excluido silenciosamente.

### Splitting

**`split_indexes(total_rows, train_size, test_size, val_size, seed, shuffle, stratify, labels)`**

Devuelve `(train_indexes, test_indexes, val_indexes)` como listas de índices de fila enteros. Usa una estrategia en dos fases:

1. Divide todas las filas en `train` vs `test+validation`.
2. Divide `test+validation` en `test` y `validation` proporcionalmente.

Soporta splitting estratificado: pasar el array de etiquetas en `labels`.

**`split_dataset(dataset, train_indexes, test_indexes, val_indexes)`**

Particiona `dataset` en un `DatasetDict` con claves `"train"`, `"test"` y `"validation"`, siendo cada uno un `DashAIDataset`. Los tipos de columnas del dataset original se preservan.

Si los tres argumentos de índice son `None`, la función lee los `split_indices` existentes en `dataset.splits`.

**`update_dataset_splits(dataset, new_splits, is_random)`**

Actualiza `dataset.splits["split_indices"]` en lugar.

- `is_random=True`: los valores de `new_splits` son proporciones flotantes; se llama a `split_indexes` para generar las listas de filas.
- `is_random=False`: los valores de `new_splits` ya son listas de índices de fila; se usan directamente.

### Preparación para Entrenamiento

**`prepare_for_model_session(dataset, splits, output_columns)`**

Punto de entrada de alto nivel usado por el sistema de jobs antes del entrenamiento. Gestiona el pipeline completo de splits:

1. Determina el tipo de split desde `splits["splitType"]` (`"manual"`, `"predefined"` o `"random"`).
2. Llama a `split_dataset` con las listas de índices apropiadas.
3. Devuelve `(prepared_dataset, index_map)` donde `index_map` tiene las claves `train_indexes`, `test_indexes`, `val_indexes`.

Para splits aleatorios con `stratify=True`, lee los valores de la columna de salida y los pasa como etiquetas a `split_indexes`.

---

## Modificar Datos con `modify_table`

**`modify_table(dataset, columns, types=None)`**

Usado dentro de converters y modelos para reemplazar o agregar columnas preservando todas las demás columnas y metadatos.

```python
import pyarrow as pa
from DashAI.back.dataloaders.classes.dashai_dataset import modify_table

new_col = pa.array([1.0, 2.0, 3.0], type=pa.float64())
result = modify_table(
    dataset, {"scaled_age": new_col}, types={"scaled_age": Float("float64")}
)
```

- Las columnas en `columns` que ya existen en el dataset son reemplazadas.
- Las columnas nuevas requieren una entrada correspondiente en `types`.
- Los metadatos Arrow originales (incluyendo `dashai_types`) se preservan y extienden.

---

## Relación con Otros Subsistemas

```
DataLoader
  └─ carga archivo en bruto → DashAIDataset (tipos inferidos por DashAIPtype)
        │
        ├─ Espacio de trabajo Notebook
        │     └─ Converter.fit_transform(DashAIDataset) → DashAIDataset
        │          (modify_table usado internamente)
        │
        └─ Entrenamiento de modelos
              └─ prepare_for_model_session → DatasetDict de DashAIDatasets
                    └─ select_columns → par (X_train, y_train)
```

- **DataLoaders** producen `DashAIDataset` mediante `to_dashai_dataset`.
- **Converters** consumen y devuelven `DashAIDataset`, usando `modify_table` para actualizar columnas.
- **Modelos** reciben un `DatasetDict` de `prepare_for_model_session` y llaman a `get_split` / `select_columns` para extraer sus entradas.
- **Explorers** reciben un `DashAIDataset` y leen `_types` para despachar visualizaciones apropiadas por tipo de columna.

---

## Archivos Fuente

| Archivo                                             | Rol                                                                                                     |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `DashAI/back/dataloaders/classes/dashai_dataset.py` | Clase `DashAIDataset` y todas las funciones a nivel de módulo                                           |
| `DashAI/back/types/utils.py`                        | Serialización de tipos Arrow ↔ dashAI (`save_types_in_arrow_metadata`, `get_types_from_arrow_metadata`) |
| `DashAI/back/types/value_types.py`                  | Clases de tipos de valor concretos usados en `_types`                                                   |
| `DashAI/back/types/categorical.py`                  | Tipo `Categorical` con codificación `str2int` / `int2str`                                               |
