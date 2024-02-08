from pydantic_settings import BaseSettings


class DefaultSettings(BaseSettings):
    """Default settings for DashAI."""

    FRONT_BUILD_PATH: str = "DashAI/front/build"
    API_V0_STR: str = "/api/v0"
    API_V1_STR: str = "/api/v1"

    LOCAL_PATH: str = "~/.DashAI"
    SQLITE_DB_PATH: str = "db.sqlite"
    DATASETS_PATH: str = "datasets"
    RUNS_PATH: str = "runs"
