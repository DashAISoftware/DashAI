import json
import logging
import os
import pickle
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Tuple

from kink import inject
from PIL import Image
from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.dependencies.database.models import GenerativeProcess
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.models import BaseModel

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class GenerativeJob(BaseJob):
    """GenerativeJob class to infer with generative models ."""

    def set_status_as_delivered(self) -> None:
        """Set the status of the job as delivered."""
        generative_process_id: int = self.kwargs["generative_process_id"]
        db: Session = self.kwargs["db"]

        process: GenerativeProcess = db.get(GenerativeProcess, generative_process_id)
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
    def run(
        self,
        component_registry: ComponentRegistry = lambda di: di["component_registry"],
        config=lambda di: di["config"],
    ) -> None:
        generative_process_id: int = self.kwargs["generative_process_id"]
        db: Session = self.kwargs["db"]

        generative_process: GenerativeProcess = db.get(
            GenerativeProcess, generative_process_id
        )

        model_class = component_registry[generative_process.model_name]["class"]

        params = generative_process.parameters

        model: BaseModel = model_class(
            num_inference_steps=params["num_inference_steps"],
            guidance_scale=params["guidance_scale"],
            device=params["device"],
        )

        prompt = generative_process.input_data

        # Start the generation process
        generative_process.set_status_as_started()
        db.commit()

        # Generate the image
        image: Image.Image = model.generate(prompt)

        # TODO: SANITIZE THE IMAGE FILE
        save_dir = Path.home() / ".DashAI" / "generated-images"
        image_path = save_dir / f"{generative_process.name}.png"

        # Save the image
        image.save(image_path, format="PNG")

        # Update the generative_process with the output path
        generative_process.output_path = str(image_path)

        # Finish the generation process
        generative_process.set_status_as_finished()
        db.commit()
