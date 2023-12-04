"""FastAPI Application module."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from DashAI.back.api.api_v0.api import api_router_v0
from DashAI.back.api.api_v1.api import api_router_v1
from DashAI.back.api.app import router as app_router
from DashAI.back.containers import Container


def create_app() -> FastAPI:
    container = Container()

    db = container.db()
    db.create_database()

    app = FastAPI()
    app.container = container

    app = FastAPI(title="DashAI")
    api_v0 = FastAPI(title="DashAI API v0")
    api_v1 = FastAPI(title="DashAI API v1")

    api_v0.include_router(api_router_v0)
    api_v1.include_router(api_router_v1)

    app.mount(container.config()["API_V0_STR"], api_v0)
    app.mount(container.config()["API_V1_STR"], api_v1)

    app.include_router(app_router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
