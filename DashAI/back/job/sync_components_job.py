import logging

from kink import inject

from DashAI.back.job.base_job import BaseJob
from DashAI.back.plugins.utils import (
    get_available_plugins,
    register_plugin_components,
    unregister_plugin_components,
)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class SyncComponentsJob(BaseJob):
    DESCRIPTION = "Sync consumer ComponentRegistry with installed DashAI plugins"
    ISOLATED = False  # mutates in-process ComponentRegistry singleton
    RESETS_WORKER = True  # worker's DI container must be rebuilt after this runs

    def set_status_as_delivered(self):
        log.debug("Sync components job marked as delivered")

    def set_status_as_error(self):
        log.debug("Sync components job failed")

    @inject
    def get_job_name(self):
        return "Adding/removing plugins"

    @inject
    def run(self):
        from kink import di

        from DashAI.back.initial_components import get_initial_components

        component_registry = di["component_registry"]

        basic_components = set(get_initial_components())
        available_plugins = set(get_available_plugins())

        all_registered = {
            component_registry[c["name"]]["class"]
            for c in component_registry.get_components_by_types()
        }
        registered_plugins = all_registered - basic_components
        to_add = list(available_plugins - registered_plugins)
        to_remove = list(registered_plugins - available_plugins)

        if to_add:
            register_plugin_components(to_add, component_registry)
        if to_remove:
            unregister_plugin_components(to_remove, component_registry)

        return {
            "added": [cls.__name__ for cls in to_add],
            "removed": [cls.__name__ for cls in to_remove],
        }
