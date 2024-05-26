import json
import subprocess
import sys
import xmlrpc.client
from typing import List

import requests

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


def available_plugins() -> List[type]:
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


def register_new_plugins(component_registry) -> List[type]:
    """
    Register only new plugins in component registry

    Parameters
    ----------
    component_registry : ComponentRegistry
        The current app component registry

    Returns
    ----------
    List[type]
        A list of plugins' classes that were registered in the component registry
    """
    installed_plugins = []
    new_plugins = []
    for component in component_registry.get_components_by_types():
        installed_plugins.append(component["class"])
    for plugin in available_plugins():
        if plugin not in installed_plugins:
            new_plugins.append(plugin)
            if plugin.__name__ != "TabularClassificationModel":
                component_registry.register_component(plugin)
    return new_plugins


def install_plugin_from_pypi(pypi_plugin_name: str):
    """
    Register only new plugins in component registry

    Parameters
    ----------
    pypi_plugin_name : str
        A string with the name of the plugin in pypi to install

    Raises
    ------
    RuntimeError
        If pip install command fails
    """
    res = subprocess.run(
        ["pip", "install", pypi_plugin_name],
        stderr=subprocess.PIPE,
        text=True,
    )
    if res.returncode != 0:
        errors = [line for line in res.stderr.split("\n") if "ERROR" in line]
        error_string = "\n".join(errors)
        raise RuntimeError(error_string)
