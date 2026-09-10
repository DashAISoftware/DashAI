---
title: Recorrido por la interfaz
sidebar_label: Recorrido por la interfaz
sidebar_position: 3
---

# Recorrido por la interfaz

Esta página describe las principales áreas de la interfaz de dashAI y qué hace cada una.

---

## Barra de navegación

La barra superior siempre está visible y proporciona acceso a todos los módulos principales:

| Sección        | Qué hace                                                                 |
| -------------- | ------------------------------------------------------------------------ |
| **DATASETS**   | Carga datasets, explora su contenido y abre notebooks                    |
| **MODELS**     | Crea sesiones, entrena modelos, compara resultados y genera predicciones |
| **GENERATIVE** | Interactúa con modelos de generación de texto e imágenes                 |
| **PLUGINS**    | Instala y gestiona plugins                                               |

El **selector de idioma** (junto al ícono de globo) cambia el idioma de la interfaz (entre inglés y español). El botón del **monitor de hardware** muestra el uso de recursos del sistema. El botón de **tutoriales** abre guías paso a paso. El botón de **tema** alterna entre el modo claro y oscuro.

---

## Barra lateral izquierda

El contenido de la barra lateral cambia según el módulo en el que te encuentres.

**En Datasets:** Muestra los **datasets disponibles** (con recuentos de filas y columnas) y los **Notebooks** (agrupados bajo su dataset padre). Una barra de búsqueda filtra ambos. El botón **New Dataset/Notebook** en la parte superior inicia el flujo de carga o creación de notebooks.

**En Models:** Muestra los **datasets disponibles** y las **sesiones** agrupadas por tipo de tarea. Una barra de búsqueda filtra datasets y sesiones. El botón **New Session** crea una nueva sesión.

**En Generative:** Muestra las sesiones organizadas por tipo de tarea generativa.

---

## Área principal

El área de contenido central cambia según lo que hayas seleccionado.

### Datasets: Vista del dataset

Cuando haces clic en un dataset en la barra lateral, el área principal muestra el panel de EDA del dataset:

- **Encabezado**: nombre del dataset, fecha de creación, Puntuación de calidad y botón NEW NOTEBOOK
- **Tarjetas de resumen**: Total de filas, Total de columnas, Tamaño del archivo, Filas duplicadas, Valores faltantes
- **Banner de calidad**: marca de verificación verde si no hay problemas, advertencia si se detectaron problemas
- **Pestañas de análisis**: Resumen, Análisis numérico, Categórico, Texto, Calidad de datos, Correlaciones

### Datasets: Vista del Notebook

Cuando hay un notebook abierto:

- **Título del notebook**: `Notebook: [Nombre del dataset] Preview`
- **Barra de herramientas**: controles de FILTROS y EXPORTAR
- **Tabla de vista previa del dataset**: vista paginada de los datos en su estado actual; se actualiza después de cada converter
- **Línea de tiempo de operaciones**: cada Explorador o Converter que agregues aparece debajo de la vista previa como un bloque con su resultado, indicador de estado y controles de edición/eliminación
- **Botón SAVE AS NEW DATASET**: en la parte superior derecha, guarda el estado actual como un nuevo dataset

### Models: Vista de sesión

Cuando hay una sesión abierta:

- **Panel de comparación de modelos**: tabla con todos los modelos y sus métricas; alterna entre las divisiones TRAINING, VALIDATION y TEST; cambia entre las vistas TABLE y CHARTS
- **Tarjetas de modelos**: una por modelo, expandibles, cada una con botones EDIT y TRAIN/RE-TRAIN, un indicador de estado y cuatro pestañas internas: LIVE METRICS, EXPLAINABILITY, PREDICTIONS, HYPERPARAMETERS

### Generative: Vista de chat

Cuando hay una sesión generativa abierta, el área principal muestra una interfaz de chat:

- **Historial de chat**: registro de conversación desplazable que muestra tus mensajes y las respuestas del modelo
- **Campo de entrada**: campo de texto en la parte inferior para escribir tu prompt; presiona Enter o haz clic en el botón de enviar para enviarlo
- **Respuestas del modelo**: se muestran en línea dentro de la conversación, con soporte para texto con formato

---

## Panel derecho

El panel derecho es sensible al contexto y aparece junto al área principal.

**En Notebooks (pestaña EXPLORE):** El panel de Herramientas de análisis lista todas las herramientas de exploración disponibles organizadas por categoría. Pasa el cursor sobre cualquier herramienta para ver una imagen de vista previa y su descripción. Haz clic para abrir el modal de configuración.

**En Notebooks (pestaña CONVERT):** El mismo panel, pero mostrando las herramientas de converter organizadas por categoría.

**En Models:** El panel de Modelos disponibles lista todos los modelos compatibles con la tarea de la sesión actual. Pasa el cursor para ver una descripción. Haz clic para abrir el modal Agregar modelo.

**En Generative:** Muestra los hiperparámetros del modelo seleccionado, lo que te permite modificarlos directamente antes o entre interacciones.

---

## Modales de configuración

Muchas herramientas abren un modal de configuración de dos pasos:

**Paso 1, Configurar alcance:** Selecciona qué columnas utilizará la herramienta. La tabla del selector de columnas muestra el índice, nombre, tipo de valor y tipo de dato. Un contador en la parte superior muestra cuántas columnas están seleccionadas y cuántas son necesarias.

Para los converters, el Paso 1 también incluye el **alcance de filas**: selecciona filas por rango, por índices específicos o usa SELECT ALL.

**Paso 2, Configurar parámetros:** Cada herramienta tiene su propio conjunto de parámetros, generados automáticamente a partir del esquema de la herramienta. Cada parámetro tiene un ícono de ayuda **?**. Haz clic en **CREATE EXPLORER** o **CREATE CONVERTER** para aplicar.

---

## Cola de trabajos

La Cola de trabajos es visible en la parte inferior derecha de la pantalla siempre que haya trabajos en ejecución o que se hayan completado recientemente. Muestra:

- Trabajos activos (con un indicador giratorio y recuento)
- Trabajos fallidos (con un indicador rojo y recuento)
- Un botón **Show Completed** para revisar los trabajos finalizados

Las operaciones de larga duración (entrenamiento, exploración, generación de predicciones) se ejecutan como trabajos en segundo plano para que puedas continuar trabajando mientras se procesan.

---

## Indicadores de estado

Los indicadores de estado aparecen en las tarjetas de modelos y en los resultados de exploradores/converters a lo largo de la interfaz:

| Indicador       | Significado                                             |
| --------------- | ------------------------------------------------------- |
| **Not Started** | La operación fue configurada pero aún no se ejecutó     |
| **Finished**    | La operación se completó con éxito                      |
| **Error**       | La operación falló; verifica los parámetros o los datos |
| **Started**     | La operación se está ejecutando actualmente             |
| **Delivered**   | La operación ha sido encolada                           |
