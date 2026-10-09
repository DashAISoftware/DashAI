---
title: Notebooks
sidebar_label: Notebooks
---

# Notebooks

A Notebook is dashAI's interactive workspace for exploring and transforming a dataset.
It provides a live, temporary environment where you can apply analysis tools and data
transformations, observe their effect on the data in real time, and track every operation
as a sequential timeline, all without modifying the original dataset until you decide to save.

When you are satisfied with the result, you can save the entire process as a new dataset,
preserving the original data intact.

---

## Key Concepts

- **Nondestructive by default.** All operations in a notebook run on a working copy of
  the dataset. The original dataset is never modified.
- **Live preview.** Every time you add an Explorer or Converter, the dataset preview
  updates immediately to reflect the current state of the data.
- **Timeline.** Each operation is added inline below the data preview, forming a
  sequential record of every transformation applied.
- **Save when ready.** Once your transformations are complete, you can save the notebook's
  current state as a new, independent dataset.

---

## Accessing Notebooks

Notebooks are linked to a specific dataset. There are two ways to open one:

- **From the Dataset Explorer:** click the **NEW NOTEBOOK** button in the top right
  corner of any dataset view. This creates a new notebook associated with that dataset.
- **From the left sidebar:** under the **Notebooks** section, click any existing notebook
  to reopen it. Each notebook entry shows the name of the dataset it belongs to.

The sidebar groups notebooks under their parent dataset, so you can maintain multiple
independent working sessions for the same dataset.

---

## The Notebook Interface

When a notebook is open, the screen is divided into two areas:

### Main Area: Dataset Preview and Timeline

The central area shows:

- **Notebook title**: displayed as `Notebook: [Dataset Name]` at the top.
- **Toolbar**: two controls available at all times:
  - **FILTERS**: apply row level filters to focus the preview on a subset of the data.
  - **EXPORT**: download the current state of the dataset preview.
- **Dataset preview table**: a paginated, scrollable view of the dataset in its current
  state. Column names and their types are shown as subheaders. As you add Converters,
  the values in this table update to reflect each transformation.
- **Operation timeline**: every Explorer or Converter you add appears as a block below
  the preview table, in the order they were applied. Each block shows:
  - The tool name and type.
  - A summary table of its configuration (target column, scope, parameters).
  - A status badge: **Finalizado** (completed) or an error state if something went wrong.
  - An **Information/Edit** button to review or modify its settings.
  - A delete button to remove the operation from the timeline.

### Right Panel: Analysis Tools

The right panel is the tool library. It has two tabs:

| Tab         | Purpose                                                                                                       |
| ----------- | ------------------------------------------------------------------------------------------------------------- |
| **EXPLORE** | Analysis tools that generate visualizations or statistical summaries from the data, without modifying it.     |
| **CONVERT** | Transformation tools that modify the data: encoding, scaling, imputation, and other preprocessing operations. |

Both tabs share the same interaction pattern: a searchable, categorized list of tools
with a thumbnail preview and description on hover.

**Browsing tools**

Tools are grouped by category. Each category shows a count of available tools and can be expanded or collapsed.

EXPLORE tab categories: **Preview Inspection**, **Relationship Analysis**, **Statistical Analysis**, **Distribution Analysis**, **Multidimensional Analysis**.

CONVERT tab categories: **Basic Preprocessing**, **Encoding**, **Scaling and Normalization**, **Dimensionality Reduction**, **Feature Selection**, **Polynomial & Kernel Methods**, **Resampling & Class Balancing**, **Advanced Preprocessing**.

Hovering over any tool card reveals a popup with:

- A preview image of the tool's output.
- A short description of what it does.
- A category tag.

**View mode**

The panel supports two display modes (list and grid), toggled with the icons next to
**View Mode** at the top of the panel.

**Search**

Use the search bar at the top of the panel to filter tools by name across all categories.

---

## Explorers

Explorers are analysis tools. They read the current state of the dataset and generate
a visualization or statistical summary inline in the notebook timeline. They do not
modify the data.

Use Explorers to understand the structure of your data at any point in the transformation
process: before applying converters, between steps, or after all transformations are complete.

### Adding an Explorer

1. In the right panel, click the **EXPLORE** tab.
2. Browse or search for the Explorer you want to use. Hover over it to read its description.
3. Click on the Explorer card to open the configuration modal.

### Configuring an Explorer

The configuration modal has two steps, shown as a progress indicator at the top:
**1. Configure Scope → 2. Configure Parameters**.

The modal also has two inner tabs: **DESCRIPTION** and **DATASET**.

- **DESCRIPTION** shows what the tool does and its scope settings.
- **DATASET** shows a preview of the dataset for reference while configuring.

**Step 1: Configure Scope**

Select which columns the Explorer will use.

The column selector table shows:

| Column         | Description                                                         |
| -------------- | ------------------------------------------------------------------- |
| Index          | The column's position in the dataset (zero based).                  |
| Column Name    | The name of the column.                                             |
| Value Type     | The semantic type assigned in dashAI (Categorical, Float, Integer). |
| Data Type      | The underlying data type (float64, string, int64, etc.).            |
| Selected Order | The order in which selected columns will be passed to the tool.     |

A counter at the top of the table shows how many columns are selected and how many
are required (e.g., `Columns required: at least 2`). The counter turns green when the
minimum requirement is met.

Use the search bar to filter columns by name. Select all with the header checkbox,
or select individually by clicking each row.

Click **NEXT** once the column requirement is satisfied.

**Step 2: Configure Parameters**

Each Explorer has its own set of parameters. These vary depending on the tool.
Common parameter types include dropdowns (e.g., correlation method: `pearson`),
numeric inputs (e.g., minimum periods), and checkboxes (e.g., numeric only, plot result).

Each parameter has a **?** help icon that shows a description when hovered.

Click **CREATE EXPLORER** to run the tool and add it to the notebook timeline.
Click **BACK** to return to Step 1.

### Explorer Result

Once created, the Explorer appears as a block in the timeline below the data preview.
The result is rendered inline. For example, a correlation matrix is shown as an
interactive heatmap directly in the notebook.

The block header shows:

- The Explorer name and icon.
- A **Finalizado** badge when processing is complete.
- An **Information/Edit** button that opens the configuration modal to review settings
  or modify the scope and parameters.
- A delete button to remove the Explorer from the timeline.

---

## Converters

Converters are transformation tools. They modify the data in the notebook's working copy,
and their effect is immediately reflected in the dataset preview table above.

Use Converters to prepare your data for model training: encode categorical variables,
scale numerical columns, handle missing values, and more.

### Adding a Converter

1. In the right panel, click the **CONVERT** tab.
2. Browse or search for the Converter you want to use. Hover over it to read its description.
3. Click on the Converter card to open the configuration modal.

### Configuring a Converter

The configuration modal follows the same two step structure as Explorers:
**1. Configure Scope → 2. Configure Parameters**.

**Step 1: Configure Scope**

Unlike Explorers, Converters let you define scope for both **columns** and **rows**.

_Column scope_

The column selector works identically to the Explorer configuration:
select the columns the Converter will be applied to. The counter shows
how many columns are selected. Use the search bar to filter, or use the
header checkbox to select all.

_Row scope_

Below the column selector, a **Selection Mode** section defines which rows
the Converter will process:

| Option         | Description                                                                                                      |
| -------------- | ---------------------------------------------------------------------------------------------------------------- |
| **By Range**   | Select rows by specifying a start index and an end index. The converter will process all rows within that range. |
| **By Indices** | Select specific row indices to process.                                                                          |
| **SELECT ALL** | Button that selects all rows in the dataset. The footer shows the count: `Rows selected: all \| Total rows: N`.  |

Click **NEXT** once the scope is configured.

**Step 2: Configure Parameters**

Each Converter exposes its own parameters. These vary by tool. For example:

- A **Binarizer** has a `Threshold` parameter and a `copy` checkbox.
- A **Min-Max Scaler** has `feature_range_min` and `feature_range_max` parameters.
- A **One-Hot Encoder** has parameters for handling unknown categories.

Each parameter has a **?** help icon. Click **BACK** to return to Step 1,
or **CREATE CONVERTER** to apply the transformation.

### Converter Result

Once created, the Converter appears as a block in the timeline and the dataset
preview table updates immediately to reflect the transformation.

The block shows a summary table with:

| Field               | Description                                                |
| ------------------- | ---------------------------------------------------------- |
| **Target Column**   | The column designated as the target/output, if applicable. |
| **Scope (Columns)** | The columns the Converter was applied to.                  |
| **Scope (Rows)**    | The row selection used (e.g., `All`).                      |

The same **Finalizado** badge, **Information/Edit** button, and delete button
are available as with Explorers.

:::note Operation order matters
Converters are applied in the order they appear in the timeline. If you apply a
scaler before an encoder, the scaler runs first on the original values. Reordering
or deleting operations will change the final state of the data.
:::

---

## Available Explorer Categories

The EXPLORE tab organizes tools into five categories:

| Category                      | What it contains                                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Preview Inspection**        | Direct views of the raw data: Describe Dataset (statistical summary table) and Show Rows (paginated record view).  |
| **Relationship Analysis**     | Tools for analyzing how pairs of variables relate: Density Heatmap, Multiple Scatter Plot, Scatter Plot.           |
| **Statistical Analysis**      | Formal quantitative measures of structure: Correlation Matrix, Covariance Matrix.                                  |
| **Distribution Analysis**     | Shape and spread of individual variables: Box Plot, Empirical Cumulative Distribution, Histogram Plot, Word Cloud. |
| **Multidimensional Analysis** | Patterns across many variables simultaneously: Multiple Column Chart, Parallel Categories, Parallel Coordinates.   |

---

## Available Converter Categories

The CONVERT tab organizes tools into eight categories:

| Category                         | What it contains                                                                                                                            |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Basic Preprocessing**          | Fundamental data cleaning: NaN Remover, Simple Imputer, KNN Imputer, Missing Indicator, Column Remover, Character Replacer.                 |
| **Encoding**                     | Categorical to numerical conversion: Binarizer, Label Binarizer, Label Encoder, One-Hot Encoder, Ordinal Encoder.                           |
| **Scaling and Normalization**    | Numerical range adjustment: Max Abs Scaler, Min-Max Scaler, Normalizer.                                                                     |
| **Dimensionality Reduction**     | Variable compression: PCA, Incremental PCA, Truncated SVD, Fast ICA, Nystroem Approximation, Variance Threshold.                            |
| **Feature Selection**            | Statistically guided variable elimination: Select K Best, Select Percentile, Select FDR, Select FPR, Select FWE, Generic Univariate Filter. |
| **Polynomial & Kernel Methods**  | Nonlinear feature expansion: Polynomial Features, RBF Sampler, Additive Chi² Sampler, Skewed Chi² Sampler.                                  |
| **Resampling & Class Balancing** | Class imbalance correction: SMOTE, SMOTE-ENN, Random Under-Sampler.                                                                         |
| **Advanced Preprocessing**       | Text to numerical transformation: TF-IDF, Bag of Words, Tokenizer, Embedding.                                                               |

---

## Saving the Result

When you are satisfied with the transformations applied in the notebook, click
**SAVE AS NEW DATASET** in the top right corner of the notebook.

This creates a new, independent dataset in dashAI that contains the data in its
current transformed state. The new dataset appears in the **Available Datasets**
list in the left sidebar and can be used for experiments just like any uploaded dataset.

The original dataset that the notebook was based on remains unchanged.

:::tip When to save
Save a new dataset when you have a stable, reproducible transformation pipeline
that you want to use for training. You can create multiple datasets from the same
notebook by saving at different points in the timeline.
:::

---

## Tips

- Add an Explorer **before and after** a Converter to visually confirm that the
  transformation had the expected effect on your data.
- Use the **FILTERS** toolbar control to inspect specific subsets of the data
  after applying a transformation.
- If a Converter produces unexpected results, click **Information/Edit** on its
  timeline block to review the scope and parameters, or delete it and reconfigure.
- The column **Selected Order** in the scope selector matters for some tools,
  for example tools that treat the first selected column as a reference.

## Troubleshooting

| Symptom                                       | Likely cause                      | Solution                                                                           |
| --------------------------------------------- | --------------------------------- | ---------------------------------------------------------------------------------- |
| NEXT button is not active in Step 1           | Not enough columns selected       | Check the required columns counter and select the minimum required                 |
| Explorer result does not appear               | Processing error                  | Check the timeline block for an error state and review the parameter configuration |
| Converter did not change the data as expected | Wrong columns or rows in scope    | Click **Information/Edit** on the block and review the scope settings              |
| Dataset preview looks wrong after a Converter | Operations applied in wrong order | Review the timeline order; delete and add operations again if needed               |
| SAVE AS NEW DATASET is not available          | No operations have been added yet | Add at least one Explorer or Converter before saving                               |
