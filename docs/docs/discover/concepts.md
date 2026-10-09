---
title: Key Concepts
sidebar_label: Key Concepts
sidebar_position: 2
---

# Key Concepts

These are the core concepts you will encounter throughout dashAI. Each term corresponds to something you can see and interact with directly in the interface.

---

## Dataset

A dataset is the collection of data you work with. It is typically a structured table (CSV, Excel, JSON). Every workflow in dashAI begins by loading a dataset into the **Datasets** module.

Once loaded, a dataset is persistent: it stays in dashAI until you delete it, and it can be used across multiple notebooks and sessions.

:::note
dashAI provides dataloaders for common formats (CSV, Excel, JSON). You can [create custom dataloaders](/build/plugin-development/overview) to support additional data sources and install them via the **Plugins** module.
:::

---

## Notebook

A notebook is a nondestructive workspace attached to a dataset. It lets you apply a sequence of **Explorers** and **Converters** to a working copy of the data, while the original dataset remains unchanged.

Each operation you add appears in the notebook timeline, so your transformation process is always visible and auditable. When the result is ready, you save it as a new dataset with **Save as New Dataset**.

---

## Explorer

An explorer is a visualization or analysis tool in the notebook's **EXPLORE** tab. Explorers read the current state of the data and produce a result, such as a chart, a statistical table, or a heatmap, without modifying the data.

dashAI comes with explorers organized into five categories: Preview Inspection, Relationship Analysis, Statistical Analysis, Distribution Analysis, and Multidimensional Analysis.

:::note
You can also [develop custom explorers](/build/plugin-development/overview) and install additional ones through the **Plugins** module.
:::

---

## Converter

A converter is a data transformation tool in the notebook's **CONVERT** tab. Converters modify the data by encoding categories, scaling numerical values, removing missing values, reducing dimensionality, and more. Each converter is applied to a specific set of columns and rows, and the effect is immediately visible in the dataset preview.

dashAI includes more than 30 converters organized into eight categories: Basic Preprocessing, Encoding, Scaling and Normalization, Dimensionality Reduction, Feature Selection, Polynomial & Kernel Methods, Resampling & Class Balancing, and Advanced Preprocessing.

:::note
You can [create custom converters](/build/plugin-development/overview) and install additional ones from the **Plugins** module.
:::

---

## Task

A task defines the type of ML problem you want to solve. The task determines which models are available, which column types are valid as inputs and outputs, and which metrics are used to evaluate results.

dashAI's **Models** module supports four core tasks:

| Task                       | What it predicts                                        |
| -------------------------- | ------------------------------------------------------- |
| **Tabular Classification** | A category from structured table data                   |
| **Regression**             | A continuous numerical value from structured table data |
| **Text Classification**    | A category assigned to a text document                  |
| **Translation**            | Text converted from one language to another             |

The **Generative** module supports separate tasks for text and image generation. See [Generative AI](/learn/tutorials/generative) for details.

:::note
You can extend dashAI by [developing new tasks](/build/plugin-development/overview) and installing them via the **Plugins** module.
:::

---

## Session

A session is the central unit of work in the Models module. It ties together a dataset, a task, a column configuration (which columns are inputs, which is the target), and a data split strategy. All models you train for that problem live inside the same session, making it easy to compare them.

Sessions are grouped by task type in the left sidebar. You can have multiple sessions for the same dataset, for example to explore different input column combinations or split strategies.

---

## Model

A model is a specific algorithm added to a session. Each model has its own name, hyperparameter configuration, and training status. You can add multiple models of the same or different types to the same session and train them independently or all at once with **Run All**.

dashAI includes a growing library of models powered by scikit-learn, Hugging Face, PyTorch, and TensorFlow.

:::note
You can [develop new model integrations](/build/plugin-development/overview) and discover additional models through the **Plugins** module.
:::

---

## Training Status

Each model in a session has one of five statuses:

| Status          | Meaning                                    |
| --------------- | ------------------------------------------ |
| **Not Started** | The model has been added but never trained |
| **Delivered**   | The models has been queued                 |
| **Started**     | The training process has started           |
| **Finished**    | Training completed successfully            |
| **Error**       | Training failed; review parameters or data |

---

## Metric

Metrics measure how well a trained model performs on each data split. dashAI automatically calculates metrics appropriate for the type of task you are solving, allowing you to understand your model's effectiveness across different data splits.

For **classification tasks**, you can review metrics like Accuracy (percentage of correct predictions), F1 (balance between precision and recall), Precision and Recall (true positives relative to total positives and total actual positives), or ROCAUC (model's ability to distinguish between classes). Additional metrics include LogLoss, HammingDistance, and CohenKappa for deeper analysis.

For **regression tasks**, metrics focus on prediction error: RMSE (root mean squared error) penalizes larger errors, while MAE (mean absolute error) provides an average error magnitude.

For **translation tasks**, metrics include BLEU (similarity to reference translations) and TER (number of edits needed to match a reference).

:::note
dashAI includes a core set of metrics appropriate for each task. If you need additional metrics for specialized use cases, you can [develop custom metrics](/build/plugin-development/overview) and add them via the **Plugins** module.
:::

---

## Prediction

A prediction is the output of a trained model applied to new data. dashAI supports two prediction modes: **Dataset Predictions** (run the model over an entire loaded dataset) and **Manual Predictions** (enter specific values row by row in the interface).

---

## Explainer

An explainer is a tool for interpreting a trained model's behavior. **Global explainers** analyze model behavior across the full dataset (e.g., which features matter most overall). **Local explainers** analyze a specific prediction (e.g., why did the model produce this output for this particular record).

dashAI provides built in explainers including Kernel SHAP, Permutation Feature Importance, and Partial Dependence Plots.

:::note
You can [create custom explainers](/build/plugin-development/overview) and install additional interpretability tools from the **Plugins** module.
:::

---

## Job

Long running operations such as training a model, running an explorer, or generating a prediction are executed as background **jobs**. The Job Queue at the bottom right of the screen shows active and completed jobs so you can continue working while an operation runs.
