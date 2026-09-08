---
title: Explicabilidad
sidebar_label: Explicabilidad
---

# Explicabilidad

La pestaña de Explicabilidad te permite adjuntar explicadores a un modelo entrenado para entender cómo toma sus decisiones. dashAI admite dos tipos de explicadores: **Explicadores Globales** y **Explicadores Locales**.

---

## Acceder a la Explicabilidad

1. Abre una sesión desde la barra lateral izquierda.
2. Expande una tarjeta de modelo que tenga estado **Finalizado**.
3. Haz clic en la pestaña **EXPLAINABILITY**.

La pestaña está dividida en dos paneles lado a lado:

| Panel                 | Descripción                                                                                                                                     |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Global Explainers** | Analiza el comportamiento del modelo en todo el dataset: qué características importan más en general.                                           |
| **Local Explainers**  | Analiza el comportamiento del modelo en predicciones individuales: por qué el modelo produjo una salida específica para una entrada específica. |

Cada panel muestra una insignia de conteo de los explicadores ya creados, y un botón para añadir uno nuevo.

---

## Explicadores Globales

Los explicadores globales responden la pregunta: _"¿En qué se basa el modelo en general?"_

Producen resultados como rankings de importancia de características o gráficos de resumen SHAP que describen los patrones generales de toma de decisiones del modelo a través de los datos de entrenamiento o prueba.

### Añadir un Explicador Global

Haz clic en **+ NEW GLOBAL EXPLAINER** para abrir el flujo de configuración del explicador.

El flujo sigue el mismo patrón de dos pasos usado en toda dashAI:

**Paso 1: Configurar Alcance**

Selecciona qué columnas analizará el explicador. La tabla de selección de columnas muestra el índice, nombre, tipo de valor y tipo de dato de cada columna. Selecciona las columnas que deseas incluir en la explicación.

Algunos explicadores requieren un número mínimo de columnas. El contador en la parte superior de la tabla muestra cuántas están seleccionadas y el mínimo requerido.

**Paso 2: Configurar Parámetros**

Cada explicador tiene sus propios parámetros. Estos varían según el algoritmo. Las opciones comunes incluyen el número de muestras a usar, configuraciones del dataset de fondo y preferencias de formato de salida. Cada parámetro tiene un icono de ayuda **?** con una descripción.

Haz clic en **CREATE EXPLAINER** para ejecutarlo y añadir el resultado a la pestaña.

---

## Explicadores Locales

Los explicadores locales responden la pregunta: _"¿Por qué el modelo predijo esta salida específica para esta instancia específica?"_

Producen explicaciones a nivel de instancia. Por ejemplo, muestran qué características empujaron la predicción hacia una clase particular para una fila de datos específica.

### Añadir un Explicador Local

Haz clic en **+ NEW LOCAL EXPLAINER** para abrir el flujo de configuración del explicador.

La configuración sigue el mismo patrón de dos pasos que los explicadores globales, con selección de alcance (columnas) y configuración de parámetros.

Algunos explicadores locales adicionalmente requieren que selecciones una predicción o fila específica para explicar. Esto varía según el tipo de explicador.

---

## Resultados del Explicador

Una vez creado, cada explicador aparece como una tarjeta de resultado en su panel con:

- El nombre y tipo del explicador.
- Una insignia **Finalizado** cuando está completo.
- La salida de la explicación renderizada en línea (gráfico, tabla o visualización según el tipo de explicador).
- Un botón **Edit** para modificar el alcance o los parámetros y volver a ejecutar.
- Un botón **Delete** para eliminar el explicador.

---

## Consejos

- Ejecuta un **Explicador Global** primero para obtener una visión general de la importancia de las características. Esto ayuda a identificar qué columnas de entrada son más relevantes y cuáles pueden ser redundantes.
- Usa **Explicadores Locales** cuando una predicción específica parezca inesperada. Ayudan a rastrear qué características impulsaron un resultado inusual.
- Las herramientas de explicabilidad están disponibles por modelo, por lo que puedes ejecutar el mismo explicador en múltiples modelos de la misma sesión para comparar cómo diferentes algoritmos usan las mismas características.
- La insignia de la pestaña **EXPLAINABILITY** muestra un conteo de los explicadores creados, facilitando el seguimiento de qué modelos han sido analizados.

## Solución de Problemas

| Síntoma                                            | Causa probable                                                  | Solución                                                                    |
| -------------------------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------- |
| La pestaña EXPLAINABILITY está inactiva            | El modelo no ha sido entrenado                                  | Entrena el modelo primero antes de añadir explicadores                      |
| La creación del explicador falla                   | Tipos de columnas incompatibles para el explicador seleccionado | Revisa los requisitos de tipo de columna del explicador y ajusta el alcance |
| No se renderizan resultados después de la creación | Error de procesamiento                                          | Revisa la Job Queue para detalles del error y vuelve a intentarlo           |
