from unittest.mock import Mock, patch

from DashAI.back.plugins.utils import (
    _get_all_plugins,
    _get_plugin_data,
    get_plugins_from_pypi,
)


def test_get_all_plugins_with_proxy():
    # Mockear la creación del cliente proxy y su método list_packages
    with patch("xmlrpc.client.ServerProxy") as MockServerProxy:
        mock_client = Mock()
        mock_client.list_packages.return_value = [
            "DashAI",
            "dashai-tabular-classification-package",
            "scikit-learn",
        ]
        MockServerProxy.return_value = mock_client

        # Llamar a la función que deseas probar
        packages = _get_all_plugins()

    assert packages == [
        "DashAI",
        "dashai-tabular-classification-package",
        "scikit-learn",
    ]


def test_get_plugin_data_success():
    # Mockear la solicitud HTTP exitosa
    mock_response = Mock()
    json_return = {
        "info": {
            "author_email": "dashai <dashaisoftware@gmail.com>",
            "keywords": "dashai,image classification,package,pytorch,torchvision",
            "description": "# Description \n",
            "description_content_type": "text/markdown",
            "name": "tabular-classification-package",
            "summary": "Tabular Classification Package",
        },
    }
    mock_response.json.return_value = json_return
    with patch("requests.get", return_value=mock_response):
        plugin_data = _get_plugin_data("test_plugin")

    assert plugin_data == {
        "author_email": "dashai <dashaisoftware@gmail.com>",
        "tags": [
            {"name": "dashai"},
            {"name": "image classification"},
            {"name": "package"},
            {"name": "pytorch"},
            {"name": "torchvision"},
        ],
        "description": "# Description \n",
        "description_content_type": "text/markdown",
        "name": "tabular-classification-package",
        "summary": "Tabular Classification Package",
    }


def test_get_plugins_from_pypi():
    # Mockear la creación del cliente proxy y su método list_packages
    with patch("xmlrpc.client.ServerProxy") as MockServerProxy:
        server_proxy_mock = Mock()
        server_proxy_mock.list_packages.return_value = [
            "image-classification-package",
            "dashai-tabular-classification-package",
            "scikit-dashai-learn",
        ]
        MockServerProxy.return_value = server_proxy_mock

        # Mockear la solicitud HTTP exitosa
        request_mock = Mock()
        json_return = {
            "info": {
                "author_email": "dashai <dashaisoftware@gmail.com>",
                "keywords": "dashai,package",
                "description": "# Description \n",
                "description_content_type": "text/markdown",
                "name": "dashai-tabular-classification-package",
                "summary": "Tabular Classification Package",
            },
        }
        request_mock.json.return_value = json_return
        with patch("requests.get", return_value=request_mock):
            plugins = get_plugins_from_pypi()

    assert plugins == [
        {
            "author_email": "dashai <dashaisoftware@gmail.com>",
            "tags": [
                {"name": "dashai"},
                {"name": "package"},
            ],
            "description": "# Description \n",
            "description_content_type": "text/markdown",
            "name": "dashai-tabular-classification-package",
            "summary": "Tabular Classification Package",
        }
    ]
