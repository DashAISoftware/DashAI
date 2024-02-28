import subprocess
import sys
from typing import List

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
    return [
        "dashai-tabular-classification-package",
        "pytorch",
        "sklearn",
    ]


def _get_plugin_data(plugin_name: str) -> dict:
    raw_plugin = {
        "name": plugin_name,
        "author": "DashAI team",
        "keywords": ["DashAI", "Package"],
        "summary": "Tabular Classification Package",
        "description": "# **Tabular Classification Package**\n\n## **Modelos**\n\n"
        "Este conjunto de plugins está diseñado específicamente para facilitar la "
        "integración de modelos de Machine Learning en aplicaciones con enfoque "
        "en clasificación tabular. Los modelos incluidos son:\n\n- "
        "**Logistic Regression:** Un modelo efectivo para abordar problemas de "
        "clasificación binaria en el contexto tabular, destacando por su "
        "simplicidad y rendimiento.\n- **SVC (Support Vector Classifier):** Este "
        "clasificador basado en vectores de soporte se adapta bien a conjuntos de "
        "datos tabulares complejos, ofreciendo soluciones robustas tanto para "
        "clasificación como para regresión.\n- **KNN:**\n- **Random Forest:**\n",
        "description_content_type": "text/markdown",
    }
    raw_plugin["tags"] = [{"name": keyword} for keyword in raw_plugin.pop("keywords")]
    return raw_plugin


def get_plugins_from_pypi() -> List[dict]:
    plugins_names = filter(lambda name: "dashai" in name, _get_all_plugins())
    return [_get_plugin_data(plugin_name) for plugin_name in plugins_names]


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
