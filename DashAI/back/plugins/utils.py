import json
import subprocess
import sys
import xmlrpc.client
from typing import List

import requests

from DashAI.back.dependencies.registry.component_registry import ComponentRegistry

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def _get_all_plugins() -> List[str]:
    """
    Make a request to PyPI server to get all package names.

    Returns
    ----------
    List[str]
        A list with the names of all PyPI packages
    """

    client = xmlrpc.client.ServerProxy("https://pypi.python.org/pypi")
    # get a list of package names
    packages = client.list_packages()

    return packages


def _get_plugin_by_name_from_pypi(plugin_name: str) -> dict:
    """
    Get a plugin json data from PyPI by its name.

    Parameters
    ----------
    plugin_name : str
        The name of the plugin to get from PyPI

    Returns
    -------
    dict
        A dictionary with the plugin data
    """
    response: requests.Response = requests.get(
        f"https://pypi.org/pypi/{plugin_name}/json"
    )

    raw_plugin: json = response.json()["info"]
    keywords: list = raw_plugin.pop("keywords").split(",")

    keywords = [keyword.strip() for keyword in keywords]

    raw_plugin["tags"] = [{"name": keyword} for keyword in keywords]

    if raw_plugin["author"] is None or raw_plugin["author"] == "":
        raw_plugin["author"] = "Unknown author"

    return raw_plugin


def get_plugins_from_pypi() -> List[dict]:
    """
    Get all DashAI plugins from PyPI.

    Returns
    -------
    List[dict]
        A list with the information of all DashAI plugins, extracted from PyPI.
    """
    plugins_names = [
        plugin_name.lower()
        for plugin_name in _get_all_plugins()
        if plugin_name.lower().startswith("dashai") and plugin_name.lower() != "dashai"
    ]
    return [_get_plugin_by_name_from_pypi(plugin_name) for plugin_name in plugins_names]


def get_available_plugins() -> List[type]:
    """
    Get available DashAI plugins entrypoints

    Returns
    ----------
    List[type]
        A list of plugins' classes
    """
    # Retrieve plugins groups (DashAI components)
    plugins = entry_points(group="dashai.plugins")

    # Look for installed plugins
    plugins_list = []
    for plugin in plugins:
        # Retrieve plugin class
        plugin_class = plugin.load()
        plugins_list.append(plugin_class)

    return plugins_list


def execute_pip_command(pypi_plugin_name: str, pip_action: str) -> None:
    """
    Execute a pip command to install or uninstall a plugin

    Parameters
    ----------
    pypi_plugin_name : str
        A string with the name of the plugin in pypi to install or uninstall

    pip_action : str
        A string with the action to perform. It can be "install" or "uninstall"

    Raises
    ------
    RuntimeError
        If the pip command fails
    """
    if pip_action not in ["install", "uninstall"]:
        raise ValueError(f"Pip action {pip_action} not supported")

    args = ["pip", pip_action, pypi_plugin_name]
    args = args if pip_action == "install" else args.append("-y")

    res = subprocess.run(
        args,
        stderr=subprocess.PIPE,
        text=True,
    )

    if res.returncode != 0:
        errors = [line for line in res.stderr.split("\n") if "ERROR" in line]
        error_string = "\n".join(errors)
        raise RuntimeError(error_string)


def install_plugin(plugin_name: str) -> List[type]:
    """
    Install and register new plugins in component registry

    Parameters
    ----------
    plugin_name : str
        A string with the name of the plugin in pypi to install

    component_registry : ComponentRegistry
        The current app component registry

    """
    pre_installed_plugins: List[type] = get_available_plugins()
    execute_pip_command(plugin_name, "install")
    installed_plugins = set(get_available_plugins()) - set(pre_installed_plugins)
    return installed_plugins


def register_plugin_components(
    plugins: List[type], component_registry: ComponentRegistry
):
    """
    Register the plugins in the component registry

    Parameters
    ----------
    plugins : List[type]
        A list of plugins' classes wanted to be registered in the component
        registry
    component_registry : ComponentRegistry
        The current app component registry
    """
    for plugin in plugins:
        component_registry.register_component(plugin)


def uninstall_plugin(
    plugin_name: str,
) -> List[type]:
    """
    Uninstall an existing plugin and delete it from component registry

    Parameters
    ----------
    plugin_name : str
        A string with the name of the plugin in pypi to install

    component_registry : ComponentRegistry
        The current app component registry

    """
    available_plugins: List[type] = get_available_plugins()
    execute_pip_command(plugin_name, "uninstall")
    uninstalled_components: List[type] = set(available_plugins) - set(
        get_available_plugins()
    )
    return uninstalled_components


def unregister_plugin_components(
    plugins: List[type],
    component_registry: ComponentRegistry,
) -> List[type]:
    """
    Remove from component registry uninstalled plugins

    Parameters
    ----------
    plugins : List[type]
        A list of plugins' classes wanted to be removed from the component registry

    component_registry : ComponentRegistry
        The current app component registry

    Returns
    ----------
    List[type]
        A list of plugins' classes wanted to be removed from the component registry
    """
    for plugin in plugins:
        component_registry.unregister_component(plugin)
    return list(plugins)
