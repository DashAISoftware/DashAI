import logging
import pathlib
from contextlib import contextmanager
from typing import Callable, ContextManager

from sqlalchemy import create_engine, orm
from sqlalchemy.orm import DeclarativeBase, Session

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class SQLiteDatabase:
    def __init__(self, db_path: pathlib.Path) -> None:
        _db_path = str(db_path)

        if not _db_path.startswith("sqlite:///"):
            db_url = "sqlite:///" + _db_path

        logger.info("Using %s as SQLite path.", db_url)

        self._engine = create_engine(db_url, echo=True)
        self._session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
            ),
        )

    def create_database(self) -> None:
        Base.metadata.create_all(self._engine)

    @contextmanager
    def session(self) -> Callable[..., ContextManager[Session]]:
        session: Session = self._session_factory()

        try:
            logger.debug("Generating a new database session.")
            yield session
        except Exception:
            logger.exception(
                "Session rollback: An exception was raised while trying to operate "
                "the database."
            )
            session.rollback()
            raise
        finally:
            logger.debug("Closing the current session.")
            session.close()
