import logging
import pathlib
from contextlib import contextmanager
from typing import Callable, ContextManager

from sqlalchemy import create_engine, orm
from sqlalchemy.orm import DeclarativeBase, Session

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


n = 0


class SQLiteDatabase:
    def __init__(self, db_path: pathlib.Path) -> None:
        _db_path = str(db_path)

        if not _db_path.startswith("sqlite:///"):
            db_url = "sqlite:///" + _db_path

        logger.info("Using %s as SQLite path.", db_url)

        self._engine = create_engine(db_url, echo=False)
        self._session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=True,
                bind=self._engine,
            ),
        )

    def create_database(self) -> None:
        Base.metadata.create_all(self._engine)

    def dispose_engine(self) -> None:
        self._engine.dispose()

    @contextmanager
    def session(self) -> Callable[..., ContextManager[Session]]:
        session: Session = self._session_factory()
        global n
        try:
            logger.debug("Generating a new database session.")
            n = n + 1
            print("Generating a new database session.", n)
            yield session
        except Exception:
            logger.exception(
                "Session rollback: An exception was raised while trying to operate "
                "the database."
            )
            print("Exception Raised. Rolling back the session.")
            session.rollback()
            raise
        finally:
            logger.debug("Closing the current session.")
            n = n - 1
            print("Closing the current session.", n)
            session.close()
