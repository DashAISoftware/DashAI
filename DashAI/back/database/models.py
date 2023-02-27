from typing import List

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from DashAI.back.models.enums.states import State


class Base(DeclarativeBase):
    pass


class Dataset(Base):
    __tablename__ = "dataset"
    """
    Class to store all the information about a dataset.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    task_name: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    experiments: Mapped[List["Experiment"]] = relationship(cascade="all, delete")
    # TODO: Check If we delete a dataset, should all experiments be deleted?


class Experiment(Base):
    __tablename__ = "experiment"
    """
    Class to store all the information about an experiment.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("dataset.id"))
    task_name: Mapped[str] = mapped_column(String, nullable=False)
    step: Mapped[Enum] = mapped_column(Enum(State), nullable=False)
    models: Mapped[List["Model"]] = relationship(cascade="all, delete")


class Model(Base):
    __tablename__ = "execution"
    """
    Class to store all the information about a specific model.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiment.id"))
    parameters: Mapped[JSON] = mapped_column(JSON)
    model_name: Mapped[str] = mapped_column(String)
    train_results: Mapped[JSON] = mapped_column(JSON)
    test_results: Mapped[JSON] = mapped_column(JSON)
    validation_restuls: Mapped[JSON] = mapped_column(JSON)
    weights_path: Mapped[str] = mapped_column(String)
    trained: Mapped[bool] = mapped_column(bool)
