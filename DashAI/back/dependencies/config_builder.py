import logging
import pathlib
from typing import Dict, Literal, Union

from beartype import beartype

from DashAI.back.config import DefaultSettings


@beartype
def build_config_dict(
    local_path: Union[pathlib.Path, None],
    logging_level: Literal["NOTSET", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"],
) -> Dict[str, Union[str, int]]:
    """
    Read configuration settings from a default source and updates them based on a
    provided local path.

    Parameters
    ----------
    local_path : Union[pathlib.Path, None]
        The path to a local directory to be used for configuration settings
        related to file paths. If None, the default values from the source
        configuration are used.
    logging_level : Literal["NOTSET", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]
        The desired logging level for the application.

    Returns
    -------
    dict
        A dictionary containing configuration settings.
        Keys include:
            * 'LOCAL_PATH': The provided local path (or default if None).
            * 'SQLITE_DB_PATH': The path to the SQLite database file
                (relative to LOCAL_PATH).
            * 'DATASETS_PATH': The path to the datasets directory
                (relative to LOCAL_PATH).
            * 'RUNS_PATH': The path to the runs directory (relative to LOCAL_PATH).
            * 'FRONT_BUILD_PATH': The absolute path to the front-end build directory.
            * 'LOGGING_LEVEL': The configured logging level.
    """

    config = DefaultSettings().model_dump()

    if local_path is not None:
        local_path = pathlib.Path(local_path)
    else:
        local_path = pathlib.Path(config["LOCAL_PATH"])

    if not local_path.is_absolute():
        local_path = local_path.expanduser().absolute()

    config["LOCAL_PATH"] = local_path
    config["SQLITE_DB_PATH"] = local_path / config["SQLITE_DB_PATH"]
    config["DATASETS_PATH"] = local_path / config["DATASETS_PATH"]
    config["EXPLANATIONS_PATH"] = local_path / config["EXPLANATIONS_PATH"]
    config["RUNS_PATH"] = local_path / config["RUNS_PATH"]
    config["FRONT_BUILD_PATH"] = pathlib.Path(config["FRONT_BUILD_PATH"]).absolute()
    config["LOGGING_LEVEL"] = getattr(logging, logging_level)

    return config
