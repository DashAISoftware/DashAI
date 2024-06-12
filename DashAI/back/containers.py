from dependency_injector import containers, providers

from DashAI.back.dependencies.database import SQLiteDatabase
from DashAI.back.dependencies.job_queues import SimpleJobQueue
from DashAI.back.dependencies.registry import ComponentRegistry


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["DashAI", "tests"],
        auto_wire=True,
    )

    config = providers.Configuration()

    db = providers.Singleton(
        provides=SQLiteDatabase,
        db_path=config.SQLITE_DB_PATH,
        logging_level=config.LOGGING_LEVEL,
    )
    job_queue = providers.Singleton(SimpleJobQueue)
    component_registry = providers.Singleton(
        ComponentRegistry, initial_components=config.INITIAL_COMPONENTS
    )


class EmptyContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["DashAI", "tests"],
        auto_wire=True,
    )

    config = providers.Configuration()

    db = providers.Singleton(
        provides=SQLiteDatabase,
        db_path=config.SQLITE_DB_PATH,
        logging_level=config.LOGGING_LEVEL,
    )
    job_queue = providers.Singleton(SimpleJobQueue)
    component_registry = providers.Singleton(
        ComponentRegistry,
        initial_components=[],
    )


def get_container(container_type: str = "local"):
    if container_type == "local":
        return Container()
    elif container_type == "empty":
        return EmptyContainer()
    else:
        raise ValueError("Unknown container type")
