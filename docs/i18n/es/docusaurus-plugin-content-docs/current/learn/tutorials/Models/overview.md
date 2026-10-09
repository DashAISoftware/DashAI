---
title: Módulo de Modelos
sidebar_label: Descripción General
---

# Módulo de Modelos

El módulo de Modelos es el entorno de dashAI para entrenar, evaluar, comparar y desplegar modelos de aprendizaje automático. Todo está organizado alrededor de **Sesiones**. Una sesión agrupa uno o más modelos entrenados sobre el mismo dataset y tarea, manteniendo todos los resultados, predicciones y herramientas de explicabilidad en un solo lugar.

---

## Conceptos Clave

- **Tarea**: El tipo de problema de aprendizaje automático que deseas resolver. Cada tarea determina qué modelos están disponibles, qué tipos de columnas son válidos como entradas y salidas, y qué métricas se usan para evaluar los resultados.
- **Sesión**: Un entorno de trabajo vinculado a un dataset y una tarea específicos. Una sesión puede contener múltiples modelos entrenados bajo las mismas condiciones, facilitando la comparación de enfoques uno al lado del otro.
- **Modelo**: Un algoritmo específico añadido a una sesión, configurado con sus propios hiperparámetros. Múltiples modelos del mismo tipo pueden coexistir en la misma sesión con diferentes configuraciones.
- **Ejecución**: Cada vez que se entrena un modelo, produce una ejecución con sus propias métricas, predicciones y resultados de explicabilidad.

---

## Tareas Disponibles

Al abrir el módulo de Modelos, el área principal muestra los tipos de tareas disponibles con una descripción de cada una. Usa la barra de búsqueda para filtrar tareas por nombre.

| Tarea                      | Descripción                                                                                                                                                         |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Clasificación Tabular**  | Predice una etiqueta categórica a partir de datos tabulares estructurados (filas y columnas).                                                                       |
| **Clasificación de Texto** | Asigna categorías o etiquetas predefinidas a documentos de texto según su contenido. Útil para análisis de sentimientos, filtrado de spam, categorización de temas. |
| **Regresión**              | Predice un valor numérico continuo a partir de datos tabulares estructurados.                                                                                       |
| **Traducción**             | Convierte texto de un idioma a otro preservando el significado y el contexto (tarea de NLP).                                                                        |

Cada tarea impone requisitos específicos sobre los tipos de columnas para entrada y salida, y estos se validan automáticamente al configurar la sesión.

---

## Sesiones

Las sesiones se listan en la barra lateral izquierda bajo **Sessions**, agrupadas por tipo de tarea. Cada entrada de sesión muestra su nombre y el dataset desde el que fue creada.

Haz clic en **New Session** (el botón `+` en la barra lateral) para comenzar a crear una nueva sesión.
Haz clic en cualquier sesión existente para reabrirla y continuar trabajando.

La barra lateral también muestra el conteo de sesiones por tipo de tarea, facilitando la navegación cuando se trabaja con múltiples experimentos.

---

## Panel Derecho: Modelos Disponibles

Cuando una sesión está abierta, el panel derecho muestra los modelos disponibles para la tarea actual. Cada modelo tiene un icono y nombre únicos. Al pasar el cursor sobre una tarjeta de modelo se muestra un popup con una descripción del algoritmo, sus fortalezas y casos de uso típicos.

El panel incluye una barra de búsqueda para filtrar modelos por nombre.

Los modelos disponibles varían según la tarea. Para Clasificación Tabular, por ejemplo, el panel incluye modelos como Support Vector Machine (SVM), Decision Tree, K-Nearest Neighbors (KNN), Logistic Regression, Random Forest, Gradient Boosting y Dummy Classifier. Otras tareas tienen sus propios catálogos de modelos correspondientes.

---

## Estructura de la Sección

Esta sección se divide en las siguientes páginas:

- **[Entrenar un Modelo](/learn/tutorials/Models/train)**: Cómo crear una sesión, configurar columnas de entrada/salida, definir divisiones de datos, añadir modelos, establecer hiperparámetros y ejecutar el entrenamiento.
- **[Predicciones](/learn/tutorials/Models/predictions)**: Cómo generar predicciones usando modelos entrenados, tanto desde un dataset completo como desde datos ingresados manualmente.
- **[Explicabilidad](/learn/tutorials/Models/explainability)**: Cómo usar explicadores globales y locales para entender el comportamiento del modelo.
- **[Comparación de Modelos](/learn/tutorials/Models/comparison)**: Cómo comparar métricas entre modelos usando tablas y gráficos.
