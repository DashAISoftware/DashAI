import json
import xmlrpc.client
from typing import List

import requests


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
