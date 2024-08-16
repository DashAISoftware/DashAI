import logging
from datetime import datetime
from typing import List

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from DashAI.back.core.enums.plugin_tags import PluginTag
from DashAI.back.core.enums.status import ExplainerStatus, PluginStatus, RunStatus

logger = logging.getLogger(__name__)


Base = declarative_base()


class Dataset(Base):
    __tablename__ = "dataset"
    """
    Table to store all the information about a dataset.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    experiments: Mapped[List["Experiment"]] = relationship()


class Experiment(Base):
    __tablename__ = "experiment"
    """
    Table to store all the information about a model.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("dataset.id"))
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    task_name: Mapped[str] = mapped_column(String, nullable=False)
    input_columns: Mapped[str] = mapped_column(JSON, nullable=False)
    output_columns: Mapped[str] = mapped_column(JSON, nullable=False)
    splits: Mapped[str] = mapped_column(JSON, nullable=False)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
    runs: Mapped[List["Run"]] = relationship()


class Run(Base):
    __tablename__ = "run"
    """
    Table to store all the information about a specific run of a model.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiment.id"))
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
    # model and parameters
    model_name: Mapped[str] = mapped_column(String)
    parameters: Mapped[JSON] = mapped_column(JSON)
    # optimizer
    optimizer_name: Mapped[str] = mapped_column(String)
    optimizer_parameters: Mapped[JSON] = mapped_column(JSON)
    plot_path: Mapped[str] = mapped_column(String, nullable=True)
    # metrics
    train_metrics: Mapped[JSON] = mapped_column(JSON, nullable=True)
    test_metrics: Mapped[JSON] = mapped_column(JSON, nullable=True)
    validation_metrics: Mapped[JSON] = mapped_column(JSON, nullable=True)
    # artifacts
    artifacts: Mapped[str] = mapped_column(JSON, nullable=True)
    # metadata
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, nullable=True)
    run_path: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[Enum] = mapped_column(
        Enum(RunStatus), nullable=False, default=RunStatus.NOT_STARTED
    )
    delivery_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    start_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    def set_status_as_delivered(self) -> None:
        """Update the status of the run to delivered and set delivery_time to now."""
        self.status = RunStatus.DELIVERED
        self.delivery_time = datetime.now()

    def set_status_as_started(self) -> None:
        """Update the status of the run to started and set start_time to now."""
        self.status = RunStatus.STARTED
        self.start_time = datetime.now()

    def set_status_as_finished(self) -> None:
        """Update the status of the run to finished and set end_time to now."""
        self.status = RunStatus.FINISHED
        self.end_time = datetime.now()

    def set_status_as_error(self) -> None:
        """Update the status of the run to error."""
        self.status = RunStatus.ERROR


class Plugin(Base):
    __tablename__ = "plugin"
    """
    Table to store all the information related to a plugin
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    lastest_version: Mapped[str] = mapped_column(String, nullable=False)
    tags: Mapped[List["Tag"]] = relationship(
        back_populates="plugin", cascade="all, delete", lazy="selectin"
    )
    status: Mapped[Enum] = mapped_column(
        Enum(PluginStatus), nullable=False, default=PluginStatus.REGISTERED
    )
    summary: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    description_content_type: Mapped[str] = mapped_column(String, nullable=False)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )


class Tag(Base):
    __tablename__ = "tag"
    """
    Table to store all the tags related to a plugin
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    plugin: Mapped["Plugin"] = relationship(back_populates="tags")
    plugin_id: Mapped[int] = mapped_column(ForeignKey("plugin.id"))
    name: Mapped[Enum] = mapped_column(Enum(PluginTag), nullable=False)


class GlobalExplainer(Base):
    __tablename__ = "global_explainer"
    """
    Table to store all the information about a global explainer.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    run_id: Mapped[int] = mapped_column(nullable=False)
    explainer_name: Mapped[str] = mapped_column(String, nullable=False)
    explanation_path: Mapped[str] = mapped_column(String, nullable=True)
    plot_path: Mapped[str] = mapped_column(String, nullable=True)
    parameters: Mapped[JSON] = mapped_column(JSON)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    status: Mapped[Enum] = mapped_column(
        Enum(ExplainerStatus), nullable=False, default=ExplainerStatus.NOT_STARTED
    )

    def set_status_as_delivered(self) -> None:
        """Update the status of the global explainer to delivered and set delivery_time
        to now."""
        self.status = ExplainerStatus.DELIVERED
        self.delivery_time = datetime.now()

    def set_status_as_started(self) -> None:
        """Update the status of the global explainer to started and set start_time
        to now."""
        self.status = ExplainerStatus.STARTED
        self.start_time = datetime.now()

    def set_status_as_finished(self) -> None:
        """Update the status of the global explainer to finished and set end_time
        to now."""
        self.status = ExplainerStatus.FINISHED
        self.end_time = datetime.now()

    def set_status_as_error(self) -> None:
        """Update the status of the global explainer to error."""
        self.status = ExplainerStatus.ERROR


class LocalExplainer(Base):
    __tablename__ = "local_explainer"
    """
    Table to store all the information about a local explainer.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    run_id: Mapped[int] = mapped_column(nullable=False)
    explainer_name: Mapped[str] = mapped_column(String, nullable=False)
    dataset_id: Mapped[int] = mapped_column(nullable=False)
    explanation_path: Mapped[str] = mapped_column(String, nullable=True)
    plots_path: Mapped[str] = mapped_column(String, nullable=True)
    parameters: Mapped[JSON] = mapped_column(JSON)
    fit_parameters: Mapped[JSON] = mapped_column(JSON)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    status: Mapped[Enum] = mapped_column(
        Enum(ExplainerStatus), nullable=False, default=ExplainerStatus.NOT_STARTED
    )

    def set_status_as_delivered(self) -> None:
        """Update the status of the local explainer to delivered and set delivery_time
        to now.
        """
        self.status = ExplainerStatus.DELIVERED
        self.delivery_time = datetime.now()

    def set_status_as_started(self) -> None:
        """Update the status of the local explainer to started and set start_time
        to now.
        """
        self.status = ExplainerStatus.STARTED
        self.start_time = datetime.now()

    def set_status_as_finished(self) -> None:
        """Update the status of the local explainer to finished and set end_time
        to now.
        """
        self.status = ExplainerStatus.FINISHED
        self.end_time = datetime.now()

    def set_status_as_error(self) -> None:
        """Update the status of the local explainer to error."""
        self.status = ExplainerStatus.ERROR
