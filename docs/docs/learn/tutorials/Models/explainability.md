---
title: Explainability
sidebar_label: Explainability
---

# Explainability

The Explainability tab lets you attach explainers to a trained model to understand
how it makes decisions. dashAI supports two types of explainers: **Global Explainers**
and **Local Explainers**.

---

## Accessing Explainability

1. Open a session from the left sidebar.
2. Expand a model card that has a **Finalizado** status.
3. Click the **EXPLAINABILITY** tab.

The tab is divided into two panels side by side:

| Panel                 | Description                                                                                                               |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Global Explainers** | Analyze the model's behavior across the entire dataset: which features matter most overall.                               |
| **Local Explainers**  | Analyze the model's behavior on individual predictions: why did the model produce a specific output for a specific input. |

Each panel shows a count badge of explainers already created, and a button to add a new one.

---

## Global Explainers

Global explainers answer the question: _"What does the model rely on in general?"_

They produce results like feature importance rankings or SHAP summary plots that
describe the model's overall decision making patterns across the training or test data.

### Adding a Global Explainer

Click **+ NEW GLOBAL EXPLAINER** to open the explainer configuration flow.

The flow follows the same two step pattern used throughout dashAI:

**Step 1: Configure Scope**

Select which columns the explainer will analyze. The column selector table shows
the index, name, value type, and data type of each column. Select the columns you
want to include in the explanation.

Some explainers require a minimum number of columns. The counter at the top of
the table shows how many are selected and the minimum required.

**Step 2: Configure Parameters**

Each explainer has its own parameters. These vary by algorithm. Common options
include the number of samples to use, background dataset settings, and output
format preferences. Each parameter has a **?** help icon with a description.

Click **CREATE EXPLAINER** to run it and add the result to the tab.

---

## Local Explainers

Local explainers answer the question: _"Why did the model predict this specific output
for this specific instance?"_

They produce instance level explanations. For example, they show which features
pushed the prediction toward a particular class for a single row of data.

### Adding a Local Explainer

Click **+ NEW LOCAL EXPLAINER** to open the explainer configuration flow.

The configuration follows the same two step pattern as global explainers, with
scope selection (columns) and parameter configuration.

Some local explainers additionally require you to select a specific prediction
or row to explain. This varies by the explainer type.

---

## Explainer Results

Once created, each explainer appears as a result card in its panel with:

- The explainer name and type.
- A **Finalizado** badge when complete.
- The explanation output rendered inline (chart, table, or visualization depending
  on the explainer type).
- An **Edit** button to modify scope or parameters and rerun.
- A **Delete** button to remove the explainer.

---

## Tips

- Run a **Global Explainer** first to get an overview of feature importance.
  This helps identify which input columns matter most and which may be redundant.
- Use **Local Explainers** when a specific prediction seems unexpected. They help
  trace which features drove an unusual result.
- Explainability tools are available per model, so you can run the same explainer
  on multiple models in the same session to compare how different algorithms
  use the same features.
- The **EXPLAINABILITY** tab badge shows a count of created explainers, making
  it easy to track which models have been analyzed.

## Troubleshooting

| Symptom                            | Likely cause                                         | Solution                                                             |
| ---------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------- |
| EXPLAINABILITY tab is inactive     | Model has not been trained                           | Train the model first before adding explainers                       |
| Explainer creation fails           | Incompatible column types for the selected explainer | Review the explainer's column type requirements and adjust the scope |
| No results rendered after creation | Processing error                                     | Check the Job Queue for error details and retry                      |
