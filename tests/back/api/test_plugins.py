from unittest.mock import Mock, patch

from fastapi.testclient import TestClient


def test_post_plugin(client: TestClient):
    response = client.post(
        "/api/v1/plugin/",
        json=[
            {
                "name": "dashai-svc-plugin",
                "author": "DashAI team",
                "tags": [{"name": "DashAI"}, {"name": "Model"}],
                "summary": "SVC Model Plugin",
                "description": "",
                "description_content_type": "text/markdown",
            }
        ],
    )
    assert response.status_code == 201, response.text
    assert len(response.json()) == 1


def test_refresh_plugins(client: TestClient):
    # Mock to server_proxy
    server_proxy_mock = Mock()
    server_proxy_mock.list_packages.return_value = [
        "image-classification-package",
        "dashai-tabular-classification-package",
        "scikit-dashai-learn",
    ]

    # Mock to request.get
    request_mock = Mock()
    json_return = {
        "info": {
            "author": "DashAI team",
            "keywords": "DashAI,Package,Model,Dataloader",
            "description": "# Description \n",
            "description_content_type": "text/markdown",
            "name": "dashai-tabular-classification-package",
            "summary": "Tabular Classification Package",
        },
    }
    request_mock.json.return_value = json_return

    with patch("xmlrpc.client.ServerProxy") as MockServerProxy:
        MockServerProxy.return_value = server_proxy_mock
        with patch("requests.get", return_value=request_mock):
            response = client.post("/api/v1/plugin/refresh")
            assert response.status_code == 201, response.text
            print(response.json())
            assert len(response.json()) == 1


def test_get_all_plugins(client: TestClient):
    response = client.get("/api/v1/plugin/")
    assert response.status_code == 200, response.text
    plugins = response.json()
    assert plugins[0]["name"] == "dashai-svc-plugin"
    assert plugins[0]["author"] == "DashAI team"
    assert plugins[0]["tags"][0]["name"] == "DashAI"
    assert plugins[0]["tags"][1]["name"] == "Model"
    assert plugins[0]["status"] == 0
    assert plugins[0]["summary"] == "SVC Model Plugin"
    assert plugins[0]["description_content_type"] == "text/markdown"

    assert plugins[1]["name"] == "dashai-tabular-classification-package"
    assert plugins[1]["author"] == "DashAI team"
    assert plugins[1]["tags"][0]["name"] == "DashAI"
    assert plugins[1]["tags"][1]["name"] == "Package"
    assert plugins[1]["tags"][2]["name"] == "Model"
    assert plugins[1]["tags"][3]["name"] == "Dataloader"
    assert plugins[1]["status"] == 0
    assert plugins[1]["summary"] == "Tabular Classification Package"
    assert plugins[1]["description_content_type"] == "text/markdown"


def test_get_plugin(client: TestClient):
    response = client.get("/api/v1/plugin/1")
    assert response.status_code == 200, response.text
    plugin = response.json()
    assert plugin["name"] == "dashai-svc-plugin"
    assert plugin["author"] == "DashAI team"
    assert plugin["tags"][0]["name"] == "DashAI"
    assert plugin["tags"][1]["name"] == "Model"
    assert plugin["status"] == 0
    assert plugin["summary"] == "SVC Model Plugin"
    assert plugin["description_content_type"] == "text/markdown"


def test_get_unexistant_plugin(client: TestClient):
    response = client.get("/api/v1/plugin/31415")
    assert response.status_code == 404, response.text


def test_patch_plugin(client: TestClient):
    response = client.patch("/api/v1/plugin/1", json={"new_status": 1})
    assert response.status_code == 200, response.text

    response = client.get("/api/v1/plugin/1")
    assert response.status_code == 200

    plugin = response.json()
    assert plugin["status"] == 1


def test_delete_plugin(client: TestClient):
    response = client.delete("/api/v1/plugin/1")
    assert response.status_code == 204, response.text
    response = client.delete("/api/v1/plugin/2")
    assert response.status_code == 204, response.text
    response = client.get("/api/v1/plugin")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 0
