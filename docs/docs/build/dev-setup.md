---
title: Development Setup
sidebar_label: Development Setup
sidebar_position: 2
---

# Development Setup

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (manages Python and dependencies; Python 3.11 to 3.13)
- Node.js (LTS) and Yarn 3.5.0
- Git

## 1. Clone the Repository

```bash
git clone https://github.com/DashAISoftware/DashAI.git
cd DashAI
git checkout develop
```

## 2. Backend Setup

Install all dependencies (uv creates the `.venv` and installs the package
in editable mode, including development dependencies):

```bash
uv sync
uv run pre-commit install
```

On machines without an NVIDIA GPU you can use the CPU-only PyTorch wheels,
which are much lighter:

```bash
uv sync --extra cpu
```

On NVIDIA machines, the `cuda` extra pins the CUDA 12.8 PyTorch wheels. To
also get LLM (GGUF) support with CUDA offload, set `CMAKE_ARGS` so that
`llama-cpp-python` compiles against CUDA (requires CMake, a C compiler and
the CUDA toolkit):

```bash
uv cache clean llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" uv sync --extra cuda --reinstall-package llama-cpp-python
```

The first command and the `--reinstall-package` flag matter: uv skips
packages that are already installed and caches built wheels, and neither
check looks at `CMAKE_ARGS`, so without them a previous CPU build gets
silently reused. Without `CMAKE_ARGS`, `llama-cpp-python` still installs but
runs on CPU (there is no prebuilt CUDA wheel on PyPI). If nvcc rejects your
default gcc as too new, point it at an older one you have installed, for
example `CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_HOST_COMPILER=/usr/bin/g++-13"`.

Alternatively, plain `pip` works inside any environment (venv or conda),
since all metadata lives in `pyproject.toml`. Note this skips the lockfile,
so versions may differ slightly from the ones the team and CI use:

```bash
pip install -e . --group dev    # --group needs pip >= 25.1
pre-commit install
```

If you go the pip route, drop the `uv run` prefix from the commands below.

## 3. Frontend Setup

```bash
cd DashAI/front
yarn install
```

## Running in Development

**Backend** (from the repo root):

```bash
uv run python -m DashAI
# or
uv run dashai --no-browser --logging-level INFO
```

**Important:** if you synced with an extra, pass the same extra to `uv run`
(for example `uv run --extra cpu python -m DashAI`). A plain `uv run` re-syncs
the environment to the default set and swaps your PyTorch build back to the
PyPI one.

**Frontend** (development server with hot reload):

```bash
cd DashAI/front
yarn start
```

The backend runs at `http://localhost:8000` and the frontend dev server at `http://localhost:3000`.

## Linting and Formatting

**Python** (using Ruff):

```bash
uv run ruff check . --fix
uv run ruff format .
```

**Frontend** (ESLint + Prettier):

```bash
cd DashAI/front
yarn lint
```

## Pre-commit Hooks

dashAI uses pre-commit hooks for consistent code quality:

```bash
# Run all hooks manually
uv run pre-commit run --all-files

# Run on staged files (happens automatically on git commit)
uv run pre-commit run
```

## Project Structure

```
DashAI/
├── DashAI/
│   ├── __main__.py         # CLI entry point (Typer)
│   ├── back/               # FastAPI backend
│   │   ├── app.py          # Application factory
│   │   ├── container.py    # Kink DI container
│   │   ├── initial_components.py  # Startup component registration
│   │   ├── api/            # Routers and request/response schemas
│   │   ├── converters/     # Converter components
│   │   ├── dataloaders/    # DataLoader components
│   │   ├── dependencies/   # Registry, database engine, job queue
│   │   ├── explainability/ # Explainer components
│   │   ├── exploration/    # Explorer components
│   │   ├── job/            # Job implementations
│   │   ├── metrics/        # Metric components
│   │   ├── models/         # ML model components
│   │   ├── optimizers/     # Hyperparameter optimizer components
│   │   ├── plugins/        # Plugin loading system
│   │   ├── tasks/          # Task components
│   │   └── types/          # Shared type definitions
│   └── front/              # React frontend
│       └── src/
│           ├── api/        # HTTP client
│           ├── components/ # UI components
│           └── pages/      # Page components
├── docs/                   # Documentation site (Docusaurus)
├── tests/                  # Backend tests
└── alembic/                # Database migrations
```
