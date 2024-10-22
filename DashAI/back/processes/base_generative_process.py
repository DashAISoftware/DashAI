from abc import ABC, abstractmethod
from typing import Any, Dict, Final, List, Union

from datasets import Dataset


class BaseGenerativeProcess(ABC):
    """Base class for DashAI compatible generative processes."""

    TYPE: Final[str] = "GenerativeProcces"

    @property
    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Get metadata values for the current generation process

        Returns:
            Dict[str, Any]: Dictionary with the metadata containing the input and output types.
        """
        metadata = cls.metadata

        parsed_metadata: dict = {
            "input_type": metadata["input_type"].__name__,
            "output_type": metadata["output_type"].__name__,
            "generation_type": metadata["generation_type"],
        }
        return parsed_metadata

    def validate_input_for_process(
        self,
        input_data: str,  # For now it's designed for text-to-something taks
        process_name: str,
    ) -> None:
        """Validate input data for the current generative process.

        Parameters
        ----------
        input_data : str
            Input data to be validated (e.g., prompts, image descriptions)
        process_name : str
            Name of the generative process
        """
        metadata = self.metadata
        allowed_input_type = metadata["input_type"]

        if not isinstance(input_data, allowed_input_type):
            raise TypeError(
                f"Error in input data for process {process_name}. "
                f"Input must be of type {allowed_input_type.__name__}."
            )

    @abstractmethod
    def prepare_input_for_process(self, input_data: str) -> Any:
        """Prepare input data for the generation process.

        Parameters
        ----------
        input_data : str
            Input data to be prepared (e.g., prompts, image descriptions)

        Returns
        -------
        Any
            Prepared input data suitable for the generation process
        """
        raise NotImplementedError

    @abstractmethod
    def process_generated_output(self, generated_output: Any) -> Any:
        """Process the generated output from the model.

        Parameters
        ----------
        generated_output : Any
            Raw output from the generation model

        Returns
        -------
        Any
            Processed output suitable for the user
        """
        raise NotImplementedError
