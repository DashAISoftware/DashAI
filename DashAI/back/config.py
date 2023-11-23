"""DashAI settings module."""
import os
from typing import Union

from pydantic_settings import BaseSettings

curr_path = os.path.dirname(os.path.realpath(__file__))
dashai_path = os.path.dirname(curr_path)


class Settings(BaseSettings):
    """DashAI base settings for configuring the app operation."""

    API_V0_STR: str = "/api/v0"
    API_V1_STR: str = "/api/v1"

    DASHAI_TEST_MODE: bool = bool(os.getenv("DASHAI_TEST_MODE", False))

    DASHAI_PATH: str = dashai_path

    DB_URL: str = os.path.join(dashai_path, "DashAI.sqlite")
    DB_PASSWORD: Union[str, None] = None

    FRONT_BUILD_PATH: str = os.path.join(dashai_path, "front/build")
    DATASETS_PATH: str = os.path.join(dashai_path, "back/user_datasets")
    RUNS_PATH: str = os.path.join(dashai_path, "back/user_runs")


settings = Settings()
