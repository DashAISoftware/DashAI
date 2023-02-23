from pydantic import BaseSettings


class Settings(BaseSettings):
    db_path: str = "DashAI/back/database/DashAI.sqlite"

settings = Settings()