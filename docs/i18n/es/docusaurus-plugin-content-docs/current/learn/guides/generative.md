---
title: "Guía del Módulo: IA Generativa"
sidebar_label: IA Generativa
sidebar_position: 3
---

# Guía del Módulo: IA Generativa

El módulo Generativo proporciona una interfaz sin código para interactuar con modelos de IA generativa: generación de texto, síntesis de imágenes y generación de imágenes condicionada por ControlNet. A diferencia del módulo de Modelos, que está construido alrededor del entrenamiento y la evaluación estructurados, el módulo Generativo está orientado a la experimentación interactiva: configuras un modelo, creas una sesión e interactúas con el modelo en tiempo real mientras ajustas parámetros y observas su efecto.

---

## Tareas y Modelos

El módulo está organizado por tipo de tarea. Seleccionar una tarea filtra los modelos disponibles a aquellos compatibles con esa modalidad de generación.

### TextToTextGenerationTask

Genera texto a partir de un mensaje de texto. Adecuado para generación abierta, resumen, seguimiento de instrucciones y preguntas y respuestas.

| Modelo      | Descripción                                                                                                          |
| ----------- | -------------------------------------------------------------------------------------------------------------------- |
| `QwenModel` | Modelo de lenguaje de la serie Qwen. Admite generación conversacional y seguimiento de instrucciones                 |
| Otros LLMs  | Es posible que haya modelos de texto adicionales disponibles según tu instalación de dashAI y los plugins instalados |

### TextToImageGenerationTask

Genera imágenes a partir de una descripción de texto.

| Modelo                   | Descripción                                                                  |
| ------------------------ | ---------------------------------------------------------------------------- |
| `StableDiffusionV2Model` | Stable Diffusion v2 para síntesis de texto a imagen de propósito general     |
| `StableDiffusionV3Model` | Stable Diffusion v3 con mayor adherencia al prompt y mejor calidad de imagen |

### ControlNetTask

Genera imágenes guiadas tanto por un mensaje de texto como por una imagen de control espacial (p. ej., una pose, un mapa de profundidad o un mapa de bordes). Otorga control preciso sobre la estructura de la imagen generada.

| Modelo                          | Descripción                                                                                     |
| ------------------------------- | ----------------------------------------------------------------------------------------------- |
| `StableDiffusionXLV1ControlNet` | Modelo basado en SDXL con condicionamiento ControlNet para generación de imágenes estructuradas |

---

## Modelo de Sesión

El módulo Generativo utiliza un concepto de **sesión** que difiere del módulo de Modelos. Aquí, una sesión es un hilo de conversación persistente vinculado a un modelo específico y una configuración de parámetros. Cada sesión almacena el historial completo de interacciones y el registro completo de los cambios de parámetros realizados durante esa sesión.

Las sesiones se listan en el lado izquierdo de la sección Generativa, organizadas por tarea. Puedes mantener múltiples sesiones por tarea, cada una con un modelo o configuración diferente.

---

## Parámetros

Los parámetros se configuran antes de crear una sesión y pueden ajustarse en cualquier momento durante una sesión activa. Los cambios surten efecto en la próxima generación, y no se requiere reinicio.

### Parámetros de Generación de Texto

| Parámetro            | Qué controla                                                                                                                                                                                                                                                                       |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Temperatura**      | Aleatoriedad de la salida. Los valores bajos (0.1–0.3) producen salidas enfocadas y deterministas. Los valores altos (0.8–1.5+) aumentan la variedad y creatividad, pero pueden reducir la coherencia                                                                              |
| **Máximo de Tokens** | Número máximo de tokens generados por respuesta. Un token equivale aproximadamente a ¾ de una palabra en español. Controla la longitud de la salida y el uso de memoria                                                                                                            |
| **Top-p**            | Umbral de muestreo por núcleo. El modelo considera solo el conjunto más pequeño de tokens cuya probabilidad acumulada alcanza este valor. Funciona junto con la Temperatura, ya que reducir Top-p hace que las salidas sean más conservadoras independientemente de la Temperatura |
| **Semilla**          | Semilla aleatoria fija. Establecer la misma semilla con los mismos parámetros y prompt reproducirá exactamente la misma salida, lo que es útil para comparaciones controladas                                                                                                      |

### Parámetros de Generación de Imágenes

| Parámetro               | Qué controla                                                                                                                                                                      |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ancho / Alto**        | Dimensiones de la imagen de salida en píxeles. **Ambos valores deben ser divisibles por 8.** Valores comunes: 512, 768, 1024                                                      |
| **Pasos de Inferencia** | Número de iteraciones de eliminación de ruido. Más pasos producen mayor calidad y detalle, pero aumentan el tiempo de generación. Rango típico: 20–50                             |
| **Escala de Guía**      | Qué tan fuertemente el modelo sigue el prompt de texto frente a la generación libre. Valores más altos (7–15) se adhieren más al prompt; valores más bajos permiten más variación |
| **Semilla**             | Semilla fija para generación de imágenes reproducible                                                                                                                             |

### Parámetros Adicionales de ControlNet

Al usar modelos ControlNet, parámetros adicionales controlan la intensidad del condicionamiento y el procesamiento aplicado a la imagen de control (p. ej., detección de bordes, estimación de profundidad). Estos varían según la variante específica de ControlNet que se utilice.

---

## Efectos de Interacción entre Parámetros

Comprender cómo interactúan los parámetros ayuda a evitar errores comunes:

**Temperatura + Top-p:** Estos dos parámetros controlan la diversidad de la salida, pero a través de mecanismos diferentes. La Temperatura escala la distribución de probabilidad (alto = más plana = más aleatoria); Top-p trunca el grupo de candidatos. Usar ambos con valores altos simultáneamente puede producir salidas incoherentes. Una combinación efectiva común es una temperatura moderada (0.7) con Top-p alrededor de 0.9.

**Pasos de Inferencia + Escala de Guía (imagen):** Más pasos de inferencia permiten al modelo refinar los detalles progresivamente. Una escala de guía más alta requiere más pasos para converger correctamente. Usar una guía alta con muy pocos pasos suele producir imágenes sobresaturadas o con muchos artefactos.

**Ancho × Alto × Pasos de Inferencia (imagen):** El tiempo de generación y el uso de memoria escalan con los tres. Comienza con 512×512 y 20–30 pasos al probar prompts, luego aumenta la resolución y los pasos para las salidas finales.

---

## Historial de Sesión

Cada sesión mantiene un registro de auditoría completo de los cambios de parámetros. Haz clic en **Historial** para ver:

- Qué parámetro fue cambiado
- El valor antes y después del cambio
- La marca de tiempo del cambio

Este registro es valioso para rastrear el camino hacia una salida particular. Cuando encuentras una generación que funciona bien, el historial muestra exactamente qué valores de parámetros la produjeron.

---

## Consideraciones de Hardware

Los modelos generativos tienen requisitos de hardware significativamente más altos que los modelos de ML clásicos.

:::note
Se recomienda encarecidamente una GPU NVIDIA con soporte CUDA. La mayoría de los modelos de generación de texto (Qwen) requieren al menos 8 GB de VRAM. Los modelos de generación de imágenes (Stable Diffusion) típicamente requieren entre 6 y 12 GB según la resolución y la versión del modelo. Ejecutar en CPU es técnicamente posible, pero prácticamente lento.
:::

**Consejos de gestión de memoria:**

- Reduce **Ancho/Alto** para reducir el uso de VRAM en modelos de imagen
- Reduce **Máximo de Tokens** para limitar la memoria en modelos de texto
- Evita ejecutar múltiples sesiones generativas simultáneamente
- Si una generación falla con un error de memoria, reducir cualquiera de los parámetros anteriores es el primer paso

**Visibilidad de errores:** Cuando una generación falla, el modal de error en dashAI muestra un mensaje genérico. Para información detallada del error, abre la consola de desarrollador del navegador (F12 → pestaña Consola) donde se registra el seguimiento completo de la pila.

---

## Consejos

- Usa **Semilla** cuando compares el efecto de un solo parámetro: fija la semilla, cambia solo un parámetro y compara las salidas directamente.
- Para la generación de imágenes, establece un buen prompt con baja resolución (512×512, 20 pasos) antes de escalar. La generación en alta resolución con un mal prompt desperdicia tiempo y memoria.
- El registro de **Historial** funciona también como receta: cuando encuentras una configuración que funciona, el registro te proporciona los valores exactos de parámetros para reproducirla en una nueva sesión.
- Los modelos ControlNet requieren una imagen de control que coincida con el tipo de condicionamiento. Un modelo de pose necesita una imagen de esqueleto de pose, y un modelo de bordes necesita una imagen con detección de bordes. Proporcionar el tipo incorrecto produce salidas incoherentes.
- Una **Escala de Guía** más baja (4–6) a menudo produce imágenes más estéticamente agradables para prompts creativos; valores más altos (10–15) funcionan mejor para prompts muy específicos o técnicos.
