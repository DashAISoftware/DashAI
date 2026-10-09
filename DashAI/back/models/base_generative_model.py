from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Final, List, Tuple, Union

from DashAI.back.config_object import ConfigObject


class BaseGenerativeModel(ConfigObject, metaclass=ABCMeta):
    """Abstract base class for all generative models in DashAI.

    Generative models differ from standard predictive models in that they
    produce new content (text, images, etc.) rather than scalar predictions.
    All generative models must extend this class and implement `__init__`
    and `generate`.
    """

    TYPE: Final[str] = "GenerativeModel"

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Get metadata values for the current generative model.

        Returns
        -------
        Dict[str, Any]
            Dictionary indicating whether the model requires a download
            before use and the expected download size in bytes.
        """
        metadata: Dict[str, Any] = {}
        metadata["requires_download"] = bool(getattr(cls, "REQUIRES_DOWNLOAD", False))
        metadata["download_size_bytes"] = getattr(cls, "DOWNLOAD_SIZE_BYTES", None)
        return metadata

    @abstractmethod
    def __init__(self, **kwargs):
        """Initialize the generative model with configuration parameters.

        Parameters
        ----------
        **kwargs
            Model-specific configuration keyword arguments as
            defined in the model's SCHEMA.
        """
        raise NotImplementedError

    @abstractmethod
    def generate(self, input: Union[Any, Tuple[Any, Any]]) -> List[Any]:
        """Generate output from the model given an input.

        Parameters
        ----------
        input : Any or Tuple[Any, Any]
            The input data or prompt. May be
            a single item or a tuple of (prompt, conditioning) depending
            on the model type.

        Returns
        -------
        List[Any]
            A list of generated outputs (e.g. strings, images).
        """
        raise NotImplementedError
