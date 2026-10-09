---
title: Architecture
sidebar_label: Architecture
---

dashAI is a modular, extensible platform for machine learning workflows. It provides a
web based interface for training models, exploring datasets, explaining predictions, and
more. This document describes how dashAI works internally.

## High Level Overview

dashAI follows a client server architecture with three main runtime processes:

1. **FastAPI backend**: serves the REST API on port 8000. In production it also serves
   the compiled React SPA at `/app/`.
2. **Huey consumer**: a background worker that processes long running jobs (training,
   exploration, prediction, etc.).
3. **React frontend**: a single page application that communicates with the backend
   through the REST API. In development it runs separately on port 3000 (`yarn start`);
   in production it is compiled and served by FastAPI.

The entry point is `DashAI/__main__.py`, which uses Typer as CLI. On startup it:

1. Resolves the local data path (defaults to `~/.DashAI`).
2. Starts the Huey consumer. In development (normal Python install) this is an external
   **subprocess**; in bundled mode (PyInstaller) it runs as an in process **thread**.
3. Starts the FastAPI server via Uvicorn.
4. Optionally opens a browser or a PyWebView window.

Dependency injection is handled by **Kink**. The DI container (`back/container.py`)
wires together the database engine, session factory, component registry, and job queue
so that API endpoints can receive them automatically.

## Key Patterns

- **Component based extensibility**: all ML functionality (models, tasks, metrics,
  explorers, etc.) is encapsulated in components that share a common registration and
  configuration mechanism.
- **Schema driven configuration**: components declare Pydantic schemas that are
  converted to JSON Schema for dynamic frontend form generation and backend validation.
- **Asynchronous job processing**: long running operations are offloaded to a Huey
  background worker, with status tracking via signals and database updates.
- **Clean separation of concerns**: the API layer handles HTTP, the component registry
  handles discovery, the job queue handles execution, and the database handles
  persistence.

## Further Reading

| Topic                                                | Page                                              |
| ---------------------------------------------------- | ------------------------------------------------- |
| REST API structure, router map, dependency injection | [API](/deep-dive/api)                             |
| Component types, registry, and configurable objects  | [Components](/deep-dive/components)               |
| SQLite schema, ORM tables, and data storage          | [Database](/deep-dive/database)                   |
| Huey job queue and job types                         | [Job System](/deep-dive/job-system)               |
| Notebook sessions, explorers, and converters         | [Notebook](/deep-dive/notebook)                   |
| End to end training and exploration walkthroughs     | [Workflow Examples](/deep-dive/workflow-examples) |
| Column semantic types and inference                  | [Semantic Types](/deep-dive/semantic-types)       |
| Core dataset primitive, splits, and data lifecycle   | [DashAIDataset](/deep-dive/dashai-dataset)        |
