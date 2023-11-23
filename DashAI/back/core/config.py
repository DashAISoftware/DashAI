"""DashAI settings module."""
import os

from pydantic_settings import BaseSettings

curr_path = os.path.dirname(os.path.realpath(__file__))
parent_path = os.path.dirname(curr_path)
dashai_path = os.path.dirname(parent_path)


class Settings(BaseSettings):
    """DashAI base settings for configuring the app operation."""

    API_V0_STR: str = "/api/v0"
    API_V1_STR: str = "/api/v1"

    DASHAI_TEST_MODE: bool = bool(os.getenv("DASHAI_TEST_MODE", False))

    DB_PATH: str = os.path.join(dashai_path, "back/database/DashAI.sqlite")
    FRONT_BUILD_PATH: str = os.path.join(dashai_path, "front/build")
    USER_DATASET_PATH: str = os.path.join(dashai_path, "back/user_datasets")
    USER_RUN_PATH: str = os.path.join(dashai_path, "back/user_runs")

    TEST_DB_PATH: str = "tests/back/database/DashAI.sqlite"
    TEST_USER_DATASET_PATH: str = "tests/back/user_datasets"
    TEST_USER_RUN_PATH: str = "tests/back/user_runs"


settings = Settings()
