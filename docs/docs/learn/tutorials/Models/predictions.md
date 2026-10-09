---
title: Predictions
sidebar_label: Predictions
---

# Predictions

Once a model has been trained, you can use it to generate predictions on new data.
dashAI supports two prediction modes: **Dataset Predictions** and **Manual Predictions**.
Both are accessed from the **PREDICTIONS** tab inside each model card.

---

## Accessing Predictions

1. Open a session from the left sidebar.
2. Expand a model card that has a **Finalizado** status.
3. Click the **PREDICTIONS** tab.

The tab is divided into two sections:

| Section                 | Description                                                              |
| ----------------------- | ------------------------------------------------------------------------ |
| **Dataset Predictions** | Run the model against an entire dataset loaded in dashAI.                |
| **Manual Predictions**  | Enter one or more rows of data manually and get an immediate prediction. |

Each section shows a count badge with the number of predictions already created,
and a button to add a new one.

---

## Dataset Predictions

Use this mode when you want to apply the model to a full dataset, for example
to generate predictions for a test set or a new batch of records.

### Creating a Dataset Prediction

Click **NEW DATASET PREDICTION** to open the **Create New Prediction** modal.
The modal has two steps.

**Step 1: Configure Input**

- **Select a dataset**: Choose from the datasets available in dashAI. The dropdown
  shows the dataset name and row count (e.g., `Dataset_1 (45000 Rows)`).
- Once a dataset is selected, a **Prediction Information** panel shows:
  - **Input Columns**: the feature columns the model expects, shown as tags.
  - **Target Column**: the column the model will predict, highlighted in teal.
- A preview table shows the first rows of the selected dataset so you can verify
  it has the right structure before proceeding.

Click **NEXT** to continue.

**Step 2: Confirm**

A summary card shows the prediction configuration:

- **Model**: the algorithm type.
- **Run**: the specific model instance name.
- **Input Type**: `Dataset`.
- **Dataset**: the dataset selected in Step 1.

Review the summary and click **SEND** to queue the prediction job.
Click **BACK** to return to Step 1, or **CANCEL** to discard.

### Prediction Result

Once complete, the prediction appears as a card under **Dataset Predictions** with:

- **Prediction #N**: sequential number.
- **Timestamp**: date and time the prediction was run.
- **Dataset name**: the source dataset used.
- **Finalizado** badge when processing is complete.
- A **preview table** showing the first 100 rows of results.
- A note: _"Preview of first 100 rows. Download the CSV for complete results."_
- A **download** button (↓) to export the full results as a CSV file.
- A **delete** button (🗑) to remove the prediction.

:::tip
The preview shows 100 rows. Always download the full CSV when working with
large datasets to access all prediction results.
:::

---

## Manual Predictions

Use this mode when you want to test the model on specific, hand crafted input values.
For example, you can understand how the model responds to a particular combination of features,
or demonstrate the model's behavior in a classroom or presentation context.

### Creating a Manual Prediction

Click **NEW MANUAL PREDICTION** to open the **Create New Prediction** modal.

**Step 1: Configure Input (Manual Data Entry)**

The modal shows a table with one row per prediction instance.
Each column corresponds to an input feature the model expects.

- **Categorical columns** appear as dropdowns with the valid category values.
- **Numerical columns** appear as editable text fields.

Fill in the values for each column in the row.

Click **Add Row** (the `+` button) to add additional rows if you want to predict
multiple instances at once.

Click **NEXT** to continue.

**Step 2: Confirm**

A summary card shows:

- **Model**: the algorithm type.
- **Run**: the specific model instance name.
- **Input Type**: `Manual Input`.
- **Manual Rows**: the number of rows you entered.

Click **SEND** to submit. Click **BACK** to return and edit the data.

### Prediction Result

The result appears under **Manual Predictions** with the same structure as
dataset predictions: a numbered card with a timestamp, **Finalizado** badge,
and a preview table showing the input values alongside the predicted output.

A download button (↓) and delete button (🗑) are available on each result card.

---

## Tips

- For **Dataset Predictions**, the selected dataset must have the same input columns
  (same names and types) as the dataset the model was trained on. If column names
  differ, the prediction will fail.
- Use **Manual Predictions** to quickly validate that the model's behavior makes
  intuitive sense on specific examples before running it on a full dataset.
- You can create multiple predictions from the same trained model. Each is stored
  independently and can be downloaded separately.
- Predictions persist in the session even after you close and reopen dashAI.

## Troubleshooting

| Symptom                                   | Likely cause                                            | Solution                                                                         |
| ----------------------------------------- | ------------------------------------------------------- | -------------------------------------------------------------------------------- |
| PREDICTIONS tab is empty or disabled      | Model has not been trained                              | Train the model first; the tab activates after a successful run                  |
| Dataset prediction fails                  | Column mismatch between training and prediction dataset | Ensure the prediction dataset has the same input columns as the training dataset |
| Manual prediction form is missing columns | Model configuration has changed since training          | Reopen the model and verify the input columns in the session setup               |
| Download button produces an empty file    | Prediction job did not complete successfully            | Check the Job Queue for errors and rerun the prediction                          |
