"""FastAPI Application module."""
import logging
import pathlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from DashAI.back.api.api_v0.api import api_router_v0
from DashAI.back.api.api_v1.api import api_router_v1
from DashAI.back.api.front_api import router as app_router
from DashAI.back.containers import Container

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _create_path(new_path: str) -> None:
    full_path = pathlib.Path(new_path)
    if not full_path.is_absolute():
        full_path = full_path.expanduser()

    if not full_path.exists():
        logging.info("Creating new path: %s.", str(full_path))
        full_path.mkdir(parents=True)

    else:
        logger.info("Using existant path: %s.", str(full_path))


def create_app() -> FastAPI:
    container = Container()

    _create_path(container.config.provided()["DATASETS_PATH"])
    _create_path(container.config.provided()["RUNS_PATH"])

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
