# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## What is DashAI

DashAI is a desktop/web graphical toolbox for training, evaluating, and deploying ML models. FastAPI backend + React frontend, optionally wrapped in PyWebView for a native desktop window. Python >= 3.10.

## Commands

### Backend

```bash
pip install -e . -r requirements-dev.txt
pre-commit install

# Run dev server
python -m DashAI --no-browser --logging-level DEBUG

# Lint / format (must pass both before committing)
ruff check --fix
ruff format

# Run all tests (in-memory SQLite — no setup needed)
pytest tests/

# Run a single test
pytest tests/back/api/test_components_api.py -v
pytest tests/back/api/test_components_api.py::test_function_name -v

# Database migrations (auto-runs on startup)
alembic upgrade head
```

### Frontend

```bash
cd DashAI/front

yarn install        # requires Node LTS + Yarn 3.5.0 (enforced by packageManager)
yarn start          # dev server on http://localhost:3000 (eslint disabled)
yarn build          # eslint disabled
yarn test           # eslint disabled
yarn test FileName.test.tsx
yarn lint           # runs eslint explicitly (uses eslint.config.js)
```

**Important:** `start`, `build`, and `test` scripts all set `DISABLE_ESLINT_PLUGIN=true`. ESLint only runs via the dedicated `yarn lint` command. Prettier is configured in `DashAI/front/.prettierrc` and runs via pre-commit.

## Architecture

```
Browser / PyWebView
  → React (port 3000 dev / port 8000 prod)
  → FastAPI (/api/v1/...)
  → Service layer → SQLite (SQLAlchemy + Alembic)
  → Huey job queue (async: training, conversion, exploration)
```

The frontend polls `/api/v1/jobs/{job_id}` for long-running task status.

## Key files

| Path                                                       | Purpose                                                                                                               |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `DashAI/__main__.py`                                       | CLI entry point (typer). Starts uvicorn + Huey consumer subprocess                                                    |
| `DashAI/back/app.py`                                       | FastAPI `create_app` factory                                                                                          |
| `DashAI/back/container.py`                                 | DI container (`kink`) — config, DB engine, ComponentRegistry, job queue                                               |
| `DashAI/back/initial_components.py`                        | **Registers all components on startup.** Add new ML components here in `get_initial_components()`                     |
| `DashAI/back/dependencies/config_builder.py`               | Builds config dict (paths, logging, calls `get_initial_components()`)                                                 |
| `DashAI/back/dependencies/registry/component_registry.py`  | `ComponentRegistry` — resolves components by name string                                                              |
| `DashAI/back/api/api_v1/endpoints/`                        | REST endpoints — each file is a FastAPI router                                                                        |
| `DashAI/back/api/api_v1/api.py`                            | Mounts all endpoint routers on `api_router_v1`                                                                        |
| `DashAI/back/core/schema_fields/`                          | Type system driving dynamic frontend forms                                                                            |
| `DashAI/back/pipeline/`                                    | DAG pipeline nodes                                                                                                    |
| `DashAI/back/plugins/`                                     | Plugin system (PyPI packages with `dashai.plugins` entry point)                                                       |
| `DashAI/front/src/components/configurableObject/`          | Auto-generates forms from backend component schemas                                                                   |
| `DashAI/front/src/pages/generative/SessionRouter.jsx`      | Routes `/app/generative/sessions/:id` to RAG or non-RAG view based on session `task_name`                             |
| `DashAI/front/src/pages/generative/RAGSession/`            | RAG session setup wizard (RAGSessionSetup) + collapsible section components per pipeline stage                        |
| `DashAI/front/src/pages/generative/RAGSession/sections/`   | Per-stage components: ChunkingSection, RetrieverSection, GeneratorSection, PromptSection                              |
| `DashAI/front/src/pages/generative/RAGSession/advanced/`   | Advanced configuration modals: CompositeRetrieverBuilder, ChunkingConfigurationStep, RetrieverConfigurationStep, etc. |
| `DashAI/front/src/pages/generative/RAGSession/components/` | Reusable bodies: GeneratorBody, PromptBody, PresetCard, AdvancedConfigCard                                            |

## Key patterns

**ComponentRegistry** — all ML components (models, metrics, converters, dataloaders, explorers, explainers, tasks, optimizers, jobs, pipeline nodes) are registered at startup and resolved by name string. To add a new component: subclass the relevant base, define its schema, and add it to `get_initial_components()` in `DashAI/back/initial_components.py`.

**Schema / type system** — every component declares parameters using `BaseSchema` + field classes (`IntField`, `FloatField`, `ComponentField`, `UnionType`, etc.) with `MultilingualString` labels. The frontend uses these schemas to auto-generate configuration forms.

**Dependency injection (`kink`)** — singletons (config, DB engine, ComponentRegistry, job queue) live in the `di` container. Use `@inject` to receive them. Config is accessed as `di["config"]` and includes `INITIAL_COMPONENTS`.

**Huey job queue** — in dev mode the Huey consumer runs as a subprocess spawned from `__main__.py`; in PyInstaller bundles it runs as a daemon thread due to limitations with frozen executables.

## RAG Module

DashAI includes a **Retrieval-Augmented Generation (RAG)** module — a 4-stage pipeline (Document Loading → Chunking → Retrieval → Generation) for chatting with your documents.

- **Backend:** `DashAI/back/models/RAG/` — pipeline orchestrator (RAGPipeline), abstract factory (RAGModelsFactory), sub-factories for prompts/chunking/retrievers/LLMs, retriever repository (all SQL), document loader, chunk-set caching.
- **Frontend:** `DashAI/front/src/pages/generative/RAGSession/` — session setup wizard (RAGSessionSetup, RAGSessionPage) with stage sections (ChunkingSection, RetrieverSection, GeneratorSection, PromptSection) and advanced config modals.
- **Jobs:** `RAGJob` extends `GenerativeJob` to run the RAG pipeline as a background task.
- **Full docs (backend + frontend):** See [`docs/rag/`](./docs/rag/) for architecture, data models, retrievers, pipeline orchestration, frontend architecture, testing guide, and known constraints.

## Testing

- Backend tests use in-memory SQLite — no setup needed.
- Key fixtures in `tests/back/conftest.py`: `test_path`, `test_datasets_path`, `test_job_queue`.
- Job queue tests: `test_job_queue.set_test_mode(immediate=True)` runs tasks synchronously.
- API tests use FastAPI `TestClient` defined in `tests/back/api/conftest.py` (module-scoped).
- Frontend test command passes `--passWithNoTests` in CI.

## Adding new things

**New ML model or converter:** subclass `BaseModel` / `BaseConverter`, define schema, register in `DashAI/back/initial_components.py::get_initial_components()`.

**New API endpoint:** add file in `DashAI/back/api/api_v1/endpoints/`, include its router in `DashAI/back/api/api_v1/api.py`.

**New async job:** subclass `BaseJob`, dispatch via `job_queue.enqueue(...)`, track status through jobs API.

## Data at runtime

Default `~/.DashAI/` (overridable via `DASHAI_LOCAL_PATH` env var):
`datasets/`, `runs/`, `explanations/`, `notebooks/`, `images/`, `documents/`, `rag/`, `sqlite.db`

## CI

Only a `publish.yml` workflow exists (on push to `production` branch). It builds the frontend, publishes to PyPI, and builds Windows/macOS installers. No CI test workflow is defined.
