"""Tests module for components API."""
import pytest
from datasets import ClassLabel, Image, Value
from fastapi.testclient import TestClient

from DashAI.back.dataloaders import BaseDataLoader
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.models import BaseModel
from DashAI.back.tasks import BaseTask

# -------------------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------------------


TEST_SCHEMA_1 = {
    "properties": {
        "parameter_1": {
            "type": "number",
        },
    }
}

TEST_SCHEMA_2 = {
    "properties": {
        "parameter_2": {
            "type": "string",
            "enum": ["a", "b"],
        },
    }
}


class TestTask1(BaseTask):
    DESCRIPTION = "Task 1."

    metadata = {
        "inputs_types": [ClassLabel, Value],
        "outputs_types": [ClassLabel],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }

    @classmethod
    def get_schema(cls) -> dict:
        return {"class": "TestTask1"}


class TestTask2(BaseTask):
    DESCRIPTION = "Task 2."
    metadata = {
        "inputs_types": [Image],
        "outputs_types": [ClassLabel],
        "inputs_cardinality": 1,
        "outputs_cardinality": 1,
    }

    @classmethod
    def get_schema(cls) -> dict:
        return {}


class AbstractTestDataloader(BaseDataLoader):
    COMPATIBLE_COMPONENTS = ["TestTask1"]

    def load_data(self, dataset_path, file=None, url=None):
        pass


class TestDataloader1(AbstractTestDataloader):
    @classmethod
    def get_schema(cls) -> dict:
        return {}


class TestDataloader2(AbstractTestDataloader):
    @classmethod
    def get_schema(cls) -> dict:
        return {}


class TestDataloader3(BaseDataLoader):
    COMPATIBLE_COMPONENTS = ["TestTask2"]

    @classmethod
    def get_schema(cls) -> dict:
        return {}

    def load_data(self, dataset_path, file=None, url=None):
        pass


class TestModel1(BaseModel):
    COMPATIBLE_COMPONENTS = ["TestTask1"]

    @classmethod
    def get_schema(cls) -> dict:
        return TEST_SCHEMA_1

    def save(self, filename=None):
        ...

    def load(self, filename):
        ...


class TestModel2(BaseModel):
    @classmethod
    def get_schema(cls) -> dict:
        return TEST_SCHEMA_2

    def save(self, filename=None):
        ...

    def load(self, filename):
        ...


@pytest.fixture(scope="module", autouse=True, name="test_registry")
def setup_test_registry(client):
    """Setup a test registry with test task, dataloader and model components."""
    container = client.app.container

    test_registry = ComponentRegistry(
        initial_components=[
            TestTask1,
            TestTask2,
            TestDataloader1,
            TestDataloader2,
            TestDataloader3,
            TestModel1,
            TestModel2,
        ]
    )
    with container.component_registry.override(test_registry):
        yield test_registry


# -------------------------------------------------------------------------------------
# Test get component by id
# -------------------------------------------------------------------------------------


def test_get_component_by_id(client: TestClient):
    """Test that a component can be retrieved by id."""
    response = client.get("/api/v1/component/TestTask1/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "TestTask1",
        "type": "Task",
        "configurable_object": False,
        "schema": None,
        "metadata": {
            "inputs_types": ["ClassLabel", "Value"],
            "outputs_types": ["ClassLabel"],
            "inputs_cardinality": "n",
            "outputs_cardinality": 1,
        },
        "description": "Task 1.",
    }

    response = client.get("/api/v1/component/TestTask2/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "TestTask2",
        "type": "Task",
        "configurable_object": False,
        "schema": None,
        "metadata": {
            "inputs_types": ["Image"],
            "outputs_types": ["ClassLabel"],
            "inputs_cardinality": 1,
            "outputs_cardinality": 1,
        },
        "description": "Task 2.",
    }

    response = client.get("/api/v1/component/TestDataloader1/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "TestDataloader1",
        "type": "DataLoader",
        "configurable_object": True,
        "schema": {},
        "metadata": None,
        "description": None,
    }


def test_get_component_by_id_not_found(client: TestClient):
    """Test that a 404 is returned when the a component is not found."""
    response = client.get("/api/v1/component/-1/")
    assert response.status_code == 404
    assert response.json() == {"detail": "Component -1 not found in the registry."}

    response = client.get("/api/v1/component/TestTask99/")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Component TestTask99 not found in the registry."
    }

    response = client.get("/api/v1/component/!TestDataloader*1/")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Component !TestDataloader*1 not found in the registry."
    }


# -------------------------------------------------------------------------------------
# Test get all components
# -------------------------------------------------------------------------------------


def test_get_all_components(client: TestClient):
    """Test that all components can be retrieved."""
    response = client.get("/api/v1/component")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 7
    assert data == [
        {
            "name": "TestTask1",
            "type": "Task",
            "configurable_object": False,
            "schema": None,
            "metadata": {
                "inputs_types": ["ClassLabel", "Value"],
                "outputs_types": ["ClassLabel"],
                "inputs_cardinality": "n",
                "outputs_cardinality": 1,
            },
            "description": "Task 1.",
        },
        {
            "name": "TestTask2",
            "type": "Task",
            "configurable_object": False,
            "schema": None,
            "metadata": {
                "inputs_types": ["Image"],
                "outputs_types": ["ClassLabel"],
                "inputs_cardinality": 1,
                "outputs_cardinality": 1,
            },
            "description": "Task 2.",
        },
        {
            "name": "TestDataloader1",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestDataloader2",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestDataloader3",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestModel1",
            "type": "Model",
            "configurable_object": True,
            "schema": {"properties": {"parameter_1": {"type": "number"}}},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestModel2",
            "type": "Model",
            "configurable_object": True,
            "schema": {
                "properties": {"parameter_2": {"type": "string", "enum": ["a", "b"]}}
            },
            "metadata": None,
            "description": None,
        },
    ]


# -------------------------------------------------------------------------------------
# Test type select parameter in component getter
# -------------------------------------------------------------------------------------


def test_get_components_select_only_tasks(client: TestClient):
    """Test that get component can retrieve only tasks."""
    response = client.get("/api/v1/component?select_types=Task")

    assert response.status_code == 200
    assert response.json() == [
        {
            "name": "TestTask1",
            "type": "Task",
            "configurable_object": False,
            "schema": None,
            "metadata": {
                "inputs_types": ["ClassLabel", "Value"],
                "outputs_types": ["ClassLabel"],
                "inputs_cardinality": "n",
                "outputs_cardinality": 1,
            },
            "description": "Task 1.",
        },
        {
            "name": "TestTask2",
            "type": "Task",
            "configurable_object": False,
            "schema": None,
            "metadata": {
                "inputs_types": ["Image"],
                "outputs_types": ["ClassLabel"],
                "inputs_cardinality": 1,
                "outputs_cardinality": 1,
            },
            "description": "Task 2.",
        },
    ]


def test_get_components_select_only_dataloaders(client: TestClient):
    """Test that get component can retrieve only dataloaders."""
    response = client.get("/api/v1/component?select_types=DataLoader")
    assert response.status_code == 200

    assert response.json() == [
        {
            "name": "TestDataloader1",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestDataloader2",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestDataloader3",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
    ]


def test_get_components_select_tasks_and_models(client: TestClient):
    """Test that get component can retrieve tasks and models."""
    response = client.get("/api/v1/component?select_types=Model&select_types=Task")
    assert response.status_code == 200

    assert response.json() == [
        {
            "name": "TestModel1",
            "type": "Model",
            "configurable_object": True,
            "schema": {"properties": {"parameter_1": {"type": "number"}}},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestModel2",
            "type": "Model",
            "configurable_object": True,
            "schema": {
                "properties": {"parameter_2": {"type": "string", "enum": ["a", "b"]}}
            },
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestTask1",
            "type": "Task",
            "configurable_object": False,
            "schema": None,
            "metadata": {
                "inputs_types": ["ClassLabel", "Value"],
                "outputs_types": ["ClassLabel"],
                "inputs_cardinality": "n",
                "outputs_cardinality": 1,
            },
            "description": "Task 1.",
        },
        {
            "name": "TestTask2",
            "type": "Task",
            "configurable_object": False,
            "schema": None,
            "metadata": {
                "inputs_types": ["Image"],
                "outputs_types": ["ClassLabel"],
                "inputs_cardinality": 1,
                "outputs_cardinality": 1,
            },
            "description": "Task 2.",
        },
    ]


def test_get_components_select_unexistant_type(client: TestClient):
    """Test get component returns an error when component type that doesn't exist."""
    response = client.get("/api/v1/component?select_types=BadType")
    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "Select type 'BadType' does not exist in the registry. "
            "Available types: ['Task', 'DataLoader', 'Model']."
        )
    }
    # test select type with one valid type and a invalid one.
    response = client.get("/api/v1/component?select_types=Task&select_types=BadType")
    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "Select type 'BadType' does not exist in the registry. "
            "Available types: ['Task', 'DataLoader', 'Model']."
        )
    }


# -------------------------------------------------------------------------------------
# Test type ignore parameter in component getter
# -------------------------------------------------------------------------------------


def test_get_components_ignore_models(client: TestClient):
    response = client.get("/api/v1/component?ignore_types=Model")
    assert response.status_code == 200

    assert response.json() == [
        {
            "name": "TestTask1",
            "type": "Task",
            "configurable_object": False,
            "schema": None,
            "metadata": {
                "inputs_types": ["ClassLabel", "Value"],
                "outputs_types": ["ClassLabel"],
                "inputs_cardinality": "n",
                "outputs_cardinality": 1,
            },
            "description": "Task 1.",
        },
        {
            "name": "TestTask2",
            "type": "Task",
            "configurable_object": False,
            "schema": None,
            "metadata": {
                "inputs_types": ["Image"],
                "outputs_types": ["ClassLabel"],
                "inputs_cardinality": 1,
                "outputs_cardinality": 1,
            },
            "description": "Task 2.",
        },
        {
            "name": "TestDataloader1",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestDataloader2",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestDataloader3",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
    ]


def test_get_components_ignore_tasks_and_models(client: TestClient):
    response = client.get("/api/v1/component?ignore_types=Model&ignore_types=Task")
    assert response.status_code == 200

    assert response.json() == [
        {
            "name": "TestDataloader1",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestDataloader2",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestDataloader3",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
    ]


def test_get_components_ignore_unexistant_type(client: TestClient):
    response = client.get("/api/v1/component?ignore_types=BadType")
    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "Ignore type 'BadType' does not exist in the registry. "
            "Available types: ['Task', 'DataLoader', 'Model']."
        )
    }

    # with one valid ignore type and one invalid
    response = client.get("/api/v1/component?ignore_types=Task&ignore_types=BadType")
    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "Ignore type 'BadType' does not exist in the registry. "
            "Available types: ['Task', 'DataLoader', 'Model']."
        )
    }


# -------------------------------------------------------------------------------------
# Test related component parameter in component getter
# -------------------------------------------------------------------------------------


def test_get_components_related_with_some_task(client: TestClient):
    response = client.get("/api/v1/component?related_component=TestTask1")
    assert response.status_code == 200
    assert response.json() == [
        {
            "name": "TestDataloader1",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestDataloader2",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestModel1",
            "type": "Model",
            "configurable_object": True,
            "schema": {"properties": {"parameter_1": {"type": "number"}}},
            "metadata": None,
            "description": None,
        },
    ]


def test_get_components_related_inverse_relation(client: TestClient):
    response = client.get("/api/v1/component?related_component=TestModel1")
    assert response.status_code == 200
    assert response.json() == [
        {
            "name": "TestTask1",
            "type": "Task",
            "configurable_object": False,
            "schema": None,
            "metadata": {
                "inputs_types": ["ClassLabel", "Value"],
                "outputs_types": ["ClassLabel"],
                "inputs_cardinality": "n",
                "outputs_cardinality": 1,
            },
            "description": "Task 1.",
        }
    ]


def test_get_components_related_empty_relation(client: TestClient):
    response = client.get("/api/v1/component?related_component=TestModel2")
    assert response.status_code == 200
    assert response.json() == []


def test_get_components_relations_unexistant_component(client: TestClient):
    response = client.get("/api/v1/component?related_component=-1")
    assert response.status_code == 422
    assert response.json() == {
        "detail": "Related component -1 does not exist in the registry."
    }


# -------------------------------------------------------------------------------------
# Test parent component parameter in component getter
# -------------------------------------------------------------------------------------


def test_get_components_dataloader_component_parent(client: TestClient):
    # In this case, only TestDataloader1 and TestDataloader2
    # extends AbstractTestDataloader. So, the expected result is an array of both
    # schemas.

    response = client.get("/api/v1/component?component_parent=AbstractTestDataloader")
    assert response.status_code == 200

    assert response.json() == [
        {
            "name": "TestDataloader1",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestDataloader2",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
    ]


def test_get_components_component_parent_unexistant_base(client: TestClient):
    # In this case, only TestDataloader1 and TestDataloader2
    # extends AbstractTestDataloader. So, the expected result is an array of both
    # schemas.

    response = client.get("/api/v1/component?component_parent=UnexistantBase")
    assert response.status_code == 200
    assert response.json() == []


# -------------------------------------------------------------------------------------
# Test more than one selector
# -------------------------------------------------------------------------------------


def test_get_components_by_type_and_task(client: TestClient):
    # Select DataLoaders related with TestTask1
    response = client.get(
        "/api/v1/component?select_types=DataLoader&related_component=TestTask1"
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "name": "TestDataloader1",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestDataloader2",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
    ]


def test_get_components_by_type_and_task_2(client: TestClient):
    # Select Models related with TestTask1
    response = client.get(
        "/api/v1/component?select_types=Model&related_component=TestTask1"
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "name": "TestModel1",
            "type": "Model",
            "configurable_object": True,
            "schema": {"properties": {"parameter_1": {"type": "number"}}},
            "metadata": None,
            "description": None,
        }
    ]


def test_get_components_select_and_ignore_by_type(client: TestClient):
    # Select DataLoaders related with TestTask1
    response = client.get(
        "/api/v1/component?select_types=DataLoader&select_types=Task&ignore_types=Task"
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "name": "TestDataloader1",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestDataloader2",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestDataloader3",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
    ]


def test_get_components_select_type_and_parent(client: TestClient):
    # Select DataLoaders related with TestTask1
    response = client.get(
        "/api/v1/component?select_types=DataLoader"
        "&component_parent=AbstractTestDataloader"
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "name": "TestDataloader1",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
        {
            "name": "TestDataloader2",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {},
            "metadata": None,
            "description": None,
        },
    ]
