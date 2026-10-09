import logging
from typing import TYPE_CHECKING

from kink import inject
from sqlalchemy import exc

from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.load_dataset_unit import LoadDatasetUnit
from DashAI.back.units.run_exploration_unit import RunExplorationUnit
from DashAI.back.units.save_exploration_unit import SaveExplorationUnit

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class ExplorerJob(BaseJob):
    """ExplorerJob class to launch explorations."""

    @inject
    def set_status_as_delivered(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the explorer as delivered."""
        explorer_id: int = self.kwargs["explorer_id"]

        with session_factory() as db:
            explorer: Explorer = db.query(Explorer).get(explorer_id)

            if explorer is None:
                raise JobError(f"Explorer with id {explorer_id} not found.")

            try:
                explorer.set_status_as_delivered()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Error while setting the status of the explorer as delivered."
                ) from e

    @inject
    def set_status_as_error(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the explorer as error."""
        explorer_id: int = self.kwargs.get("explorer_id")
        if explorer_id is None:
            return

        with session_factory() as db:
            try:
                explorer: Explorer = db.query(Explorer).get(explorer_id)
                if explorer:
                    explorer.set_status_as_error()
                    db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)

    @inject
    def get_job_name(self) -> str:
        """Get a descriptive name for the job."""
        explorer_id = self.kwargs.get("explorer_id")
        if not explorer_id:
            return "Exploration"

        from kink import di

        session_factory = di["session_factory"]

        try:
            with session_factory() as db:
                explorer: Explorer = db.query(Explorer).get(explorer_id)
                if explorer and explorer.name:
                    return f"Explore: {explorer.name}"
                if explorer and explorer.exploration_type:
                    return f"Explore: {explorer.exploration_type}"
        except Exception:
            pass

        return f"Exploration ({explorer_id})"

    @inject
    def run(
        self,
    ) -> None:
        from kink import di

        from DashAI.back.exploration.artifact_store import store_artifacts

        session_factory = di["session_factory"]
        explorer_id: int = self.kwargs["explorer_id"]

        ctx = ExecutionContext()

        with session_factory() as db:
            # Load the explorer information
            try:
                explorer_info: Explorer = db.query(Explorer).get(explorer_id)
                if explorer_info is None:
                    raise JobError(f"Explorer with id {explorer_id} not found.")
                explorer_info.set_status_as_started()
                explorer_info.huey_id = self.kwargs.get("huey_id", None)
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError("Error while loading the explorer info.") from e

            # Load the notebook information
            try:
                notebook_info: Notebook = db.query(Notebook).get(
                    explorer_info.notebook_id
                )
                if notebook_info is None:
                    raise JobError(
                        f"Notebook with id {explorer_info.notebook_id} not found."
                    )
            except exc.SQLAlchemyError as e:
                log.exception(e)
                explorer_info.set_status_as_error()
                db.commit()
                raise JobError("Error while loading the notebook info.") from e
            except Exception:
                # A notebook that is simply not there used to escape the
                # SQLAlchemyError handler above and leave the row STARTED
                # forever, because nothing else marks it: the Huey error signal
                # writes only to its own task_copy table, and
                # _execute_base_job calls run() with no handler at all.
                # Re-raised as-is so the "not found" message survives.
                explorer_info.set_status_as_error()
                db.commit()
                raise

            # Load the dataset from the notebook: its own working copy, which
            # is what the converters rewrite.
            try:
                LoadDatasetUnit(notebook_id=notebook_info.id)(ctx)
            except Exception as e:
                # Anything the load unit raises has to leave the row in ERROR.
                # Nothing else marks it: the Huey error signal only writes to
                # its own task_copy table, never to the Explorer row, so
                # without this the exploration would stay STARTED forever.
                # Re-raised as-is; the unit reports the same
                # "Can not load dataset from path ..." message the job used to
                # build here.
                log.exception(e)
                explorer_info.set_status_as_error()
                db.commit()
                raise

            # How the exploration configuration is stored on the row — the
            # component name and its parameters live in separate columns —
            # rather than part of the exploration itself.
            explorer = {
                "component": explorer_info.exploration_type,
                "params": explorer_info.parameters,
            }

            # Run the exploration. The unit reports the registry, instancing,
            # preparation and launch errors with the same texts the job used
            # to build here; re-raised as-is so they reach the user intact.
            try:
                RunExplorationUnit(explorer_id=explorer_id, explorer=explorer)(ctx)
            except Exception as e:
                log.exception(e)
                explorer_info.set_status_as_error()
                db.commit()
                raise

            # Save the result
            try:
                SaveExplorationUnit(explorer_id=explorer_id)(ctx)

                # Update the explorer info. The status is not set to finished
                # here: the artifacts below are part of the work, so the row
                # only counts as done once they exist too.
                explorer_info.exploration_path = ctx.require("exploration_path")
                db.commit()
            except Exception as e:
                log.exception(e)
                explorer_info.set_status_as_error()
                db.commit()
                raise JobError(
                    (
                        f"Error while saving the exploration "
                        f"{explorer_info.exploration_type}."
                    )
                ) from e

            # Build and persist the render artifacts. This is the only moment
            # the explorer class is asked for its results: from here on the
            # stored artifacts are served as is, so the exploration keeps
            # rendering even if the explorer is removed from the registry.
            #
            # Both inputs come from the context rather than from local
            # variables: the explorer instance is what ran the exploration
            # (published by RunExplorationUnit, so the artifacts are built from
            # the same object that produced the result, not a rebuilt one), and
            # the path is where SaveExplorationUnit actually wrote it.
            try:
                explorer_info.artifacts_path = store_artifacts(
                    ctx.require("explorer"),
                    ctx.require("exploration_path"),
                    explorer_info.id,
                )
                explorer_info.set_status_as_finished()
                db.commit()
            except Exception as e:
                log.exception(e)
                explorer_info.set_status_as_error()
                db.commit()
                raise JobError(
                    (
                        f"Error while building the artifacts of the exploration "
                        f"{explorer_info.exploration_type}."
                    )
                ) from e
            finally:
                ctx.clear_cache()
