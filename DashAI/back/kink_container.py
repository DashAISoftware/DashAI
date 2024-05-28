import logging
import pathlib
from typing import Literal, Union

from kink import di
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from DashAI.back.config import DefaultSettings
from DashAI.back.dataloaders import CSVDataLoader, ImageDataLoader, JSONDataLoader
from DashAI.back.dependencies.database import SQLiteDatabase
from DashAI.back.dependencies.database.sqlite_database import Base
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.job.model_job import ModelJob
from DashAI.back.metrics import F1, Accuracy, Bleu, Precision, Recall
from DashAI.back.models import (
    SVC,
    DecisionTreeClassifier,
    DistilBertTransformer,
    DummyClassifier,
    HistGradientBoostingClassifier,
    KNeighborsClassifier,
    LogisticRegression,
    OpusMtEnESTransformer,
    RandomForestClassifier,
    ViTTransformer,
)
from DashAI.back.tasks import (
    ImageClassificationTask,
    TabularClassificationTask,
    TextClassificationTask,
    TranslationTask,
)

logger = logging.getLogger(__name__)


def create_kink_container(
    local_path: Union[pathlib.Path, None],
    logging_level: Literal["NOTSET", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"],
):
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
    config["RUNS_PATH"] = local_path / config["RUNS_PATH"]
    config["FRONT_BUILD_PATH"] = pathlib.Path(config["FRONT_BUILD_PATH"]).absolute()
    config["LOGGING_LEVEL"] = getattr(logging, logging_level)

    db = SQLiteDatabase(
        db_path=config["SQLITE_DB_PATH"],
        logging_level=config["LOGGING_LEVEL"],
    )

    if not str(config["SQLITE_DB_PATH"]).startswith("sqlite:///"):
        db_url = "sqlite:///" + str(config["SQLITE_DB_PATH"]).replace(
            "db.sqlite", "db_di2.sqlite"
        )  # TODO: BORRAR_ESTO!!!!

    logger.info("Using %s as SQLite path.", db_url)

    engine: Engine = create_engine(
        db_url,
        echo=logging_level == logging.DEBUG,
        connect_args={"check_same_thread": False},
    )

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    component_registry = ComponentRegistry(
        initial_components=[
            # Tasks
            TabularClassificationTask,
            TextClassificationTask,
            TranslationTask,
            ImageClassificationTask,
            # Models
            SVC,
            DecisionTreeClassifier,
            DummyClassifier,
            HistGradientBoostingClassifier,
            KNeighborsClassifier,
            LogisticRegression,
            RandomForestClassifier,
            DistilBertTransformer,
            ViTTransformer,
            OpusMtEnESTransformer,
            # Dataloaders
            CSVDataLoader,
            JSONDataLoader,
            ImageDataLoader,
            # Metrics
            F1,
            Accuracy,
            Precision,
            Recall,
            Bleu,
            # Jobs
            ModelJob,
        ],
    )

    Base.metadata.create_all(bind=engine)

    di["config"] = config

    di[Engine] = engine
    di[sessionmaker] = Session

    def get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    di["get_db"] = get_db

    di[ComponentRegistry] = component_registry

    return di
