"""FastAPI Application module."""
import logging
import pathlib
from typing import Any, Dict, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from DashAI.back.api.api_v0.api import api_router_v0
from DashAI.back.api.api_v1.api import api_router_v1
from DashAI.back.api.front_api import router as app_router
from DashAI.back.config import DefaultSettings
from DashAI.back.containers import Container

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _create_path_if_not_exists(new_path: str) -> None:
    """Create a new path if it does not exist."""
    if not new_path.exists():
        logging.info("Creating new path: %s.", str(new_path))
        new_path.mkdir(parents=True)

    else:
        logger.info("Using existant path: %s.", str(new_path))


def _generate_config_dict(
    local_path: Union[pathlib.Path, None] = None
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
    settings["RUNS_PATH"] = local_path / settings["RUNS_PATH"]
    settings["FRONT_BUILD_PATH"] = pathlib.Path(settings["FRONT_BUILD_PATH"]).absolute()

    return settings


def create_app(local_path: Union[pathlib.Path, None] = None) -> FastAPI:
    container = Container()
    config = _generate_config_dict(local_path=local_path)
    container.config.from_dict(config)

    _create_path_if_not_exists(container.config.provided()["DATASETS_PATH"])
    _create_path_if_not_exists(container.config.provided()["RUNS_PATH"])

    db = container.db()
    db.create_database()

    app = FastAPI(title="DashAI")
    api_v0 = FastAPI(title="DashAI API v0")
    api_v1 = FastAPI(title="DashAI API v1")

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

    return app
