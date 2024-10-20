from typing import Any, List, Union

from datasets import Dataset
from PIL import Image

from DashAI.back.processs.base_generative_process import BaseGenerativeProcess


class ImageGenerationprocess(BaseGenerativeProcess):
    """Base class for image generation process."""

    metadata: dict = {
        "input_type": str,
        "output_type": Image.Image,
        "generation_type": "image",
    }

    def validate_input_for_process(
        self,
        input_data: str,
        process_name: str,
    ) -> None:
        """Validate input data for the image generation process."""
        super().validate_input_for_process(input_data, process_name)

        # TODO: validate the prompt

    def prepare_input_for_process(self, input_data: str) -> List[dict]:
        """Prepare input data for the image generation process."""
        if isinstance(input_data, str):
            return [{"prompt": input_data}]
        else:
            raise ValueError("Invalid input data type. Expected str")

    def process_generated_output(
        self, generated_output: List[Image.Image]
    ) -> List[Image.Image]:
        """Process the generated output from the model."""
        # For image generation, we don't need to do any additional processing
        # as the output is already in the form of PIL Image objects.
        return generated_output
