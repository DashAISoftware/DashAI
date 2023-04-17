import pytest

from DashAI.back.registries.task_registry import TaskRegistry
from DashAI.back.tasks.base_task import BaseTask
from fastapi.testclient import TestClient
from DashAI.back.core import config

default_task_dict = {'foo': 'bar'}

class TestTask1(BaseTask):
    name: str = "TestTask1"
    @classmethod
    def get_schema(self) -> dict:
        return default_task_dict

class TestTask2(BaseTask):
    name: str = "TestTask2"
    @classmethod
    def get_schema(self) -> dict:
        return default_task_dict

@pytest.fixture(scope="module", name='test_task_registry')
def fixture_test_task_registry():
    original_task_registry = config.task_registry

    test_task_registry = TaskRegistry(initial_components=[TestTask1, TestTask2])
    # replace the default tasks with the previously test tasks
    config.task_registry._registry = test_task_registry._registry
    yield test_task_registry

    config.task_registry._registry = original_task_registry._registry 

def test_get_all_tasks(client: TestClient, test_task_registry: TaskRegistry):
    task_names = test_task_registry.registry.keys()
    response = client.get("/api/v1/task/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data.keys()) == 2
    for task_name, task_data in data.items():
        assert task_name in task_names
        assert isinstance(task_data, dict)
        assert task_data == default_task_dict