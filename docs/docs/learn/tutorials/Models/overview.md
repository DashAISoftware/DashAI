---
title: Models Module
sidebar_label: Overview
---

# Models Module

The Models module is dashAI's environment for training, evaluating, comparing, and
deploying machine learning models. Everything is organized around **Sessions**. A
session groups one or more models trained on the same dataset and task, keeping all
results, predictions, and explainability tools in one place.

---

## Key Concepts

- **Task**: The type of machine learning problem you want to solve. Each task determines
  which models are available, what column types are valid as inputs and outputs, and which
  metrics are used to evaluate results.
- **Session**: A working environment tied to a specific dataset and task. A session can
  contain multiple models trained under the same conditions, making it easy to compare
  approaches side by side.
- **Model**: A specific algorithm added to a session, configured with its own
  hyperparameters. Multiple models of the same type can coexist in the same session
  with different configurations.
- **Run**: Each time a model is trained, it produces a run with its own metrics,
  predictions, and explainability results.

---

## Available Tasks

When you open the Models module, the main area shows the available task types with
a description of each. Use the search bar to filter tasks by name.

| Task                       | Description                                                                                                                                           |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Tabular Classification** | Predict a categorical label from structured tabular data (rows and columns).                                                                          |
| **Text Classification**    | Assign predefined categories or labels to text documents based on their content. Useful for sentiment analysis, spam filtering, topic categorization. |
| **Regression**             | Predict a continuous numerical value from structured tabular data.                                                                                    |
| **Translation**            | Convert text from one language to another while preserving meaning and context (NLP task).                                                            |

Each task enforces specific requirements on column types for input and output, and these
are validated automatically when you configure the session.

---

## Sessions

Sessions are listed in the left sidebar under **Sessions**, grouped by task type.
Each session entry shows its name and the dataset it was created from.

Click **New Session** (the `+` button in the sidebar) to start creating a new session.
Click any existing session to reopen it and continue working.

The sidebar also shows the count of sessions per task type, making it easy to navigate
when working with multiple experiments.

---

## Right Panel: Available Models

When a session is open, the right panel shows the models available for the current task.
Each model has a unique icon and name. Hovering over a model card shows a popup with
a description of the algorithm, its strengths, and typical use cases.

The panel includes a search bar to filter models by name.

Available models vary by task. For Tabular Classification, for example, the panel
includes models such as Support Vector Machine (SVM), Decision Tree, K-Nearest
Neighbors (KNN), Logistic Regression, Random Forest, Gradient Boosting, and Dummy Classifier.
Other tasks have their own corresponding model catalogs.

---

## Section Structure

This section is divided into the following pages:

- **[Train a Model](/learn/tutorials/Models/train)**: How to create a session, configure input/output columns,
  define data splits, add models, set hyperparameters, and run training.
- **[Predictions](/learn/tutorials/Models/predictions)**: How to generate predictions using trained models,
  both from a full dataset and from manually entered data.
- **[Explainability](/learn/tutorials/Models/explainability)**: How to use global and local explainers to
  understand model behavior.
- **[Model Comparison](/learn/tutorials/Models/comparison)**: How to compare metrics across models using
  tables and charts.
