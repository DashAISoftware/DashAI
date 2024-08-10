import subprocess
from unittest.mock import Mock, patch

import pytest

from DashAI.back.plugins.utils import (
    _get_all_plugins,
    _get_plugin_by_name_from_pypi,
    execute_pip_command,
    get_plugins_from_pypi,
)


def test_get_all_plugins_with_proxy():
    mock_client = Mock()
    mock_client.list_packages.return_value = [
        "DashAI",
        "dashai-tabular-classification-package",
        "scikit-learn",
    ]
    with patch("xmlrpc.client.ServerProxy") as MockServerProxy:
        MockServerProxy.return_value = mock_client
        packages = _get_all_plugins()

    assert packages == [
        "DashAI",
        "dashai-tabular-classification-package",
        "scikit-learn",
    ]


def test_get_plugin_by_name_from_pypi():
    # Mockear la solicitud HTTP exitosa
    mock_response = Mock()
    json_return = {
        "info": {
            "author": "DashAI Team",
            "keywords": "DashAI,Package,Model,Dataloader",
            "description": "# Description \n",
            "description_content_type": "text/markdown",
            "name": "tabular-classification-package",
            "summary": "Tabular Classification Package",
        },
    }
    mock_response.json.return_value = json_return
    with patch("requests.get", return_value=mock_response):
        plugin_data = _get_plugin_by_name_from_pypi("test_plugin")

    assert plugin_data == {
        "author": "DashAI Team",
        "tags": [
            {"name": "DashAI"},
            {"name": "Package"},
            {"name": "Model"},
            {"name": "Dataloader"},
        ],
        "description": "# Description \n",
        "description_content_type": "text/markdown",
        "name": "tabular-classification-package",
        "summary": "Tabular Classification Package",
    }


def test_get_plugins_from_pypi():
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
            "author": "DashAI Team",
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
            plugins = get_plugins_from_pypi()

    assert plugins == [
        {
            "author": "DashAI Team",
            "tags": [
                {"name": "DashAI"},
                {"name": "Package"},
                {"name": "Model"},
                {"name": "Dataloader"},
            ],
            "description": "# Description \n",
            "description_content_type": "text/markdown",
            "name": "dashai-tabular-classification-package",
            "summary": "Tabular Classification Package",
        }
    ]


def test_execute_pip_install_command():
    subprocess_mock = Mock()
    subprocess_mock.returncode = 0
    with patch("subprocess.run", return_value=subprocess_mock) as mock_run:
        result = execute_pip_command("dashai-tabular-classification-package", "install")

    assert result == 0
    mock_run.assert_called_once_with(
        ["pip", "install", "dashai-tabular-classification-package"],
        stderr=subprocess.PIPE,
        text=True,
    )


def test_execute_pip_uninstall_command():
    subprocess_mock = Mock()
    subprocess_mock.returncode = 0
    with patch("subprocess.run", return_value=subprocess_mock) as mock_run:
        result = execute_pip_command(
            "dashai-tabular-classification-package", "uninstall"
        )

    assert result == 0
    mock_run.assert_called_once_with(
        ["pip", "uninstall", "dashai-tabular-classification-package", "-y"],
        stderr=subprocess.PIPE,
        text=True,
    )


def test_error_execute_pip_command():
    subprocess_mock = Mock()
    subprocess_mock.returncode = 1
    subprocess_mock.stderr = "ERROR: ...\nERROR: ..."
    with patch("subprocess.run", return_value=subprocess_mock), pytest.raises(
        RuntimeError, match="ERROR: ...\nERROR: ..."
    ):
        execute_pip_command("dashai-tabular-classification-package", "install")


def test_execute_incorrect_pip_command():
    with pytest.raises(ValueError, match="Pip action not supported"):
        execute_pip_command("dashai-tabular-classification-package", "incorrect")
