---
title: "Module Guide: Models"
sidebar_label: Models
sidebar_position: 2
---

# Module Guide: Models

The Models module manages the complete ML experimentation cycle: defining tasks, training models, optimizing hyperparameters, evaluating results, generating predictions, and interpreting model behavior through explainability tools. Everything is organized around **Sessions**, self contained experiments that group models, metrics, predictions, and explainability results in one place.

---

## Core Concepts

### Tasks

A task defines the type of machine learning problem. It determines which models are available, which column types are valid as inputs and outputs, and which evaluation metrics are computed.

| Task                       | Input types                 | Output type                 | Use case                                |
| -------------------------- | --------------------------- | --------------------------- | --------------------------------------- |
| **Tabular Classification** | Float, Integer, Categorical | Categorical (1 column)      | Predict a category from structured data |
| **Text Classification**    | Text                        | Categorical                 | Classify documents, reviews, messages   |
| **Regression**             | Float, Integer, Categorical | Float or Integer (1 column) | Predict a continuous value              |
| **Translation**            | Text                        | Text                        | Convert text between languages          |

### Sessions

A session ties together a dataset, a task configuration (input/output columns, data split), and all the models trained within that context. Sessions are persistent, so closing dashAI and reopening it returns you to the same state.

The left sidebar organizes sessions by task type. Each session entry shows its name and the dataset it was created from. You can maintain multiple sessions for the same dataset and task to explore different column configurations or split strategies.

### Data Splits

dashAI supports three split strategies:

| Strategy                  | When to use                                                              |
| ------------------------- | ------------------------------------------------------------------------ |
| **Predefined**            | Dataset already contains train/test/validation structure from the source |
| **Random by proportion**  | Standard split using configurable ratios (default: 60/20/20)             |
| **Manual by row indices** | Full control over which rows go into each subset                         |

For random splits, three additional options refine the behavior:

- **Shuffle**: randomizes row order before splitting. Enabled by default. Disable only when row order is meaningful (e.g., time series).
- **Stratify**: preserves the class distribution of the output column in each split. Critical for imbalanced datasets where minority classes could be underrepresented in smaller splits.
- **Seed**: fixed random seed for reproducibility. Default is 42. Set a specific value when you need to compare models trained on identical splits.

---

## Available Models

### Tabular Classification (Scikit-learn)

| Model                            | Notes                                                                                                    |
| -------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `SVC`                            | Support Vector Classifier. Effective in high dimensional spaces. Kernel options: linear, rbf, polynomial |
| `LogisticRegression`             | Linear model for binary and multiclass classification. Fast and interpretable                            |
| `RandomForestClassifier`         | Ensemble of decision trees. Robust to overfitting, handles mixed feature types                           |
| `DecisionTreeClassifier`         | Single tree model. Fully interpretable, prone to overfitting without depth limits                        |
| `KNeighborsClassifier`           | Instance based learning using distance to k nearest neighbors                                            |
| `HistGradientBoostingClassifier` | Histogram based gradient boosting. Handles large datasets efficiently, supports native NA values         |
| `DummyClassifier`                | Baseline model using simple rules (most frequent, stratified, etc.). Use as a performance floor          |

### Regression (Scikit-learn)

| Model                       | Notes                                                               |
| --------------------------- | ------------------------------------------------------------------- |
| `LinearRegression`          | Ordinary least squares. Simple, fast, interpretable                 |
| `LinearSVR`                 | Support Vector Regression with a linear kernel                      |
| `RidgeRegression`           | Linear regression with L2 regularization. Handles multicollinearity |
| `RandomForestRegressor`     | Ensemble regression. Handles nonlinear relationships                |
| `GradientBoostingRegressor` | Sequential ensemble. High accuracy, slower to train                 |
| `MLPRegressor`              | Multilayer perceptron. Flexible nonlinear model                     |

### Text Classification (Hugging Face)

| Model                               | Notes                                                                                                   |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `DistilBertTransformer`             | Distilled BERT, a fast and accurate transformer for text classification. Requires GPU for practical use |
| `BagOfWordsTextClassificationModel` | Traditional sparse vector approach with a linear classifier. Fast, interpretable, CPU friendly          |

### Translation (Hugging Face)

| Model                   | Notes                                                                |
| ----------------------- | -------------------------------------------------------------------- |
| `OpusMtEnESTransformer` | English to Spanish translation using the Helsinki-NLP Opus-MT models |

---

## Hyperparameter Configuration

Each model exposes its configurable hyperparameters in the **Add Model** modal. Parameters vary by algorithm, and every parameter has a **?** help icon with a description.

### Manual Configuration

Set a fixed value for each parameter. This is the default mode, suitable when you have prior knowledge about good values or want to test specific configurations.

### Hyperparameter Optimization

Each numeric parameter has an **Optimize** toggle. Enabling it tells dashAI to automatically search for the best value for that parameter instead of using the fixed value. You can enable optimization on any subset of parameters simultaneously.

Two optimizers are available:

| Optimizer             | Strategy                                                                                                                      |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **OptunaOptimizer**   | Bayesian optimization using Optuna's TPE sampler. Efficient, as it focuses trials on promising regions of the parameter space |
| **HyperOptOptimizer** | Tree structured Parzen Estimator (TPE) via HyperOpt. Similar strategy to Optuna                                               |

During optimization, dashAI records per trial metrics and generates visualization plots:

- **History plot**: metric value across all trials
- **Parallel coordinates**: relationship between parameter combinations and metric values
- **Slice plot**: effect of individual parameters on the metric
- **Importance plot**: which parameters have the most influence on the result

---

## Training and Status

Each model in a session has a status that reflects its current state:

| Status          | Meaning                                    |
| --------------- | ------------------------------------------ |
| **Not Started** | Model has been added but never trained     |
| **Finalizado**  | Training completed successfully            |
| **Error**       | Training failed; review parameters or data |

Action buttons per model:

- **TRAIN / RE-TRAIN**: start or restart training. Retraining overwrites the previous run's results.
- **EDIT**: modify the model name or hyperparameters before retraining.
- **RUN ALL**: queues all untrained models in the session for sequential execution.

Training runs as a background job tracked in the **Job Queue** (bottom right of the screen). You can monitor progress and see error details there.

---

## Evaluation Metrics

Metrics are shown in the **LIVE METRICS** tab of each model card, split across three subtabs: Training, Validation, and Test.

### Classification Metrics

| Metric              | What it measures                                                                     |
| ------------------- | ------------------------------------------------------------------------------------ |
| **Accuracy**        | Proportion of correct predictions overall                                            |
| **F1**              | Harmonic mean of Precision and Recall. Better than Accuracy for imbalanced classes   |
| **Precision**       | Of all predicted positives, how many were actually positive                          |
| **Recall**          | Of all actual positives, how many were correctly predicted                           |
| **ROCAUC**          | Area under the ROC curve. Measures separability across all classification thresholds |
| **LogLoss**         | Penalizes confident wrong predictions. Lower is better                               |
| **HammingDistance** | Fraction of labels that are incorrectly predicted                                    |
| **CohenKappa**      | Agreement between predictions and true labels, correcting for chance                 |

### Regression Metrics

| Metric   | What it measures                                              |
| -------- | ------------------------------------------------------------- |
| **RMSE** | Root Mean Squared Error, penalizes large errors more than MAE |
| **MAE**  | Mean Absolute Error, the average magnitude of errors          |

### Translation Metrics

| Metric   | What it measures                                            |
| -------- | ----------------------------------------------------------- |
| **BLEU** | N-gram overlap between generated and reference translations |
| **TER**  | Translation Edit Rate, edits needed to match reference      |

---

## Model Comparison

The **Model Comparison** panel at the top of every session provides a unified view of all models and their performance.

### Table View

All models in the session appear as rows with their metric values side by side. Switch between **TRAINING**, **VALIDATION**, and **TEST** splits using the buttons at the top. Models that haven't been trained show `-` in metric columns.

Always evaluate final model selection on the **TEST** split, because training and validation metrics may not reflect true generalization performance.

### Charts View

Two chart types support visual comparison:

**Bar chart**: groups metrics on the x-axis with one bar per model per metric. Best for comparing models on a single metric at a glance.

**Radar chart**: each axis is a metric; each model is a polygon. A larger, more regular polygon indicates consistently strong performance across all metrics. Irregular polygons reveal trade offs. A model strong on Accuracy but weak on Recall, for example, creates a visibly uneven shape.

The **Metrics** panel lets you select which metrics appear in the chart. Use **ALL** / **NONE** to toggle quickly.

---

## Predictions

After training, each model can generate predictions in two modes, accessed from the **PREDICTIONS** tab of the model card.

### Dataset Predictions

Run the model against an entire dataset loaded in dashAI. Useful for batch scoring, such as applying the model to a validation set, a holdout set, or new incoming data.

The modal shows a preview of the selected dataset with its input columns and target column highlighted, so you can verify compatibility before submitting. Results are available as an inline preview (first 100 rows) and as a full CSV download.

### Manual Predictions

Enter one or more rows of data directly, with no file needed. Categorical columns appear as dropdowns with valid values; numerical columns are free text. Multiple rows can be added with **Add Row**.

This mode is particularly useful for:

- Demonstrating model behavior on specific examples
- Testing edge cases and boundary conditions
- Classroom or presentation contexts where you want to show how individual inputs affect predictions

---

## Explainability

The **EXPLAINABILITY** tab of each trained model provides tools for understanding model decisions. Two types are available.

### Global Explainers

Analyze model behavior across the entire dataset: which features matter most overall, and how they relate to model output.

| Explainer                          | What it produces                                                                             |
| ---------------------------------- | -------------------------------------------------------------------------------------------- |
| **Kernel SHAP**                    | SHAP values for each feature, quantifying its contribution to predictions across the dataset |
| **Permutation Feature Importance** | Ranks features by how much model performance drops when each feature is randomly shuffled    |
| **Partial Dependence**             | Shows the marginal effect of one or two features on the predicted outcome                    |

### Local Explainers

Analyze model behavior for a specific prediction: why did the model produce this output for this particular input.

Local explainers help identify unexpected behavior on specific instances, which is valuable both for debugging models and for explaining individual decisions to stakeholders.

---

## Tips

- Always include a **DummyClassifier** (or equivalent baseline) in every session. Any model that doesn't outperform the dummy needs further tuning.
- Enable **Stratify** whenever your target column has class imbalance, because it prevents splits where the minority class is absent or underrepresented in validation or test.
- Use a fixed **Seed** across sessions when comparing approaches, since identical splits eliminate data variability as a confounding factor.
- The **TEST** split metrics are the authoritative measure of generalization. Good training metrics with poor test metrics indicate overfitting.
- Run **Permutation Feature Importance** before finalizing a model. It often reveals that some input columns add noise rather than signal and can be removed to simplify the model.
- When using **DistilBertTransformer** for text classification, ensure your raw text columns are passed directly. Do not apply TF-IDF or BagOfWords converters beforehand, as the transformer handles its own tokenization.
