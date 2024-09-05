"""FastAPI Application module."""

import logging
import pathlib
from typing import Literal, Union

import datasets
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from DashAI.back.api.api_v0.api import api_router_v0
from DashAI.back.api.api_v1.api import api_router_v1
from DashAI.back.api.front_api import router as app_router
from DashAI.back.container import build_container
from DashAI.back.dependencies.config_builder import build_config_dict
from DashAI.back.dependencies.database.models import Base

logger = logging.getLogger(__name__)


def _create_path_if_not_exists(new_path: pathlib.Path) -> None:
    """Create a new path if it does not exist."""
    if not new_path.exists():
        logger.debug("Creating new path: %s.", str(new_path))
        new_path.mkdir(parents=True)

    else:
        logger.debug("Using existant path: %s.", str(new_path))


def create_app(
    local_path: Union[pathlib.Path, None] = None,
    logging_level: Literal[
        "NOTSET", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"
    ] = "INFO",
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

    config = build_config_dict(
        local_path=local_path,
        logging_level=logging_level,
    )

    logging.getLogger(__package__).setLevel(level=config["LOGGING_LEVEL"])
    datasets.logging.set_verbosity(int(config["LOGGING_LEVEL"]))

    logger.debug("App parameters: %s.", str(config))
    logger.debug("Logging level set to %s.", config["LOGGING_LEVEL"])

    logger.debug("3. Creating app container and setting up dependency injection.")
    container = build_container(config=config)

    logger.debug("Creating local paths.")
    _create_path_if_not_exists(config["LOCAL_PATH"])
    _create_path_if_not_exists(config["DATASETS_PATH"])
    _create_path_if_not_exists(config["EXPLANATIONS_PATH"])
    _create_path_if_not_exists(config["EXPLORATIONS_PATH"])
    _create_path_if_not_exists(config["RUNS_PATH"])

    logger.debug("5. Creating database.")
    Base.metadata.create_all(bind=container["engine"])

    logger.debug("6. Initializing FastAPI application.")
    app = FastAPI(title="DashAI")
    api_v0 = FastAPI(title="DashAI API v0")
    api_v1 = FastAPI(title="DashAI API v1")

    logger.debug("7. Mounting API routers.")
    api_v0.include_router(api_router_v0)
    api_v1.include_router(api_router_v1)

    app.mount(config["API_V0_STR"], api_v0)
    app.mount(config["API_V1_STR"], api_v1)

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
