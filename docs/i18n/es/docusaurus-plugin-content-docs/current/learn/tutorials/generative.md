---
title: IA Generativa
sidebar_label: IA Generativa
---

# IA Generativa

El módulo Generativo te permite interactuar con modelos de IA generativa directamente dentro de dashAI, sin escribir ningún código. Puedes generar texto o imágenes, ajustar parámetros del modelo en tiempo real y hacer seguimiento de cada cambio de configuración en el historial de la sesión.

:::note Requisito de hardware
Los modelos generativos son computacionalmente intensivos. Se recomienda encarecidamente una GPU NVIDIA con soporte CUDA. Ejecutar estos modelos en CPU es posible pero significativamente más lento, y algunos modelos más grandes pueden fallar al cargarse por limitaciones de memoria.
:::

---

## Tareas Disponibles

Al abrir el módulo Generativo, seleccionas un tipo de tarea que determina qué modelos están disponibles:

| Tarea           | Descripción                                                                                |
| --------------- | ------------------------------------------------------------------------------------------ |
| **TextToText**  | Genera texto a partir de un prompt de texto. Incluye LLMs como Qwen, Llama y otros.        |
| **TextToImage** | Genera imágenes a partir de una descripción de texto usando modelos como Stable Diffusion. |
| **ControlNet**  | Transforma o modifica una imagen existente guiada por texto y una imagen de entrada.       |

---

## Guía Paso a Paso

### 1. Seleccionar una Tarea

Navega a la sección **GENERATIVE** en la barra de navegación superior.
Haz clic en el tipo de tarea que deseas usar (p. ej., **TextToText**).

### 2. Seleccionar un Modelo

Se muestra una lista de modelos disponibles para la tarea seleccionada. Haz clic en un modelo para seleccionarlo.

### 3. Configurar los Parámetros del Modelo

Cada modelo expone un conjunto de parámetros que controlan su comportamiento. Estos aparecen en un panel en el lado derecho de la pantalla. Los parámetros comunes incluyen:

| Parámetro       | Descripción                                                                                                                                                                                         |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Temperature** | Controla la aleatoriedad de la salida. Valores bajos (p. ej., 0.1) producen respuestas más deterministas y enfocadas. Valores altos (p. ej., 1.0+) producen salidas más variadas y creativas.       |
| **Max tokens**  | El número máximo de tokens (aproximadamente palabras o partes de palabras) que el modelo generará en una sola respuesta.                                                                            |
| **Top-p**       | Muestreo por núcleo, que limita la generación al conjunto mínimo de tokens cuya probabilidad acumulada supera este valor. Funciona junto con temperature para controlar la diversidad de la salida. |
| **Seed**        | Una semilla aleatoria fija para reproducibilidad. Establecer la misma semilla con los mismos parámetros producirá la misma salida.                                                                  |

Los parámetros varían según el modelo, y no todos los modelos exponen todos los anteriores. Cada parámetro tiene un icono de ayuda **?** que muestra una descripción al pasar el cursor.

Para tareas de generación de imágenes, hay parámetros adicionales disponibles como:

- **Width / Height**: dimensiones de la imagen de salida. Ambas deben ser divisibles por 8.
- **Inference steps**: número de pasos de eliminación de ruido. Más pasos generalmente producen imágenes de mayor calidad pero tardan más.
- **Guidance scale**: qué tan fielmente el modelo sigue el prompt de texto.

### 4. Configurar los Parámetros de la Sesión

Antes de crear la sesión puedes opcionalmente establecer:

- **Nombre de sesión**: una etiqueta para identificar esta sesión en la lista de sesiones.
- **Descripción de sesión**: una nota opcional sobre el propósito de esta sesión.

Ambos campos son opcionales. Si se dejan vacíos, dashAI asigna un nombre por defecto.

### 5. Crear la Sesión

Haz clic en **"Create a session"** para inicializar la sesión. dashAI cargará el modelo seleccionado. Esto puede tardar un momento, especialmente en el primer uso cuando los pesos del modelo necesitan descargarse.

Una vez que la sesión esté lista, se abre la interfaz de interacción.

### 6. Interactuar con el Modelo

El área principal de la sesión es la interfaz de interacción:

- **TextToText**: un campo de entrada donde escribes un prompt y recibes la respuesta de texto del modelo. Cada intercambio se muestra como un hilo de conversación.
- **TextToImage / ControlNet**: un campo de entrada para el prompt de texto y, donde aplique, un área de carga de imágenes. La imagen generada se muestra en línea.

Envía tu entrada y espera a que el modelo genere una respuesta. El tiempo de generación depende del tamaño del modelo, la configuración de parámetros y tu hardware.

### 7. Ajustar Parámetros Durante la Sesión

Puedes cambiar cualquier parámetro del modelo en cualquier momento durante una sesión activa usando el panel de parámetros a la derecha. Los cambios surten efecto en la siguiente generación, así que no necesitas crear una nueva sesión.

### 8. Ver el Historial de la Sesión

Haz clic en el botón **"History"** para abrir un registro de todos los cambios de parámetros realizados durante la sesión. Cada entrada muestra:

- El parámetro que fue cambiado.
- Los valores anterior y nuevo.
- La fecha y hora del cambio.

Esto es útil para rastrear qué configuración produjo una salida particular y para volver a un estado anterior.

### 9. Acceder a Sesiones Anteriores

Todas las sesiones que has creado están listadas en el lado izquierdo de la sección Generativa, organizadas por tipo de tarea. Haz clic en cualquier sesión para reabrirla y continuar interactuando con el modelo usando la misma configuración.

---

## Consejos

- Comienza con los valores de parámetros predeterminados y ajusta de forma incremental. Cambiar múltiples parámetros a la vez dificulta entender qué cambio afectó la salida.
- Para la generación de imágenes, **el ancho y el alto deben ser divisibles por 8**. Los valores que no cumplan este requisito causarán un error.
- Usa una **Seed** fija cuando experimentes con parámetros. Te permite comparar salidas de diferentes configuraciones manteniendo constante la aleatoriedad.
- Si el modelo se queda sin memoria durante la generación, intenta reducir **Max tokens** (para texto) o **Width/Height** e **Inference steps** (para imágenes).
- El historial de sesión es particularmente útil en un contexto de enseñanza: crea un registro visible de cómo los cambios de parámetros afectan el comportamiento del modelo.

## Solución de Problemas

| Síntoma                                         | Causa probable                                        | Solución                                                                                           |
| ----------------------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| La generación falla inmediatamente              | Memoria GPU insuficiente                              | Reduce las dimensiones de imagen o max tokens; cierra otras aplicaciones que usen la GPU           |
| Error en dimensiones de imagen                  | Ancho o alto no divisible por 8                       | Ajusta las dimensiones al múltiplo de 8 más cercano (p. ej., 512, 768, 1024)                       |
| El modelo tarda mucho en cargar                 | Primer uso, descargando pesos del modelo              | Espera a que se complete la descarga; las cargas posteriores serán más rápidas                     |
| La salida siempre es idéntica                   | La semilla está fija y los parámetros no han cambiado | Cambia la semilla o aumenta la temperature para obtener salidas variadas                           |
| Los detalles del error no son visibles en la UI | El modal de error muestra un mensaje genérico         | Abre la consola de desarrollador del navegador (F12) y revisa los registros para el error completo |
