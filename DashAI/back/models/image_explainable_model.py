"""Mixins declaring image explainer support on model classes.

Models that support white-box image explainers inherit one of these mixins
instead of listing the explainers manually: the mixin carries the
``COMPATIBLE_COMPONENTS`` entries (merged with the task entries through the
registry MRO union) and forces the model to implement the inference
transform the explainers need to prepare input tensors.
"""

from abc import ABC, abstractmethod


class OcclusionSaliencyCompatibleModel(ABC):
    """Marks a torch image model as compatible with occlusion explainers.

    Any torch image model (convolutional or not) can support perturbation
    based explainers such as ``OcclusionSaliency``. Subclasses must expose
    the exact preprocessing they apply to input images.
    """

    COMPATIBLE_COMPONENTS = ["OcclusionSaliency"]

    @abstractmethod
    def get_inference_transform(self):
        """Return the transform applied to input images at inference time.

        Returns
        -------
        Callable
            A transform mapping a PIL image to the normalized tensor the
            model consumes.
        """
        raise NotImplementedError


class GradCamCompatibleModel(OcclusionSaliencyCompatibleModel, ABC):
    """Marks a convolutional torch image model as compatible with Grad-CAM.

    Requires a convolutional backbone (Grad-CAM hooks the last ``Conv2d``
    layer). Implies occlusion saliency support.
    """

    COMPATIBLE_COMPONENTS = ["GradCam"]
