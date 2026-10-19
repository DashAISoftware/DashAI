"""Tests for the app-config endpoint."""

import pytest
from fastapi.testclient import TestClient


def test_tours_autostart_enabled_by_default(client: TestClient, monkeypatch):
    monkeypatch.delenv("DASHAI_NO_TOURS", raising=False)
    response = client.get("/api/v1/app-config/")
    assert response.status_code == 200
    assert response.json() == {"tours_autostart": True}


@pytest.mark.parametrize("value", ["1", "true", "YES", " on "])
def test_no_tours_disables_autostart(client: TestClient, monkeypatch, value):
    monkeypatch.setenv("DASHAI_NO_TOURS", value)
    response = client.get("/api/v1/app-config/")
    assert response.json() == {"tours_autostart": False}


@pytest.mark.parametrize("value", ["", "0", "false", "no"])
def test_falsy_no_tours_keeps_autostart(client: TestClient, monkeypatch, value):
    monkeypatch.setenv("DASHAI_NO_TOURS", value)
    response = client.get("/api/v1/app-config/")
    assert response.json() == {"tours_autostart": True}
