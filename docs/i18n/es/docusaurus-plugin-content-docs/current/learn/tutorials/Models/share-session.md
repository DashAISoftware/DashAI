---
title: Compartir una sesión
sidebar_label: Compartir una sesión
---

# Compartir una sesión

Una sesión de modelos completa puede salir de dashAI como un único archivo
`.dashai` e importarse en otro dashAI, o en el mismo. Sirve para repartir una
sesión a un curso, pasarle tu trabajo a un compañero, mover sesiones a otro
computador o dejar que otra persona reentrene tu experimento y compare.

## Exportar

En el panel izquierdo, abre el menú (**...**) de una sesión y elige
**Exportar**. El diálogo permite:

- **Elegir los runs** que se incluyen. Vienen todos marcados; los runs que
  siguen entrenando no se pueden exportar hasta que terminen.
- **Incluir modelos entrenados**, marcado por defecto. Desmárcalo para
  exportar solo la configuración, sin modelos entrenados: el dataset y los
  ajustes de la sesión y sus runs. El archivo pesa menos y quien lo importe
  entrena los modelos de nuevo.

Los runs terminados van con su modelo y sus métricas. Los runs que fallaron o
nunca se entrenaron van sin modelo y llegan sin entrenar.

## Importar

Junto al título **Sesiones** del panel izquierdo, presiona el botón de
importar, lee el aviso y elige el archivo `.dashai`. dashAI crea una sesión
nueva con su propia copia del dataset y la abre. Desde ahí puedes predecir,
re-entrenar y agregar modelos como en cualquier otra sesión.

Importar nunca cambia lo que ya tienes. Si existe una sesión o un dataset con
el mismo nombre, el nuevo lleva un número, por ejemplo `iris (2)`.

## Qué contiene el archivo

- El dataset, con su división en entrenamiento, validación y prueba.
- La configuración de la sesión: tarea, columnas, preprocesamiento y
  evaluación.
- La configuración de cada run elegido y, si se incluyen, su modelo
  entrenado, sus métricas y el preprocesamiento ajustado.

Las explicaciones, predicciones y reportes todavía no se incluyen; genéralos
de nuevo después de importar.

## Compatibilidad

- Un archivo de un dashAI más nuevo se rechaza: actualiza dashAI para abrirlo.
- Si la sesión usa un plugin que no tienes, la importación se rechaza y el
  mensaje indica cuál instalar.
- Si tus versiones de librerías son distintas a las usadas al exportar, la
  sesión se importa con una advertencia. Si luego un modelo falla, usa
  **Re-entrenar**: la configuración siempre va en el archivo.
- Si un modelo debe descargarse (por ejemplo, un traductor de HuggingFace) y
  no lo tienes, dashAI te avisa al importar. Un run entrenado igual predice
  con su propia copia, y solo necesitas la descarga para re-entrenarlo. Un run
  que llega sin entrenar la necesita antes de entrenar, y el aviso ofrece un
  botón **Descargar**.

:::warning
Un archivo de sesión contiene objetos de Python y usar sus modelos ejecuta
código. Importa solo sesiones de personas en las que confíes.
:::

:::note
El archivo siempre incluye el dataset, y algunos modelos (por ejemplo, KNN)
además guardan filas de entrenamiento dentro de sí. No compartas una sesión
entrenada con datos privados.
:::
