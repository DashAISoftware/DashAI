import importlib
from typing import List

class PluginInterface:

    @staticmethod
    def initialize() -> None:
        """Initialize Model"""

def import_module(name: str) -> PluginInterface:
    return importlib.import_module(name)

def load_plugins(plugins: List[str]) -> None:
    """Load plugins defined in the plugins list"""
    for plugin_name in plugins:
        plugin = import_module(plugin_name)
        plugin.initialize()