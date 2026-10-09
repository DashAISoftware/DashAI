import gc
import logging
from typing import TYPE_CHECKING, Any

from kink import di, inject
from sqlalchemy import exc

from DashAI.back.core.enums.status import RunStatus
from DashAI.back.dependencies.database.models import (
    GenerativeProcess,
    GenerativeSession,
    ProcessData,
)
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.models.RAG.RAG_constants import RAG_PARAM_KEYS as _RAG_PARAM_KEYS
from DashAI.back.models.RAG.RAG_pipeline import (
    RAGPipeline,
    RAGPipelineConfig,
)
from DashAI.back.services.RAG.setup_service import SetupService
from DashAI.back.tasks.RAG_task import RAGTask

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

log = logging.getLogger(__name__)


class RAGJob(BaseJob):
    """RAGJob handles the full RAG pipeline lifecycle as a background job."""

    @inject
    def set_status_as_delivered(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the job as delivered.

        Args:
            session_factory: Injected SQLAlchemy session factory.

        Raises:
            JobError: If the generative process does not exist or a DB error
                occurs.
        """
        generative_process_id: int = self.kwargs["generative_process_id"]

        with session_factory() as db:
            process: GenerativeProcess = db.get(
                GenerativeProcess, generative_process_id
            )
            if not process:
                raise JobError(
                    f"Generative process {generative_process_id} does not exist in DB."
                )
            try:
                process.set_status_as_delivered()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError("Internal database error") from e

    @inject
    def set_status_as_error(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the job as error.

        Args:
            session_factory: Injected SQLAlchemy session factory.
        """
        generative_process_id: int = self.kwargs.get("generative_process_id")
        if generative_process_id is None:
            log.warning(
                "Cannot set error status: generative_process_id is missing from kwargs"
            )
            return

        with session_factory() as db:
            process: GenerativeProcess = db.get(
                GenerativeProcess, generative_process_id
            )
            if not process:
                return
            try:
                process.set_status_as_error()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)

    @inject
    def get_job_name(self) -> str:
        """Get a descriptive name for the job.

        Returns:
            A human-readable name including the session name if available,
            otherwise a fallback like ``"RAG Process #<id>"``.
        """
        generative_process_id = self.kwargs.get("generative_process_id")
        if not generative_process_id:
            return "RAG Process"

        session_factory = di["session_factory"]

        try:
            with session_factory() as db:
                process: GenerativeProcess = db.get(
                    GenerativeProcess, generative_process_id
                )
                if process:
                    session: GenerativeSession = db.get(
                        GenerativeSession, process.session_id
                    )
                    if session and session.name:
                        return f"RAG: {session.name}"
                    return f"RAG Process #{generative_process_id}"
        except Exception as e:
            log.exception(f"Error getting job name: {e}")

        return f"RAG Process #{generative_process_id}"

    @inject
    def run(self) -> None:
        """Execute the full RAG pipeline lifecycle as a background job.

        Uses two separate DB sessions to avoid holding a connection open
        during LLM inference (which may take minutes):
        - **Session 1**: load data, build pipeline, prepare input, mark as started.
        - **(no session)**: LLM inference via ``model.generate()``.
        - **Session 2**: save output, mark as finished.

        Raises:
            JobError: If any stage of execution fails.
        """
        component_registry = di["component_registry"]
        session_factory = di["session_factory"]
        config = di["config"]

        if "generative_process_id" not in self.kwargs:
            raise JobError("RAGJob requires 'generative_process_id' in kwargs.")

        generative_process_id: int = self.kwargs["generative_process_id"]
        model = None

        # ── Session 1: Load, build, prepare ────────────────────────────
        try:
            with session_factory() as db:
                generative_process = db.get(GenerativeProcess, generative_process_id)
                if not generative_process:
                    raise JobError(
                        f"Generative process {generative_process_id} not found in DB."
                    )
                generative_session = db.get(
                    GenerativeSession, generative_process.session_id
                )
                if not generative_session:
                    raise JobError(
                        f"Session {generative_process.session_id} not found in DB."
                    )

                # Whitelist-only: accept only known RAG pipeline keys.
                raw_params = dict(generative_session.parameters)
                extra_keys: set[str] = set(raw_params) - _RAG_PARAM_KEYS
                if extra_keys:
                    log.debug(
                        "Filtered extra session parameter keys: %s",
                        sorted(extra_keys),
                    )
                clean_params = {
                    k: v for k, v in raw_params.items() if k in _RAG_PARAM_KEYS
                }
                pipeline_config = RAGPipelineConfig.from_kwargs(
                    db=db,
                    component_registry=component_registry,
                    session_id=generative_session.id,
                    env_RAG_path=config["RAG_PATH"],
                    **clean_params,
                )
                setup_service = SetupService(
                    db,
                    component_registry,
                    config["RAG_PATH"],
                )
                model: RAGPipeline = setup_service.build_pipeline(pipeline_config)

                # Build conversation history from prior finished processes
                input_data = generative_process.input
                task = RAGTask()
                finished_processes: list[GenerativeProcess] = (
                    db.query(GenerativeProcess)
                    .filter(
                        GenerativeProcess.session_id == generative_session.id,
                        GenerativeProcess.status == RunStatus.FINISHED,
                    )
                    .order_by(GenerativeProcess.id)
                    .all()
                )
                history = [
                    (p.input[0].data, p.output[0].data) for p in finished_processes
                ]
                input_data = task.prepare_for_task(input_data, history=history)

                generative_process.set_status_as_started()
                db.commit()

                process_id = generative_process.id
                log.debug(
                    "Pipeline built and ready for process %d", generative_process_id
                )
        except JobError:
            self.set_status_as_error()
            raise
        except Exception as e:
            log.exception(e)
            self.set_status_as_error()
            raise JobError("Error during RAG pipeline setup.") from e

        # ── Generation (no DB session) ──────────────────────────────────
        try:
            output: Any = model.generate(input_data)
            log.debug("Generation completed for process %d", generative_process_id)
        except Exception as e:
            log.exception(e)
            self.set_status_as_error()
            raise JobError("Error during RAG model generation.") from e

        # ── Session 2: Save output ──────────────────────────────────────
        try:
            with session_factory() as db:
                generative_process = db.get(GenerativeProcess, process_id)
                if not generative_process:
                    raise JobError(
                        f"Generative process {process_id} not found when saving output."
                    )

                output_data = task.process_output(
                    output, images_path=config["IMAGES_PATH"]
                )
                outputs_for_database = []
                for o in output_data:
                    if not isinstance(o, tuple) or len(o) != 2:
                        raise JobError(
                            "Output from task must be a list of tuples (data, type)."
                        )
                    data, data_type = o
                    outputs_for_database.append(
                        ProcessData(
                            data=data,
                            data_type=data_type,
                            process_id=generative_process.id,
                            is_input=False,
                        )
                    )

                db.add_all(outputs_for_database)
                db.commit()

                db.refresh(generative_process)
                generative_process.set_status_as_finished()
                db.commit()
                log.debug("Output saved for process %d", generative_process_id)
        except Exception as e:
            log.exception(e)
            self.set_status_as_error()
            raise JobError("Error processing and saving RAG generation output.") from e

        finally:
            import torch

            if model:
                del model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
