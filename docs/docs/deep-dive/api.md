---
title: API
sidebar_label: API
---

dashAI exposes a RESTful API at `/api/v1`. All endpoints return JSON. The API is built
with **FastAPI** and supports OpenAPI documentation at `/docs` (Swagger UI) and `/redoc`.

## Router Structure

| Router file             | Resource                     | Purpose                                             |
| ----------------------- | ---------------------------- | --------------------------------------------------- |
| `components.py`         | `/api/v1/component`          | List and filter registered components               |
| `datasets.py`           | `/api/v1/dataset`            | Upload, list, and validate datasets                 |
| `model_sessions.py`     | `/api/v1/model-session`      | CRUD for model training sessions                    |
| `runs.py`               | `/api/v1/run`                | CRUD for training runs, metrics, optimization plots |
| `jobs.py`               | `/api/v1/job`                | Enqueue jobs and query job status                   |
| `explorers.py`          | `/api/v1/explorer`           | Launch and retrieve data explorations               |
| `explainers.py`         | `/api/v1/explainer`          | Launch model explanations                           |
| `converters.py`         | `/api/v1/converter`          | Apply data transformations                          |
| `predict.py`            | `/api/v1/predict`            | Run predictions on new data                         |
| `plugins.py`            | `/api/v1/plugin`             | Manage installed plugins                            |
| `generative_session.py` | `/api/v1/generative-session` | Generative model sessions                           |
| `generative_process.py` | `/api/v1/generative-process` | Generative process execution and results            |

## Key Endpoints

### Components

```http
GET /api/v1/component/
GET /api/v1/component/?select_types=["Model","Metric"]
```

Returns all registered components with their schemas and metadata. Accepts an optional
`select_types` query parameter to filter by component category. The frontend uses this
response to render configuration forms dynamically.

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

`POST` creates a dataset entry (upload is handled as multipart form data). `PATCH`
renames a dataset. The `/sample` endpoint returns 10 representative rows; `/info`
returns schema and column metadata; `/types` returns per column data types. `/filter/`
supports pagination and column filtering for the frontend data grid. `POST /copy`
duplicates an existing dataset. `/export/csv` downloads the full dataset as a CSV file.

### Model Sessions (Experiments)

```http
GET    /api/v1/model-session/
POST   /api/v1/model-session/
GET    /api/v1/model-session/{session_id}
PATCH  /api/v1/model-session/{session_id}
DELETE /api/v1/model-session/{session_id}
POST   /api/v1/model-session/validation
```

A ModelSession captures the full experiment configuration: dataset, task, input/output
columns, split ratios, and selected metrics. `POST /validation` checks that the selected
dataset columns are compatible with the chosen task before the session is created.

### Runs

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

Each Run belongs to a ModelSession and holds the model name, parameters, optimizer
config, and training artifacts. `PATCH /{run_id}/reset` resets a run back to
`NOT_STARTED`. `/operations/count` returns the number of explainers and predictions
associated with a run; `DELETE /operations` removes them all. `/plot/{run_id}/{plot_type}`
fetches hyperparameter optimization plots, where `plot_type` is one of `history`, `slice`,
`contour`, or `importance`.

### Jobs

```http
POST   /api/v1/job/
GET    /api/v1/job/status/{job_id}
```

All long running operations (training, exploration, prediction, conversion) are submitted
as jobs. `POST` enqueues a job and returns a job ID immediately. The frontend polls
`GET /status/{job_id}` until the job reaches `finished` or `error`.

### Explorers

```http
GET    /api/v1/explorer/
POST   /api/v1/explorer/
GET    /api/v1/explorer/{explorer_id}/
PATCH  /api/v1/explorer/{explorer_id}/
DELETE /api/v1/explorer/{explorer_id}/
POST   /api/v1/explorer/{explorer_id}/results/
PUT    /api/v1/explorer/{explorer_id}/results/
```

Explorers run visualizations (scatter plots, histograms, etc.) on a Notebook's dataset.
`POST /` creates an Explorer record and enqueues an `ExplorerJob`. `POST /{explorer_id}/results/`
retrieves the computed result; `PUT` updates it. Results are stored as Plotly JSON
specifications.

### Converters

```http
POST   /api/v1/converter/
GET    /api/v1/converter/{converter_list_id}
GET    /api/v1/converter/notebook/{notebook_id}
DELETE /api/v1/converter/{converter_list_id}
```

`POST` saves a single converter step to a Notebook. `GET /notebook/{notebook_id}` returns
all finished converter records for that Notebook. `DELETE` reverts the Notebook dataset
to the state before the deleted converter and reenqueues all preceding converters.

### Explainers

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

**Global** explainers (e.g., Permutation Feature Importance) produce a single explanation
covering the whole model. **Local** explainers (e.g., KernelShap) produce per instance
explanations. Both support a `/plot` endpoint that returns the visualization.
`POST /local/validate-dataset` checks that an input dataset is compatible with the
trained run before creating a local explainer.

### Predictions

```http
GET    /api/v1/predict/
POST   /api/v1/predict/
DELETE /api/v1/predict/{prediction_id}
GET    /api/v1/predict/filter_datasets
POST   /api/v1/predict/preview
```

`POST /` creates a persisted prediction job linked to a trained Run. `GET /filter_datasets`
returns only those datasets whose column schema is compatible with the run's training
dataset. `POST /preview` runs a synchronous prediction and returns the result immediately
without persisting it, which is useful for quick interactive inference.

### Generative Sessions and Processes

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

A **GenerativeSession** stores the model and parameters for a generative workflow
(text-to-text, text-to-image, ControlNet, etc.). `PATCH` updates the session parameters
and records a snapshot in the parameter history. Each invocation creates a
**GenerativeProcess** record that tracks status and stores input/output payloads via
`ProcessData` records. `GET /{process_id}/results` returns the output after the process
completes.

## Dependency Injection

Endpoints receive dependencies through FastAPI's `Depends` mechanism combined with
Kink's `di` container:

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

## Internationalization

The API supports multilingual responses. Component display names and descriptions are
stored as `MultilingualString` objects, and the API filters them based on the
`Accept-Language` header.

## Interactive Docs

When running dashAI locally, you can explore the full API interactively:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
