import logging
import pathlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.core.enums.plugin_tags import PluginTag
from DashAI.back.core.enums.status import (
    ConverterStatus,
    DatafileStatus,
    DatasetStatus,
    ExplainerStatus,
    ExplorerStatus,
    NodeRunStatus,
    PipelineRunStatus,
    PluginStatus,
    PredictionStatus,
    ReportStatus,
    RunStatus,
)

logger = logging.getLogger(__name__)


naming_convention = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)


class Folder(Base):
    __tablename__ = "folder"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )

    datasets: Mapped[List["Dataset"]] = relationship(back_populates="folder")


class Dataset(Base):
    __tablename__ = "dataset"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    huey_id: Mapped[str] = mapped_column(String, nullable=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=True)
    total_columns: Mapped[int] = mapped_column(Integer, nullable=True)
    folder_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("folder.id", ondelete="SET NULL"), nullable=True
    )

    notebooks: Mapped[List["Notebook"]] = relationship(
        cascade="all, delete-orphan", back_populates="dataset"
    )
    model_sessions: Mapped[List["ModelSession"]] = relationship(
        "ModelSession", cascade="all, delete-orphan", back_populates="dataset"
    )
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction", cascade="all, delete-orphan", back_populates="dataset"
    )
    folder: Mapped[Optional["Folder"]] = relationship(back_populates="datasets")

    status: Mapped[Enum] = mapped_column(
        Enum(DatasetStatus), nullable=False, default=DatasetStatus.NOT_STARTED
    )

    def set_status_as_delivered(self) -> None:
        """
        Update the status of the dataset to delivered and set last_modified to now.
        """
        self.status = DatasetStatus.DELIVERED
        self.last_modified = datetime.now()

    def set_status_as_started(self) -> None:
        """
        Update the status of the dataset to started and set created to now.

        Unlike ``Run`` or ``Explorer``, this table has no ``start_time`` /
        ``end_time`` columns, so there is nothing to stamp beyond the timestamps
        it does declare. Assigning them anyway only set an attribute on the
        instance that was dropped at commit and read back as missing.
        """
        self.status = DatasetStatus.STARTED
        self.created = datetime.now()

    def set_status_as_finished(self) -> None:
        """
        Update the status of the dataset to finished and set last_modified to now.
        """
        self.status = DatasetStatus.FINISHED
        self.last_modified = datetime.now()

    def set_status_as_error(self) -> None:
        """
        Update the status of the dataset to error.
        """
        self.status = DatasetStatus.ERROR


class ModelSession(Base):
    __tablename__ = "model_session"
    """
    Table to store all the information about a model session.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("dataset.id"))
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    task_name: Mapped[str] = mapped_column(String, nullable=False)
    input_columns: Mapped[str] = mapped_column(JSON, nullable=False)
    output_columns: Mapped[str] = mapped_column(JSON, nullable=False)

    # Metrics per split
    train_metrics: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    validation_metrics: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    test_metrics: Mapped[list[str]] = mapped_column(JSON, nullable=True)

    evaluation_strategy: Mapped[str] = mapped_column(String, nullable=False)
    splits: Mapped[str] = mapped_column(JSON, nullable=False)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
    runs: Mapped[List["Run"]] = relationship(
        "Run", cascade="all, delete-orphan", back_populates="model_session"
    )
    dataset = relationship("Dataset", back_populates="model_sessions")


class Run(Base):
    __tablename__ = "run"
    """
    Table to store all the information about a specific run of a model.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    model_session_id: Mapped[int] = mapped_column(
        ForeignKey("model_session.id", ondelete="CASCADE")
    )
    huey_id: Mapped[str] = mapped_column(String, nullable=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
    # model and parameters
    model_name: Mapped[str] = mapped_column(String)
    parameters: Mapped[JSON] = mapped_column(JSON)
    split_indexes: Mapped[str] = mapped_column(JSON, nullable=True)
    # optimizer
    optimizer_name: Mapped[str] = mapped_column(String)
    optimizer_parameters: Mapped[JSON] = mapped_column(JSON)
    nested: Mapped[JSON] = mapped_column(JSON, nullable=True)
    plot_history_path: Mapped[str] = mapped_column(String, nullable=True)
    plot_slice_path: Mapped[str] = mapped_column(String, nullable=True)
    plot_contour_path: Mapped[str] = mapped_column(String, nullable=True)
    plot_importance_path: Mapped[str] = mapped_column(String, nullable=True)
    # goal metrics
    goal_metric: Mapped[str] = mapped_column(String)
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
    model_session = relationship("ModelSession", back_populates="runs")
    predictions = relationship(
        "Prediction", cascade="all, delete-orphan", back_populates="run"
    )
    metrics = relationship("Metric", cascade="all, delete-orphan", back_populates="run")

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


class Prediction(Base):
    __tablename__ = "prediction"
    """
    Table to store all the information about a specific prediction.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id", ondelete="CASCADE"))
    dataset_id: Mapped[int] = mapped_column(ForeignKey("dataset.id"), nullable=True)
    split: Mapped[str] = mapped_column(String, nullable=True)
    huey_id: Mapped[str] = mapped_column(String, nullable=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
    results_path: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[Enum] = mapped_column(
        Enum(PredictionStatus), nullable=False, default=PredictionStatus.NOT_STARTED
    )
    delivery_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    start_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    # Relationships
    run: Mapped["Run"] = relationship("Run", back_populates="predictions")
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="predictions")

    def set_status_as_delivered(self) -> None:
        """Update the status of the prediction to delivered and set
        delivery_time to now."""
        self.status = PredictionStatus.DELIVERED
        self.delivery_time = datetime.now()

    def set_status_as_started(self) -> None:
        """Update the status of the prediction to started and set start_time to now."""
        self.status = PredictionStatus.STARTED
        self.start_time = datetime.now()

    def set_status_as_finished(self) -> None:
        """Update the status of the prediction to finished and set end_time to now."""
        self.status = PredictionStatus.FINISHED
        self.end_time = datetime.now()

    def set_status_as_error(self) -> None:
        """Update the status of the prediction to error."""
        self.status = PredictionStatus.ERROR


class Metric(Base):
    __tablename__ = "metric"
    """
    Table to store all the information related to a metric
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("run.id", ondelete="CASCADE"), index=True
    )
    split: Mapped[SplitEnum] = mapped_column(Enum(SplitEnum), nullable=False)
    level: Mapped[LevelEnum] = mapped_column(Enum(LevelEnum), nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    std_value: Mapped[float] = mapped_column(Float, nullable=True)
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    fold_index: Mapped[int] = mapped_column(Integer, nullable=True)
    inner_fold_index: Mapped[int] = mapped_column(Integer, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, index=True
    )

    # Relationships
    run: Mapped["Run"] = relationship("Run", back_populates="metrics")


class Plugin(Base):
    __tablename__ = "plugin"
    """
    Table to store all the information related to a plugin
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    installed_version: Mapped[str] = mapped_column(String, nullable=False)
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
    name: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    run_id: Mapped[int] = mapped_column(nullable=False)
    huey_id: Mapped[str] = mapped_column(String, nullable=True)
    explainer_name: Mapped[str] = mapped_column(String, nullable=False)
    explanation_path: Mapped[str] = mapped_column(String, nullable=True)
    plot_path: Mapped[str] = mapped_column(String, nullable=True)
    plot_overrides: Mapped[JSON] = mapped_column(JSON, nullable=True)
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


class Report(Base):
    __tablename__ = "report"
    """
    Table to store an evaluation report of a run. One row covers every
    evaluation partition; the artifacts carry one group per partition.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("run.id", ondelete="CASCADE"), nullable=False
    )
    huey_id: Mapped[str] = mapped_column(String, nullable=True)
    report_name: Mapped[str] = mapped_column(String, nullable=False)
    parameters: Mapped[JSON] = mapped_column(JSON, nullable=True)
    artifacts_path: Mapped[str] = mapped_column(String, nullable=True)
    plot_overrides: Mapped[JSON] = mapped_column(JSON, nullable=True)
    created: Mapped[DateTime] = mapped_column(
        DateTime, default=datetime.now, nullable=True
    )
    status: Mapped[Enum] = mapped_column(
        Enum(ReportStatus), nullable=False, default=ReportStatus.NOT_STARTED
    )

    def set_status_as_delivered(self) -> None:
        """Update the status of the report to delivered."""
        self.status = ReportStatus.DELIVERED

    def set_status_as_started(self) -> None:
        """Update the status of the report to started."""
        self.status = ReportStatus.STARTED

    def set_status_as_finished(self) -> None:
        """Update the status of the report to finished."""
        self.status = ReportStatus.FINISHED

    def set_status_as_error(self) -> None:
        """Update the status of the report to error."""
        self.status = ReportStatus.ERROR


class LocalExplainer(Base):
    __tablename__ = "local_explainer"
    """
    Table to store all the information about a local explainer.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    run_id: Mapped[int] = mapped_column(nullable=False)
    huey_id: Mapped[str] = mapped_column(String, nullable=True)
    explainer_name: Mapped[str] = mapped_column(String, nullable=False)
    dataset_id: Mapped[int] = mapped_column(nullable=False)
    explanation_path: Mapped[str] = mapped_column(String, nullable=True)
    plots_path: Mapped[str] = mapped_column(String, nullable=True)
    plot_overrides: Mapped[JSON] = mapped_column(JSON, nullable=True)
    input_dataset_path: Mapped[str] = mapped_column(String, nullable=True)
    parameters: Mapped[JSON] = mapped_column(JSON)
    fit_parameters: Mapped[JSON] = mapped_column(JSON)
    scope: Mapped[JSON] = mapped_column(JSON)
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


class GenerativeProcess(Base):
    __tablename__ = "generative_process"
    """
    Table to store all the information about a specific process of a generative model.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
    # metadata
    session_id: Mapped[int] = mapped_column(
        ForeignKey("generative_session.id", ondelete="CASCADE")
    )
    status: Mapped[Enum] = mapped_column(
        Enum(RunStatus), nullable=False, default=RunStatus.NOT_STARTED
    )
    delivery_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    start_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    session = relationship("GenerativeSession", back_populates="processes")
    input = relationship(
        "ProcessData",
        primaryjoin=(
            "and_("
            "GenerativeProcess.id == ProcessData.process_id, "
            "ProcessData.is_input == True)"
        ),
        lazy="selectin",
        order_by="ProcessData.id",
        overlaps="output,process",
    )
    output = relationship(
        "ProcessData",
        primaryjoin=(
            "and_("
            "GenerativeProcess.id == ProcessData.process_id, "
            "ProcessData.is_input == False)"
        ),
        lazy="selectin",
        order_by="ProcessData.id",
        overlaps="input,process",
    )

    def set_status_as_delivered(self) -> None:
        """
        Update the status of the run to delivered and set delivery_time
        to now.
        """
        self.status = RunStatus.DELIVERED
        self.delivery_time = datetime.now()

    def set_status_as_started(self) -> None:
        """Update the status of the process to started and set start_time to now."""
        self.status = RunStatus.STARTED
        self.start_time = datetime.now()

    def set_status_as_finished(self) -> None:
        """Update the status of the process to finished and set end_time to now."""
        self.status = RunStatus.FINISHED
        self.end_time = datetime.now()

    def set_status_as_error(self) -> None:
        """Update the status of the process to error."""
        self.status = RunStatus.ERROR


class ProcessData(Base):
    __tablename__ = "process_data"
    """
    Base table to store the data of a generative process.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[str] = mapped_column(String, nullable=False)
    data_type: Mapped[str] = mapped_column(String, nullable=False)
    process_id: Mapped[int] = mapped_column(
        ForeignKey("generative_process.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_input: Mapped[bool] = mapped_column(Boolean, default=True)

    process = relationship(
        "GenerativeProcess", foreign_keys=[process_id], overlaps="input,output"
    )


class GenerativeSession(Base):
    __tablename__ = "generative_session"
    """
    Table to store all the information about a specific session of a generative model.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
    # task name
    task_name: Mapped[str] = mapped_column(String, nullable=False)
    # model and parameters
    model_name: Mapped[str] = mapped_column(String)
    parameters: Mapped[JSON] = mapped_column(JSON)
    # metadata
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)

    # Relationship with GenerativeSessionParameterHistory
    parameters_history: Mapped[List["GenerativeSessionParameterHistory"]] = (
        relationship(
            "GenerativeSessionParameterHistory",
            cascade="all, delete-orphan",
            back_populates="session",
        )
    )

    # Relationship with GenerativeProcess
    processes: Mapped[List["GenerativeProcess"]] = relationship(
        "GenerativeProcess", cascade="all, delete-orphan", back_populates="session"
    )

    # Relationship with RAGDocumentPipelineSessionLink
    pipeline_links: Mapped[List["RAGDocumentPipelineSessionLink"]] = relationship(
        back_populates="session"
    )


class Pipeline(Base):
    __tablename__ = "pipeline"
    """
    Table to store all the information about a pipeline.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    steps: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    edges: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    # Dead columns, kept for compatibility. Results live in NodeArtifact now,
    # keyed by a PROVIDES key rather than by node type. They are still read by
    # the pipelines endpoints (dataexploration/results, filter_models) and by
    # the results view in the front, so dropping them is a change to those.
    exploration: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    train: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    prediction: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)

    pipeline_runs: Mapped[List["PipelineRun"]] = relationship(
        "PipelineRun", cascade="all, delete-orphan", back_populates="pipeline"
    )


class PipelineRun(Base):
    __tablename__ = "pipeline_run"
    """
    Table to store one execution of a pipeline.

    The definition of a graph lives in ``Pipeline`` and changes as the user
    edits it; a run freezes the ``steps`` and ``edges`` it actually executed,
    so a past execution stays readable after the pipeline it came from was
    rewritten.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    pipeline_id: Mapped[int] = mapped_column(
        ForeignKey("pipeline.id", ondelete="CASCADE"), nullable=False
    )
    steps: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    edges: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    delivery_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    start_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    status: Mapped[Enum] = mapped_column(
        Enum(PipelineRunStatus),
        nullable=False,
        default=PipelineRunStatus.NOT_STARTED,
    )
    error_message: Mapped[str] = mapped_column(String, nullable=True)

    pipeline: Mapped["Pipeline"] = relationship(
        "Pipeline", back_populates="pipeline_runs"
    )
    node_runs: Mapped[List["NodeRun"]] = relationship(
        "NodeRun", cascade="all, delete-orphan", back_populates="pipeline_run"
    )

    def set_status_as_delivered(self) -> None:
        """Update the status of the pipeline run to delivered."""
        self.status = PipelineRunStatus.DELIVERED
        self.delivery_time = datetime.now()

    def set_status_as_started(self) -> None:
        """Update the status of the pipeline run to started."""
        self.status = PipelineRunStatus.STARTED
        self.start_time = datetime.now()

    def set_status_as_finished(self) -> None:
        """Update the status of the pipeline run to finished."""
        self.status = PipelineRunStatus.FINISHED
        self.end_time = datetime.now()

    def set_status_as_error(self, error_message: Optional[str] = None) -> None:
        """Update the status of the pipeline run to error."""
        self.status = PipelineRunStatus.ERROR
        self.error_message = error_message
        self.end_time = datetime.now()


class NodeRun(Base):
    __tablename__ = "pipeline_node_run"
    """
    Table to store the execution of one node of a pipeline run.

    A node is one unit. ``block_id`` is the visual block the node belongs to:
    an editor groups several units into one block on the canvas, so a block
    maps to N node runs and its status is an aggregate of theirs. In the first
    version every block holds exactly one unit and ``block_id`` equals
    ``node_id``, but the column is here from the start so growing to N never
    needs a migration.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    pipeline_run_id: Mapped[int] = mapped_column(
        ForeignKey("pipeline_run.id", ondelete="CASCADE"), nullable=False
    )
    node_id: Mapped[str] = mapped_column(String, nullable=False)
    block_id: Mapped[str] = mapped_column(String, nullable=False)
    #: Class name of the unit this node runs, as the component registry knows it.
    node_type: Mapped[str] = mapped_column(String, nullable=False)
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    input: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    output: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    delivery_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    start_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    status: Mapped[Enum] = mapped_column(
        Enum(NodeRunStatus),
        nullable=False,
        default=NodeRunStatus.NOT_STARTED,
    )
    error_message: Mapped[str] = mapped_column(String, nullable=True)

    pipeline_run: Mapped["PipelineRun"] = relationship(
        "PipelineRun", back_populates="node_runs"
    )
    artifacts: Mapped[List["NodeArtifact"]] = relationship(
        "NodeArtifact", cascade="all, delete-orphan", back_populates="node_run"
    )

    def set_status_as_delivered(self) -> None:
        """Update the status of the node run to delivered."""
        self.status = NodeRunStatus.DELIVERED
        self.delivery_time = datetime.now()

    def set_status_as_started(self) -> None:
        """Update the status of the node run to started."""
        self.status = NodeRunStatus.STARTED
        self.start_time = datetime.now()

    def set_status_as_finished(self) -> None:
        """Update the status of the node run to finished."""
        self.status = NodeRunStatus.FINISHED
        self.end_time = datetime.now()

    def set_status_as_error(self, error_message: Optional[str] = None) -> None:
        """Update the status of the node run to error."""
        self.status = NodeRunStatus.ERROR
        self.error_message = error_message
        self.end_time = datetime.now()

    def set_status_as_cancelled(self) -> None:
        """Update the status of the node run to cancelled.

        A node that never ran because an earlier one failed, as opposed to one
        still waiting its turn.
        """
        self.status = NodeRunStatus.CANCELLED
        self.end_time = datetime.now()


class NodeArtifact(Base):
    __tablename__ = "pipeline_node_artifact"
    """
    Table to store one output of a node run.

    ``key`` is a key from the unit's ``PROVIDES``, so what a node emits is
    named by its own declared contract rather than by a column per node type.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    node_run_id: Mapped[int] = mapped_column(
        ForeignKey("pipeline_node_run.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)

    node_run: Mapped["NodeRun"] = relationship("NodeRun", back_populates="artifacts")


class Converter(Base):
    __tablename__ = "converter"
    """
    Table to store a list of converters applied to a dataset.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebook.id", ondelete="CASCADE")
    )
    huey_id: Mapped[str] = mapped_column(String, nullable=True)
    converter: Mapped[str] = mapped_column(String, nullable=False)
    parameters: Mapped[JSON] = mapped_column(JSON)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
    status: Mapped[Enum] = mapped_column(
        Enum(ConverterStatus),
        nullable=False,
        default=ConverterStatus.NOT_STARTED,
    )
    delivery_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    start_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    # Relationships
    notebook: Mapped["Notebook"] = relationship(back_populates="converters")

    def set_status_as_delivered(self) -> None:
        """Update the status of the list to delivered and set delivery_time
        to now.
        """
        self.status = ConverterStatus.DELIVERED
        self.delivery_time = datetime.now()

    def set_status_as_started(self) -> None:
        """Update the status of the list to started and set start_time
        to now.
        """
        self.status = ConverterStatus.STARTED
        self.start_time = datetime.now()

    def set_status_as_finished(self) -> None:
        """Update the status of the list to finished and set end_time
        to now.
        """
        self.status = ConverterStatus.FINISHED
        self.end_time = datetime.now()

    def set_status_as_error(self) -> None:
        """Update the status of the list to error."""
        self.status = ConverterStatus.ERROR


class Notebook(Base):
    __tablename__ = "notebook"
    """
    Table to store all the information about a notebook.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("dataset.id", ondelete="CASCADE")
    )
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    # Relationships
    explorers: Mapped[List["Explorer"]] = relationship(
        back_populates="notebook", cascade="all, delete-orphan"
    )
    converters: Mapped[List["Converter"]] = relationship(
        back_populates="notebook", cascade="all, delete-orphan"
    )
    dataset: Mapped["Dataset"] = relationship(back_populates="notebooks")


class GenerativeSessionParameterHistory(Base):
    __tablename__ = "parameter_history"
    """
    Table to store the parameters of a generative session and their
    modification history.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("generative_session.id", ondelete="CASCADE"),
        nullable=False,
    )
    parameters: Mapped[JSON] = mapped_column(JSON, nullable=False)
    # Model active when this snapshot was taken. Nullable so pre-migration rows
    # remain valid; the parameters-history derivation only emits a model-change
    # event when two consecutive snapshots both carry a model name that differs.
    model_name: Mapped[str] = mapped_column(String, nullable=True)
    modified_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
    )

    # Relationship with GenerativeSession
    session = relationship(
        "GenerativeSession",
        back_populates="parameters_history",
        cascade="all, delete",
    )


class Explorer(Base):
    __tablename__ = "explorer"
    """
    Table to store all the information about a explorer.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebook.id", ondelete="CASCADE")
    )
    huey_id: Mapped[str] = mapped_column(String, nullable=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
    # explorer
    columns: Mapped[JSON] = mapped_column(JSON, nullable=False)
    exploration_type: Mapped[str] = mapped_column(String, nullable=False)
    parameters: Mapped[JSON] = mapped_column(JSON, nullable=False)
    exploration_path: Mapped[str] = mapped_column(String, nullable=True)
    # Render artifacts built once, when the exploration is created, so results
    # keep rendering after the explorer class is removed from the registry.
    artifacts_path: Mapped[str] = mapped_column(String, nullable=True)
    # Per artifact index -> edited plotly figure, applied over the stored
    # artifacts on read. Kept apart from artifacts_path so the computed figure
    # survives an edit and a reset can restore it.
    plot_overrides: Mapped[JSON] = mapped_column(JSON, nullable=True)
    # Metadata
    name: Mapped[str] = mapped_column(String, nullable=True)

    delivery_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    start_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    status: Mapped[Enum] = mapped_column(
        Enum(ExplorerStatus), nullable=False, default=ExplorerStatus.NOT_STARTED
    )
    # Relationships
    notebook: Mapped["Notebook"] = relationship(back_populates="explorers")

    def set_status_as_delivered(self) -> None:
        """Update the status to delivered and set delivery_time to now."""
        self.status = ExplorerStatus.DELIVERED
        self.delivery_time = datetime.now()

    def set_status_as_started(self) -> None:
        """Update the status to started and set start_time to now."""
        self.status = ExplorerStatus.STARTED
        self.start_time = datetime.now()

    def set_status_as_finished(self) -> None:
        """Update the status to finished and set end_time to now."""
        self.status = ExplorerStatus.FINISHED
        self.end_time = datetime.now()

    def set_status_as_error(self) -> None:
        """Update the status to error."""
        self.status = ExplorerStatus.ERROR

    def delete_result(self) -> None:
        """Delete the result of the explorer."""
        from DashAI.back.exploration.artifact_store import delete_artifacts

        delete_artifacts(self.artifacts_path)
        self.artifacts_path = None

        if self.exploration_path is not None:
            path = pathlib.Path(self.exploration_path)
            if path.exists():
                if path.is_dir():
                    if len(list(path.iterdir())) == 0:
                        path.rmdir()
                    else:
                        raise FileExistsError(
                            f"Error deleting the exploration result, "
                            f"directory {path} is not empty."
                        )
                else:
                    path.unlink()

            self.exploration_path = None
            self.status = ExplorerStatus.NOT_STARTED
            self.delivery_time = None
            self.start_time = None
            self.end_time = None


"""
RAG tables
"""


class RAGExtractor(Base):
    __tablename__ = "rag_extractor"
    """
    Canonical extractor configuration shared across documents.

    Stores a component_name + params pair. Multiple documents can reference
    the same extractor config via extractor_id FK.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    component_name: Mapped[str] = mapped_column(String, nullable=False)
    params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationship back to documents using this extractor
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="extractor_record"
    )


class ProcessedDocumentContent(Base):
    __tablename__ = "processed_document_content"
    """
    Cache of extracted document text, one row per document (1:1).

    The signature captures the file content hash and the extractor
    configuration used. It is kept for tracking purposes but no longer
    participates in uniqueness: re-extraction overwrites the single row.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    signature: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)

    document: Mapped["Document"] = relationship(
        "Document", back_populates="processed_contents"
    )

    __table_args__ = (
        UniqueConstraint("document_id", name="uq_processed_document_content_document"),
    )


class Document(Base):
    __tablename__ = "document"
    """
    Table to store all the information about a document.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    optional_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    extractor_id: Mapped[int] = mapped_column(
        ForeignKey("rag_extractor.id", ondelete="RESTRICT"), nullable=False
    )
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )

    # Create a relationship for the related sessions and related chunks
    pipeline_links: Mapped[List["RAGDocumentPipelineSessionLink"]] = relationship(
        "RAGDocumentPipelineSessionLink",
        cascade="all, delete-orphan",
        back_populates="document",
    )

    chunks: Mapped[List["Chunk"]] = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    embedding_matrices: Mapped[List["RAGEmbeddingMatrix"]] = relationship(
        "RAGEmbeddingMatrix", back_populates="document", cascade="all, delete-orphan"
    )

    extractor_record: Mapped[Optional["RAGExtractor"]] = relationship(
        "RAGExtractor", back_populates="documents"
    )

    processed_contents: Mapped[List["ProcessedDocumentContent"]] = relationship(
        "ProcessedDocumentContent",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    @property
    def get_related_sessions(self) -> List["GenerativeSession"]:
        """Return a list of sessions related to the document."""
        return [link.session for link in self.pipeline_links]

    @property
    def get_related_pipelines(self) -> List["RAGPipeline"]:
        """Return a list of pipelines related to the document."""
        return [link.pipeline for link in self.pipeline_links]

    def get_embedding_matrix(
        self, chunk_set_id: int, embedding_model_id: int
    ) -> Optional["RAGEmbeddingMatrix"]:
        for matrix in self.embedding_matrices:
            if (
                matrix.chunk_set_id == chunk_set_id
                and matrix.embedding_model_id == embedding_model_id
            ):
                return matrix
        return None


class Chunk(Base):
    __tablename__ = "chunk"
    """
    Table to store all the information about a chunk.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chunk_set_id: Mapped[int] = mapped_column(
        ForeignKey("rag_chunk_set.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[int] = mapped_column(
        ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSON, nullable=True
    )

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    chunk_set: Mapped["RAGChunkSet"] = relationship(
        "RAGChunkSet", back_populates="chunks"
    )

    __table_args__ = (
        UniqueConstraint(
            "chunk_set_id",
            "document_id",
            "chunk_index",
            name="uix_chunk_set_doc_index",
        ),
    )


class RAGChunkSet(Base):
    __tablename__ = "rag_chunk_set"
    """
    Canonical identity for a set of chunks produced by a processing pipeline.
    Two sessions with the same documents + same pipeline config share the same
    chunk set (same signature → same row).
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    signature: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    chunks: Mapped[List["Chunk"]] = relationship(
        "Chunk",
        back_populates="chunk_set",
        cascade="all, delete-orphan",
    )
    documents: Mapped[List["RAGChunkSetDocument"]] = relationship(
        "RAGChunkSetDocument",
        back_populates="chunk_set",
        cascade="all, delete-orphan",
    )
    embedding_matrices: Mapped[List["RAGEmbeddingMatrix"]] = relationship(
        "RAGEmbeddingMatrix",
        back_populates="chunk_set",
    )
    retriever_links: Mapped[List["RAGRetrieverChunkSet"]] = relationship(
        "RAGRetrieverChunkSet",
        back_populates="chunk_set",
        cascade="all, delete-orphan",
    )


class RAGChunkSetDocument(Base):
    __tablename__ = "rag_chunk_set_document"
    """Which documents belong to a chunk set."""
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chunk_set_id: Mapped[int] = mapped_column(
        ForeignKey("rag_chunk_set.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[int] = mapped_column(
        ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )

    chunk_set: Mapped["RAGChunkSet"] = relationship(
        "RAGChunkSet",
        back_populates="documents",
    )
    document: Mapped["Document"] = relationship("Document")

    __table_args__ = (
        UniqueConstraint(
            "chunk_set_id",
            "document_id",
            name="uix_chunk_set_document",
        ),
    )


class RAGRetrieverChunkSet(Base):
    __tablename__ = "rag_retriever_chunk_set"
    """Links a retriever to the chunk set it operates on."""
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    retriever_id: Mapped[int] = mapped_column(
        ForeignKey("rag_retriever.id", ondelete="CASCADE"), nullable=False
    )
    chunk_set_id: Mapped[int] = mapped_column(
        ForeignKey("rag_chunk_set.id", ondelete="CASCADE"), nullable=False
    )

    chunk_set: Mapped["RAGChunkSet"] = relationship(
        "RAGChunkSet",
        back_populates="retriever_links",
    )

    __table_args__ = (
        UniqueConstraint(
            "retriever_id",
            "chunk_set_id",
            name="uix_retriever_chunk_set",
        ),
    )


class RAGPrompt(Base):
    __tablename__ = "rag_prompt"
    """
    Table to store all the information about a RAG prompt.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_name: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=True)
    parameters: Mapped[JSON] = mapped_column(JSON, nullable=True)
    parameters_hash: Mapped[str] = mapped_column(String, nullable=False)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )

    # Relationship with RAGPipeline
    pipelines: Mapped[List["RAGPipeline"]] = relationship(
        "RAGPipeline", back_populates="prompt", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("parameters_hash", name="uq_rag_prompt_params_hash"),
    )


class RAGGenerationModel(Base):
    __tablename__ = "rag_generation_model"
    """
    Table to store all the information about a generation model.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_name: Mapped[str] = mapped_column(String, nullable=False)
    parameters: Mapped[JSON] = mapped_column(JSON, nullable=True)
    parameters_hash: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    pipelines: Mapped[List["RAGPipeline"]] = relationship(
        back_populates="generation_model"
    )

    __table_args__ = (
        UniqueConstraint("parameters_hash", name="uq_rag_gen_model_params_hash"),
    )


class RAGPipeline(Base):
    __tablename__ = "rag_pipeline"
    """
    Table to store all the information about a RAG pipeline.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("generative_session.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    parameters: Mapped[JSON] = mapped_column(JSON, nullable=True)

    chunking_model_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("rag_chunking_model.id", ondelete="CASCADE"), nullable=True
    )
    prompt_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("rag_prompt.id", ondelete="CASCADE"), nullable=True
    )
    generation_model_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("rag_generation_model.id", ondelete="CASCADE"), nullable=True
    )

    # Relationships
    chunking_model: Mapped["RAGChunkingModel"] = relationship(
        "RAGChunkingModel", back_populates="pipelines"
    )
    retriever: Mapped["RAGRetriever"] = relationship(
        "RAGRetriever",
        back_populates="pipeline",
        uselist=False,
    )
    prompt: Mapped["RAGPrompt"] = relationship("RAGPrompt", back_populates="pipelines")
    generation_model: Mapped["RAGGenerationModel"] = relationship(
        "RAGGenerationModel", back_populates="pipelines"
    )
    pipeline_links: Mapped[List["RAGDocumentPipelineSessionLink"]] = relationship(
        "RAGDocumentPipelineSessionLink", back_populates="pipeline"
    )


class RAGChunkingModel(Base):
    __tablename__ = "rag_chunking_model"
    """
    Table to store all the information about a chunking model.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_name: Mapped[str] = mapped_column(String, nullable=False)
    parameters: Mapped[JSON] = mapped_column(JSON, nullable=True)

    pipelines: Mapped[List["RAGPipeline"]] = relationship(
        "RAGPipeline", back_populates="chunking_model"
    )

    __table_args__ = (
        UniqueConstraint(
            "class_name",
            "parameters",
            name="uix_rag_chunking_model_class_params",
        ),
    )


class RAGRetriever(Base):
    __tablename__ = "rag_retriever"
    """
    Canonical identity row for every retriever — unit (sparse/dense) or composite.

    Sub-tables (RAGSparseRetriever, RAGDenseRetriever) reference this row
    via bridge_id. Composite children are stored in rag_retriever_child.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_name: Mapped[str] = mapped_column(String, nullable=False)
    pipeline_id: Mapped[int] = mapped_column(
        ForeignKey("rag_pipeline.id", ondelete="CASCADE"), nullable=False
    )

    pipeline: Mapped["RAGPipeline"] = relationship(back_populates="retriever")
    children: Mapped[List["RAGRetrieverChild"]] = relationship(
        "RAGRetrieverChild",
        foreign_keys="RAGRetrieverChild.parent_id",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    sparse_detail: Mapped[Optional["RAGSparseRetriever"]] = relationship(
        "RAGSparseRetriever",
        back_populates="bridge",
        uselist=False,
    )
    dense_detail: Mapped[Optional["RAGDenseRetriever"]] = relationship(
        "RAGDenseRetriever",
        back_populates="bridge",
        uselist=False,
    )


class RAGRetrieverChild(Base):
    __tablename__ = "rag_retriever_child"
    """
    Link table for composite retrievers: maps a parent composite to its
    ordered child retrievers. Both parent and child reference rag_retriever.id.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(
        ForeignKey("rag_retriever.id", ondelete="CASCADE"),
        nullable=False,
    )
    child_id: Mapped[int] = mapped_column(
        ForeignKey("rag_retriever.id", ondelete="CASCADE"),
        nullable=False,
    )
    child_order: Mapped[int] = mapped_column(Integer, nullable=False)

    parent: Mapped["RAGRetriever"] = relationship(
        "RAGRetriever",
        foreign_keys=[parent_id],
        back_populates="children",
    )

    __table_args__ = (
        UniqueConstraint(
            "parent_id",
            "child_order",
            name="uix_retriever_child_order",
        ),
    )


class RAGSparseRetriever(Base):
    __tablename__ = "rag_sparse_retriever"
    """
    Table to store all the information about a sparse retriever.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bridge_id: Mapped[int] = mapped_column(
        ForeignKey("rag_retriever.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_set_id: Mapped[int] = mapped_column(
        ForeignKey("rag_chunk_set.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_name: Mapped[str] = mapped_column(String, nullable=False)
    parameters: Mapped[JSON] = mapped_column(JSON, nullable=True)
    storage_folder: Mapped[str] = mapped_column(String, nullable=False)

    bridge: Mapped["RAGRetriever"] = relationship(
        "RAGRetriever",
        back_populates="sparse_detail",
    )
    chunk_set: Mapped["RAGChunkSet"] = relationship("RAGChunkSet")

    __table_args__ = (
        UniqueConstraint(
            "class_name",
            "parameters",
            "chunk_set_id",
            name="uix_rag_sparse_retriever",
        ),
    )


class RAGDenseRetriever(Base):
    __tablename__ = "rag_dense_retriever"
    """
    Table to store all the information about a dense retriever.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bridge_id: Mapped[int] = mapped_column(
        ForeignKey("rag_retriever.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_set_id: Mapped[int] = mapped_column(
        ForeignKey("rag_chunk_set.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_name: Mapped[str] = mapped_column(String, nullable=False)
    parameters: Mapped[JSON] = mapped_column(JSON, nullable=True)
    embedding_model_id: Mapped[int] = mapped_column(
        ForeignKey("rag_embedding_model.id", ondelete="CASCADE"), nullable=False
    )
    bridge: Mapped["RAGRetriever"] = relationship(
        "RAGRetriever",
        back_populates="dense_detail",
    )
    chunk_set: Mapped["RAGChunkSet"] = relationship("RAGChunkSet")
    embedding_model: Mapped["RAGEmbeddingModel"] = relationship(
        "RAGEmbeddingModel", back_populates="dense_retrievers"
    )

    __table_args__ = (
        UniqueConstraint(
            "class_name",
            "parameters",
            "chunk_set_id",
            "embedding_model_id",
            name="uix_rag_dense_retriever",
        ),
    )


class RAGEmbeddingModel(Base):
    __tablename__ = "rag_embedding_model"
    """
    Table to store embedding model configurations.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_name: Mapped[str] = mapped_column(String, nullable=False)
    parameters: Mapped[JSON] = mapped_column(JSON, nullable=True)

    # Relationships
    embedding_matrices: Mapped[List["RAGEmbeddingMatrix"]] = relationship(
        back_populates="embedding_model", cascade="all, delete-orphan"
    )
    dense_retrievers: Mapped[List["RAGDenseRetriever"]] = relationship(
        back_populates="embedding_model"
    )

    __table_args__ = (
        UniqueConstraint(
            "class_name",
            "parameters",
            name="uix_rag_embedding_model_class_params",
        ),
    )


class RAGEmbeddingMatrix(Base):
    __tablename__ = "rag_embedding_matrix"
    """
    Table to store embedding matrices for each unique combination of
    document, chunk set, and embedding model.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )
    chunk_set_id: Mapped[int] = mapped_column(
        ForeignKey("rag_chunk_set.id", ondelete="CASCADE"), nullable=False
    )
    embedding_model_id: Mapped[int] = mapped_column(
        ForeignKey("rag_embedding_model.id", ondelete="CASCADE"), nullable=False
    )
    storage_folder: Mapped[str] = mapped_column(String, nullable=False)
    matrix_shape: Mapped[List[int]] = mapped_column(JSON, nullable=False)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )

    document: Mapped["Document"] = relationship(
        "Document", back_populates="embedding_matrices"
    )
    chunk_set: Mapped["RAGChunkSet"] = relationship(
        "RAGChunkSet",
        back_populates="embedding_matrices",
    )
    embedding_model: Mapped["RAGEmbeddingModel"] = relationship(
        "RAGEmbeddingModel", back_populates="embedding_matrices"
    )

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_set_id",
            "embedding_model_id",
            name="uix_document_chunk_set_embedding",
        ),
    )

    @property
    def num_chunks(self) -> int:
        """Return the number of chunks in this embedding matrix."""
        return self.matrix_shape[0] if self.matrix_shape else 0

    @property
    def embedding_dimension(self) -> int:
        """Return the embedding dimension."""
        return self.matrix_shape[1] if len(self.matrix_shape) > 1 else 0

    @classmethod
    def get_by_tuple(
        cls, session, document_id: int, chunk_set_id: int, embedding_model_id: int
    ) -> Optional["RAGEmbeddingMatrix"]:
        return (
            session.query(cls)
            .filter(
                cls.document_id == document_id,
                cls.chunk_set_id == chunk_set_id,
                cls.embedding_model_id == embedding_model_id,
            )
            .first()
        )


"""
RAG relationship tables
"""


class RAGDocumentPipelineSessionLink(Base):
    __tablename__ = "rag_document_pipeline_session_link"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )
    session_id: Mapped[int] = mapped_column(
        ForeignKey("generative_session.id", ondelete="CASCADE"), nullable=False
    )
    pipeline_id: Mapped[int] = mapped_column(
        ForeignKey("rag_pipeline.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    document = relationship("Document", back_populates="pipeline_links")
    pipeline = relationship("RAGPipeline", back_populates="pipeline_links")
    session = relationship("GenerativeSession", back_populates="pipeline_links")

    __table_args__ = (
        UniqueConstraint("document_id", "session_id", name="uix_document_session"),
        UniqueConstraint("session_id", "pipeline_id", name="uix_session_pipeline"),
        UniqueConstraint("document_id", "pipeline_id", name="uix_document_pipeline"),
    )


class Datafile(Base):
    __tablename__ = "datafile"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    dataset_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    local_path: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[Enum] = mapped_column(
        Enum(DatafileStatus),
        nullable=False,
        default=DatafileStatus.DOWNLOADING,
    )
    error_message: Mapped[str] = mapped_column(String, nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )

    __table_args__ = (
        UniqueConstraint(
            "source_name",
            "dataset_id",
            name="uq_datafile_source_dataset",
        ),
    )


class StatisticalTest(Base):
    __tablename__ = "statistical_test"
    """
    A saved statistical test result.
    """

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Shared by every row of a per-run batch (e.g. a Shapiro fan-out) so they
    # can be listed together. its null for single row results
    group_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    model_session_id: Mapped[int] = mapped_column(
        ForeignKey("model_session.id", ondelete="CASCADE")
    )

    # optional name and description when test is saved by the user
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # What was tested
    test_name: Mapped[str] = mapped_column(String, nullable=False)
    metric_name: Mapped[str] = mapped_column(String, nullable=False)
    metric_split: Mapped[str] = mapped_column(String, nullable=False)
    alpha: Mapped[float] = mapped_column(Float, nullable=False)

    # Participating runs + a name map
    run_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    run_names: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Extra test-specific input params (e.g. {"alternative": "two-sided"})
    params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Outcome. statistic / p_value nullable: not every test reports them.
    statistic: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    p_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    significant: Mapped[bool] = mapped_column(Boolean, nullable=False)
    interpretation: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Free-form JSON payloads keep the table test-agnostic.
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    posthoc: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Credential(Base):
    __tablename__ = "credential"
    """
    Table to store encrypted credentials for external platforms.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)
    verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    created: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    last_modified: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
