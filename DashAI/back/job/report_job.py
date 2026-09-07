"""Job that turns a run's predictions into one report per evaluation partition.

A report covers every partition the run exposes rather than one chosen at
creation, and which partitions those are is decided by the splitter that
produced the run rather than by this module: a holdout run yields train, test
and validation, while a cross validated one yields the rows it reserved as a
test set and the rest the final model was refit on. The set is read through
the same helpers the prediction and local explainer flows use, so a report can
never cover a different set than the one the user was offered. No report class
changes to support a new splitter, because none of them know what a partition
is.
"""

import logging
from typing import TYPE_CHECKING, List, Optional

from kink import inject
from sqlalchemy import exc

from DashAI.back.dependencies.database.models import (
    Dataset,
    ModelSession,
    Report,
    Run,
)
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.models.base_model import BaseModel
from DashAI.back.splitters.splits_payload import run_split_indexes, run_splits

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


PARTITION_LABELS = {
    "train": "Train",
    "test": "Test",
    "val": "Validation",
    "validation": "Validation",
    "all": "Whole dataset",
}


def partition_label(name: str) -> str:
    """Build the selector entry title for one partition.

    Names outside :data:`PARTITION_LABELS` fall back to their own titled form,
    so a splitter added later needs no change here.

    Parameters
    ----------
    name : str
        Partition name as reported by the run's splitter.

    Returns
    -------
    str
        The mapped label, or the name in title case when it is not mapped.
    """
    return PARTITION_LABELS.get(name, name.replace("_", " ").title())


class ReportJob(BaseJob):
    """Compute one evaluation report for a run over one split.

    Rebuilds the requested split, predicts with the trained model, and hands
    the truth and the predictions to the report. The model's inputs are
    never passed on: a report compares predictions against the truth and
    nothing else, which is what separates it from an explainer.
    """

    @inject
    def set_status_as_delivered(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Mark the report as queued.

        Parameters
        ----------
        session_factory : sessionmaker
            Factory producing a SQLAlchemy session.

        Raises
        ------
        JobError
            If the report does not exist or the database rejects the update.
        """
        report_id: int = self.kwargs["report_id"]
        with session_factory() as db:
            report: Report = db.get(Report, report_id)
            if not report:
                raise JobError(f"Report with id {report_id} does not exist in DB.")
            try:
                report.set_status_as_delivered()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError("Internal database error") from e

    @inject
    def set_status_as_error(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Mark the report as failed.

        Parameters
        ----------
        session_factory : sessionmaker
            Factory producing a SQLAlchemy session.
        """
        report_id: Optional[int] = self.kwargs.get("report_id")
        if report_id is None:
            return
        with session_factory() as db:
            try:
                report: Report = db.get(Report, report_id)
                if report:
                    report.set_status_as_error()
                    db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)

    def get_job_name(self) -> str:
        """Build a descriptive name for this job.

        Returns
        -------
        str
            The report's name when it can be read, a generic label
            otherwise.
        """
        report_id = self.kwargs.get("report_id")
        if not report_id:
            return "Report"

        from kink import di

        try:
            with di["session_factory"]() as db:
                report: Report = db.get(Report, report_id)
                if report:
                    return f"Report: {report.report_name}"
        except Exception:
            pass
        return f"Report ({report_id})"

    @staticmethod
    def _class_names(model: BaseModel) -> Optional[List[str]]:
        """Recover the human readable class labels of a fitted classifier.

        Parameters
        ----------
        model : BaseModel
            The trained model, which may carry output encodings.

        Returns
        -------
        Optional[List[str]]
            Class labels in encoded order, or None for a regressor.
        """
        encodings = getattr(model, "output_encodings", None)
        mapping = next(iter(encodings.values()), None) if encodings else None
        if mapping:
            return [
                str(label) for label, _ in sorted(mapping.items(), key=lambda p: p[1])
            ]
        classes = getattr(model, "classes_", None)
        if classes is None:
            return None
        return [str(label) for label in classes]

    @inject
    def run(self) -> None:
        """Compute and persist the report's artifacts.

        The dataset is prepared once over every row and then indexed per
        partition, because the row indexes a splitter reports are indexes into
        the dataset as stored. Inputs reach the model unprepared, exactly as
        the prediction job feeds them, since the model applies its own
        preprocessing; targets are encoded so they line up with the class
        indexes the model predicts.

        A partition that the report cannot describe, such as one holding a
        single class, is skipped and named in the saved output rather than
        costing the user the partitions that did compute. The job only fails
        when no partition produced anything.

        Raises
        ------
        JobError
            If any stage of the reconstruction or computation fails.
        """
        import os
        import pickle

        from kink import di

        from DashAI.back.core.artifacts import (
            ArtifactGroup,
            GroupedArtifacts,
            TextArtifact,
            normalize_artifacts,
        )
        from DashAI.back.dataloaders.classes.dashai_dataset import (
            load_dataset,
            select_columns,
        )
        from DashAI.back.reports.base_report import ReportError
        from DashAI.back.tasks.base_task import BaseTask

        component_registry = di["component_registry"]
        session_factory = di["session_factory"]
        config = di["config"]
        report_id: int = self.kwargs["report_id"]

        with session_factory() as db:
            report: Report = db.get(Report, report_id)
            if not report:
                raise JobError(f"Report with id {report_id} does not exist in DB.")

            try:
                run: Run = db.get(Run, report.run_id)
                if not run:
                    raise JobError(f"Run {report.run_id} does not exist in DB.")
                model_session: ModelSession = db.get(ModelSession, run.model_session_id)
                if not model_session:
                    raise JobError(
                        f"Model session {run.model_session_id} does not exist in DB."
                    )
                dataset: Dataset = db.get(Dataset, model_session.dataset_id)
                if not dataset:
                    raise JobError(
                        f"Dataset {model_session.dataset_id} does not exist in DB."
                    )

                try:
                    report.set_status_as_started()
                    db.commit()
                except exc.SQLAlchemyError as e:
                    log.exception(e)
                    raise JobError("Connection with the database failed") from e

                try:
                    model_class = component_registry[run.model_name]["class"]
                    model: BaseModel = model_class(**run.parameters)
                    trained_model = model.load(run.run_path)
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"Can not load model {run.model_name} from {run.run_path}"
                    ) from e

                try:
                    report_class = component_registry[report.report_name]["class"]
                    instance = report_class(**(report.parameters or {}))
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"Unable to instantiate report {report.report_name}."
                    ) from e

                self.report_progress(0.3, "Resolving the run's partitions")
                try:
                    splits = run_splits(
                        model_session.splits,
                        run.split_indexes,
                        component_registry,
                    )
                except ValueError as e:
                    log.exception(e)
                    raise JobError(str(e)) from e

                if not splits:
                    raise JobError(
                        "The run has no partition a report can be computed on: "
                        "every row went into fitting the model."
                    )

                try:
                    partition_indexes = {
                        split["name"]: run_split_indexes(
                            model_session.splits,
                            run.split_indexes,
                            component_registry,
                            split["name"],
                        )
                        for split in splits
                    }
                except ValueError as e:
                    log.exception(e)
                    raise JobError(str(e)) from e

                try:
                    loaded_dataset = load_dataset(f"{dataset.file_path}/dataset")
                    task: BaseTask = component_registry[model_session.task_name][
                        "class"
                    ]()
                    prepared_dataset = task.prepare_for_task(
                        dataset=loaded_dataset,
                        input_columns=model_session.input_columns,
                        output_columns=model_session.output_columns,
                    )
                    data_x, data_y = select_columns(
                        prepared_dataset,
                        model_session.input_columns,
                        model_session.output_columns,
                    )
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"Can not prepare dataset {dataset.id} for the report"
                    ) from e

                self.report_progress(0.6, "Computing every partition")
                class_names = self._class_names(trained_model)
                groups = []
                skipped = []
                last_error = None

                for partition, row_indexes in partition_indexes.items():
                    partition_x = (
                        data_x if row_indexes is None else data_x.select(row_indexes)
                    )
                    partition_y = (
                        data_y if row_indexes is None else data_y.select(row_indexes)
                    )
                    if partition_x.num_rows == 0:
                        continue
                    try:
                        y_pred = trained_model.predict(partition_x)
                        y_true = (
                            trained_model.prepare_output(partition_y, is_fit=False)
                            .to_pandas()
                            .to_numpy()
                            .ravel()
                        )
                    except Exception as e:
                        log.exception(e)
                        raise JobError(
                            f"Failed to predict the {partition} partition"
                        ) from e

                    try:
                        leaves = instance.compute(y_true, y_pred, class_names)
                    except ReportError as e:
                        log.warning("Skipping %s partition: %s", partition, e)
                        skipped.append(f"{partition_label(partition)}: {e}")
                        last_error = e
                        continue
                    except Exception as e:
                        log.exception(e)
                        raise JobError("Failed to compute the report") from e

                    if leaves:
                        groups.append(
                            ArtifactGroup(
                                title=partition_label(partition),
                                artifacts=leaves,
                            )
                        )

                if not groups:
                    raise JobError(
                        str(last_error)
                        if last_error
                        else "The report produced no output for any partition."
                    )

                self.report_progress(0.8, "Saving the report")
                items = [GroupedArtifacts(title=None, groups=groups)]
                if skipped:
                    items.append(
                        TextArtifact(
                            payload="\n".join(skipped),
                            title="Partitions not shown",
                        )
                    )
                artifacts = normalize_artifacts(items)

                try:
                    path = os.path.join(
                        config["RUNS_PATH"], f"report_{report_id}.pickle"
                    )
                    with open(path, "wb") as file:
                        pickle.dump(artifacts, file)
                except Exception as e:
                    log.exception(e)
                    raise JobError("Report file saving failed") from e

                try:
                    report.artifacts_path = path
                    report.plot_overrides = None
                    report.set_status_as_finished()
                    db.commit()
                except Exception as e:
                    log.exception(e)
                    raise JobError("Report path saving failed") from e

            except Exception as e:
                report.set_status_as_error()
                db.commit()
                raise e
