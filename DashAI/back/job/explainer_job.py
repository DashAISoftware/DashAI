import logging
from typing import TYPE_CHECKING

from kink import inject
from sqlalchemy import exc

from DashAI.back.dependencies.database.models import (
    Dataset,
    GlobalExplainer,
    LocalExplainer,
    ModelSession,
    Run,
)
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.splitters.splits_payload import (
    explainable_indexes,
    splitter_class_for,
)
from DashAI.back.units.build_global_explainer_unit import BuildGlobalExplainerUnit
from DashAI.back.units.build_local_explainer_unit import BuildLocalExplainerUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.generate_global_explanation_unit import (
    GenerateGlobalExplanationUnit,
)
from DashAI.back.units.generate_local_explanation_unit import (
    GenerateLocalExplanationUnit,
)
from DashAI.back.units.load_dataset_unit import LoadDatasetUnit
from DashAI.back.units.load_run_model_unit import LoadRunModelUnit
from DashAI.back.units.prepare_explanation_data_unit import PrepareExplanationDataUnit

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class ExplainerJob(BaseJob):
    """ExplainerJob class to calculate explanations."""

    @inject
    def set_status_as_delivered(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the job as delivered."""
        explainer_id: int = self.kwargs["explainer_id"]
        explainer_scope: str = self.kwargs["explainer_scope"]

        with session_factory() as db:
            if explainer_scope == "global":
                explainer: GlobalExplainer = db.get(GlobalExplainer, explainer_id)
            elif explainer_scope == "local":
                explainer: LocalExplainer = db.get(LocalExplainer, explainer_id)
            else:
                raise JobError(f"{explainer_scope} is an invalid explainer type")

            if not explainer:
                raise JobError(
                    f"Explainer with id {explainer_id} does not exist in DB."
                )
            try:
                explainer.set_status_as_delivered()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Internal database error",
                ) from e

    @inject
    def set_status_as_error(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the explainer as error."""
        explainer_id: int = self.kwargs.get("explainer_id")
        explainer_scope: str = self.kwargs.get("explainer_scope", "")

        if explainer_id is None:
            return

        with session_factory() as db:
            try:
                if explainer_scope == "global":
                    explainer = db.get(GlobalExplainer, explainer_id)
                elif explainer_scope == "local":
                    explainer = db.get(LocalExplainer, explainer_id)
                else:
                    return

                if explainer:
                    explainer.set_status_as_error()
                    db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)

    @inject
    def get_job_name(self) -> str:
        """Get a descriptive name for the job."""
        explainer_id = self.kwargs.get("explainer_id")
        explainer_scope = self.kwargs.get("explainer_scope", "")

        if not explainer_id:
            return f"{explainer_scope.capitalize()} Explanation"

        from kink import di

        session_factory = di["session_factory"]

        try:
            with session_factory() as db:
                if explainer_scope == "global":
                    explainer = db.get(GlobalExplainer, explainer_id)
                elif explainer_scope == "local":
                    explainer = db.get(LocalExplainer, explainer_id)
                else:
                    return (
                        f"{explainer_scope.capitalize()} Explanation ({explainer_id})"
                    )

                if explainer and explainer.name:
                    return f"Explain: {explainer.name}"
                if explainer and explainer.explainer_name:
                    return f"Explain: {explainer.explainer_name.split('.')[-1]}"
        except Exception:
            pass

        return f"{explainer_scope.capitalize()} Explanation ({explainer_id})"

    @inject
    def run(
        self,
    ) -> None:
        import json

        from kink import di

        session_factory = di["session_factory"]

        explainer_id: int = self.kwargs["explainer_id"]
        explainer_scope: str = self.kwargs["explainer_scope"]

        ctx = ExecutionContext()

        with session_factory() as db:
            if explainer_scope == "global":
                self.explainer_db: GlobalExplainer = db.get(
                    GlobalExplainer, explainer_id
                )
            elif explainer_scope == "local":
                self.explainer_db: LocalExplainer = db.get(LocalExplainer, explainer_id)
            else:
                raise JobError(f"{explainer_scope} is an invalid explainer type")

            if not self.explainer_db:
                # Checked before the try below, whose handler would otherwise
                # be the thing that crashes: it calls set_status_as_error on
                # this very row.
                raise JobError(
                    f"Explainer with id {explainer_id} does not exist in DB."
                )

            try:
                run: Run = db.get(Run, self.explainer_db.run_id)
                if not run:
                    raise JobError(
                        f"Run {self.explainer_db.run_id} does not exist in DB."
                    )
                model_session: ModelSession = db.get(ModelSession, run.model_session_id)
                if not model_session:
                    raise JobError(
                        f"Model session {run.model_session_id} does not exist in DB."
                    )
                dataset: Dataset = db.get(Dataset, model_session.dataset_id)
                if not dataset:
                    # The id named here is the one that was looked up. It used
                    # to interpolate the explainer's own dataset_id, a column
                    # global explainers do not even have.
                    raise JobError(
                        f"Dataset {model_session.dataset_id} does not exist in DB."
                    )

                self.explainer_db.huey_id = self.kwargs.get("huey_id", None)
                db.commit()

                input_columns = model_session.input_columns
                output_columns = model_session.output_columns

                LoadRunModelUnit(run_id=run.id)(ctx)

                # How the explainer configuration is stored on the row — the
                # component name and its parameters live in separate columns —
                # rather than part of the explanation itself.
                explainer_config = {
                    "component": self.explainer_db.explainer_name,
                    "params": self.explainer_db.parameters,
                }
                build_explainer = (
                    BuildGlobalExplainerUnit
                    if explainer_scope == "global"
                    else BuildLocalExplainerUnit
                )
                build_explainer(explainer=explainer_config)(ctx)

                LoadDatasetUnit(dataset_id=model_session.dataset_id)(ctx)

                prepare = PrepareExplanationDataUnit(
                    task_name=model_session.task_name,
                    input_columns=input_columns,
                    output_columns=output_columns,
                )
                # Resolving the task outside the wrapper below keeps a missing
                # task reported as a registry problem rather than a generic
                # "cannot prepare" message.
                prepare.validate(ctx)

                try:
                    # Which partitions a run has, and what they are called, is
                    # the splitter's answer and not something to read off the
                    # shape of the payload: a holdout run stores one flat
                    # mapping and a cross-validated one stores an entry per
                    # fold plus the pooled rows. The splitter maps whichever it
                    # produced onto the three slots the explainers are built
                    # from, so a splitter added later needs no change here.
                    from kink import di

                    splitter_class = splitter_class_for(
                        json.loads(model_session.splits), di["component_registry"]
                    )
                    train_idx, evaluation_idx, val_idx = explainable_indexes(
                        splitter_class, json.loads(run.split_indexes)
                    )
                except ValueError as e:
                    # Reported as itself: it says which of the two happened --
                    # a payload that does not match its splitter, or a run that
                    # fitted on every row it had and so has nothing to explain.
                    log.exception(e)
                    raise JobError(str(e)) from e

                try:
                    # Unpacking the JSON column is an artifact of how the row
                    # stores it, but it stays inside this block because a
                    # malformed value has always been reported as a
                    # preparation failure.
                    ctx.put_ref(
                        "split_indexes",
                        {
                            "train_indexes": train_idx,
                            "test_indexes": evaluation_idx,
                            "val_indexes": val_idx,
                        },
                    )
                    prepare(ctx)
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"""Can not prepare dataset {dataset.id} for the explanation""",
                    ) from e

                try:
                    self.explainer_db.set_status_as_started()
                    db.commit()
                except exc.SQLAlchemyError as e:
                    log.exception(e)
                    raise JobError(
                        "Connection with the database failed",
                    ) from e

                if explainer_scope == "global":
                    GenerateGlobalExplanationUnit(explainer_id=explainer_id)(ctx)
                    paths = {
                        "explanation_path": ctx.require("explanation_path"),
                        "plot_path": ctx.require("plot_path"),
                    }
                else:
                    same_dataset = (
                        model_session.dataset_id == self.explainer_db.dataset_id
                    )
                    GenerateLocalExplanationUnit(
                        explainer_id=explainer_id,
                        instance_dataset_id=self.explainer_db.dataset_id,
                        scope=self.explainer_db.scope,
                        fit_parameters=self.explainer_db.fit_parameters,
                        input_columns=input_columns,
                        output_columns=output_columns,
                        manual_input_data=self.kwargs.get("manual_input_data"),
                        same_dataset=same_dataset,
                        session_splits=(None if same_dataset else model_session.splits),
                    )(ctx)
                    paths = {
                        "explanation_path": ctx.require("explanation_path"),
                        "plots_path": ctx.require("plots_path"),
                        "input_dataset_path": ctx.require("input_dataset_path"),
                    }

                try:
                    for column, value in paths.items():
                        setattr(self.explainer_db, column, value)
                    self.explainer_db.plot_overrides = None
                    db.commit()
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        "Explanation path saving failed",
                    ) from e

                self.explainer_db.set_status_as_finished()
                db.commit()

            except Exception as e:
                self.explainer_db.set_status_as_error()
                db.commit()
                raise e
            finally:
                ctx.clear_cache()
