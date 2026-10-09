---
title: Migraciones de Base de Datos
sidebar_label: Migraciones de Base de Datos
sidebar_position: 3
---

# Migraciones de Base de Datos

dashAI usa **Alembic** para las migraciones del esquema de base de datos. Las migraciones se ejecutan automáticamente al iniciar la aplicación.

## Aplicar Migraciones

Para ejecutar todas las migraciones pendientes manualmente (desde el directorio `DashAI/`):

```bash
alembic upgrade head
```

## Crear una Nueva Migración

Después de modificar los modelos SQLAlchemy en `back/dependencies/database/`:

```bash
alembic revision --autogenerate -m "description of changes"
```

El archivo de migración generado se guarda en `alembic/versions/` y debe ser incluido en el repositorio.

:::tip
Siempre revisa el archivo de migración generado automáticamente antes de aplicarlo. Alembic no siempre detecta correctamente cambios complejos (como renombrado de columnas o cambios en restricciones).
:::

## Revertir

Revertir la migración más reciente:

```bash
alembic downgrade -1
```

Revertir a una revisión específica:

```bash
alembic downgrade <revision_id>
```

## Verificar Estado

```bash
# Migración aplicada actualmente
alembic current

# Historial completo de migraciones
alembic history
```

## Verificaciones en CI

El pipeline de CI ejecuta verificaciones de migraciones en cada PR:

- `alembic upgrade head`: verificar que la migración se aplica correctamente
- `alembic downgrade -1` / `alembic upgrade head`: verificar reversibilidad
- Verificación de consistencia del esquema: verificar que el esquema final coincide con los modelos SQLAlchemy

## Ubicación de la Base de Datos

La base de datos principal se almacena en `~/.DashAI/db.sqlite`. La cola de jobs usa una base de datos separada en `~/.DashAI/job_queue.db`.
