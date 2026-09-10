---
title: Model Comparison
sidebar_label: Model Comparison
---

# Model Comparison

The Model Comparison panel sits at the top of every session and gives you a unified
view of all models in the session and their performance metrics. It updates
automatically as models finish training.

---

## The Comparison Table

By default the panel shows a **TABLE** view with one row per model. Columns include:

| Column             | Description                                                                                                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Model Name**     | The name assigned when the model was added.                                                                                                                                          |
| **Model**          | The algorithm type (e.g., Support Vector Machine, Decision Tree).                                                                                                                    |
| **Metric columns** | One column per evaluation metric. For classification: Accuracy, F1, Precision, Recall, ROCAUC, LogLoss, and more. For regression: RMSE, MAE, and others. Metrics shown vary by task. |
| **Actions**        | ▶ run, 👁 view details, 🗑 delete.                                                                                                                                                     |

Models that have not been trained yet show `-` in the metric columns.

### Switching Between Splits

Three buttons above the table let you choose which data split the metrics reflect:

| Button         | Description                                                                                            |
| -------------- | ------------------------------------------------------------------------------------------------------ |
| **TRAINING**   | Metrics calculated on the training subset.                                                             |
| **VALIDATION** | Metrics calculated on the validation subset. Used during development to tune hyperparameters.          |
| **TEST**       | Metrics calculated on the held out test subset. The most reliable indicator of real world performance. |

Switch between splits to understand whether a model is overfitting (high training
metrics but low test metrics) or generalizing well.

---

## Charts View

Click **CHARTS** in the top right of the comparison panel to switch to a visual view.

### Chart Types

Two chart types are available, selectable with the **BARRA** (Bar) and **RADAR** toggles:

**Bar Chart**

Displays a grouped bar chart where each group represents a metric and each bar
within the group represents a model. This makes it easy to compare models
on any individual metric at a glance.

**Radar Chart**

Displays a spider/radar chart where each axis represents a metric. Each model
is drawn as a polygon. A model with uniformly good performance across all metrics
appears as a larger, more balanced polygon. Useful for identifying trade offs:
a model may score high on Accuracy but low on Recall, visible as an irregular shape.

### Metric Selection

On the left side of the charts view, a **Metrics** panel lists all available metrics
with checkboxes. Two quick select buttons are available:

- **ALL** enables all metrics.
- **NONE** clears all selections.

Select only the metrics relevant to your analysis to reduce visual clutter.
The chart updates immediately as you check or uncheck metrics.

---

## Tips

- Always compare models on the **TEST** split for final evaluation, because training and
  validation metrics can be misleading if the model overfit.
- Use the **Radar Chart** to quickly spot models with balanced performance across
  all metrics vs. models that excel in one area but underperform in others.
- Add a baseline model (e.g., Dummy Classifier for classification tasks) to the
  session before training other models. It sets a minimum performance floor
  that all other models should exceed.
- The comparison table is scrollable horizontally when many metrics are shown.
  Scroll right to see all columns.

## Troubleshooting

| Symptom                                       | Likely cause                       | Solution                                                               |
| --------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------- |
| All metric columns show `-`                   | No models have been trained yet    | Train at least one model using the **TRAIN** button on its card        |
| Some models show `-` while others show values | Those models have not been trained | Click **TRAIN** on each untrained model card, or use **RUN ALL**       |
| Charts view is empty                          | No trained models in the session   | Train at least one model before switching to charts view               |
| Radar chart is hard to read                   | Too many metrics selected          | Deselect less relevant metrics using the **Metrics** panel on the left |
