---
title: Train a Model
sidebar_label: Train a Model
---

# Train a Model

This page walks you through creating a session, adding models, configuring
hyperparameters, and running training in dashAI.

## Prerequisites

- At least one dataset uploaded to dashAI.
- The dataset must have columns compatible with the task you want to run
  (e.g., a categorical output column for classification tasks).

---

## Step 1: Select a Task

In the Models module landing page, click on the task that matches your problem.
Each task card shows a description to help you choose the right one.

If you have an existing session, you can also click it directly in the left sidebar
to skip this step and resume working.

---

## Step 2: Create a Session

After selecting a task, a two step session creation flow begins.

### 2a: Select Dataset and Name the Session

- Use the **Select a dataset** dropdown to choose from your available datasets.
  Once selected, a summary card shows the dataset name, creation date, row count,
  and column count.
- Enter a name in the **Session Name** field. A default name is prefilled
  based on the task type (e.g., `Session_Tabular Classification_1`), but you
  can change it to something more descriptive.

Click **NEXT** to continue.

### 2b: Prepare the Dataset

This step has two parts: defining columns and defining the data split.

**Input and Output Columns**

dashAI validates whether the selected dataset is compatible with the chosen task.
A banner at the top of the step confirms compatibility and shows the required column
types for inputs and outputs.

- **Input Columns**: Select the features the model will use to learn. Each column
  is shown as a tag with its type badge (Float, Integer, Categorical). Click inside
  the field and select columns from the dropdown. Remove any column by clicking the
  `×` on its tag.
- **Output Columns**: Select the target column the model will predict. The output
  must match the type required by the task (e.g., Categorical for classification tasks).

:::tip Column type requirements
Each task enforces specific type requirements. For Tabular Classification, inputs
can be Float, Integer, or Categorical, while the output must be Categorical with
cardinality 1. If the compatibility banner shows a warning, review your column types
in the Dataset Explorer before creating the session.
:::

**Data Split**

Define how dashAI divides the dataset into training, validation, and test subsets.
Three options are available:

| Option                          | Description                                                                                                                                |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **Use predefined splits**       | Uses train/validation/test splits already defined in the dataset file. Only available if the dataset was uploaded with presplit structure. |
| **Random split by proportion**  | Randomly assigns rows to each subset according to the proportions you specify. Default is Train: 0.6, Validation: 0.2, Test: 0.2.          |
| **Manual split by row indices** | Manually specify the start and end row indices for each subset.                                                                            |

When using **Random split**, three additional options are available:

| Option       | Description                                                                                                                     |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| **Shuffle**  | Randomly shuffles the rows before splitting. Recommended to avoid ordering bias in the data. Enabled by default.                |
| **Stratify** | Ensures each split preserves the same class proportions as the full dataset. Useful for imbalanced datasets.                    |
| **Seed**     | A fixed random seed for reproducibility. Default is `42`. Set a specific value to ensure the same split is produced every time. |

Click **CREATE SESSION** to finish setup. The session opens immediately.

---

## Step 3: Add Models

Once the session is open, the main area shows the **Model Comparison** panel and the
right panel lists the **Available Models** for your task.

To add a model:

1. Click on a model in the right panel. A description popup appears on hover. Read
   it to understand what the algorithm does before adding it.
2. Clicking the model opens the **Add Model to Session** modal.

### Configure the Model

The modal has one step: **Configure Model**.

- **Model Name**: A unique name for this model instance within the session.
  Prefilled with a default (e.g., `SVC_1`). Change it to something meaningful
  if you plan to add multiple instances of the same model type.
- **Model**: Shows the algorithm type (read only, set by your selection).

**Hyperparameters**

Below the name, each configurable hyperparameter is listed with its current value
and a **?** help icon. Parameters vary by model. For example:

- An SVM (SVC) has parameters like `C`, `coef0`, `degree`, `gamma`, `kernel`,
  `max_iter`, `shrinking`, `tolerance`.
- A Decision Tree has `max_depth`, `min_samples_split`, `criterion`, and others.
- A KNN has `n_neighbors`, `weights`, `metric`, and others.

**Hyperparameter Optimization**

Each numeric hyperparameter has a toggle: **Optimize hyperparameter [name]**.
When enabled, dashAI will automatically search for the best value for that parameter
during training instead of using the fixed value you entered. You can enable
optimization for any combination of parameters.

Click **ADD MODEL** to add it to the session. Click **CANCEL** to discard.

You can add as many models as needed, including multiple instances of the same
algorithm with different configurations. Each appears as an independent row in the
comparison table.

---

## Step 4: Train Models

Once models are added, they appear in two places:

**Comparison Table (top)**

A summary table showing all models in the session with columns:

- **Model Name**: the name you assigned.
- **Model**: the algorithm type.
- **Actions**: three buttons per row: ▶ run, 👁 view details, 🗑 delete.

**Model Cards (below the table)**

Each model has an expandable card showing its name, algorithm, current status badge,
and action buttons:

| Button           | Description                                                                         |
| ---------------- | ----------------------------------------------------------------------------------- |
| **EDIT**         | Reopens the configuration modal to change the model name or hyperparameters.        |
| **TRAIN**        | Starts training this model. Changes to **RE-TRAIN** after the first run.            |
| **Status badge** | Shows the current state: **Not Started**, **Finalizado** (completed), or **Error**. |
| 🗑                | Deletes the model from the session.                                                 |

**To train a single model:** click **TRAIN** on its card.

**To train all models at once:** click **RUN ALL** in the top right of the comparison
table header. This queues all untrained models for sequential execution.

Training runs as a background job, so you can monitor progress in the **Job Queue**
at the bottom right of the screen.

---

## Step 5: Review Results

After training completes, each model card shows a **Finalizado** badge and expands
to show four tabs:

### LIVE METRICS

Shows the model's performance metrics organized into three subtabs:
**TRAINING**, **VALIDATION**, and **TEST**.

A **Metrics** dropdown lets you select which metric to display. Available metrics
depend on the task. For classification they include Accuracy, F1, Precision,
Recall, ROCAUC, LogLoss, HammingDistance, CohenKappa. For regression they include
RMSE, MAE, and others.

:::note
Metrics are only available after training is complete. If a model shows
"No metrics available for this view", it has not been trained yet.
:::

### EXPLAINABILITY

Shows global and local explainers attached to this model. See the
[Explainability](/learn/tutorials/Models/explainability) page for details.

### PREDICTIONS

Shows dataset predictions and manual predictions generated from this model. See the
[Predictions](/learn/tutorials/Models/predictions) page for details.

### HYPERPARAMETERS

Shows the exact hyperparameter values used in the last training run. Useful for
verifying which values were selected when hyperparameter optimization was enabled.

---

## Tips

- Add a **Dummy Classifier** (or equivalent baseline model for your task) alongside
  your main models. It gives you a performance baseline to compare against:
  any model that doesn't beat the dummy needs more tuning.
- Enable **Stratify** when working with imbalanced datasets to ensure each split
  has a representative sample of all classes.
- Use a fixed **Seed** when comparing multiple models to ensure they all train and
  evaluate on exactly the same data split.
- You can add multiple instances of the same model type with different hyperparameter
  configurations to explore how parameters affect performance.

## Troubleshooting

| Symptom                                    | Likely cause                                | Solution                                                                      |
| ------------------------------------------ | ------------------------------------------- | ----------------------------------------------------------------------------- |
| Compatibility banner shows a warning       | Column types don't match task requirements  | Check column types in the Dataset Explorer and reupload if needed             |
| NEXT button is not active in session setup | Required fields are empty                   | Ensure a dataset is selected and a session name is entered                    |
| Model shows **Error** badge after training | Invalid hyperparameter values or data issue | Click **EDIT** to review parameters, or check the Job Queue for error details |
| No metrics available after training        | Model trained on incompatible data          | Review input/output column selection and retrain                              |
| RUN ALL is not visible                     | No models have been added yet               | Add at least one model before using RUN ALL                                   |
