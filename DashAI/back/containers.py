import sys

from dependency_injector import containers, providers

from DashAI.back.dataloaders import CSVDataLoader, ImageDataLoader, JSONDataLoader
from DashAI.back.dependencies.database import SQLiteDatabase
from DashAI.back.dependencies.job_queues import SimpleJobQueue
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.job.model_job import ModelJob
from DashAI.back.metrics import F1, Accuracy, Bleu, Precision, Recall

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["DashAI", "tests"],
        auto_wire=True,
    )

    config = providers.Configuration(yaml_files=["DashAI/back/config.yaml"])

    db = providers.Singleton(SQLiteDatabase, db_path=config.SQLITE_DB_PATH)
    job_queue = providers.Singleton(SimpleJobQueue)

    # Retrieve plugins groups (DashAI components)
    plugins = entry_points(group="dashai.plugins")

    plugins_list = [
        # Dataloaders
        CSVDataLoader,
        JSONDataLoader,
        ImageDataLoader,
        # Metrics
        F1,
        Accuracy,
        Precision,
        Recall,
        Bleu,
        # Jobs
        ModelJob,
    ]

    # Look for installed plugins
    for plugin in plugins:
        # Retrieve plugin class
        plugin_class = plugin.load()
        plugins_list.append(plugin_class)

    component_registry = providers.Singleton(
        ComponentRegistry, initial_components=plugins_list
    )
