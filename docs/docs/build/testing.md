---
title: Testing
sidebar_label: Testing
sidebar_position: 4
---

# Testing

## Backend Tests

dashAI uses **pytest** for backend testing.

### Run All Tests

```bash
pytest -v
```

### Run a Single Test File

```bash
pytest tests/back/api/test_components_api.py -v
```

### Run a Single Test by Name

```bash
pytest tests/back/api/test_components_api.py::test_name -v
```

### Run with Coverage

```bash
pytest --cov=DashAI --cov-report=html
```

## Frontend Tests

```bash
cd DashAI/front
yarn test
```

## Test Structure

```
tests/
├── back/
│   ├── api/            # API endpoint tests
│   ├── job/            # Job execution tests
│   ├── models/         # Model component tests
│   ├── converters/     # Converter tests
│   ├── explorers/      # Explorer tests
│   └── ...
└── docs/               # Documentation generator tests
```

## CI

GitHub Actions runs the full test suite on every PR and push across:

- **Python versions**: 3.10, 3.11, 3.12, 3.13
- **Operating systems**: Ubuntu, Windows, macOS

Additional CI checks:

- **pre-commit**: Ruff linting, formatting, and other hooks
- **db-migrations**: Alembic upgrade/downgrade/reversibility checks
- **docs**: Docusaurus build

## Writing Tests

Backend tests follow pytest conventions:

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

A `client` fixture is provided that creates a test FastAPI app with an in-memory SQLite database.
