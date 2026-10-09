from abc import abstractmethod
from typing import Any, Dict, Final, List, Tuple

from DashAI.back.dependencies.database.models import ProcessData


class BaseGenerativeTask:
    """Base task for generative processes."""

    TYPE: Final[str] = "GenerativeTask"

    #: How the task is reached in the UI. ``"generic"`` tasks are offered
    #: through the shared "create session" model gallery; ``"standalone"``
    #: tasks own a dedicated entry point and are kept out of that gallery.
    ENTRY_POINT: str = "generic"

    @property
    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        """Return the schema of components compatible with this generative task.

        Concrete subclasses must implement this property to return a mapping
        that describes which models and other components are compatible with
        the task.

        Returns
        -------
        Dict[str, Any]
            A dictionary whose keys are component category names and whose
            values are lists or mappings of the compatible component classes
            or identifiers.

        Raises
        ------
        NotImplementedError
            If the subclass does not provide an implementation.
        """
        raise NotImplementedError

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Return serialisable metadata for the current generative task.

        ``inputs`` and ``outputs`` are dicts mapping type name to per-type
        cardinality (e.g. ``{"str": 1, "Image": 1}``) so the frontend can
        render the correct number of inputs per modality. ``entry_point`` tells
        the frontend whether the task belongs in the shared model gallery or
        owns a dedicated entry point.

        Returns
        -------
        Dict[str, Any]
            Dictionary with keys ``"inputs"``, ``"outputs"`` and
            ``"entry_point"``.
        """
        metadata = cls.metadata
        return {
            "inputs": dict(metadata["inputs"]),
            "outputs": dict(metadata["outputs"]),
            "entry_point": cls.ENTRY_POINT,
        }

    @abstractmethod
    def prepare_for_task(
        self,
        input: List[ProcessData],
        **kwargs: Any,
    ) -> Any:
        """Prepare input data for the task.

        Parameters
        ----------
        input : List[ProcessData]
            Input data to be prepared, a list of ProcessData objects

        Returns
        -------
        Any
            Prepared input data
        """
        raise NotImplementedError

    @abstractmethod
    def prepare_input_for_database(
        self,
        input: List[Any],
        **kwargs: Any,
    ) -> List[Tuple[str, str]]:
        """Prepare input data for the database.

        Parameters
        ----------
        input : List[Any]
            Input data to be prepared

        Returns
        -------
        List[Tuple[str, str]]
            Prepared input data as a list of tuples containing the data and its type
        """
        raise NotImplementedError

    @abstractmethod
    def process_output(
        self,
        output: List[Any],
        **kwargs: Any,
    ) -> List[Tuple[str, str]]:
        """Process output data of the task.

        Parameters
        ----------
        output : List[Any]
            Output data to be processed

        Returns
        -------
        List[Tuple[str, str]]
            Processed output data as a list of tuples containing the data and its type
        """
        raise NotImplementedError

    @abstractmethod
    def process_output_from_database(
        self,
        output: List[ProcessData],
        **kwargs: Any,
    ) -> List[ProcessData]:
        """Process output data from the database.

        Parameters
        ----------
        output : List[ProcessData]
            Output data to be processed, a list of ProcessData objects

        Returns
        -------
        List[ProcessData]
            Processed output data, a list of ProcessData objects
        """
        raise NotImplementedError

    @abstractmethod
    def process_input_from_database(
        self,
        input: List[ProcessData],
        **kwargs: Any,
    ) -> List[ProcessData]:
        """Process input data from the database.

        Parameters
        ----------
        input : List[ProcessData]
            Input data to be processed, a list of ProcessData objects

        Returns
        -------
        List[ProcessData]
            Processed input data, a list of ProcessData objects
        """
        raise NotImplementedError
