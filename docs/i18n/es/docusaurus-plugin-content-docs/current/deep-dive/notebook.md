---
title: Notebook
sidebar_label: Notebook
---

Un **Notebook** es una sesión de trabajo que permite a los usuarios interactuar con un dataset sin modificar los datos originales.

## ¿Qué es un Notebook?

Cuando se crea un Notebook a partir de un dataset, dashAI realiza una **copia mutable** del dataset original. El registro `Dataset` fuente nunca se modifica. Dentro de un Notebook, los usuarios pueden:

- Ejecutar **Exploradores** (gráficos de dispersión, histogramas, diagramas de caja) para visualizar los datos.
- Aplicar **Converters** (StandardScaler, PCA, SMOTE, etc.) para transformar la copia del dataset.
- **Revertir** cualquier converter para restaurar un estado anterior.
- **Guardar** el dataset modificado como un nuevo registro `Dataset` disponible para el entrenamiento de modelos.

## Representación en la Base de Datos

Un Notebook se almacena en la tabla `Notebook`, vinculado al `Dataset` fuente. Cada Explorador o Converter aplicado dentro del Notebook crea un registro `Explorer` o `Converter`. Los converters se aplican secuencialmente mediante un `ConverterJob`.

## Ciclo de Vida

```
Dataset Original ──(copia)──► Dataset del Notebook
                                      │
                         Aplicar Exploradores   (visualizaciones de solo lectura)
                         Aplicar Converters    (en el lugar sobre la copia mutable)
                         Revertir Converters   (restaurar estado anterior)
                                      │
                              Guardar ──► Nuevo Dataset (disponible para entrenamiento)
```
