---
title: Sistema de Trabajos
sidebar_label: Sistema de Trabajos
---

## Cola de Trabajos

La **Cola de Trabajos** maneja la ejecución asíncrona de tareas de larga duración. dashAI usa **Huey**, una cola de tareas Python ligera, respaldada por una base de datos SQLite.

### Arquitectura

| Capa                    | Implementación                                                    |
| ----------------------- | ----------------------------------------------------------------- |
| Base abstracta          | `BaseJobQueue` (`back/dependencies/job_queues/base_job_queue.py`) |
| Implementación concreta | `HueyJobQueue` (`back/dependencies/job_queues/huey_job_queue.py`) |
| Almacenamiento          | SQLite en `~/.DashAI/job_queue.db` (separado de la BD principal)  |
| Serialización           | `dill` (maneja objetos Python complejos como lambdas)             |

### Cómo Funciona la Cola

1. Un endpoint de la API llama a `job_queue.put(job)`, que encola el trabajo y devuelve un ID de trabajo de inmediato.
2. El hilo consumidor de Huey (iniciado al arrancar la aplicación) recoge el trabajo y llama a `job.run()`.
3. El ciclo de vida del trabajo se rastrea mediante señales de Huey y una tabla `task_copy`:

   | Señal              | Actualización de estado |
   | ------------------ | ----------------------- |
   | `SIGNAL_ENQUEUED`  | `not_started`           |
   | `SIGNAL_EXECUTING` | `started`               |
   | `SIGNAL_COMPLETE`  | `finished`              |
   | `SIGNAL_ERROR`     | `error`                 |

4. El frontend consulta `GET /api/v1/job/status/{job_id}` para rastrear el progreso.

### Métodos Clave

| Método              | Descripción                                     |
| ------------------- | ----------------------------------------------- |
| `put(job)`          | Encolar un trabajo, devuelve el ID del trabajo  |
| `get(job_id)`       | Obtener el estado y metadatos del trabajo       |
| `peek()`            | Ver el siguiente trabajo sin sacarlo de la cola |
| `is_empty()`        | Verificar si la cola tiene trabajos pendientes  |
| `async_get(job_id)` | Versión asíncrona de get                        |

El backend SQLite usa el modo Write-Ahead Logging (WAL) para un acceso concurrente seguro entre el proceso de la API y el consumidor Huey.

---

## Trabajos

Un **Trabajo** encapsula una unidad de trabajo en segundo plano. Todos los trabajos heredan de `BaseJob` (`back/job/base_job.py`).

### Interfaz Base

```python
class BaseJob(metaclass=ABCMeta):
    TYPE = "Job"

    @abstractmethod
    def run(self) -> None: ...

    @abstractmethod
    def set_status_as_delivered(self) -> None: ...

    @abstractmethod
    def set_status_as_error(self) -> None: ...

    @abstractmethod
    def get_job_name(self) -> str: ...
```

### Tipos de Trabajos

| Clase de trabajo | Propósito                                                   |
| ---------------- | ----------------------------------------------------------- |
| `ModelJob`       | Entrenar un modelo y calcular métricas                      |
| `ExplorerJob`    | Ejecutar una exploración/visualización de datos             |
| `ExplainerJob`   | Generar explicaciones del modelo (SHAP, etc.)               |
| `PredictJob`     | Ejecutar predicciones sobre nuevos datos                    |
| `ConverterJob`   | Aplicar transformaciones de datos al dataset de un Notebook |
| `GenerativeJob`  | Manejar interacciones con modelos generativos               |
| `DatasetJob`     | Cargar y procesar datasets                                  |

Cada tipo de trabajo gestiona sus propias transiciones de estado en la base de datos y el manejo de errores. Cuando un trabajo falla, registra el mensaje de error en la base de datos y actualiza el estado de la entidad correspondiente a `ERROR`.
