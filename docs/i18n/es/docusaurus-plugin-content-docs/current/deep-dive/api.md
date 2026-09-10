---
title: API
sidebar_label: API
---

dashAI expone una API RESTful en `/api/v1`. Todos los endpoints devuelven JSON. La API está construida con **FastAPI** y soporta documentación OpenAPI en `/docs` (Swagger UI) y `/redoc`.

## Estructura de Rutas

| Archivo del router      | Recurso                      | Propósito                                                                   |
| ----------------------- | ---------------------------- | --------------------------------------------------------------------------- |
| `components.py`         | `/api/v1/component`          | Listar y filtrar componentes registrados                                    |
| `datasets.py`           | `/api/v1/dataset`            | Cargar, listar y validar datasets                                           |
| `model_sessions.py`     | `/api/v1/model-session`      | CRUD para sesiones de entrenamiento de modelos                              |
| `runs.py`               | `/api/v1/run`                | CRUD para ejecuciones de entrenamiento, métricas y gráficos de optimización |
| `jobs.py`               | `/api/v1/job`                | Encolar trabajos y consultar el estado de un trabajo                        |
| `explorers.py`          | `/api/v1/explorer`           | Lanzar y recuperar exploraciones de datos                                   |
| `explainers.py`         | `/api/v1/explainer`          | Lanzar explicaciones de modelos                                             |
| `converters.py`         | `/api/v1/converter`          | Aplicar transformaciones de datos                                           |
| `predict.py`            | `/api/v1/predict`            | Ejecutar predicciones sobre nuevos datos                                    |
| `plugins.py`            | `/api/v1/plugin`             | Gestionar plugins instalados                                                |
| `generative_session.py` | `/api/v1/generative-session` | Sesiones de modelos generativos                                             |
| `generative_process.py` | `/api/v1/generative-process` | Ejecución y resultados de procesos generativos                              |

## Endpoints Clave

### Componentes

```http
GET /api/v1/component/
GET /api/v1/component/?select_types=["Model","Metric"]
```

Devuelve todos los componentes registrados con sus esquemas y metadatos. Acepta un parámetro de consulta opcional `select_types` para filtrar por categoría de componente. El frontend usa esta respuesta para renderizar formularios de configuración de forma dinámica.

### Datasets

```http
GET    /api/v1/dataset/
POST   /api/v1/dataset/
GET    /api/v1/dataset/{dataset_id}
PATCH  /api/v1/dataset/{dataset_id}
DELETE /api/v1/dataset/{dataset_id}
GET    /api/v1/dataset/{dataset_id}/sample
GET    /api/v1/dataset/{dataset_id}/info
GET    /api/v1/dataset/{dataset_id}/types
GET    /api/v1/dataset/{dataset_id}/model-sessions-exist
GET    /api/v1/dataset/filter/
POST   /api/v1/dataset/copy
PATCH  /api/v1/dataset/{dataset_id}/columns/rename
GET    /api/v1/dataset/export/csv
```

`POST` crea una entrada de dataset (la carga se maneja como datos de formulario multiparte). `PATCH` renombra un dataset. El endpoint `/sample` devuelve 10 filas representativas; `/info` devuelve el esquema y metadatos de las columnas; `/types` devuelve los tipos de datos por columna. `/filter/` soporta paginación y filtrado de columnas para la cuadrícula de datos del frontend. `POST /copy` duplica un dataset existente. `/export/csv` descarga el dataset completo como un archivo CSV.

### Sesiones de Modelo (Experimentos)

```http
GET    /api/v1/model-session/
POST   /api/v1/model-session/
GET    /api/v1/model-session/{session_id}
PATCH  /api/v1/model-session/{session_id}
DELETE /api/v1/model-session/{session_id}
POST   /api/v1/model-session/validation
```

Una ModelSession captura la configuración completa del experimento: dataset, tarea, columnas de entrada/salida, proporciones de división y métricas seleccionadas. `POST /validation` verifica que las columnas del dataset seleccionado son compatibles con la tarea elegida antes de crear la sesión.

### Ejecuciones

```http
GET    /api/v1/run/
POST   /api/v1/run/
GET    /api/v1/run/{run_id}
PATCH  /api/v1/run/{run_id}
PATCH  /api/v1/run/{run_id}/reset
DELETE /api/v1/run/{run_id}
DELETE /api/v1/run/{run_id}/operations
GET    /api/v1/run/{run_id}/operations/count
GET    /api/v1/run/plot/{run_id}/{plot_type}
```

Cada ejecución pertenece a una ModelSession y almacena el nombre del modelo, los parámetros, la configuración del optimizador y los artefactos de entrenamiento. `PATCH /{run_id}/reset` restablece una ejecución al estado `NOT_STARTED`. `/operations/count` devuelve el número de explicadores y predicciones asociados a una ejecución; `DELETE /operations` los elimina todos. `/plot/{run_id}/{plot_type}` obtiene los gráficos de optimización de hiperparámetros, donde `plot_type` es uno de `history`, `slice`, `contour` o `importance`.

### Trabajos

```http
POST   /api/v1/job/
GET    /api/v1/job/status/{job_id}
```

Todas las operaciones de larga duración (entrenamiento, exploración, predicción, conversión) se envían como trabajos. `POST` encola un trabajo y devuelve un ID de trabajo de inmediato. El frontend consulta `GET /status/{job_id}` hasta que el trabajo alcanza el estado `finished` o `error`.

### Exploradores

```http
GET    /api/v1/explorer/
POST   /api/v1/explorer/
GET    /api/v1/explorer/{explorer_id}/
PATCH  /api/v1/explorer/{explorer_id}/
DELETE /api/v1/explorer/{explorer_id}/
POST   /api/v1/explorer/{explorer_id}/results/
PUT    /api/v1/explorer/{explorer_id}/results/
```

Los exploradores ejecutan visualizaciones (gráficos de dispersión, histogramas, etc.) sobre el dataset de un Notebook. `POST /` crea un registro de Explorer y encola un `ExplorerJob`. `POST /{explorer_id}/results/` recupera el resultado calculado; `PUT` lo actualiza. Los resultados se almacenan como especificaciones JSON de Plotly.

### Converters

```http
POST   /api/v1/converter/
GET    /api/v1/converter/{converter_list_id}
GET    /api/v1/converter/notebook/{notebook_id}
DELETE /api/v1/converter/{converter_list_id}
```

`POST` guarda un paso de converter individual en un Notebook. `GET /notebook/{notebook_id}` devuelve todos los registros de converters finalizados para ese Notebook. `DELETE` revierte el dataset del Notebook al estado previo al converter eliminado y vuelve a encolar todos los converters anteriores.

### Explicadores

```http
GET    /api/v1/explainer/global
POST   /api/v1/explainer/global
GET    /api/v1/explainer/global/{explainer_id}
GET    /api/v1/explainer/global/plot/{explainer_id}
DELETE /api/v1/explainer/global/{explainer_id}

GET    /api/v1/explainer/local
POST   /api/v1/explainer/local
GET    /api/v1/explainer/local/{explainer_id}
GET    /api/v1/explainer/local/plot/{explainer_id}
DELETE /api/v1/explainer/local/{explainer_id}
POST   /api/v1/explainer/local/validate-dataset

PATCH  /api/v1/explainer/
```

Los explicadores **globales** (p. ej., Permutation Feature Importance) producen una explicación única que cubre todo el modelo. Los explicadores **locales** (p. ej., KernelShap) producen explicaciones por instancia. Ambos soportan un endpoint `/plot` que devuelve la visualización. `POST /local/validate-dataset` verifica que un dataset de entrada es compatible con la ejecución entrenada antes de crear un explicador local.

### Predicciones

```http
GET    /api/v1/predict/
POST   /api/v1/predict/
DELETE /api/v1/predict/{prediction_id}
GET    /api/v1/predict/filter_datasets
POST   /api/v1/predict/preview
```

`POST /` crea un trabajo de predicción persistido vinculado a una ejecución entrenada. `GET /filter_datasets` devuelve solo los datasets cuyo esquema de columnas es compatible con el dataset de entrenamiento de la ejecución. `POST /preview` ejecuta una predicción sincrónica y devuelve el resultado de inmediato sin persistirlo, lo que resulta útil para inferencia interactiva rápida.

### Sesiones y Procesos Generativos

```http
GET    /api/v1/generative-session/
POST   /api/v1/generative-session/
GET    /api/v1/generative-session/{session_id}
PATCH  /api/v1/generative-session/{session_id}
DELETE /api/v1/generative-session/{session_id}

POST   /api/v1/generative-process/
GET    /api/v1/generative-process/{process_id}
GET    /api/v1/generative-process/{process_id}/results
```

Una **GenerativeSession** almacena el modelo y los parámetros para un flujo de trabajo generativo (texto a texto, texto a imagen, ControlNet, etc.). `PATCH` actualiza los parámetros de la sesión y registra una instantánea en el historial de parámetros. Cada invocación crea un registro **GenerativeProcess** que rastrea el estado y almacena las cargas útiles de entrada/salida a través de registros `ProcessData`. `GET /{process_id}/results` devuelve la salida una vez que el proceso finaliza.

## Inyección de Dependencias

Los endpoints reciben dependencias a través del mecanismo `Depends` de FastAPI combinado con el contenedor `di` de Kink:

```python
@router.post("/")
@inject
async def enqueue_job(
    job_params: JobParams,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
    component_registry: ComponentRegistry = Depends(lambda: di["component_registry"]),
    job_queue: BaseJobQueue = Depends(lambda: di["job_queue"]),
): ...
```

## Internacionalización

La API soporta respuestas multilingües. Los nombres de visualización y descripciones de los componentes se almacenan como objetos `MultilingualString`, y la API los filtra según el encabezado `Accept-Language`.

## Documentación Interactiva

Al ejecutar dashAI localmente, puedes explorar la API completa de forma interactiva:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
