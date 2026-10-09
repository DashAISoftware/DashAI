---
title: Workflow Examples
sidebar_label: Workflow Examples
---

## Training a Model

This example walks through the entire process of training a text classification model,
from user interaction to final results.

### Step 1: Create a Model Session

The user selects a dataset, a task, input/output columns, metrics, and data splits in
the frontend. The frontend sends:

```
POST /api/v1/model-session/
{
    "dataset_id": 1,
    "task_name": "TextClassification",
    "input_columns": ["text"],
    "output_columns": ["label"],
    "train_metrics": ["Accuracy", "F1"],
    "validation_metrics": ["Accuracy"],
    "test_metrics": ["Accuracy"],
    "splits": { "train": 0.7, "validation": 0.15, "test": 0.15 }
}
```

The API creates a `ModelSession` record in the database and returns its ID.

### Step 2: Create a Run

The user selects a model, configures its parameters, and optionally selects a
hyperparameter optimizer. The frontend sends:

```
POST /api/v1/run/
{
    "model_session_id": 1,
    "model_name": "DistilBertTransformer",
    "parameters": { "learning_rate": 1e-5, "num_epochs": 3 },
    "optimizer_name": null,
    "optimizer_parameters": {},
    "goal_metric": "F1",
    "name": "DistilBERT run"
}
```

The API creates a `Run` record with status `NOT_STARTED`.

### Step 3: Enqueue the Training Job

The frontend requests job execution:

```
POST /api/v1/job/
{
    "job_type": "ModelJob",
    "kwargs": { "run_id": 1 }
}
```

The API instantiates a `ModelJob` with the given `run_id`, calls `job_queue.put(job)`,
and returns the Huey job ID to the frontend immediately.

### Step 4: Background Execution

The Huey consumer picks up the `ModelJob` and calls `job.run()`. Inside `run()`:

1. Load the `Run`, `ModelSession`, and `Dataset` records from the database.
2. Load the dataset from its Arrow file.
3. Instantiate the `Task` class (e.g., `TextClassification`) and call
   `prepare_for_task()` to validate and format the data.
4. Split the data into train/validation/test subsets based on the session's split
   ratios.
5. Instantiate the `Model` class (e.g., `DistilBertTransformer`) with the user's
   parameters via `validate_and_transform()`.
6. Call `model.train(x_train, y_train, x_val, y_val)`.
7. For each split (train, validation, test), call `model.calculate_metrics()` which
   computes all selected metrics and stores them in the `Metric` table.
8. Save the trained model to disk at `~/.DashAI/runs/{run_id}/`.
9. Update the `Run` status from `STARTED` to `FINISHED`.

If a hyperparameter optimizer is configured, step 6 is replaced by
`optimizer.optimize()`, which runs multiple trials, tracks per trial metrics
(`LevelEnum.TRIAL`), and generates Plotly visualization plots (history, slice, contour,
importance) saved alongside the run.

### Step 5: Retrieve Results

The frontend polls for completion and retrieves results:

```
GET /api/v1/job/status/{job_id}         # Poll until finished
GET /api/v1/run/{run_id}                # Get run details with metrics
GET /api/v1/run/plot/{run_id}/history   # Get optimization plots (if applicable)
```

The frontend displays the metrics and any optimization visualizations to the user.

---

## Creating a Plot for a Dataset

This example shows how a user creates a scatter plot exploration for a dataset.

### Step 1: Select an Explorer

The frontend fetches available explorers from the registry:

```
GET /api/v1/component/?select_types=["Explorer"]
```

The response includes component schemas, so the frontend can render configuration forms
dynamically. The user selects `ScatterPlotExplorer`.

### Step 2: Configure and Launch the Exploration

The user selects columns and sets parameters (e.g., color mapping). The frontend
validates the explorer's parameters:

```
POST /api/v1/explorer/validate
{
    "exploration_type": "ScatterPlotExplorer",
    "columns": ["sepal_length", "sepal_width"],
    "parameters": { "color": "species" }
}
```

After validation, the frontend creates the explorer and enqueues the job:

```
POST /api/v1/explorer/
{
    "notebook_id": 1,
    "exploration_type": "ScatterPlotExplorer",
    "columns": ["sepal_length", "sepal_width"],
    "parameters": { "color": "species" }
}
```

This creates an `Explorer` record in the database and enqueues an `ExplorerJob`.

### Step 3: Background Execution

The Huey consumer picks up the `ExplorerJob` and calls `job.run()`:

1. Load the `Explorer` record and the associated dataset.
2. Instantiate the `ScatterPlotExplorer` component.
3. Call `explorer.launch_exploration(dataset, explorer_info)`, which generates the
   visualization.
4. Call `explorer.save_notebook()` to persist the exploration as a notebook.
5. Call `explorer.get_results()` to extract the renderable output.
6. Save results to disk and update the `Explorer` status to `FINISHED`.

### Step 4: Display Results

The frontend retrieves the exploration results:

```
GET /api/v1/explorer/{explorer_id}/results
```

The response contains the plot data (typically a Plotly JSON specification), which the
frontend renders as an interactive visualization.
