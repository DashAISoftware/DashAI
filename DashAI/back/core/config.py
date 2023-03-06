from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_PATH: str = "DashAI/back/database/DashAI.sqlite"
    FRONT_BUILD_PATH: str = "DashAI/front/build"
    API_V0_STR: str = "/api/v0"
    API_V1_STR: str = "/api/v1"


settings = Settings()
