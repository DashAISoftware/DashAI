---
title: Arquitectura
sidebar_label: Arquitectura
---

dashAI es una plataforma modular y extensible para flujos de trabajo de aprendizaje automático. Provee una interfaz web para entrenar modelos, explorar datasets, explicar predicciones y más. Este documento describe el funcionamiento interno de dashAI.

## Visión General

dashAI sigue una arquitectura cliente servidor con tres procesos de ejecución principales:

1. **Backend FastAPI**: sirve la API REST en el puerto 8000. En producción también sirve la SPA compilada de React en `/app/`.
2. **Consumidor Huey**: un trabajador en segundo plano que procesa tareas de larga duración (entrenamiento, exploración, predicción, etc.).
3. **Frontend React**: una aplicación de página única que se comunica con el backend a través de la API REST. En desarrollo se ejecuta de forma separada en el puerto 3000 (`yarn start`); en producción se compila y es servida por FastAPI.

El punto de entrada es `DashAI/__main__.py`, que usa Typer como CLI. Al iniciar:

1. Resuelve la ruta de datos local (por defecto `~/.DashAI`).
2. Inicia el consumidor Huey. En desarrollo (instalación normal de Python) este es un **subproceso** externo; en modo empaquetado (PyInstaller) se ejecuta como un **hilo** interno al proceso.
3. Inicia el servidor FastAPI mediante Uvicorn.
4. Opcionalmente abre un navegador o una ventana PyWebView.

La inyección de dependencias es gestionada por **Kink**. El contenedor DI (`back/container.py`) conecta el motor de base de datos, la fábrica de sesiones, el registro de componentes y la cola de trabajos para que los endpoints de la API los reciban automáticamente.

## Patrones Clave

- **Extensibilidad basada en componentes**: toda la funcionalidad de ML (modelos, tareas, métricas, exploradores, etc.) está encapsulada en componentes que comparten un mecanismo común de registro y configuración.
- **Configuración dirigida por esquemas**: los componentes declaran esquemas Pydantic que se convierten a JSON Schema para la generación dinámica de formularios en el frontend y la validación en el backend.
- **Procesamiento asíncrono de trabajos**: las operaciones de larga duración se delegan a un trabajador Huey en segundo plano, con seguimiento de estado mediante señales y actualizaciones en la base de datos.
- **Separación limpia de responsabilidades**: la capa API maneja HTTP, el registro de componentes maneja el descubrimiento, la cola de trabajos maneja la ejecución y la base de datos maneja la persistencia.

## Lecturas Adicionales

| Tema                                                                | Página                                                       |
| ------------------------------------------------------------------- | ------------------------------------------------------------ |
| Estructura de la API REST, mapa de rutas, inyección de dependencias | [API](/deep-dive/api)                                        |
| Tipos de componentes, registro y objetos configurables              | [Componentes](/deep-dive/components)                         |
| Esquema SQLite, tablas ORM y almacenamiento de datos                | [Base de Datos](/deep-dive/database)                         |
| Cola de trabajos Huey y tipos de trabajos                           | [Sistema de Trabajos](/deep-dive/job-system)                 |
| Sesiones de Notebook, exploradores y converters                     | [Notebook](/deep-dive/notebook)                              |
| Recorridos completos de entrenamiento y exploración                 | [Ejemplos de Flujo de Trabajo](/deep-dive/workflow-examples) |
| Tipos semánticos de columnas e inferencia                           | [Tipos Semánticos](/deep-dive/semantic-types)                |
| Primitivo central de datos, splits y ciclo de vida del dato         | [DashAIDataset](/deep-dive/dashai-dataset)                   |
