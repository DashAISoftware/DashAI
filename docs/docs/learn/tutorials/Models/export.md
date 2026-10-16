---
title: Export a model
sidebar_label: Export a model
---

# Export a model

A trained model can leave dashAI as a single `.dashai-model` file and be used
from your own Python code, without opening the app or running its server.

## Model file or session file

| | `.dashai-model` | `.dashai` |
|---|---|---|
| Holds | One trained run | A whole session, its dataset and chosen runs |
| Opened with | Python, `load_model` | The dashAI app |
| Predict | Yes | Yes |
| Retrain or add models | No | Yes |

To share a whole session, see [Share a session](share-session.md).

## Export

Open a session, click a finished model to open its detail view, and click the
**Export model** button (download icon) next to **Retrain**. The file contains
the trained model, the preprocessing fitted for its session, and the types of
the training columns. The dataset itself is not included, but some models keep
training rows inside them to predict (for example KNN stores all of them). Do
not share the file if the training data is private.

## Use it from Python

Install dashAI in the environment where you want to predict:

```bash
pip install dashai
```

Then:

```python
from DashAI import load_model
import pandas as pd

model = load_model("my_model.dashai-model")
print(model.info)  # model, task, columns, versions and test metrics

new_rows = pd.read_csv("new_data.csv")
predictions = model.predict(new_rows)
```

`predict` takes a pandas DataFrame or a list of dicts with the **original**
columns of the dataset. Preprocessing is applied for you, and the target
column is ignored if it is present.

## Serving it

dashAI does not include a server for exported models yet. A minimal one with
FastAPI:

```python
from fastapi import FastAPI
from DashAI import load_model

app = FastAPI()
model = load_model("my_model.dashai-model")


@app.post("/predict")
def predict(rows: list[dict]):
    return {"predictions": model.predict(rows)}
```

## Compatibility

- If the libraries installed differ from the ones the model was trained with,
  dashAI shows a warning and still tries to load it.
- If the model needs a plugin that is not installed, loading fails and the
  error says which one to install.

:::warning
A model file contains Python objects, and loading it runs code. Only load
files from people you trust.
:::

Tabular classification and regression models are tested. Other model types
(images, text, time series) can be exported but are experimental.
