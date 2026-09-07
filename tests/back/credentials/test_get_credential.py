from kink import di

from DashAI.back.config_object import ConfigObject
from DashAI.back.credentials.base_credential import BaseCredential
from DashAI.back.dependencies.registry import ComponentRegistry


class DummyCredential(BaseCredential):
    DISPLAY_NAME = "Dummy"
    DESCRIPTION = "dummy"

    def verify(self, key: str) -> bool:
        return True


class DummyComponentBase:
    TYPE = "DummyType"


class DummyComponent(ConfigObject, DummyComponentBase):
    REQUIRED_CREDENTIALS = ["DummyCredential"]


def test_get_credential_returns_instance():
    registry = ComponentRegistry(initial_components=[DummyCredential])
    di["component_registry"] = registry
    try:
        component = DummyComponent()
        cred = component.get_credential("DummyCredential")
        assert isinstance(cred, DummyCredential)
    finally:
        del di["component_registry"]
