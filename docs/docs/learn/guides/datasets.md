---
title: "Module Guide: Datasets"
sidebar_label: Datasets
sidebar_position: 1
---

# Module Guide: Datasets

The Datasets module is the entry point for all data in dashAI. Every other module (Models, Notebooks, Generative) depends on a dataset being loaded here first. This guide covers what the module does, how its components work, and how to get the most out of each feature.

---

## The Dataset Module Interface

The left sidebar lists all available datasets and notebooks. Each dataset entry shows its name, row count, and column count at a glance. Clicking a dataset opens its full view in the main area.

The **New Dataset/Notebook** button at the top of the sidebar is the entry point for both uploading a new dataset and creating a new notebook linked to an existing one.

---

## Uploading Data

dashAI supports four file formats. Each has a dedicated dataloader that controls how the file is parsed.

### Supported Formats and Dataloaders

| Format | Dataloader        | Extensions      |
| ------ | ----------------- | --------------- |
| CSV    | `CSVDataLoader`   | `.csv`          |
| Excel  | `ExcelDataLoader` | `.xlsx`, `.xls` |
| JSON   | `JSONDataLoader`  | `.json`         |

The upload flow is inline. Everything happens within the Datasets page without navigating away.

### Type Inference

After uploading a file, dashAI reads a configurable number of rows (**Inference Rows**, default 1000) and automatically assigns a semantic type to each column: `Categorical`, `Float`, or `Integer`. These types are used throughout the platform: by the Explorer tabs, the Models module for column compatibility checks, and Notebook converters for filtering applicable operations.

You can override any inferred type directly in the upload preview by clicking the dropdown in each column header. Correcting types at upload time prevents downstream issues in experiments and transformations.

### CSVDataLoader Parameters

| Parameter | Default  | Description                                                                                                             |
| --------- | -------- | ----------------------------------------------------------------------------------------------------------------------- |
| Name      | filename | Display name for the dataset inside dashAI                                                                              |
| Separator | `,`      | Character separating column values. Use `;` for European locale Excel exports                                           |
| Header    | `infer`  | Row containing column names. `infer` detects automatically; set a number for files with metadata rows before the header |
| Names     | Null     | Override column names manually                                                                                          |
| Encoding  | `utf-8`  | File character encoding. Use `latin-1` or `ISO-8859-1` for files with accented characters                               |
| NA values | Null     | Additional strings to treat as missing (e.g. `"?"`, `"N/A"`)                                                            |

### ExcelDataLoader Parameters

| Parameter       | Default | Description                                             |
| --------------- | ------- | ------------------------------------------------------- |
| Sheet           | `0`     | Zero based index of the sheet to load                   |
| Header          | `0`     | Zero based row index of the column header               |
| Use columns     | Null    | Comma separated list of columns to load; Null loads all |
| Skip rows       | Null    | Rows to skip at the beginning of the sheet              |
| N rows          | Null    | Maximum rows to load; Null loads all                    |
| Names           | Null    | Override column names                                   |
| NA values       | Null    | Additional NA strings                                   |
| Keep default NA | Yes     | Recognize built in NA strings automatically             |
| True values     | Null    | Strings to interpret as boolean `True`                  |
| False values    | Null    | Strings to interpret as boolean `False`                 |

### JSONDataLoader Parameters

| Parameter | Default  | Description                                                |
| --------- | -------- | ---------------------------------------------------------- |
| Name      | filename | Display name                                               |
| Data key  | `data`   | Key inside the JSON object that contains the records array |

The JSONDataLoader expects a structure like `{ "data": [{...}, {...}] }`. Change `Data key` to match the actual key in your file if it differs from `data`.

---

## Dataset Explorer (EDA)

Clicking a dataset opens its built in EDA panel, a set of automatic analyses that run immediately with no configuration. The panel is organized into six tabs.

### Quality Score

A percentage shown at the top right of every dataset view. It reflects the absence of structural data quality issues. A score of 100% means no constant columns, high cardinality issues, or potential ID columns were detected. Any score below 100% means the **Data Quality** tab has findings worth reviewing before training.

### Overview Tab

Shows a **Dataset Preview** table with the actual data rows. Four toolbar controls are available:

- **COLUMNS**: show/hide specific columns to focus on what matters
- **FILTERS**: apply row level filters to inspect subsets
- **DENSITY**: toggle row height between compact and comfortable
- **EXPORT**: download the current view

The five summary cards at the top of every dataset view give an immediate health check: Total Rows, Total Columns, File Size (MB), Duplicated Rows, and Missing Values. Nonzero values in Duplicated Rows or Missing Values indicate data quality work may be needed before training.

### Numerical Analysis Tab

For every `Float` or `Integer` column, dashAI computes and displays:

**Descriptive statistics:** Mean, Median, Standard Deviation, Unique count

**Distribution metrics:** Min, Q1, Median, Q3, Max

**Shape indicators:** Skewness, Kurtosis, Outlier count, Range

**Boxplot:** Visual five number summary. Outliers appear as points beyond the whiskers.

**Intelligent alerts:** dashAI detects common distribution patterns and suggests actions automatically. For example:

> ⚠️ Right skewed distribution: Consider applying a log transformation.

These suggestions are actionable: if you see one, the corresponding Notebook converter (e.g., a log transform) is the recommended next step.

### Categorical Tab

For every `Categorical` column:

- **Unique Values**: how many distinct categories exist
- **Most Frequent**: the dominant category value
- **Top Value Count**: how many times the dominant value appears
- **Value Distribution**: bar chart of all category counts
- **Proportion**: pie chart showing each category's share

A heavily imbalanced distribution (where one category dominates) in your target column is a signal to consider resampling converters (SMOTE, RandomUnderSampler) before training classification models.

### Text Tab

Active only when text typed columns exist. Shows length based statistics per column: Average Length, Median Length, Average Word Count, Unique Values, Min/Max Length, Range.

A **low uniqueness warning** appears when a text column has very few distinct values. This typically means the column was misclassified as text and should be `Categorical`. Fixing this at the dataset level (via reupload) avoids issues downstream.

### Data Quality Tab

Reports three structural issue categories:

| Issue                   | What it means                                                         | What to do                                                     |
| ----------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------- |
| **Constant Columns**    | Every row has the same value, so no predictive information            | Remove before training                                         |
| **High Cardinality**    | A categorical column has an unusually large number of distinct values | Investigate; may be a free text field or ID column in disguise |
| **Possible ID Columns** | Column appears to be a unique row identifier                          | Exclude from model input columns                               |

The **Missing Data Patterns** panel shows whether missing values are randomly distributed or concentrated in specific columns. Concentrated missing values may indicate a systematic data collection issue worth addressing before modeling.

### Correlations Tab

Computes pairwise Pearson correlations between all numerical columns. The interactive bar chart shows each column pair with color coded bars (green = positive, red/pink = negative). Hovering shows the exact correlation value.

**Strong Correlations (|r| > 0.5)** are listed separately, since these are the relationships most likely to be meaningful. A high correlation between two input features suggests potential redundancy; a high correlation between a feature and the target column suggests predictive value.

---

## Notebooks

Notebooks are nondestructive workspaces attached to a dataset. They allow you to apply sequences of **Explorers** (visualizations) and **Converters** (transformations) to a working copy of the data, preview the effect of each operation live, and save the result as a new dataset.

The original dataset is never modified. All changes are isolated to the notebook's working copy until you explicitly save.

### Explorer Tools (EXPLORE tab)

Explorers generate visualizations and statistical summaries from the current state of the data. They do not modify the data. Available explorers are organized into five categories:

| Category                      | What it contains                                                                |
| ----------------------------- | ------------------------------------------------------------------------------- |
| **Preview Inspection**        | Describe Dataset (statistical summary table), Show Rows (paginated record view) |
| **Relationship Analysis**     | Density Heatmap, Multiple Scatter Plot, Scatter Plot                            |
| **Statistical Analysis**      | Correlation Matrix, Covariance Matrix                                           |
| **Distribution Analysis**     | Box Plot, Empirical Cumulative Distribution, Histogram Plot, Word Cloud         |
| **Multidimensional Analysis** | Multiple Column Chart, Parallel Categories, Parallel Coordinates                |

Each explorer has a two step configuration: first select which columns to include (scope), then set the explorer's parameters. Results render inline in the notebook timeline below the data preview.

### Converter Tools (CONVERT tab)

Converters modify the data. Each is applied to a configurable set of columns and rows, and the dataset preview updates immediately after each converter runs. Available converters are organized into eight categories:

**Basic Preprocessing**

| Converter            | What it does                                                         |
| -------------------- | -------------------------------------------------------------------- |
| `NaN Remover`        | Removes rows that contain at least one missing value                 |
| `Simple Imputer`     | Fills missing values with mean, median, most frequent, or a constant |
| `KNN Imputer`        | Fills missing values using k nearest neighbors                       |
| `Missing Indicator`  | Adds binary columns marking which values were missing                |
| `Column Remover`     | Removes selected columns entirely from the dataset                   |
| `Character Replacer` | Replaces specific characters or strings in text columns              |

**Encoding**

| Converter         | What it does                                                |
| ----------------- | ----------------------------------------------------------- |
| `Binarizer`       | Maps numeric values to 0 or 1 based on a threshold          |
| `Label Binarizer` | Binarizes labels in a one-vs-all scheme                     |
| `Label Encoder`   | Encodes categorical labels as integers (for target columns) |
| `One-Hot Encoder` | Creates a binary column for each category value             |
| `Ordinal Encoder` | Encodes categories as ordered integers                      |

**Scaling and Normalization**

| Converter        | What it does                                                       |
| ---------------- | ------------------------------------------------------------------ |
| `Max Abs Scaler` | Scales each feature by its maximum absolute value (range: -1 to 1) |
| `Min-Max Scaler` | Scales features to a specified range (default: 0 to 1)             |
| `Normalizer`     | Scales each row (record) to unit norm                              |

**Dimensionality Reduction**

| Converter                      | What it does                                                   |
| ------------------------------ | -------------------------------------------------------------- |
| `Principal Component Analysis` | Reduces to n components explaining maximum variance            |
| `Incremental PCA`              | PCA for large datasets processed in memory efficient batches   |
| `Truncated SVD`                | SVD based reduction, works with sparse matrices                |
| `Fast ICA`                     | Independent Component Analysis                                 |
| `Nystroem Approximation`       | Approximates a kernel feature map for nonlinear representation |
| `Variance Threshold`           | Removes features with variance below a threshold               |

**Feature Selection**

| Converter                   | What it does                                                          |
| --------------------------- | --------------------------------------------------------------------- |
| `Select K Best`             | Keeps the K features with the highest statistical scores              |
| `Select Percentile`         | Keeps the top X% of features by score                                 |
| `Select FDR`                | Selects features controlling the false discovery rate                 |
| `Select FPR`                | Selects features by p-value significance threshold                    |
| `Select FWE`                | Selects features with strict family wise error correction             |
| `Generic Univariate Filter` | Configurable univariate selector combining scoring and selection mode |

**Polynomial & Kernel Methods**

| Converter               | What it does                                                         |
| ----------------------- | -------------------------------------------------------------------- |
| `Polynomial Features`   | Generates polynomial and interaction terms from input features       |
| `RBF Sampler`           | Approximates an RBF kernel feature map using random Fourier features |
| `Additive Chi² Sampler` | Approximates the additive chi-squared kernel for nonnegative data    |
| `Skewed Chi² Sampler`   | Variant of chi-squared kernel approximation with a shift parameter   |

**Resampling & Class Balancing**

| Converter              | What it does                                                   |
| ---------------------- | -------------------------------------------------------------- |
| `SMOTE`                | Generates synthetic minority class records by interpolation    |
| `SMOTE-ENN`            | SMOTE followed by Edited Nearest Neighbors cleaning            |
| `Random Under-Sampler` | Randomly removes majority class records to balance the dataset |

**Advanced Preprocessing**

| Converter      | What it does                                                        |
| -------------- | ------------------------------------------------------------------- |
| `TF-IDF`       | Converts text to TF-IDF feature vectors (weighted word frequencies) |
| `Bag of Words` | Converts text to raw word count vectors                             |
| `Tokenizer`    | Converts text into sequences of integer token indices               |
| `Embedding`    | Maps token sequences to dense semantic vector representations       |

### Saving a Transformed Dataset

When the notebook contains the transformations you want, click **SAVE AS NEW DATASET**. This creates a new independent dataset in dashAI with the data in its current state. The new dataset is immediately available for experiments without affecting the source dataset.

---

## Tips

- Use the **Quality Score** as a first pass health check before doing any analysis. A score below 100% always has a specific cause visible in the Data Quality tab.
- The **Intelligent Alerts** in Numerical Analysis are prioritized suggestions. Address them with the corresponding Notebook converter before training to improve model performance.
- Build Notebook transformation pipelines incrementally: add one converter at a time and verify the preview before adding the next.
- Resampling converters (SMOTE, RandomUnderSampler) should be applied only to the training split, not the full dataset. Keep this in mind when saving a transformed dataset for use in experiments.
- For text data, apply **TF-IDF** or **Bag of Words** when working with traditional ML models (Logistic Regression, SVM, Random Forest). Neural models that accept raw text (like DistilBERT) do not require these preprocessing steps.
