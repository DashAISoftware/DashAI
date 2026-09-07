---
title: Componentes
sidebar_label: Componentes
---

## ¿Qué es un Componente?

Un **componente** es el bloque de construcción fundamental de dashAI. Toda pieza de funcionalidad conectable es un componente: modelos, tareas, métricas, exploradores, explicadores, converters, cargadores de datos, optimizadores y trabajos.

## Tipos de Componentes

Cada clase de componente declara un atributo de clase `TYPE` que determina su categoría:

| TYPE              | Clase base            | Propósito                                    | Ejemplos                                                            |
| ----------------- | --------------------- | -------------------------------------------- | ------------------------------------------------------------------- |
| `Model`           | `BaseModel`           | Entrenar y predecir                          | SVC, RandomForest, DistilBertTransformer                            |
| `GenerativeModel` | `BaseGenerativeModel` | Generar salidas a partir de prompts/entradas | QwenModel, StableDiffusionV2Model                                   |
| `Task`            | `BaseTask`            | Definir la semántica de tareas de ML         | TextClassification, Regression, Translation                         |
| `GenerativeTask`  | `BaseGenerativeTask`  | Definir la semántica de tareas generativas   | TextToTextGenerationTask, TextToImageGenerationTask, ControlNetTask |
| `Metric`          | `BaseMetric`          | Evaluar el rendimiento del modelo            | Accuracy, F1, RMSE, MAE                                             |
| `Explorer`        | `BaseExplorer`        | Visualizar y analizar datos                  | ScatterPlotExplorer, HistogramPlotExplorer                          |
| `Explainer`       | `BaseExplainer`       | Interpretar las predicciones del modelo      | KernelShap, PermutationFeatureImportance                            |
| `Converter`       | `BaseConverter`       | Transformar características                  | StandardScaler, OneHotEncoder, PCA, SMOTE                           |
| `DataLoader`      | `BaseDataLoader`      | Cargar datasets desde archivos               | CSVDataLoader, ExcelDataLoader                                      |
| `Optimizer`       | `BaseOptimizer`       | Optimización de hiperparámetros              | Optimizadores basados en Optuna                                     |
| `Job`             | `BaseJob`             | Ejecución de tareas en segundo plano         | ModelJob, ExplorerJob, PredictJob                                   |

## Metadatos de los Componentes

Cada componente puede exponer metadatos utilizados por el frontend para visualización y filtrado:

- `DESCRIPTION`: una descripción multilingüe de lo que hace el componente.
- `DISPLAY_NAME`: un nombre legible por humanos.
- `COLOR`: un color hexadecimal para la representación en la UI.
- `COMPATIBLE_COMPONENTS`: una lista de nombres de componentes con los que este componente es compatible (p. ej., una métrica que solo aplica a tareas de clasificación).

---

## Registro de Componentes

El **Registro de Componentes** (`back/dependencies/registry/component_registry.py`) es un catálogo centralizado de todos los componentes disponibles. Se crea durante el inicio de la aplicación y se almacena en el contenedor DI.

### Registro

Cuando se registra una clase de componente, el registro:

1. Lee el atributo de clase `TYPE` para determinar la categoría del componente.
2. Verifica si la clase es un objeto configurable (tiene `get_schema()`).
3. Extrae los metadatos (`DESCRIPTION`, `DISPLAY_NAME`, `COLOR`, etc.).
4. Almacena el componente en un diccionario jerárquico indexado por tipo y nombre.

Cada componente registrado se almacena como un diccionario:

```python
{
    "name": "SVC",
    "type": "Model",
    "class": SVCClass,
    "configurable_object": True,
    "schema": {...},  # JSON Schema si es configurable
    "metadata": {...},
    "description": MultilingualString(...),
    "display_name": MultilingualString(...),
    "color": "#3498db",
}
```

### Métodos de Búsqueda

| Método                                    | Descripción                                                         |
| ----------------------------------------- | ------------------------------------------------------------------- |
| `registry[name]`                          | Búsqueda directa por nombre de componente                           |
| `get_components_by_types(select, ignore)` | Filtrar componentes por tipo (p. ej., solo Modelos)                 |
| `get_child_components(parent_name)`       | Obtener todos los componentes que heredan de un padre dado          |
| `get_related_components(component_id)`    | Obtener componentes compatibles a través de `COMPATIBLE_COMPONENTS` |

### Inicialización

La lista de componentes a registrar al inicio está definida en `back/initial_components.py`. Se pueden agregar componentes adicionales en tiempo de ejecución a través del sistema de plugins.

---

## Objetos Configurables

Un **Objeto Configurable** es cualquier componente cuyo comportamiento puede personalizarse mediante parámetros suministrados por el usuario. El mecanismo está construido sobre Pydantic y JSON Schema.

### Cómo Funciona

1. **Definición del esquema**: Un componente define un atributo de clase `SCHEMA` como un modelo Pydantic. Cada campo del modelo representa un parámetro configurable:

   ```python
   class LogisticRegressionSchema(BaseSchema):
       penalty: schema_field(
           none_type(enum_field(enum=["l1", "l2", "elasticnet"])),
           placeholder="l2",
           description=MultilingualString(
               en="Type of regularization penalty.",
               es="Tipo de penalización de regularización.",
           ),
           alias=MultilingualString(en="Penalty", es="Penalización"),
       )  # type: ignore
       C: schema_field(
           optimizer_float_field(gt=0.0),
           placeholder={
               "optimize": False,
               "fixed_value": 1.0,
               "lower_bound": 0.01,
               "upper_bound": 100.0,
           },
           description=MultilingualString(
               en="Inverse of regularization strength.",
               es="Inverso de la fuerza de regularización.",
           ),
           alias=MultilingualString(en="C", es="C"),
       )  # type: ignore
   ```

   Cada campo usa `schema_field()` con un validador de tipo (p. ej., `optimizer_float_field`, `enum_field`), un valor por defecto de marcador, una descripción bilingüe y un alias para la etiqueta de la UI. El frontend usa el JSON Schema generado para renderizar controles de formulario; el optimizador usa los metadatos de tipo para definir los límites de búsqueda.

2. **Generación del esquema**: `get_schema()` convierte el modelo Pydantic en un diccionario JSON Schema. El frontend usa este esquema para renderizar formularios de configuración dinámicamente.

3. **Validación y transformación**: Cuando el usuario envía una configuración, el backend llama a `validate_and_transform(params)` que:
   - Valida los datos de parámetros en bruto contra el esquema Pydantic.
   - Instancia recursivamente cualquier referencia a componentes anidados (un parámetro de tipo `ComponentType` se resuelve en una instancia real del componente).

### Campos de Componente

La utilidad `component_field()` (`back/core/schema_fields/component_field.py`) crea parámetros que hacen referencia a otros componentes. Por ejemplo, un modelo podría aceptar otro modelo como parámetro:

```python
class BagOfWordsSchema(BaseSchema):
    tabular_classifier: schema_field(
        component_field(component_type="TabularClassificationModel"),
        placeholder=None,
        description=MultilingualString(
            en="Tabular classifier used as the underlying model.",
            es="Clasificador tabular usado como modelo subyacente.",
        ),
        alias=MultilingualString(en="Tabular classifier", es="Clasificador tabular"),
    )  # type: ignore
```

El frontend renderiza los campos de componente como un menú desplegable con búsqueda, poblado desde el registro. Cuando el componente se instancia, `validate_and_transform()` resuelve el nombre del componente seleccionado en una instancia activa.
