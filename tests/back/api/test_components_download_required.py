"""Tests for the nested download-resolution endpoint."""

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.downloads.downloadable import DownloadableMixin
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.models.base_model import BaseModel

URL = "/api/v1/component/downloads/required"


class PlainModel(BaseModel):
    """A model with no download requirement."""

    @classmethod
    def get_schema(cls) -> dict:
        return {}

    def save(self, filename=None): ...

    def load(self, filename): ...


class DownloadableModel(DownloadableMixin, BaseModel):
    """A nested-selectable model that reports as not downloaded."""

    DOWNLOAD_SIZE_BYTES = 123
    DESCRIPTION = "Downloadable"
    DISPLAY_NAME = "Downloadable Model"

    @classmethod
    def is_downloaded(cls) -> bool:
        return False

    @classmethod
    def get_schema(cls) -> dict:
        return {}

    def save(self, filename=None): ...

    def load(self, filename): ...


@pytest.fixture(autouse=True)
def _registry(client, monkeypatch):
    registry = ComponentRegistry(initial_components=[PlainModel, DownloadableModel])
    monkeypatch.setitem(client.app.container._services, "component_registry", registry)
    return registry


def test_required_downloads_reports_nested(client: TestClient):
    body = {
        "parameters": {
            "clf": {"component": "DownloadableModel", "params": {}},
        }
    }
    response = client.post(URL, json=body)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "DownloadableModel"
    assert data[0]["download_size_bytes"] == 123
    assert data[0]["display_name"] == "Downloadable Model"


def test_required_downloads_empty_for_plain(client: TestClient):
    body = {"parameters": {"clf": {"component": "PlainModel", "params": {}}}}
    response = client.post(URL, json=body)
    assert response.status_code == 200
    assert response.json() == []


def test_required_downloads_includes_parent_model(client: TestClient):
    body = {"model_name": "DownloadableModel", "parameters": {}}
    response = client.post(URL, json=body)
    assert response.status_code == 200
    data = response.json()
    assert [d["name"] for d in data] == ["DownloadableModel"]
