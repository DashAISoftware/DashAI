"""SQLite database module, implemented to be compatible with dependency injection."""

import logging
from typing import Dict, Tuple

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


def setup_sqlite_db(config: Dict[str, str]) -> Tuple[Engine, sessionmaker]:
    """
    Sets up a SQLAlchemy engine and session factory for a SQLite database.

    Parameters
    ----------
    config : Dict[str, str]
        A dictionary containing configuration options.
        Must contain the following keys:
            * 'SQLITE_DB_PATH': The path to the SQLite database file.
            * 'LOGGING_LEVEL' (optional): The logging level (e.g., 'DEBUG', 'INFO').
                Defaults to 'INFO' if not provided.

    Returns
    -------
    tuple
        A tuple containing two elements:
            * engine (sqlalchemy.engine.Engine): The created SQLAlchemy engine.
            * session_factory (sqlalchemy.orm.sessionmaker): A session factory
                for creating database sessions.
    """

    if not str(config["SQLITE_DB_PATH"]).startswith("sqlite:///"):
        db_url = "sqlite:///" + str(config["SQLITE_DB_PATH"])

    logger.info("Using %s as SQLite path.", db_url)

    engine: Engine = create_engine(
        db_url,
        echo=config["LOGGING_LEVEL"] == logging.DEBUG,
        connect_args={"check_same_thread": False},
    )

    session_factory = sessionmaker(
        autocommit=False,
        autoflush=True,
        bind=engine,
    )

    return engine, session_factory
