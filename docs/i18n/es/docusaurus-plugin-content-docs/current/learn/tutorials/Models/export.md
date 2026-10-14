---
title: Exportar un modelo
sidebar_label: Exportar un modelo
---

# Exportar un modelo

Un modelo entrenado puede salir de dashAI como un único archivo
`.dashai-model` y usarse desde tu propio código Python, sin abrir la app ni
levantar su servidor.

## Exportar

Abre una sesión, haz clic en un modelo terminado para abrir su vista de
detalle y presiona el botón **Exportar modelo** (ícono de descarga), junto a
**Re-entrenar**. El archivo contiene el modelo entrenado, el preprocesamiento
ajustado de su sesión y los tipos de las columnas de entrenamiento. El
dataset no se incluye como tal, pero algunos modelos guardan filas de
entrenamiento dentro de sí para predecir (por ejemplo, KNN las guarda todas).
No compartas el archivo si los datos de entrenamiento son privados.

## Usarlo desde Python

Instala dashAI en el entorno donde quieres predecir:

```bash
pip install dashai
```

Luego:

```python
from DashAI import load_model
import pandas as pd

model = load_model("my_model.dashai-model")
print(model.info)  # modelo, tarea, columnas, versiones y métricas de test

new_rows = pd.read_csv("new_data.csv")
predictions = model.predict(new_rows)
```

`predict` recibe un DataFrame de pandas o una lista de diccionarios con las
columnas **originales** del dataset. El preprocesamiento se aplica solo, y la
columna objetivo se ignora si viene incluida.

## Servirlo

dashAI todavía no incluye un servidor para modelos exportados. Uno mínimo con
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

## Compatibilidad

- Si las librerías instaladas son distintas a las usadas al entrenar, dashAI
  muestra una advertencia e intenta cargar el modelo de todas formas.
- Si el modelo necesita un plugin que no está instalado, la carga falla y el
  error indica cuál instalar.

:::warning
Un archivo de modelo contiene objetos de Python y cargarlo ejecuta código.
Carga solo archivos de personas en las que confíes.
:::

Los modelos de clasificación y regresión tabular están probados. Los demás
tipos de modelo (imágenes, texto, series de tiempo) se pueden exportar, pero
son experimentales.
