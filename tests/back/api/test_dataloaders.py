import pytest
from fastapi.testclient import TestClient

from DashAI.back.core import config
from DashAI.back.dataloaders import BaseDataLoader
from DashAI.back.registries import DataloaderRegistry, TaskRegistry
from DashAI.back.tasks import BaseTask


class TestTask(BaseTask):
    name: str = "TestTask"


class AbstractTestDataloader(BaseDataLoader):
    _compatible_tasks = ["TestTask"]

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
    _compatible_tasks = ["FooTask"]

    @classmethod
    def get_schema(cls) -> dict:
        return {"class": "TestDataloader3"}

    def load_data(self, dataset_path, file=None, url=None):
        pass


@pytest.fixture(scope="module", name="test_dataloader_registry")
def fixture_test_dataloader_registry():
    original_dataloader_registry = config.dataloader_registry

    test_task_registry = TaskRegistry(initial_components=[TestTask])

    test_dataloader_registry = DataloaderRegistry(
        initial_components=[TestDataloader1, TestDataloader2],
        task_registry=test_task_registry,
    )
    # replace the default dataloaders with the previously test dataloaders
    config.dataloader_registry._registry = test_dataloader_registry._registry
    config.dataloader_registry.task_component_mapping = (
        test_dataloader_registry.task_component_mapping
    )
    yield test_dataloader_registry

    config.dataloader_registry._registry = original_dataloader_registry._registry
    config.dataloader_registry.task_component_mapping = (
        original_dataloader_registry.task_component_mapping
    )


def test_get_all_dataloaders(
    client: TestClient,
    test_dataloader_registry: DataloaderRegistry,
):
    dataloader_names = test_dataloader_registry.task_to_components("TestTask")
    response = client.get("/api/v1/dataloader/TestTask")
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 2
    for dataloader_data in data:
        assert dataloader_data["class"] in dataloader_names
        assert dataloader_data["class"] != "TestDataloader3"
        assert isinstance(dataloader_data, dict)
