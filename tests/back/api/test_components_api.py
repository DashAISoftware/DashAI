import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.config import component_registry
from DashAI.back.dataloaders import BaseDataLoader
from DashAI.back.registries import ComponentRegistry
from DashAI.back.tasks import BaseTask


class TestTask1(BaseTask):
    name: str = "TestTask1"

    @classmethod
    def get_schema(cls) -> dict:
        return {"class": "TestTask1"}


class TestTask2(BaseTask):
    name: str = "TestTask2"

    @classmethod
    def get_schema(cls) -> dict:
        return {"class": "TestTask2"}


class AbstractTestDataloader(BaseDataLoader):
    _compatible_tasks = ["TestTask1"]

    def load_data(self, dataset_path, file=None, url=None):
        pass


class TestDataloader1(AbstractTestDataloader):
    @classmethod
    def get_schema(cls) -> dict:
        return {"class": "TestDataloader1"}


class TestDataloader2(AbstractTestDataloader):
    @classmethod
    def get_schema(cls) -> dict:
        return {"class": "TestDataloader2"}


class TestDataloader3(BaseDataLoader):
    _compatible_tasks = ["TestTask2"]

    @classmethod
    def get_schema(cls) -> dict:
        return {"class": "TestDataloader3"}

    def load_data(self, dataset_path, file=None, url=None):
        pass


@pytest.fixture(scope="module", name="test_components")
def fixture_test_components():
    original_registry = component_registry._registry
    original_relationships = component_registry._relationship_manager

    test_registry = ComponentRegistry(
        initial_components=[
            TestTask1,
            TestTask2,
            TestDataloader1,
            TestDataloader2,
            TestDataloader3,
        ]
    )

    # replace the default dataloaders with the previously test dataloaders
    component_registry._registry = test_registry._registry
    component_registry._relationship_manager = test_registry._relationship_manager

    yield test_registry

    # cleanup: restore orginal registers
    component_registry._registry = original_registry
    component_registry._relationship_manager = original_relationships


def test_get_component_by_id(client: TestClient, test_components):
    response = client.get("/api/v1/component/TestTask1/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "TestTask1",
        "type": "Task",
        "configurable_object": False,
        "schema": None,
        "description": None,
    }

    response = client.get("/api/v1/component/TestTask2/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "TestTask2",
        "type": "Task",
        "configurable_object": False,
        "schema": None,
        "description": None,
    }

    response = client.get("/api/v1/component/TestDataloader1/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "TestDataloader1",
        "type": "DataLoader",
        "configurable_object": True,
        "schema": {"class": "TestDataloader1"},
        "description": None,
    }


def test_get_component_by_id_wrong_query(client: TestClient):
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


def test_get_all_components(client: TestClient, test_components):
    response = client.get("/api/v1/component")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 5
    assert data == [
        {
            "name": "TestTask1",
            "type": "Task",
            "configurable_object": False,
            "schema": None,
            "description": None,
        },
        {
            "name": "TestTask2",
            "type": "Task",
            "configurable_object": False,
            "schema": None,
            "description": None,
        },
        {
            "name": "TestDataloader1",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {"class": "TestDataloader1"},
            "description": None,
        },
        {
            "name": "TestDataloader2",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {"class": "TestDataloader2"},
            "description": None,
        },
        {
            "name": "TestDataloader3",
            "type": "DataLoader",
            "configurable_object": True,
            "schema": {"class": "TestDataloader3"},
            "description": None,
        },
    ]


def test_get_components_only_tasks(client: TestClient, test_components):
    task_registry = test_components[0]
    task_names = task_registry.registry.keys()

    response = client.get("/api/v1/component?component_type=task")

    assert response.status_code == 200
    data = response.json()
    assert [{"class": "TestTask1"}, {"class": "TestTask2"}] == data
    assert len(data) == 2

    for task_schema in data:
        assert isinstance(task_schema, dict)
        assert task_schema["class"] in task_names


def test_get_components_only_dataloaders(client: TestClient, test_components):
    dataloader_registry = test_components[1]
    dataloader_names = dataloader_registry.registry.keys()

    response = client.get("/api/v1/component?component_type=dataloader")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 3

    for dataloader_data in data:
        assert isinstance(dataloader_data, dict)
        assert dataloader_data["class"] in dataloader_names


def test_get_components_wrong_type(client: TestClient, test_components):
    response = client.get("/api/v1/component?component_type=-1")
    assert response.status_code == 422
    assert response.json() == {
        "detail": "component_type -1 does not exist in the registry."
    }


def test_get_components_by_task(client: TestClient, test_components):
    dataloader_registry = test_components[1]
    dataloader_names = dataloader_registry.registry.keys()

    response = client.get("/api/v1/component?task_name=TestTask2")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1

    for dataloader_data in data:
        assert isinstance(dataloader_data, dict)
        assert dataloader_data["class"] in dataloader_names
        assert dataloader_data["class"] != "TestDataloader2"
        assert dataloader_data["class"] != "TestDataloader1"


def test_get_components_by_task_wrong_name(client: TestClient, test_components):
    response = client.get("/api/v1/component?task_name=-1")
    assert response.status_code == 422
    assert response.json() == {"detail": "task_name -1 does not exist in the registry."}


def test_get_components_dataloaders_by_task(client: TestClient, test_components):
    dataloader_registry = test_components[1]
    dataloader_names = dataloader_registry.registry.keys()

    # in this case, since we use TestTask1 as task_name, the request should return
    # only TestDataloader1 and TestDataloader2 which are related to TestTask1.
    # this implies that TestDataloader3 is excluded from the returned elements.
    response = client.get(
        "/api/v1/component?component_type=dataloader&task_name=TestTask1"
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2

    for dataloader_data in data:
        assert isinstance(dataloader_data, dict)
        assert dataloader_data["class"] in dataloader_names
        assert dataloader_data["class"] != "TestDataloader3"


def test_get_components_by_component_parent(client: TestClient, test_components):
    # In this case, only TestDataloader1 and TestDataloader2
    # extends AbstractTestDataloader. So, the expected result is an array of both
    # schemas.

    dataloader_registry = test_components[1]
    dataloader_names = dataloader_registry.registry.keys()

    response = client.get("/api/v1/component?component_parent=AbstractTestDataloader")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2

    for dataloader_data in data:
        assert isinstance(dataloader_data, dict)
        assert dataloader_data["class"] in dataloader_names
        assert dataloader_data["class"] != "TestDataloader3"
