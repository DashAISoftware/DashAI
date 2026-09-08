import os

from pydantic_settings import BaseSettings

curr_path = os.path.dirname(os.path.realpath(__file__))
dashai_path = os.path.dirname(curr_path)


class DefaultSettings(BaseSettings):
    """Default settings for DashAI."""

    FRONT_BUILD_PATH: str = os.path.join(dashai_path, "front/build")
    BACK_PATH: str = os.path.join(dashai_path, "back")
    API_V0_STR: str = "/api/v0"
    API_V1_STR: str = "/api/v1"

    LOCAL_PATH: str = "~/.DashAI"
    SQLITE_DB_PATH: str = "db.sqlite"
    DATASETS_PATH: str = "datasets"
    IMAGES_PATH: str = "images"
    RUNS_PATH: str = "runs"
    EXPLANATIONS_PATH: str = "explanations"
    EXPLORATIONS_PATH: str = "explorations"
    DOCUMENTS_PATH: str = "documents"
    RAG_PATH: str = "RAG"
    NOTEBOOK_PATH: str = "notebook"
    DATAFILE_PATH: str = "datafiles"
    CREDENTIALS_KEY_PATH: str = ".credentials_key"
    COMPONENT_PATH: str = "components"
