---
title: Notebook
sidebar_label: Notebook
---

A **Notebook** is a working session that lets users interact with a dataset without
modifying the original data.

## What is a Notebook?

When a Notebook is created from a dataset, dashAI makes a **mutable copy** of the
original dataset. The source `Dataset` record is never modified. Within a Notebook,
users can:

- Run **Explorers** (scatter plots, histograms, box plots) to visualize the data.
- Apply **Converters** (StandardScaler, PCA, SMOTE, etc.) to transform the dataset copy.
- **Revert** any converter to restore an earlier state.
- **Save** the modified dataset as a new `Dataset` record available for model training.

## Database Representation

A Notebook is stored in the `Notebook` table, linked to the source `Dataset`. Each
Explorer or Converter applied within the Notebook creates an `Explorer` or `Converter`
record. Converters are applied sequentially via a `ConverterJob`.

## Lifecycle

```
Original Dataset ──(copy)──► Notebook Dataset
                                    │
                       Apply Explorers   (read-only visualizations)
                       Apply Converters  (in-place on mutable copy)
                       Revert Converters (restore earlier state)
                                    │
                            Save ──► New Dataset (available for training)
```
