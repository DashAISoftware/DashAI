from unittest.mock import Mock, patch

from fastapi.testclient import TestClient


def test_post_plugin(client: TestClient):
    response = client.post(
        "/api/v1/plugin/",
        json=[
            {
                "name": "dashai-svc-plugin",
                "author": "DashAI team",
                "installed_version": "0.0.1",
                "lastest_version": "0.0.1",
                "tags": [{"name": "DashAI"}, {"name": "Model"}],
                "summary": "SVC Model Plugin v1.0",
                "description": "",
                "description_content_type": "text/markdown",
            }
        ],
    )
    assert response.status_code == 201, response.text
    assert len(response.json()) == 1


def test_refresh_plugins(client: TestClient):
    # Mock para requests.get (lista global /simple/)
    mock_client = Mock()
    mock_client.json.return_value = {
        "meta": {"_last-serial": 0, "api-version": "1.0"},
        "projects": [
            {"_last-serial": 0, "name": "image-classification-package"},
            {"_last-serial": 1, "name": "dashai-tabular-classification-package"},
            {"_last-serial": 2, "name": "scikit-dashai-learn"},
        ],
    }
    mock_client.status_code = 200

    # Mock para requests.get (status /simple/<project>/)
    status_mock = Mock()
    status_mock.status_code = 200
    status_mock.raise_for_status.return_value = None
    status_mock.json.return_value = {"project-status": {"status": "active"}}

    # Mock para requests.get (metadata /pypi/<project>/json)
    request_mock = Mock()
    json_return = {
        "info": {
            "author": "DashAI team",
            "version": "0.0.2",
            "keywords": "DashAI,Package,Model,Dataloader",
            "description": "# Description \n",
            "description_content_type": "text/markdown",
            "name": "dashai-tabular-classification-package",
            "summary": "Tabular Classification Package",
        },
    }
    request_mock.json.return_value = json_return

    with patch("requests.get", side_effect=[mock_client, status_mock, request_mock]):
        response = client.post("/api/v1/plugin/index")
        assert response.status_code == 201, response.text
        assert len(response.json()) == 1


def test_post_existing_plugin(client: TestClient):
    response = client.post(
        "/api/v1/plugin/",
        json=[
            {
                "name": "dashai-svc-plugin",
                "author": "DashAI team",
                "installed_version": "0.0.1",
                "lastest_version": "0.0.3",
                "tags": [{"name": "DashAI"}, {"name": "Model"}],
                "summary": "SVC Model Plugin v2.0",
                "description": "",
                "description_content_type": "text/markdown",
            }
        ],
    )
    assert response.status_code == 201, response.text
    plugin = response.json()[0]
    assert plugin["name"] == "dashai-svc-plugin"
    assert plugin["summary"] == "SVC Model Plugin v2.0"
    assert plugin["lastest_version"] == "0.0.3"


def test_refresh_existing_plugin_with_new_version(client: TestClient):
    mock_client = Mock()
    mock_client.json.return_value = {
        "meta": {"_last-serial": 0, "api-version": "1.0"},
        "projects": [
            {"_last-serial": 0, "name": "image-classification-package"},
            {"_last-serial": 1, "name": "dashai-tabular-classification-package"},
            {"_last-serial": 2, "name": "scikit-dashai-learn"},
        ],
    }
    mock_client.status_code = 200

    status_mock = Mock()
    status_mock.status_code = 200
    status_mock.raise_for_status.return_value = None
    status_mock.json.return_value = {"project-status": {"status": "active"}}

    request_mock = Mock()
    json_return = {
        "info": {
            "author": "DashAI team",
            "version": "0.0.5",
            "keywords": "DashAI,Package,Model,Dataloader",
            "description": "# Description \n",
            "description_content_type": "text/markdown",
            "name": "dashai-tabular-classification-package",
            "summary": "Tabular Classification Package",
        },
    }
    request_mock.json.return_value = json_return

    with patch("requests.get", side_effect=[mock_client, status_mock, request_mock]):
        response = client.post("/api/v1/plugin/index")
        assert response.status_code == 201, response.text
        assert len(response.json()) == 1
        plugin = response.json()[0]
        assert plugin["name"] == "dashai-tabular-classification-package"
        assert plugin["summary"] == "Tabular Classification Package"
        assert plugin["installed_version"] == "0.0.2"
        assert plugin["lastest_version"] == "0.0.5"


def test_refresh_plugins_skips_archived(client: TestClient):
    mock_client = Mock()
    mock_client.json.return_value = {
        "meta": {"_last-serial": 0, "api-version": "1.0"},
        "projects": [
            {"_last-serial": 1, "name": "dashai-tabular-classification-package"}
        ],
    }
    mock_client.status_code = 200

    status_mock = Mock()
    status_mock.status_code = 200
    status_mock.raise_for_status.return_value = None
    status_mock.json.return_value = {"project-status": {"status": "archived"}}

    # No debería llamarse, pero igual lo dejamos por seguridad
    request_mock = Mock()

    with patch("requests.get", side_effect=[mock_client, status_mock, request_mock]):
        response = client.post("/api/v1/plugin/index")
        assert response.status_code == 201, response.text
        assert len(response.json()) == 0


def test_get_all_plugins(client: TestClient):
    response = client.get("/api/v1/plugin/")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 2
    plugins = response.json()
    assert plugins[0]["name"] == "dashai-svc-plugin"
    assert plugins[0]["author"] == "DashAI team"
    assert plugins[0]["installed_version"] == "0.0.1"
    assert plugins[0]["tags"][0]["name"] == "DashAI"
    assert plugins[0]["tags"][1]["name"] == "Model"
    assert plugins[0]["status"] == 1
    assert plugins[0]["summary"] == "SVC Model Plugin v2.0"
    assert plugins[0]["description_content_type"] == "text/markdown"

    assert plugins[1]["name"] == "dashai-tabular-classification-package"
    assert plugins[1]["author"] == "DashAI team"
    assert plugins[1]["installed_version"] == "0.0.2"
    assert plugins[1]["tags"][0]["name"] == "DashAI"
    assert plugins[1]["tags"][1]["name"] == "Package"
    assert plugins[1]["tags"][2]["name"] == "Model"
    assert plugins[1]["tags"][3]["name"] == "Dataloader"
    assert plugins[1]["status"] == 1
    assert plugins[1]["summary"] == "Tabular Classification Package"
    assert plugins[1]["description_content_type"] == "text/markdown"


def test_get_plugin(client: TestClient):
    response = client.get("/api/v1/plugin/1")
    assert response.status_code == 200, response.text
    plugin = response.json()
    assert plugin["name"] == "dashai-svc-plugin"
    assert plugin["author"] == "DashAI team"
    assert plugin["installed_version"] == "0.0.1"
    assert plugin["tags"][0]["name"] == "DashAI"
    assert plugin["tags"][1]["name"] == "Model"
    assert plugin["status"] == 1
    assert plugin["summary"] == "SVC Model Plugin v2.0"
    assert plugin["description_content_type"] == "text/markdown"


def test_get_unexistant_plugin(client: TestClient):
    response = client.get("/api/v1/plugin/31415")
    assert response.status_code == 404, response.text


def test_patch_plugin(client: TestClient):
    with patch(
        "DashAI.back.plugins.utils.install_requirement",
        return_value=["dashai-svc-plugin"],
    ) as mock_install:
        response = client.patch("/api/v1/plugin/1", json={"new_status": 2})
        mock_install.assert_called_once_with("dashai-svc-plugin")
        assert response.status_code == 200, response.text

        response = client.get("/api/v1/plugin/1")
        assert response.status_code == 200

        plugin = response.json()
        assert plugin["status"] == 2


def test_get_filtered_plugins(client: TestClient):
    response = client.get("/api/v1/plugin/?plugin_status=NONE")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 0

    response = client.get("/api/v1/plugin/?plugin_status=REGISTERED")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1

    response = client.get("/api/v1/plugin/?plugin_status=INSTALLED")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1

    response = client.get("/api/v1/plugin/?tags=Model")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 2
    plugin = response.json()[0]
    assert plugin["name"] == "dashai-svc-plugin"
    assert plugin["tags"][0]["name"] == "DashAI"
    assert plugin["tags"][1]["name"] == "Model"

    response = client.get("/api/v1/plugin/?tags=Dataloader")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1

    response = client.get("/api/v1/plugin/?tags=Model&tags=Package")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 2
    plugins = response.json()
    assert plugins[0]["name"] == "dashai-svc-plugin"
    assert plugins[0]["tags"][0]["name"] == "DashAI"
    assert plugins[0]["tags"][1]["name"] == "Model"
    assert plugins[1]["name"] == "dashai-tabular-classification-package"
    assert plugins[1]["tags"][0]["name"] == "DashAI"
    assert plugins[1]["tags"][1]["name"] == "Package"
    assert plugins[1]["tags"][2]["name"] == "Model"
    assert plugins[1]["tags"][3]["name"] == "Dataloader"

    response = client.get("/api/v1/plugin/?tags=Model&plugin_status=REGISTERED")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1
    plugin = response.json()[0]
    assert plugin["name"] == "dashai-tabular-classification-package"
    assert plugin["tags"][0]["name"] == "DashAI"
    assert plugin["tags"][1]["name"] == "Package"
    assert plugin["tags"][2]["name"] == "Model"
    assert plugin["tags"][3]["name"] == "Dataloader"


def test_delete_plugin(client: TestClient):
    response = client.delete("/api/v1/plugin/1")
    assert response.status_code == 204, response.text
    response = client.delete("/api/v1/plugin/2")
    assert response.status_code == 204, response.text
    response = client.get("/api/v1/plugin")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 0
