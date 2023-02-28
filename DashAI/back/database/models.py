from typing import List

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from DashAI.back.models.enums.states import State


class Base(DeclarativeBase):
    pass


class Dataset(Base):
    __tablename__ = "dataset"
    """
    Table to store all the information about a dataset.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    task_name: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    experiments: Mapped[List["Experiment"]] = relationship()


class Experiment(Base):
    __tablename__ = "experiment"
    """
    Table to store all the information about a model.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("dataset.id"))
    task_name: Mapped[str] = mapped_column(String, nullable=False)
    step: Mapped[Enum] = mapped_column(Enum(State), nullable=False)
    models: Mapped[List["Model"]] = relationship()


class Model(Base):
    __tablename__ = "model"
    """
    Table to store all the information about a model.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiment.id"))
    parameters: Mapped[JSON] = mapped_column(JSON)
    model_name: Mapped[str] = mapped_column(String)
    run: Mapped["Run"] = relationship(back_populates="run", cascade="all, delete")


class Run(Base):
    __tablename__ = "run"
    """
    Table to store all the information about a specific run of a model.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("model.id"))
    train_results: Mapped[JSON] = mapped_column(JSON)
    test_results: Mapped[JSON] = mapped_column(JSON)
    validation_restuls: Mapped[JSON] = mapped_column(JSON)
    weights_path: Mapped[str] = mapped_column(String)
    trained: Mapped[Boolean] = mapped_column(Boolean)
    model: Mapped["Model"] = relationship(back_populates="model", cascade="all, delete")
