import gc
import logging
from typing import TYPE_CHECKING, Any, Callable, Dict

from kink import di, inject
from sqlalchemy import exc

from DashAI.back.core.enums.status import RunStatus
from DashAI.back.dependencies.database.models import (
    GenerativeProcess,
    GenerativeSession,
    ProcessData,
)
from DashAI.back.job.base_job import BaseJob, JobError, _release_frames
from DashAI.back.models.RAG.RAG_constants import (
    RAG_OPTIONAL_MODEL_KEYS,
    RAG_OUTPUT_MESSAGE_TYPE,
    RAG_PARAM_KEYS,
)
from DashAI.back.models.RAG.RAG_pipeline import (
    RAGPipeline,
    RAGPipelineConfig,
)
from DashAI.back.services.RAG.setup_service import SetupService
from DashAI.back.tasks.RAG_task import RAGTask

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

#: Session parameters the pipeline understands: the required model keys plus
#: the optional (but still pipeline-shaped) model keys such as the query
#: transformation stage. Any other key is filtered before the config guard.
_RAG_PARAM_KEYS = frozenset(RAG_PARAM_KEYS) | frozenset(RAG_OPTIONAL_MODEL_KEYS)

log = logging.getLogger(__name__)

#: Upper bound on the raw exception text surfaced in a user-visible job error.
#: Cause messages can be multi-KB and may embed absolute paths, SQL or URLs, so
#: they are truncated at the job boundary before being stored or displayed.
_JOB_ERROR_DETAIL_MAX_CHARS = 2000


def _empty_accelerator_cache() -> None:
    """Return cached CUDA blocks to the driver when torch is available.

    Kept best-effort: a missing torch installation or a failed cache clear
    must never replace the failure that ended the job.
    """
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        log.warning(
            "Could not clear the CUDA cache after RAG job cleanup.",
            exc_info=True,
        )


def _job_error(prefix: str, error: Exception) -> JobError:
    """Build a job error that preserves the underlying cause.

    Parameters
    ----------
    prefix : str
        Human-readable stage description, e.g. ``"Error during RAG pipeline
        setup"``.
    error : Exception
        The exception whose message is appended as the detail.

    Returns
    -------
    JobError
        A ``JobError`` formatted as ``"{prefix}: {detail}"``. The detail is the
        stripped exception message, truncated to
        ``_JOB_ERROR_DETAIL_MAX_CHARS`` with a trailing ellipsis when longer.
        When the detail is empty the bare ``prefix`` is returned.
    """
    detail = str(error).strip()
    if not detail:
        return JobError(prefix)
    if len(detail) > _JOB_ERROR_DETAIL_MAX_CHARS:
        detail = f"{detail[:_JOB_ERROR_DETAIL_MAX_CHARS]}…"
    return JobError(f"{prefix}: {detail}")


def _make_progress_reporter(
    session_factory: "sessionmaker", process_id: int
) -> Callable[[Dict[str, Any]], None]:
    """Build a best-effort live-progress reporter for a generative process.

    The pipeline calls the returned closure once per stage while the run is in
    flight. Each call opens a short-lived session, stores the payload on the
    process's ``progress`` column, and commits — so the chat frontend polling
    the process sees the current stage. A write is ignored unless the process is
    still ``STARTED``, so a late event cannot revive progress on a terminal
    (finished/error/cancelled) process.

    Reporting is best-effort: any failure is logged as a warning and swallowed.
    A transient DB error must never fail the chat turn, so the guard lives here
    rather than in the pipeline (which deliberately does not catch reporter
    exceptions).

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory.
    process_id : int
        The generative process whose ``progress`` column is updated.

    Returns
    -------
    Callable[[Dict[str, Any]], None]
        A reporter accepting one stage payload.

    """

    def report(progress: Dict[str, Any]) -> None:
        """Persist one stage payload, swallowing any failure."""
        try:
            with session_factory() as db:
                process: GenerativeProcess = db.get(GenerativeProcess, process_id)
                if process is None or process.status != RunStatus.STARTED:
                    return
                process.set_progress(progress)
                db.commit()
        except Exception as e:
            log.warning("Failed to report progress for process %s: %s", process_id, e)

    return report


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
                process.set_progress(None)
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

        Cleanup (drop the model reference, release traceback frames, garbage
        collect and clear the CUDA cache) runs after the body on every path,
        including setup, generation and save failures. The original failure is
        then re-raised unchanged.

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
        failure: BaseException | None = None

        # The whole body is captured instead of re-raised immediately: while a
        # failure is propagating its traceback still pins the model (and the
        # half-built pipeline), so cleanup must run after the except block.
        try:
            # ── Session 1: Load, build, prepare ────────────────────────
            try:
                with session_factory() as db:
                    generative_process = db.get(
                        GenerativeProcess, generative_process_id
                    )
                    if not generative_process:
                        raise JobError(
                            f"Generative process {generative_process_id} "
                            "not found in DB."
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
                    # Resolve each prior answer by row TYPE rather than position:
                    # a finished process now stores its message last (after the
                    # Queries and Dict rows), so ``output[0]`` is no longer the
                    # message. A process whose output has no message row is
                    # malformed; skip it instead of crashing the whole job.
                    history: list[tuple[str, str]] = []
                    for prior in finished_processes:
                        message = task.extract_message_from_output(prior.output)
                        if message is None:
                            log.debug(
                                "Skipping process %d from history: no %r output row.",
                                prior.id,
                                RAG_OUTPUT_MESSAGE_TYPE,
                            )
                            continue
                        history.append((prior.input[0].data, message))
                    input_data = task.prepare_for_task(input_data, history=history)

                    generative_process.set_status_as_started()
                    generative_process.set_progress(None)
                    db.commit()

                    process_id = generative_process.id
                    log.debug(
                        "Pipeline built and ready for process %d",
                        generative_process_id,
                    )
            except JobError:
                self.set_status_as_error()
                raise
            except Exception as e:
                log.exception(e)
                self.set_status_as_error()
                raise _job_error("Error during RAG pipeline setup", e) from e

            # ── Generation (no DB session) ─────────────────────────────
            reporter = _make_progress_reporter(session_factory, process_id)
            try:
                output: Any = model.generate(input_data, progress_callback=reporter)
                log.debug("Generation completed for process %d", generative_process_id)
            except Exception as e:
                log.exception(e)
                self.set_status_as_error()
                raise _job_error("Error during RAG pipeline execution", e) from e

            # ── Session 2: Save output ─────────────────────────────────
            try:
                with session_factory() as db:
                    generative_process = db.get(GenerativeProcess, process_id)
                    if not generative_process:
                        raise JobError(
                            f"Generative process {process_id} not found when "
                            "saving output."
                        )

                    output_data = task.process_output(
                        output, images_path=config["IMAGES_PATH"]
                    )
                    outputs_for_database = []
                    for o in output_data:
                        if not isinstance(o, tuple) or len(o) != 2:
                            raise JobError(
                                "Output from task must be a list of tuples "
                                "(data, type)."
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
                    generative_process.set_progress(None)
                    generative_process.set_status_as_finished()
                    db.commit()
                    log.debug("Output saved for process %d", generative_process_id)
            except Exception as e:
                log.exception(e)
                self.set_status_as_error()
                raise _job_error(
                    "Error processing and saving RAG generation output", e
                ) from e
        except BaseException as error:
            failure = error

        # Cleanup runs here, after the except block, because while an exception
        # is propagating its traceback still references the model and pipeline.
        # The frame release runs first, then gc.collect() so empty_cache() can
        # hand the freed blocks back to CUDA. All steps are best-effort and must
        # not replace the original failure.
        model = None
        if failure is not None:
            _release_frames(failure)
        gc.collect()
        _empty_accelerator_cache()
        if failure is not None:
            raise failure
