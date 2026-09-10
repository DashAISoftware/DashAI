---
title: Upload a Dataset
sidebar_label: Upload a Dataset
---

# Upload a Dataset

This tutorial walks you through uploading a dataset to dashAI.
Uploading a dataset is always the first step. Once loaded, it becomes available
across the platform for exploration, preprocessing, and model training.

## Supported Formats

| Format | Dataloader        | Extension       |
| ------ | ----------------- | --------------- |
| CSV    | `CSVDataLoader`   | `.csv`          |
| Excel  | `ExcelDataLoader` | `.xlsx`, `.xls` |
| JSON   | `JSONDataLoader`  | `.json`         |

---

## Step by Step Guide

### 1. Open the Datasets Section

In the top navigation bar, click on **DATASETS**.
In the main area, click the **"Upload Dataset"** option at the center of the screen.

This opens the upload flow inline, so you stay on the same screen throughout the entire process.

### 2. Select a Dataloader

A panel appears listing the available dataloaders, each with a brief description
of the file format it handles.

Click the dataloader that matches your file (e.g., **CSVDataLoader**) and click **"Next"**.

:::tip What is a Dataloader?
A Dataloader is the component that knows how to read a specific file format.
Selecting the right one ensures dashAI can parse your file correctly and expose
the appropriate configuration parameters for that format.
:::

### 3. Upload Your File

Once a dataloader is selected, the file upload button becomes available.
Click **"Upload a File"** and select your dataset file from your computer.

After the file is processed, dashAI displays a **Dataset Preview** in the center of the screen.

---

### 4. Review the Dataset Preview

The preview table shows the first 5 rows of a **100 row sample** taken from your file.
This sample is used by dashAI to automatically infer the data type of each column.

```
Showing 100 of 1000 rows analyzed for type inference.
You can change column types by clicking on the dropdown in each column header.
```

**Editing column types**

Each column header has a dropdown showing the inferred type. Click it to change it manually:

| Type          | When to use                                                                                          |
| ------------- | ---------------------------------------------------------------------------------------------------- |
| `Categorical` | Discrete values representing groups or labels (e.g., gender, education level, home ownership status) |
| `Float`       | Continuous numbers with decimals (e.g., income, price, ratio)                                        |
| `Integer`     | Whole numbers without decimals (e.g., age, count, years of experience)                               |
| `Text`        | Free form natural language content (e.g., comments, descriptions, reviews)                           |

Reviewing and correcting column types at this stage ensures the platform interprets
your data correctly in every subsequent step.

:::note Reuploading
If you need to swap the file after seeing the preview, click the **"RE-UPLOAD DATASET"**
button above the preview table. This takes you back to the file selection step
without losing your current parameter configuration.
:::

---

### 5. Configure the Parameters

The right panel is divided into two sections: **Type Inference Configuration**
and **Dataloader Configuration**. Both affect how the dataset is read and stored.

#### Type Inference Configuration

This section appears for all dataloaders.

| Parameter          | Type    | Description                                                                                                                                                                                                                                           |
| ------------------ | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Inference Rows** | Integer | The number of rows dashAI reads to automatically determine each column's data type. Default is `1000`. Increasing this value improves inference accuracy on datasets with inconsistent or mixed values, at the cost of a slightly longer upload time. |

#### Dataloader Configuration

The parameters in this section depend on the dataloader you selected.

---

**CSVDataLoader**

| Parameter     | Type          | Description                                                                                                                                                                                                    |
| ------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Name**      | String        | The name that will identify this dataset inside dashAI. Prefilled from your filename, and you can change it here.                                                                                              |
| **Separator** | Dropdown      | The character that separates column values in your CSV. Default is `,` (comma). Switch to `;` (semicolon) for files exported from Excel in Spanish or European locales, where comma is the decimal separator.  |
| **Header**    | String        | How dashAI identifies the row containing column names. Default `infer` detects it automatically (usually the first row). Set a row number explicitly if your file has metadata lines before the actual header. |
| **Names**     | String / Null | Optional list of column names to assign manually, overriding the names found in the file. Leave as `Null` to use the file's own column names.                                                                  |
| **Encoding**  | Dropdown      | Character encoding of your file. Default is `utf-8`. Change to `latin-1` or `ISO-8859-1` if special characters (accents, symbols) appear garbled after upload.                                                 |
| **NA values** | String / Null | Additional strings to treat as missing values. For example, `"?"` or `"N/A"`. Leave as `Null` to rely on default behavior.                                                                                     |

---

**JSONDataLoader**

| Parameter    | Type   | Description                                                                                                                                                                                                          |
| ------------ | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Name**     | String | The name that will identify this dataset inside dashAI. Prefilled from your filename, and you can change it here.                                                                                                    |
| **Data key** | String | The key inside your JSON file that contains the actual data records. Default is `data`. Change this to match the key in your file where the rows or records are located (e.g., `"results"`, `"records"`, `"items"`). |

:::note JSON structure
dashAI expects your JSON file to contain a top level object with a key pointing to
an array of records. For example: `{ "data": [ {...}, {...} ] }`.
If your data is stored under a different key, set **Data key** accordingly.
:::

---

**ExcelDataLoader**

| Parameter           | Type           | Description                                                                                                                                                                                                    |
| ------------------- | -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Name**            | String         | The name that will identify this dataset inside dashAI. Prefilled from your filename, and you can change it here.                                                                                              |
| **Sheet**           | Integer        | The index of the sheet to load, starting at `0`. Default is `0` (the first sheet). Change this if your data is on a different sheet.                                                                           |
| **Header**          | Integer / Null | The row number (zero indexed) that contains the column names. Default is `0` (first row). Set to `Null` if your file has no header row.                                                                        |
| **Use columns**     | String / Null  | Specifies which columns to load. Leave as `Null` to load all columns. You can enter a comma separated list of column names or indices to load only specific columns.                                           |
| **Skip rows**       | Integer / Null | Number of rows to skip at the start of the sheet before reading. Useful if your Excel file has title rows, report headers, or blank lines before the data. Leave as `Null` to skip nothing.                    |
| **N rows**          | Integer / Null | Maximum number of rows to load. Leave as `Null` to load the entire sheet. Useful for testing with a large file.                                                                                                |
| **Names**           | String / Null  | Optional list of column names to assign manually. Leave as `Null` to use the column names found in the file.                                                                                                   |
| **NA values**       | String / Null  | Additional strings to treat as missing values. Leave as `Null` to use default behavior.                                                                                                                        |
| **Keep default NA** | Checkbox       | When enabled (default), dashAI recognizes a built in list of common NA strings (`"NA"`, `"NaN"`, `"null"`, empty strings, etc.) as missing values automatically. Disable only if you need full manual control. |
| **True values**     | String / Null  | Strings to interpret as boolean `True` (e.g., `"yes"`, `"Y"`, `"1"`). Leave as `Null` if your data has no boolean columns encoded as text.                                                                     |
| **False values**    | String / Null  | Strings to interpret as boolean `False` (e.g., `"no"`, `"N"`, `"0"`). Leave as `Null` if not applicable.                                                                                                       |

:::note Keep default NA + NA values
These two parameters work together. When **Keep default NA** is enabled and you also
define custom **NA values**, both sets are combined, and your custom strings are added
on top of the defaults. Disabling **Keep default NA** means only your explicitly
defined strings will be treated as missing.
:::

---

### 6. Upload the Dataset

Once you have reviewed the column types and configured the parameters, click **"UPLOAD"**
to finalize the process.

dashAI will process the file and add it to the **Available Datasets** list in the left
sidebar, showing the total number of rows and columns.

Click **"BACK"** at any point to return to the previous step without losing your configuration.

---

## Tips

- After uploading, use the **Explorations** module to visually verify that columns
  loaded correctly before running any experiment.
- If a numeric column appears as `Categorical`, it likely contains nonnumeric characters
  (spaces, symbols, or mixed values), so check the source file and reupload after cleaning.
- Use the **N rows** parameter (available in some dataloaders) to load only a portion
  of a large file while testing your configuration.
- The **Separator** parameter is the most common source of single column load errors
  in CSV files. If your dataset appears as one long column, this is the first thing to check.

## Troubleshooting

| Symptom                                   | Likely cause                          | Solution                                                   |
| ----------------------------------------- | ------------------------------------- | ---------------------------------------------------------- |
| Dataset loads as a single column          | Wrong separator selected (CSV)        | Click **RE-UPLOAD DATASET** and set the correct separator  |
| A numeric column shows as `Categorical`   | Column contains nonnumeric characters | Fix the source file and reupload                           |
| Special characters appear garbled         | Wrong encoding (CSV)                  | Change **Encoding** to `latin-1` or `ISO-8859-1`           |
| Column names are wrong or missing         | Header row not at expected position   | Adjust the **Header** parameter to the correct row index   |
| Wrong sheet loaded (Excel)                | Default sheet index is `0`            | Change the **Sheet** parameter to the correct index        |
| Extra rows at the top of the data (Excel) | File has title/metadata rows          | Use **Skip rows** to skip them                             |
| NA values not recognized as missing       | Custom NA strings not defined         | Add your NA strings in the **NA values** field             |
| JSON loads with wrong columns             | Data is under a different key         | Set **Data key** to the correct key in your JSON structure |
