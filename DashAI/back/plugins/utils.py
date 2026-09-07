import importlib
import json
import logging
import sys
from typing import TYPE_CHECKING, List

import requests

from DashAI.back.core.enums.plugin_tags import PluginTag
from DashAI.back.plugins.environment import activate_plugins_directory
from DashAI.back.plugins.installer import (
    PluginInstallError,
    install_requirement,
    uninstall_requirement,
)

if TYPE_CHECKING:
    from DashAI.back.dependencies.registry.component_registry import ComponentRegistry

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

logger = logging.getLogger(__name__)

__all__ = [
    "PluginInstallError",
    "get_available_plugins",
    "get_plugin_by_name_from_pypi",
    "get_plugins_from_pypi",
    "install_plugin",
    "register_plugin_components",
    "uninstall_plugin",
    "unregister_plugin_components",
]

_PYPI_SIMPLE_JSON_ACCEPT = "application/vnd.pypi.simple.v1+json"
_PYPI_SIMPLE_URL = "https://pypi.org/simple/"
_REQUEST_TIMEOUT_SECONDS = 15

# Author metadata that identifies a plugin as published by the official
# DashAI account (PyPI user "dashai.nocode"). PyPI does not expose the
# uploader account through its API, so verification is approximated by
# matching the package's declared author metadata.
_VERIFIED_AUTHOR_EMAIL = "dashaisoftware@gmail.com"
_VERIFIED_AUTHOR_NAME = "dashai team"


def _is_verified_author(author: str, author_email: str) -> bool:
    """Check whether a plugin's author metadata matches the official DashAI
    account.

    Parameters
    ----------
    author : str
        The author name declared in the package metadata.
    author_email : str
        The author email declared in the package metadata. PyPI may format
        this as a bare address or as "Name <address>".

    Returns
    -------
    bool
        True if the metadata matches the official DashAI author, else False.
    """
    email = (author_email or "").lower()
    name = (author or "").lower()
    return _VERIFIED_AUTHOR_EMAIL in email or name == _VERIFIED_AUTHOR_NAME


def _get_pypi_project_status(plugin_name: str) -> str:
    """
    Retrieve PyPI project status marker using the Simple API project endpoint.

    Returns
    -------
    str
        One of: "active", "archived", "quarantined" (or other future values).
        Defaults to "active" on missing marker.
        Returns "unknown" on request/parse errors.
    """
    try:
        response = requests.get(
            f"{_PYPI_SIMPLE_URL}{plugin_name}/",
            headers={"Accept": _PYPI_SIMPLE_JSON_ACCEPT},
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        project_status = data.get("project-status") or {}
        return (project_status.get("status") or "active").lower()
    except Exception:
        return "unknown"


def _get_all_plugins() -> List[str]:
    """
    Make a request to PyPI server to get all package names.

    Returns
    ----------
    List[str]
        A list with the names of all PyPI packages
    """

    # Define the URL for PyPI Simple API
    url = "https://pypi.org/simple/"

    # Set the appropriate headers to request JSON format
    headers = {"Accept": "application/vnd.pypi.simple.v1+json"}

    # Send a GET request to the API
    response = requests.get(url, headers=headers, timeout=_REQUEST_TIMEOUT_SECONDS)

    # Check for a successful response
    if response.status_code == 200:
        data = response.json()
        projects = data.get("projects", [])
        packages = [project["name"] for project in projects]

    else:
        print(f"Failed to retrieve packages. Status code: {response.status_code}")
        packages = []

    return packages


def get_plugin_by_name_from_pypi(plugin_name: str) -> dict:
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

    Raises
    ------
    ValueError
        When the plugin is not found or the response is invalid
    """
    response: requests.Response = requests.get(
        f"https://pypi.org/pypi/{plugin_name}/json",
        timeout=_REQUEST_TIMEOUT_SECONDS,
    )

    response_data = response.json()
    try:
        raw_plugin: json = response_data["info"]
    except KeyError as err:
        raise ValueError(
            f"No se pudo obtener la información del plugin '{plugin_name}'."
            f"Respuesta del servidor: {str(response_data)}."
        ) from err

    try:
        keywords: list = raw_plugin.pop("keywords", "").split(",")
        keywords = [keyword.strip() for keyword in keywords if keyword.strip()]
    except AttributeError:
        keywords = []

    # remove keywords that are not tags
    posible_tags = [tag.value for tag in PluginTag]
    keywords = [keyword for keyword in keywords if keyword in posible_tags]

    raw_plugin["tags"] = [{"name": keyword} for keyword in keywords]

    raw_plugin["verified"] = _is_verified_author(
        raw_plugin.get("author"), raw_plugin.get("author_email")
    )

    if raw_plugin["author"] is None or raw_plugin["author"] == "":
        raw_plugin["author"] = "Unknown author"

    raw_plugin["installed_version"] = raw_plugin["version"]
    raw_plugin["lastest_version"] = raw_plugin["version"]

    del raw_plugin["version"]

    return raw_plugin


def get_plugins_from_pypi() -> List[dict]:
    """
    Get all DashAI plugins from PyPI.

    Returns
    -------
    List[dict]
        A list with the information of all DashAI plugins, extracted from PyPI.
    """
    plugins = []
    plugins_names = [
        plugin_name.lower()
        for plugin_name in _get_all_plugins()
        if plugin_name.lower().startswith("dashai") and plugin_name.lower() != "dashai"
    ]

    for plugin_name in plugins_names:
        try:
            status = _get_pypi_project_status(plugin_name)
            if status == "archived":
                continue

            plugin_info = get_plugin_by_name_from_pypi(plugin_name)
            plugins.append(plugin_info)
        except (ValueError, requests.RequestException) as e:
            print(f"Error al obtener información del plugin {plugin_name}: {str(e)}")
            continue

    return plugins


def get_available_plugins() -> List[type]:
    """
    Get available DashAI plugins entrypoints

    The plugins directory is activated first, so plugins installed while the
    app is running are discovered without restarting it. A plugin that fails to
    import is skipped instead of taking the whole registry down with it.

    Returns
    ----------
    List[type]
        A list of plugins' classes
    """
    activate_plugins_directory()
    importlib.invalidate_caches()

    # Retrieve plugins groups (DashAI components)
    plugins = entry_points(group="dashai.plugins")

    # Look for installed plugins
    plugins_list = []
    for plugin in plugins:
        # Retrieve plugin class
        try:
            plugin_class = plugin.load()
        except Exception:
            logger.exception("Could not load the plugin entry point %s", plugin)
            continue
        if plugin_class in plugins_list:
            continue
        plugins_list.append(plugin_class)

    return plugins_list


def install_plugin(plugin_name: str) -> List[type]:
    """
    Install and register new plugins in component registry

    Parameters
    ----------
    plugin_name : str
        A string with the name of the plugin in pypi to install

    Returns
    ----------
    List[type]
        The plugin classes that became available after the installation.

    Raises
    ----------
    PluginInstallError
        If the plugin distribution could not be installed.
    """
    pre_installed_plugins: List[type] = get_available_plugins()
    install_requirement(plugin_name)
    installed_plugins = set(get_available_plugins()) - set(pre_installed_plugins)
    return installed_plugins


def register_plugin_components(
    plugins: List[type], component_registry: "ComponentRegistry"
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
        A string with the name of the plugin in pypi to uninstall

    Returns
    ----------
    List[type]
        The plugin classes that stopped being available after the removal.
    """
    available_plugins: List[type] = get_available_plugins()
    uninstall_requirement(plugin_name)
    uninstalled_components: List[type] = set(available_plugins) - set(
        get_available_plugins()
    )
    return uninstalled_components


def unregister_plugin_components(
    plugins: List[type],
    component_registry: "ComponentRegistry",
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
