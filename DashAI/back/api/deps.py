"""API dependencies."""
from collections.abc import Generator

from DashAI.back.core import db_session


def get_db() -> Generator:
    try:
        db = db_session()
        yield db
    finally:
        db.close()
