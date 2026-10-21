---
title: Share a session
sidebar_label: Share a session
---

# Share a session

A whole model session can leave dashAI as a single `.dashai` file and be
imported in another dashAI, or in the same one. Use it to hand out a session
to a class, pass your work to a teammate, move sessions to another computer,
or let someone retrain your experiment and compare.

## Export

In the left panel, open the menu (**...**) of a session and choose
**Export**. The dialog lets you:

- **Choose the runs** to include. All of them are selected; runs still
  training cannot be exported until they finish.
- **Include trained models**, checked by default. Uncheck it to export only
  the configuration, without trained models: the dataset and the settings of
  the session and its runs. The file is smaller, and whoever imports it trains
  the models again.

Finished runs travel with their model and metrics. Runs that failed or were
never trained travel without a model and arrive untrained.

## Import

Next to the **Sessions** title in the left panel, click the import button,
read the warning and choose the `.dashai` file. dashAI creates a new session
with its own copy of the dataset and opens it. From there you can predict,
retrain and add models as in any other session.

Importing never changes what you already have. If a session or dataset with
the same name exists, the new one gets a number, such as `iris (2)`.

## What the file contains

- The dataset, including its train, validation and test split.
- The session configuration: task, columns, preprocessing and evaluation
  settings.
- Each chosen run's configuration and, when included, its trained model,
  metrics and the fitted preprocessing.

Explanations, predictions and reports are not included yet; generate them
again after importing.

## Compatibility

- A file from a newer dashAI is refused: update dashAI to open it.
- If the session uses a plugin you do not have, the import is refused and the
  message says which one to install.
- If your library versions differ from the ones used to export, the session
  is imported with a warning. If a model then fails, use **Retrain**: the
  configuration is always in the file.
- If a model must be downloaded (for example a HuggingFace translator) and
  you do not have it, dashAI tells you after importing. A trained run still
  predicts from its own copy, and you only need the download to retrain it. A
  run that arrives untrained needs it before training, and the notice offers a
  **Download** button.

:::warning
A session file contains Python objects, and using its models runs code.
Import only sessions from people you trust.
:::

:::note
The file always includes the dataset, and some models (for example KNN) also
keep training rows inside them. Do not share a session trained on private
data.
:::
