---
title: Database
sidebar_label: Database
---

dashAI uses **SQLite** as its database (stored at `~/.DashAI/db.sqlite`) with
**SQLAlchemy** as ORM and **Alembic** for schema migrations.

## Key Tables

| Table                               | Purpose                                                                                                                                                                                                                        |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Dataset`                           | Uploaded dataset: name, Arrow file path, loading status, and timestamps.                                                                                                                                                       |
| `ModelSession`                      | Experiment configuration: dataset, task name, input/output columns, train/validation/test split ratios, and selected metrics per split.                                                                                        |
| `Run`                               | Individual training execution within a ModelSession: model name, parameters, optimizer config, goal metric, run artifacts, execution status and timing, and paths to optimization plots (history, slice, contour, importance). |
| `Metric`                            | Single metric measurement: name, value, split (`TRAIN`/`VALIDATION`/`TEST`), level (`LAST`/`STEP`/`BATCH`/`TRIAL`), and step index. Linked to a Run.                                                                           |
| `Prediction`                        | Prediction job that links a trained Run to an input Dataset, tracks execution status and timing, and stores the path to output results.                                                                                        |
| `GenerativeSession`                 | Generative model session: task type, model name, current parameters, and a human readable name and description. Owns a history of parameter snapshots and all associated GenerativeProcess records.                            |
| `GenerativeProcess`                 | Single invocation of a GenerativeSession that tracks execution status and timing. Linked to ProcessData records that hold the input and output payloads.                                                                       |
| `ProcessData`                       | Input or output payload for a GenerativeProcess: serialized data value, data type (text, image, etc.), and an `is_input` flag to distinguish inputs from outputs.                                                              |
| `GenerativeSessionParameterHistory` | Immutable snapshot of a GenerativeSession's parameters captured at each change, providing a full audit trail of parameter evolution over time.                                                                                 |
| `Notebook`                          | Working dataset session: a mutable copy of a source Dataset on which Explorers and Converters can be applied. Changes can be reverted; the result can be saved as a new Dataset for model training.                            |
| `Explorer`                          | Visualization record within a Notebook: explorer type, selected columns, parameters, path to saved results, and execution status.                                                                                              |
| `Converter`                         | Single converter step applied to a Notebook's mutable dataset: converter type, parameters, execution status, and timing. Multiple records form an ordered transformation pipeline on the Notebook.                             |
| `Plugin`                            | Installed plugin: name, author, installed and latest versions, status, summary, and full description. Owns Tag records for classification.                                                                                     |
| `Tag`                               | Classification tag for a Plugin (e.g., `Model`, `Task`, `Metric`), used for filtering and discovery.                                                                                                                           |
| `GlobalExplainer`                   | Global model explanation: explainer type, linked Run, parameters, paths to explanation data and plot, and execution status. Covers the model as a whole.                                                                       |
| `LocalExplainer`                    | Local (per instance) explanation: explainer type, linked Run and Dataset, parameters, fit parameters, scope, result paths, and execution status.                                                                               |

## Important Enums

- **`RunStatus`**: `NOT_STARTED` → `DELIVERED` → `STARTED` → `FINISHED` | `ERROR`
- **`SplitEnum`**: `TRAIN`, `VALIDATION`, `TEST`
- **`LevelEnum`**: `LAST` (final value), `STEP`, `BATCH`, `TRIAL` (for optimization)

## Data Storage

- **Datasets** are stored in Apache Arrow IPC format (columnar, efficient for ML
  workloads).
- **Trained models** are saved as pickle/joblib files under `~/.DashAI/runs/{run_id}/`.
- **Plots** generated during hyperparameter optimization are stored as serialized Plotly
  objects.
- **Metric time series** (per step, batch, or trial) are stored in the `Metric` table
  for tracking training progress.
