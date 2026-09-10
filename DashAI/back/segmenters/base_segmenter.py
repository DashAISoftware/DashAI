"""Abstraction over promptable instance segmentation models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    import numpy as np
    from PIL.Image import Image as PILImage


@dataclass(frozen=True, eq=False)
class SegmentInstance:
    """One detected object.

    Attributes
    ----------
    mask : numpy.ndarray
        Boolean array of shape ``(height, width)`` matching the source image,
        true where the object is present.
    score : float
        Confidence assigned by the model, between 0 and 1.
    bbox : tuple of int
        Bounding box as ``(x0, y0, x1, y1)``, with ``x1`` and ``y1`` exclusive.

    Notes
    -----
    Instances compare by identity, not by value. The numpy mask field makes
    elementwise equality ambiguous, so ``__eq__`` is not auto-generated. Callers
    should compare the fields they care about explicitly.
    """

    mask: "np.ndarray"
    score: float
    bbox: Tuple[int, int, int, int]


class BaseSegmenter(ABC):
    """A promptable segmentation model.

    Deliberately not a registry component. ``ComponentRegistry._get_base_type``
    rejects a class with two ``Base`` ancestors declaring a ``TYPE``, so a
    converter that inherited from both ``BaseConverter`` and a registered
    segmenter base would fail to register. Converters hold a segmenter instead.
    """

    @abstractmethod
    def segment(self, image: "PILImage", prompt: str) -> List[SegmentInstance]:
        """Detect every instance of ``prompt`` in ``image``.

        Parameters
        ----------
        image : PIL.Image.Image
            Image to segment.
        prompt : str
            Text describing the concept to find, for example ``"cow"``.

        Returns
        -------
        list of SegmentInstance
            Detected instances in arbitrary order. Ranking and filtering are
            the caller's responsibility. An empty list means nothing matched.
        """
        raise NotImplementedError
