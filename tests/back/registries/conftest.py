import pytest

from DashAI.back.tasks import BaseTask


@pytest.fixture()
def tasks():
    class Task1(BaseTask):
        ...

    class Task2(BaseTask):
        ...

    class NoTask:
        ...

    return Task1, Task2, NoTask
