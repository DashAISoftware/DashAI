---
title: Testing
sidebar_label: Testing
sidebar_position: 4
---

# Testing

## Tests del Backend

dashAI usa **pytest** para los tests del backend.

### Ejecutar Todos los Tests

```bash
pytest -v
```

### Ejecutar un Archivo de Test Específico

```bash
pytest tests/back/api/test_components_api.py -v
```

### Ejecutar un Test por Nombre

```bash
pytest tests/back/api/test_components_api.py::test_name -v
```

### Ejecutar con Cobertura

```bash
pytest --cov=DashAI --cov-report=html
```

## Tests del Frontend

```bash
cd DashAI/front
yarn test
```

## Estructura de Tests

```
tests/
├── back/
│   ├── api/            # Tests de endpoints de la API
│   ├── job/            # Tests de ejecución de jobs
│   ├── models/         # Tests de componentes de modelos
│   ├── converters/     # Tests de converters
│   ├── explorers/      # Tests de explorers
│   └── ...
└── docs/               # Tests del generador de documentación
```

## CI

GitHub Actions ejecuta la suite completa de tests en cada PR y push sobre:

- **Versiones de Python**: 3.11, 3.12, 3.13
- **Sistemas operativos**: Ubuntu, Windows, macOS

Verificaciones adicionales en CI:

- **pre-commit**: Linting con Ruff, formateo y otros hooks
- **db-migrations**: Verificaciones de upgrade/downgrade/reversibilidad con Alembic
- **docs**: Build de Docusaurus

## Escribir Tests

Los tests del backend siguen las convenciones de pytest:

```python
def test_create_dataset(client, tmp_path):
    # Arrange
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("a,b\n1,2\n3,4")

    # Act
    response = client.post("/api/v1/dataset/", files={"file": open(csv_file)})

    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == "test"
```

Se provee un fixture `client` que crea una aplicación FastAPI de prueba con una base de datos SQLite en memoria.
