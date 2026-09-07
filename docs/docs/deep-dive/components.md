---
title: Components
sidebar_label: Components
---

## What is a Component?

A **component** is the fundamental building block of dashAI. Every pluggable piece of
functionality is a component: models, tasks, metrics, explorers, explainers, converters,
data loaders, optimizers, and jobs.

## Component Types

Each component class declares a `TYPE` class attribute that determines its category:

| TYPE              | Base class            | Purpose                              | Examples                                                            |
| ----------------- | --------------------- | ------------------------------------ | ------------------------------------------------------------------- |
| `Model`           | `BaseModel`           | Train and predict                    | SVC, RandomForest, DistilBertTransformer                            |
| `GenerativeModel` | `BaseGenerativeModel` | Generate outputs from prompts/inputs | QwenModel, StableDiffusionV2Model                                   |
| `Task`            | `BaseTask`            | Define ML task semantics             | TextClassification, Regression, Translation                         |
| `GenerativeTask`  | `BaseGenerativeTask`  | Define generative task semantics     | TextToTextGenerationTask, TextToImageGenerationTask, ControlNetTask |
| `Metric`          | `BaseMetric`          | Evaluate model performance           | Accuracy, F1, RMSE, MAE                                             |
| `Explorer`        | `BaseExplorer`        | Visualize and analyze data           | ScatterPlotExplorer, HistogramPlotExplorer                          |
| `GlobalExplainer` | `BaseGlobalExplainer` | Interpret overall model behavior     | PermutationFeatureImportance, PartialDependence                     |
| `LocalExplainer`  | `BaseLocalExplainer`  | Interpret individual predictions     | KernelShap                                                          |
| `Converter`       | `BaseConverter`       | Transform features                   | StandardScaler, OneHotEncoder, PCA, SMOTE                           |
| `DataLoader`      | `BaseDataLoader`      | Load datasets from files             | CSVDataLoader, ExcelDataLoader                                      |
| `Optimizer`       | `BaseOptimizer`       | Hyperparameter optimization          | Optuna based optimizers                                             |
| `Job`             | `BaseJob`             | Background task execution            | ModelJob, ExplorerJob, PredictJob                                   |

## Component Metadata

Every component can expose metadata used by the frontend for display and filtering:

- `DESCRIPTION`: a multilingual description of what the component does.
- `DISPLAY_NAME`: a human readable name.
- `COLOR`: a hex color for UI rendering.
- `COMPATIBLE_COMPONENTS`: a list of component names this component works with
  (e.g., a metric that only applies to classification tasks).

---

## Component Registry

The **Component Registry** (`back/dependencies/registry/component_registry.py`) is a
centralized catalog of all available components. It is created during application
startup and stored in the DI container.

### Registration

When a component class is registered, the registry:

1. Reads the `TYPE` class attribute to determine the component category.
2. Checks whether the class is a configurable object (has `get_schema()`).
3. Extracts metadata (`DESCRIPTION`, `DISPLAY_NAME`, `COLOR`, etc.).
4. Stores the component in a hierarchical dictionary keyed by type and name.

Each registered component is stored as a dictionary:

```python
{
    "name": "SVC",
    "type": "Model",
    "class": SVCClass,
    "configurable_object": True,
    "schema": {...},  # JSON Schema if configurable
    "metadata": {...},
    "description": MultilingualString(...),
    "display_name": MultilingualString(...),
    "color": "#3498db",
}
```

### Lookup Methods

| Method                                    | Description                                           |
| ----------------------------------------- | ----------------------------------------------------- |
| `registry[name]`                          | Direct lookup by component name                       |
| `get_components_by_types(select, ignore)` | Filter components by type (e.g., only Models)         |
| `get_child_components(parent_name)`       | Get all components that inherit from a given parent   |
| `get_related_components(component_id)`    | Get compatible components via `COMPATIBLE_COMPONENTS` |

### Initialization

The list of components to register on startup is defined in
`back/initial_components.py`. Additional components can be added at runtime through the
plugin system.

---

## Configurable Objects

A **Configurable Object** is any component whose behavior can be customized through
user supplied parameters. The mechanism is built on top of Pydantic and JSON Schema.

### How It Works

1. **Schema definition**: A component defines a `SCHEMA` class attribute as a Pydantic
   model. Each field in the model represents a configurable parameter:

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

   Each field uses `schema_field()` with a type validator (e.g. `optimizer_float_field`,
   `enum_field`), a placeholder default, a bilingual description, and an alias for the UI
   label. The frontend uses the generated JSON Schema to render form controls; the
   optimizer uses type metadata to define search bounds.

2. **Schema generation**: `get_schema()` converts the Pydantic model into a JSON
   Schema dictionary. The frontend uses this schema to dynamically render configuration
   forms.

3. **Validation and transformation**: When the user submits a configuration, the
   backend calls `validate_and_transform(params)` which:
   - Validates raw parameter data against the Pydantic schema.
   - Recursively instantiates any nested component references (a parameter of type
     `ComponentType` is resolved into an actual component instance).

### Component Fields

The `component_field()` utility (`back/core/schema_fields/component_field.py`) creates
parameters that reference other components. For example, a model might accept another
model as a parameter:

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

The frontend renders component fields as a searchable dropdown populated from the
registry. When the component is instantiated, `validate_and_transform()` resolves the
selected component name into a live instance.
