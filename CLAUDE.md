# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is DashAI

DashAI is a desktop/web graphical toolbox for training, evaluating, and deploying ML models. It runs as a FastAPI backend serving a React frontend, optionally wrapped in PyWebView for a native desktop window.

## Commands

### Backend

```bash
# Install (uv creates .venv, installs the package editable + dev deps)
uv sync                  # add --extra cpu on machines without NVIDIA GPU
uv run pre-commit install

# Run dev server (if you synced with --extra cpu/cuda, pass the same
# --extra to uv run; a plain uv run re-syncs to the default torch build)
uv run python -m DashAI --no-browser --logging-level DEBUG

# Lint / format
uv run ruff check --fix
uv run ruff format

# Run all tests
uv run pytest tests/

# Run a single test file or function
uv run pytest tests/back/api/test_components_api.py -v
uv run pytest tests/back/api/test_components_api.py::test_function_name -v

# Database migrations (auto-runs on startup, but also manually)
uv run alembic upgrade head

# Add / remove a dependency (updates pyproject.toml + uv.lock)
uv add <package>
uv remove <package>
```

### Frontend

```bash
cd DashAI/front

yarn install        # requires Node LTS + Yarn 3.5.0
yarn start          # dev server on http://localhost:3000
yarn build
yarn lint
yarn test
yarn test FileName.test.tsx   # single test file
```

## Architecture

### Request flow

```
Browser / PyWebView
  → React (port 3000 dev / port 8000 prod)
  → FastAPI (/api/v1/...)
  → Service layer
  → SQLite (SQLAlchemy + Alembic)
  → Huey job queue (async tasks: training, conversion, exploration)
```

Long-running operations (training, data conversion, explanations) are dispatched as Huey tasks and tracked in the DB. The frontend polls `/api/v1/jobs/{job_id}` for status.

### Backend layout

| Path                                         | Purpose                                                                         |
| -------------------------------------------- | ------------------------------------------------------------------------------- |
| `DashAI/back/app.py`                         | FastAPI app factory (`create_app`)                                              |
| `DashAI/back/runner.py`                      | CLI entry point (starts uvicorn + huey)                                         |
| `DashAI/back/container.py`                   | Dependency injection (`kink`) — config, DB engine, registry, job queue          |
| `DashAI/back/dependencies/registry/`         | `ComponentRegistry`: central registry of all ML components                      |
| `DashAI/back/dependencies/config_builder.py` | Registers initial components on startup                                         |
| `DashAI/back/api/api_v1/endpoints/`          | REST endpoints                                                                  |
| `DashAI/back/core/schema_fields/`            | Type system for component parameters (drives dynamic frontend forms)            |
| `DashAI/back/pipeline/`                      | DAG pipeline nodes: DataSelector → Converter → Train → Prediction → Exploration |
| `DashAI/back/plugins/`                       | Plugin system (PyPI packages with `dashai.plugins` entry point)                 |

### Key patterns

**ComponentRegistry** — all ML components (models, metrics, converters, dataloaders, explorers, explainers, tasks) are registered at startup and resolved by name string. To add a new component: subclass the relevant base, define its schema, and add it to `config_builder.py`.

**Schema / type system** — every component declares its parameters using `BaseSchema` + field classes (`IntField`, `FloatField`, `ComponentField`, `UnionType`, etc.) with `MultilingualString` labels. The frontend uses these schemas to auto-generate configuration forms.

**Dependency injection (`kink`)** — singletons (config, DB session factory, registry, job queue) live in the `di` container. Use `@inject` to receive them; don't import globals directly.

**Pipeline as DAG** — `PipelineValidator` validates the graph before execution. Each node is a `BaseJob` subclass. Results flow between nodes via a shared `context` dict.

**Plugin system** — plugins are PyPI packages prefixed `dashai-*` that register components via `entry_points` group `dashai.plugins`. Install/uninstall via `/api/v1/plugins`.

### Frontend layout

| Path                                              | Purpose                                             |
| ------------------------------------------------- | --------------------------------------------------- |
| `DashAI/front/src/api/`                           | Axios HTTP client for all backend calls             |
| `DashAI/front/src/components/configurableObject/` | Auto-generates forms from backend component schemas |
| `DashAI/front/src/components/pipelines/`          | Pipeline builder/editor                             |
| `DashAI/front/src/i18n/`                          | i18next translations                                |

### Data stored at runtime

Default path `~/.DashAI/` (overridable via `DASHAI_LOCAL_PATH`):

- `datasets/`, `runs/`, `explanations/`, `notebooks/`, `images/`, `sqlite.db`

### Testing notes

- Backend tests use in-memory SQLite — no setup needed.
- `conftest.py` fixtures: `test_path`, `test_datasets_path`, `test_job_queue`.
- Job queue tests use `test_job_queue.set_test_mode(immediate=True)` to run tasks synchronously.
- API tests use FastAPI `TestClient` defined in `tests/back/api/conftest.py`.

## Adding new things

**New ML model or converter:** subclass `BaseModel` / `BaseConverter`, define schema, register in `config_builder.py`.

**New API endpoint:** add file in `DashAI/back/api/api_v1/endpoints/`, include its router in `DashAI/back/api/api_v1/api.py`.

**New async job:** subclass `BaseJob`, dispatch via `job_queue.enqueue(...)`, track status through the jobs API.
