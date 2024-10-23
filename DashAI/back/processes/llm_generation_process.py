from typing import Any, List

from DashAI.back.processs.base_generative_process import BaseGenerativeProcess


class LLMGenerationProcess(BaseGenerativeProcess):
    """Base class for text generation process using LLM models."""

    metadata: dict = {
        "input_type": str,  # Input is expected to be a string (text prompt)
        "output_type": str,  # Output will also be a string (generated text)
        "generation_type": "text",  # Specifies that this process generates text
    }

    def validate_input_for_process(
        self,
        input_data: str,
        process_name: str,
    ) -> None:
        """Validate input data for the LLM generation process."""
        super().validate_input_for_process(input_data, process_name)
        # TODO: add further validation if necessary for the prompt

    def prepare_input_for_process(self, input_data: str) -> List[dict]:
        """Prepare input data for the LLM generation process."""
        if isinstance(input_data, str):
            return [{"prompt": input_data}]
        else:
            raise ValueError("Invalid input data type. Expected str")

    def process_generated_output(self, generated_output: List[str]) -> List[str]:
        """Process the generated output from the model."""
        # For text generation, the output is already a string, so no additional processing is required
        return generated_output
