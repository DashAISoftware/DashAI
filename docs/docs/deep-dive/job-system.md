---
title: Job System
sidebar_label: Job System
---

## Job Queue

The **Job Queue** handles asynchronous execution of long running tasks. dashAI uses
**Huey**, a lightweight Python task queue, backed by a SQLite database.

### Architecture

| Layer          | Implementation                                                    |
| -------------- | ----------------------------------------------------------------- |
| Abstract base  | `BaseJobQueue` (`back/dependencies/job_queues/base_job_queue.py`) |
| Concrete impl. | `HueyJobQueue` (`back/dependencies/job_queues/huey_job_queue.py`) |
| Storage        | SQLite at `~/.DashAI/job_queue.db` (separate from main DB)        |
| Serialization  | `dill` (handles complex Python objects like lambdas)              |

### How the Queue Works

1. An API endpoint calls `job_queue.put(job)`, which enqueues the job and returns a
   job ID immediately.
2. The Huey consumer thread (started at application boot) picks up the job and calls
   `job.run()`.
3. Job lifecycle is tracked via Huey signals and a `task_copy` table:

   | Signal             | Status update |
   | ------------------ | ------------- |
   | `SIGNAL_ENQUEUED`  | `not_started` |
   | `SIGNAL_EXECUTING` | `started`     |
   | `SIGNAL_COMPLETE`  | `finished`    |
   | `SIGNAL_ERROR`     | `error`       |

4. The frontend polls `GET /api/v1/job/status/{job_id}` to track progress.

### Key Methods

| Method              | Description                         |
| ------------------- | ----------------------------------- |
| `put(job)`          | Enqueue a job, returns job ID       |
| `get(job_id)`       | Get job status and metadata         |
| `peek()`            | View the next job without dequeuing |
| `is_empty()`        | Check if the queue has pending jobs |
| `async_get(job_id)` | Async version of get                |

The SQLite backend uses Write-Ahead Logging (WAL) mode for safe concurrent access
between the API process and the Huey consumer.

---

## Jobs

A **Job** encapsulates a unit of background work. All jobs inherit from `BaseJob`
(`back/job/base_job.py`).

### Base Interface

```python
class BaseJob(metaclass=ABCMeta):
    TYPE = "Job"

    @abstractmethod
    def run(self) -> None: ...

    @abstractmethod
    def set_status_as_delivered(self) -> None: ...

    @abstractmethod
    def set_status_as_error(self) -> None: ...

    @abstractmethod
    def get_job_name(self) -> str: ...
```

### Job Types

| Job class       | Purpose                                          |
| --------------- | ------------------------------------------------ |
| `ModelJob`      | Train a model and compute metrics                |
| `ExplorerJob`   | Execute a data exploration/visualization         |
| `ExplainerJob`  | Generate model explanations (SHAP, etc.)         |
| `PredictJob`    | Run predictions on new data                      |
| `ConverterJob`  | Apply data transformations to a Notebook dataset |
| `GenerativeJob` | Handle generative model interactions             |
| `DatasetJob`    | Load and process datasets                        |

Each job type manages its own database status transitions and error handling. When a job
fails, it records the error message in the database and updates the relevant entity's
status to `ERROR`.
