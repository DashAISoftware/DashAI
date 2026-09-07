import logging
from typing import TYPE_CHECKING, Any

from kink import inject
from sqlalchemy import exc

from DashAI.back.core.enums.status import RunStatus
from DashAI.back.dependencies.database.models import (
    GenerativeProcess,
    GenerativeSession,
    ProcessData,
)
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.job.RAG_job import RAGJob
from DashAI.back.models.base_generative_model import BaseGenerativeModel
from DashAI.back.tasks.base_generative_task import BaseGenerativeTask
from DashAI.back.tasks.RAG_task import RAGTask

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

log = logging.getLogger(__name__)


class GenerativeJob(BaseJob):
    """GenerativeJob class to infer with generative models ."""

    @inject
    def set_status_as_delivered(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the job as delivered."""
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
                raise JobError(
                    "Internal database error",
                ) from e

    @inject
    def set_status_as_error(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the job as error."""
        generative_process_id: int = self.kwargs.get("generative_process_id")
        if generative_process_id is None:
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
        """Get a descriptive name for the job."""
        generative_process_id = self.kwargs.get("generative_process_id")
        if not generative_process_id:
            return "Generative Process"

        from kink import di

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
                        return f"Generate: {session.name}"
                    if session and session.model_name:
                        return f"Generate with {session.model_name}"
                    return f"Generative Process #{generative_process_id}"
        except Exception as e:
            log.exception(f"Error getting job name: {e}")

        return f"Generative Process #{generative_process_id}"

    @inject
    def run(
        self,
    ) -> None:
        import gc

        import torch
        from kink import di

        component_registry = di["component_registry"]
        session_factory = di["session_factory"]
        config = di["config"]

        with session_factory() as db:
            process = db.get(
                GenerativeProcess, self.kwargs.get("generative_process_id")
            )
            if process is not None:
                session = db.get(GenerativeSession, process.session_id)
                if session is not None:
                    task_class = component_registry[session.task_name]["class"]
                    if issubclass(task_class, RAGTask):
                        RAG_job = RAGJob(**self.kwargs)
                        RAG_job.run()
                        return

        model = None
        generative_process = None
        with session_factory() as db:
            try:
                generative_process_id: int = self.kwargs["generative_process_id"]

                try:
                    generative_process: GenerativeProcess = db.get(
                        GenerativeProcess, generative_process_id
                    )
                    if not generative_process:
                        raise JobError(
                            f"Generative process {generative_process_id} "
                            "not found in DB."
                        )
                except Exception as e:
                    log.exception(e)
                    generative_process.set_status_as_error()
                    db.commit()
                    raise JobError("Error retrieving generative process.") from e

                try:
                    generative_session: GenerativeSession = db.get(
                        GenerativeSession, generative_process.session_id
                    )
                    if not generative_session:
                        raise JobError(
                            f"Session {generative_process.session_id} not found in DB."
                        )
                except Exception as e:
                    log.exception(e)
                    generative_process.set_status_as_error()
                    db.commit()
                    raise JobError("Error retrieving generative session.") from e

                try:
                    model_class = component_registry[generative_session.model_name][
                        "class"
                    ]
                    if (
                        getattr(model_class, "REQUIRES_DOWNLOAD", False)
                        and not model_class.is_downloaded()
                    ):
                        raise JobError(
                            f"Model {generative_session.model_name} is not downloaded."
                            " Download it before use."
                        )
                    params = generative_session.parameters
                    model: BaseGenerativeModel = model_class(**params)
                except JobError:
                    generative_process.set_status_as_error()
                    db.commit()
                    raise
                except Exception as e:
                    log.exception(e)
                    generative_process.set_status_as_error()
                    db.commit()
                    raise JobError(
                        "Error instantiating model with given parameters."
                    ) from e

                input_data = generative_process.input

                try:
                    task_class = component_registry[generative_session.task_name][
                        "class"
                    ]
                    task: BaseGenerativeTask = task_class()
                except KeyError as e:
                    log.exception(e)
                    generative_process.set_status_as_error()
                    db.commit()
                    raise JobError(
                        f"Task '{generative_session.task_name}' not found in registry."
                    ) from e
                except Exception as e:
                    log.exception(e)
                    generative_process.set_status_as_error()
                    db.commit()
                    raise JobError("Error instantiating task.") from e

                try:
                    use_history = getattr(task_class, "USE_HISTORY", False)
                    if use_history:
                        history = [
                            (proc.input[0].data, proc.output[0].data)
                            for proc in db.query(GenerativeProcess)
                            .filter(
                                GenerativeProcess.session_id == generative_session.id
                            )
                            .filter(GenerativeProcess.status == RunStatus.FINISHED)
                            .all()
                        ]
                        input_data = task.prepare_for_task(
                            input_data,
                            history=history,
                        )
                    else:
                        input_data = task.prepare_for_task(input_data)
                except Exception as e:
                    log.exception(e)
                    generative_process.set_status_as_error()
                    db.commit()
                    raise JobError("Error preparing task with history.") from e

                try:
                    generative_process.set_status_as_started()
                    db.commit()
                except exc.SQLAlchemyError as e:
                    log.exception(e)
                    generative_process.set_status_as_error()
                    db.commit()
                    raise JobError(
                        "Failed to update process status in database."
                    ) from e

                try:
                    output: Any = model.generate(input_data)
                except Exception as e:
                    log.exception(e)
                    generative_process.set_status_as_error()
                    db.add(
                        ProcessData(
                            data=f"Error details: {str(e)}",
                            data_type="str",
                            process_id=generative_process.id,
                            is_input=False,
                        )
                    )
                    db.commit()
                    raise JobError("Error during model generation.") from e

                try:
                    output: Any = task.process_output(
                        output, images_path=config["IMAGES_PATH"]
                    )
                    outputs_for_database = []
                    for o in output:
                        if not isinstance(o, tuple) or len(o) != 2:
                            raise JobError(
                                (
                                    "Output from task must be a list of "
                                    "tuples (data, type)."
                                )
                            )
                        output_data, output_type = o
                        process_data = ProcessData(
                            data=output_data,
                            data_type=output_type,
                            process_id=generative_process.id,
                            is_input=False,
                        )
                        outputs_for_database.append(process_data)

                    db.add_all(outputs_for_database)
                    db.commit()

                    # Update the generative process with the output
                    db.refresh(generative_process)
                    generative_process.set_status_as_finished()
                    db.commit()
                except Exception as e:
                    log.exception(e)
                    generative_process.set_status_as_error()
                    db.commit()
                    raise JobError(
                        "Error processing and saving generation output."
                    ) from e

            finally:
                if model:
                    del model
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()
