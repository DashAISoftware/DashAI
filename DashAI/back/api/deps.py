"""API dependencies."""
from collections.abc import Generator

from DashAI.back.dependencies import db_session


def get_db() -> Generator:
    try:
        db = db_session()
        yield db
    finally:
        db.close()
