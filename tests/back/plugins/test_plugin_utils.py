import subprocess
from abc import ABCMeta
from typing import Final
from unittest.mock import Mock, patch

import pytest

from DashAI.back.config_object import ConfigObject
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.plugins.utils import (
    _get_all_plugins,
    _get_plugin_by_name_from_pypi,
    execute_pip_command,
    get_plugins_from_pypi,
    uninstall_plugin,
    unregister_plugin_components,
)


class DummyBaseComponent(ConfigObject, metaclass=ABCMeta):
    """Dummy base class representing a component"""

    TYPE: Final[str] = "Component"


class DummyComponent1(DummyBaseComponent):
    pass


class DummyComponent2(DummyBaseComponent):
    pass


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
            "version": "0.1.0",
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
        "version": "0.1.0",
        "lastest_version": "0.1.0",
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


def test_get_plugin_by_name_from_pypi_with_other_tags():
    # Mockear la solicitud HTTP exitosa
    mock_response = Mock()
    json_return = {
        "info": {
            "author": "DashAI Team",
            "version": "0.1.0",
            "keywords": "DashAI,Package,Model,Dataloader,Other",
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
        "version": "0.1.0",
        "lastest_version": "0.1.0",
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
            "version": "0.1.0",
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
            "version": "0.1.0",
            "lastest_version": "0.1.0",
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
        ["pip", "install", "--no-cache-dir", "dashai-tabular-classification-package"],
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
        ["pip", "uninstall", "-y", "dashai-tabular-classification-package"],
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
    incorrect_pip_action = "incorrect"
    with pytest.raises(
        ValueError, match=f"Pip action {incorrect_pip_action} not supported"
    ):
        execute_pip_command(
            "dashai-tabular-classification-package", incorrect_pip_action
        )


def test_uninstall_plugin():
    entry_points_mock = Mock()
    entry_points_mock.side_effect = [
        [
            Mock(load=lambda: DummyComponent1, name="Plugin1"),
            Mock(load=lambda: DummyComponent2, name="Plugin2"),
        ],
        [Mock(load=lambda: DummyComponent2, name="Plugin2")],
    ]
    execute_pip_command_mock = Mock()
    execute_pip_command_mock.return_value = 0

    with patch("DashAI.back.plugins.utils.entry_points", entry_points_mock), patch(
        "DashAI.back.plugins.utils.execute_pip_command", execute_pip_command_mock
    ):
        uninsalled_plugins = uninstall_plugin("Plugin1")

    assert uninsalled_plugins == {DummyComponent1}
    assert execute_pip_command_mock.call_count == 1
    assert entry_points_mock.call_count == 2
    execute_pip_command_mock.assert_called_once_with("Plugin1", "uninstall")


def test_unregister_plugin_components():
    component_registry = ComponentRegistry(
        initial_components=[DummyComponent1, DummyComponent2]
    )

    unregistered_components = unregister_plugin_components(
        [DummyComponent1], component_registry
    )
    registry_components = component_registry.registry["Component"]

    assert unregistered_components == [DummyComponent1]
    assert len(registry_components) == 1
    assert "DummyComponent1" not in registry_components
    assert "DummyComponent2" in registry_components
