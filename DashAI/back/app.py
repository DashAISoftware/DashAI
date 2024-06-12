"""FastAPI Application module."""

import logging
import pathlib
from typing import Any, Dict, Literal, Union

import datasets
from beartype import beartype
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from DashAI.back.api.api_v0.api import api_router_v0
from DashAI.back.api.api_v1.api import api_router_v1
from DashAI.back.api.front_api import router as app_router
from DashAI.back.config import DefaultSettings
from DashAI.back.containers import Container
from DashAI.back.plugins_config import get_initial_components

logger = logging.getLogger(__name__)


def _create_path_if_not_exists(new_path: pathlib.Path) -> None:
    """Create a new path if it does not exist."""
    if not new_path.exists():
        logger.debug("Creating new path: %s.", str(new_path))
        new_path.mkdir(parents=True)

    else:
        logger.debug("Using existant path: %s.", str(new_path))


@beartype
def _generate_config_dict(
    local_path: Union[pathlib.Path, None],
    logging_level: Literal["NOTSET", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"],
    container_type: str = "local",
) -> Dict[str, Any]:
    """Generate the initial app configuration.

    The configuration is generated from the DashAI DefaultSettings class, and
    is intended to be used by the configuration provider of the app dependency
    injection container.

    Parameters
    ----------
    local_path : Union[pathlib.Path, None], optional
        Path where DashAI files will be stored. If None, the default
        value of config (~/.DashAI) will be used , by default None.
    logging_level: Literal["NOTSET", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"],
        Global app logging level, by default "INFO".

    Returns
    -------
    Dict[str, Any]
        The configuration dictionary.
    """
    settings = DefaultSettings().model_dump()

    if local_path is not None:
        local_path = pathlib.Path(local_path)
    else:
        local_path = pathlib.Path(settings["LOCAL_PATH"])

    if not local_path.is_absolute():
        local_path = local_path.expanduser().absolute()

    settings["LOCAL_PATH"] = local_path
    settings["SQLITE_DB_PATH"] = local_path / settings["SQLITE_DB_PATH"]
    settings["DATASETS_PATH"] = local_path / settings["DATASETS_PATH"]
    settings["EXPLANATIONS_PATH"] = local_path / settings["EXPLANATIONS_PATH"]
    settings["RUNS_PATH"] = local_path / settings["RUNS_PATH"]
    settings["FRONT_BUILD_PATH"] = pathlib.Path(settings["FRONT_BUILD_PATH"]).absolute()
    settings["LOGGING_LEVEL"] = getattr(logging, logging_level)
    settings["INITIAL_COMPONENTS"] = get_initial_components(container_type)

    return settings


def create_app(
    local_path: Union[pathlib.Path, None] = None,
    logging_level: Literal[
        "NOTSET", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"
    ] = "INFO",
    container_type: str = "local",
) -> FastAPI:
    """Create the main application.

    Steps:
    1. Create the configuration dictionary and sets it as container configuration.
    2. Set the logging level for all subpackages.
    3. Initialize the dependency injection container and wires the subpackages.
    4. Create the local paths where the files are stored.
    5. Initialize the SQlite database.
    6. Initialize the FastAPI application and mount the API routers.

    Parameters
    ----------
    local_path : Union[pathlib.Path, None], optional
        Path where DashAI files will be stored , by default None
    logging_level : Literal['NOTSET', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL']
        Set the package logging level. It affects all subpackages loggers that does
        not specifies mannualy the logging level, by default "INFO"

    Returns
    -------
    FastAPI
        The created FastAPI application.
    """
    # generating config dict and setting logging level
    config = _generate_config_dict(
        local_path=local_path,
        logging_level=logging_level,
        container_type=container_type,
    )
    logging.getLogger(__package__).setLevel(config["LOGGING_LEVEL"])
    datasets.logging.set_verbosity(config["LOGGING_LEVEL"])
    logger.debug("App parameters: %s.", str(config))
    logger.debug("Logging level set to %s.", config["LOGGING_LEVEL"])

    logger.debug("Creating app container and setting up dependency injection.")
    container = Container()
    container.config.from_dict(options=config)

    logger.debug("Creating local paths.")
    _create_path_if_not_exists(container.config.provided()["LOCAL_PATH"])
    _create_path_if_not_exists(container.config.provided()["DATASETS_PATH"])
    _create_path_if_not_exists(container.config.provided()["EXPLANATIONS_PATH"])
    _create_path_if_not_exists(container.config.provided()["RUNS_PATH"])

    logger.debug("Creating database.")
    db = container.db()
    db.create_database()

    logger.debug("Initializing FastAPI application.")
    app = FastAPI(title="DashAI")
    api_v0 = FastAPI(title="DashAI API v0")
    api_v1 = FastAPI(title="DashAI API v1")

    logger.debug("Mounting API routers.")
    api_v0.include_router(api_router_v0)
    api_v1.include_router(api_router_v1)

    app.mount(container.config.provided()["API_V0_STR"], api_v0)
    app.mount(container.config.provided()["API_V1_STR"], api_v1)

    app.include_router(app_router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.container = container
    logger.debug("Application successfully created.")

    return app
