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


def _get_plugin_data(plugin_name: str) -> dict:
    response: requests.Response = requests.get(
        f"https://pypi.org/pypi/{plugin_name}/json"
    )

    raw_plugin: json = response.json()["info"]
    raw_plugin["tags"] = [
        {"name": keyword} for keyword in raw_plugin.pop("keywords").split(",")
    ]
    return raw_plugin


def get_plugins_from_pypi() -> List[dict]:
    plugins_names = [
        plugin_name.lower()
        for plugin_name in _get_all_plugins()
        if plugin_name.lower().startswith("dashai") and plugin_name.lower() != "dashai"
    ]
    return [_get_plugin_data(plugin_name) for plugin_name in plugins_names]
