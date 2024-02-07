from typing import List


def _get_all_plugins() -> List[str]:
    """
    Make a request to PyPI server to get all package names.

    Returns
    ----------
    List[str]
        A list with the names of all PyPI packages
    """
    return ["dashai-tabular-classification-package", "pytorch", "sklearn"]


def _get_plugin_data(plugin_name: str) -> dict:
    return {
        "name": plugin_name,
        "author": "DashAI team",
        "keywords": ["DashAI", "Package"],
        "summary": "Tabular Classification Package",
        "description": "# **Tabular Classification Package**\n\n## **Modelos**\n\n"
        "Este conjunto de plugins está diseñado específicamente para facilitar la "
        "integración de modelos de Machine Learning en aplicaciones con enfoque en "
        "clasificación tabular. Los modelos incluidos son:\n\n- "
        "**Logistic Regression:** Un modelo efectivo para abordar problemas de "
        "clasificación binaria en el contexto tabular, destacando por su simplicidad "
        "y rendimiento.\n- **SVC (Support Vector Classifier):** Este clasificador "
        "basado en vectores de soporte se adapta bien a conjuntos de datos tabulares "
        "complejos, ofreciendo soluciones robustas tanto para clasificación como para "
        "regresión.\n- **KNN:**\n- **Random Forest:**\n",
        "description_content_type": "text/markdown",
    }


def get_plugins_from_pypi() -> List[dict]:
    plugins_names = filter(lambda name: "dashai" in name, _get_all_plugins())
    return [_get_plugin_data(plugin_name) for plugin_name in plugins_names]
