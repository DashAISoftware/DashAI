---
title: Configuración de Desarrollo
sidebar_label: Configuración de Desarrollo
sidebar_position: 2
---

# Configuración de Desarrollo

## Requisitos Previos

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (administra Python y las dependencias; Python 3.11 a 3.13)
- Node.js (LTS) y Yarn 3.5.0
- Git

## 1. Clonar el Repositorio

```bash
git clone https://github.com/DashAISoftware/DashAI.git
cd DashAI
git checkout develop
```

## 2. Configuración del Backend

Instala todas las dependencias (uv crea el `.venv` e instala el paquete
en modo editable, incluyendo las dependencias de desarrollo):

```bash
uv sync
uv run pre-commit install
```

En máquinas sin GPU NVIDIA puedes usar los wheels de PyTorch solo-CPU,
que son mucho más livianos:

```bash
uv sync --extra cpu
```

En máquinas con NVIDIA, el extra `cuda` fija los wheels de PyTorch CUDA 12.8.
Para tener además soporte LLM (GGUF) con offload a CUDA, define `CMAKE_ARGS`
para que `llama-cpp-python` compile contra CUDA (requiere CMake, un compilador
C y el toolkit de CUDA):

```bash
uv cache clean llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" uv sync --extra cuda --reinstall-package llama-cpp-python
```

El primer comando y el flag `--reinstall-package` importan: uv omite paquetes
que ya están instalados y cachea los wheels compilados, y ninguna de esas dos
verificaciones mira `CMAKE_ARGS`, así que sin ellos se reutiliza en silencio
un build CPU anterior. Sin `CMAKE_ARGS`, `llama-cpp-python` se instala igual
pero corre en CPU (no existe wheel CUDA precompilado en PyPI). Si nvcc rechaza
tu gcc por ser muy nuevo, apúntalo a uno más antiguo que tengas instalado, por
ejemplo `CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_HOST_COMPILER=/usr/bin/g++-13"`.

Como alternativa, `pip` a secas funciona dentro de cualquier entorno (venv o
conda), ya que toda la metadata vive en `pyproject.toml`. Ojo que esto no usa
el lockfile, así que las versiones pueden diferir levemente de las que usan el
equipo y el CI:

```bash
pip install -e . --group dev    # --group requiere pip >= 25.1
pre-commit install
```

Si usas la vía pip, omite el prefijo `uv run` en los comandos siguientes.

## 3. Configuración del Frontend

```bash
cd DashAI/front
yarn install
```

## Ejecutar en Desarrollo

**Backend** (desde la raíz del repositorio):

```bash
uv run python -m DashAI
# o
uv run dashai --no-browser --logging-level INFO
```

**Importante:** si sincronizaste con un extra, pásale el mismo extra a
`uv run` (por ejemplo `uv run --extra cpu python -m DashAI`). Un `uv run` sin
flags re-sincroniza el entorno al set por defecto y revierte tu build de
PyTorch al de PyPI.

**Frontend** (servidor de desarrollo con recarga en caliente):

```bash
cd DashAI/front
yarn start
```

El backend corre en `http://localhost:8000` y el servidor de desarrollo del frontend en `http://localhost:3000`.

## Linting y Formateo

**Python** (usando Ruff):

```bash
uv run ruff check . --fix
uv run ruff format .
```

**Frontend** (ESLint + Prettier):

```bash
cd DashAI/front
yarn lint
```

## Hooks de Pre-commit

dashAI usa hooks de pre-commit para mantener la calidad del código:

```bash
# Ejecutar todos los hooks manualmente
uv run pre-commit run --all-files

# Ejecutar sobre archivos en staging (ocurre automáticamente en git commit)
uv run pre-commit run
```

## Estructura del Proyecto

```
DashAI/
├── DashAI/
│   ├── __main__.py         # Punto de entrada CLI (Typer)
│   ├── back/               # Backend FastAPI
│   │   ├── app.py          # Application factory
│   │   ├── container.py    # Kink DI container
│   │   ├── initial_components.py  # Registro de componentes al iniciar
│   │   ├── api/            # Routers y schemas de request/response
│   │   ├── converters/     # Componentes Converter
│   │   ├── dataloaders/    # Componentes DataLoader
│   │   ├── dependencies/   # Registry, motor de base de datos, cola de jobs
│   │   ├── explainability/ # Componentes Explainer
│   │   ├── exploration/    # Componentes Explorer
│   │   ├── job/            # Implementaciones de Jobs
│   │   ├── metrics/        # Componentes Metric
│   │   ├── models/         # Componentes de modelos ML
│   │   ├── optimizers/     # Componentes optimizadores de hiperparámetros
│   │   ├── plugins/        # Sistema de carga de plugins
│   │   ├── tasks/          # Componentes Task
│   │   └── types/          # Definiciones de tipos compartidos
│   └── front/              # Frontend React
│       └── src/
│           ├── api/        # Cliente HTTP
│           ├── components/ # Componentes de UI
│           └── pages/      # Componentes de páginas
├── docs/                   # Sitio de documentación (Docusaurus)
├── tests/                  # Tests del backend
└── alembic/                # Migraciones de base de datos
```
