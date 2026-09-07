"""FastAPI Application module."""

import logging
import os
import pathlib
from typing import Literal, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from kink import di

from DashAI.back.api.api_v1.api import api_router_v1
from DashAI.back.api.front_api import router as app_router
from DashAI.back.container import build_container
from DashAI.back.dependencies.config_builder import build_config_dict
from DashAI.back.dependencies.database.backfill import (
    backfill_dataset_counts,
    backfill_explorer_artifacts,
)
from DashAI.back.dependencies.database.migrate import migrate_on_startup
from DashAI.back.plugins.environment import activate_plugins_directory
from DashAI.back.seeds import seed_datasets_if_first_run

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
    enable_seeding: bool = True,
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
        Set the package logging level. It affects all subpackages loggers that
        does not specifies mannualy the logging level, by default "INFO"
    enable_seeding : bool, optional
        Seed bundled datasets on first run, by default True

    Returns
    -------
    FastAPI
        The created FastAPI application.
    """
    # Plugins live in a writable per user directory that has to be importable
    # before the initial components are collected, since building the config
    # dict already enumerates the installed plugin entry points.
    if local_path is not None:
        os.environ["DASHAI_LOCAL_PATH"] = str(
            pathlib.Path(local_path).expanduser().absolute()
        )
    activate_plugins_directory()

    # generating config dict and setting logging level
    config = build_config_dict(
        local_path=local_path,
        logging_level=logging_level,
    )

    logging.getLogger(__package__).setLevel(level=config["LOGGING_LEVEL"])

    logger.debug("App parameters: %s.", str(config))
    logger.debug("Logging level set to %s.", config["LOGGING_LEVEL"])

    logger.debug("Creating local paths.")
    _create_path_if_not_exists(config["LOCAL_PATH"])
    _create_path_if_not_exists(config["DATASETS_PATH"])
    _create_path_if_not_exists(config["IMAGES_PATH"])
    _create_path_if_not_exists(config["EXPLANATIONS_PATH"])
    _create_path_if_not_exists(config["NOTEBOOK_PATH"])
    _create_path_if_not_exists(config["RUNS_PATH"])
    _create_path_if_not_exists(config["DOCUMENTS_PATH"])
    _create_path_if_not_exists(config["DATAFILE_PATH"])

    logger.debug("3. Creating app container and setting up dependency injection.")
    container = build_container(config=config)

    logger.debug("4. Applying database migrations.")
    migrate_on_startup(
        sqlite_file_path=pathlib.Path(config["SQLITE_DB_PATH"]),
    )

    logger.debug("4b. Backfilling dataset row/column counts.")
    backfill_dataset_counts(di["session_factory"])

    # Runs after the container so the explorer classes are registered: old
    # explorations can only be upgraded while their explorer is installed.
    logger.debug("4b-bis. Backfilling explorer render artifacts.")
    backfill_explorer_artifacts(di["session_factory"])

    if enable_seeding:
        logger.debug("4c. Seeding initial datasets if first run.")
        seed_datasets_if_first_run()

    logger.debug("5. Initializing FastAPI application.")
    app = FastAPI(title="dashAI")
    api_v1 = FastAPI(title="dashAI API v1")

    logger.debug("6. Mounting API router.")
    api_v1.include_router(api_router_v1)

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
