"""SAM 3 promptable instance segmenter, backed by HuggingFace transformers."""

import logging
from typing import TYPE_CHECKING, List, Optional

import numpy as np

from DashAI.back.segmenters.base_segmenter import BaseSegmenter, SegmentInstance

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

logger = logging.getLogger(__name__)

# Public model card, named in the actionable error raised when the model
# fails to load, most commonly because no HuggingFace credential was added
# or the gated model's terms were never accepted.
SAM3_MODEL_PAGE_URL = "https://huggingface.co/facebook/sam3"


class SAM3Segmenter(BaseSegmenter):
    """Promptable instance segmentation backed by Meta's SAM 3.

    Wraps ``transformers.Sam3Model`` and ``transformers.Sam3Processor``.
    Model and processor are loaded lazily, on the first call to
    :meth:`segment`, never in ``__init__``: constructing this object (as
    ``SAM3SegmentConverter._get_segmenter`` does, once per pipeline run)
    never triggers a load or a network call by itself.

    This class never decides where its weights come from, which device to
    run on, or which thresholds to apply: all of them are handed in by the
    caller. The only caller in this codebase is ``SAM3SegmentConverter``,
    which resolves ``model_source`` through
    ``HFPretrainedDownloadMixin._pretrained_source`` (preferring the
    component's own downloaded copy and falling back to the Hub repo id)
    and forwards its ``min_score`` and ``mask_threshold`` schema fields as
    ``score_threshold`` and ``mask_threshold``. This class does not perform
    its own download.

    Parameters
    ----------
    model_source : str
        Local directory or HuggingFace repo id, accepted as-is by
        ``Sam3Model.from_pretrained`` / ``Sam3Processor.from_pretrained``.
    device : str, optional
        Torch device string, e.g. ``"cuda"`` or ``"cpu"``. Defaults to
        ``"cuda"`` when available, otherwise ``"cpu"``.
    score_threshold : float, optional
        Instance score cutoff, passed to
        ``post_process_instance_segmentation`` as ``threshold``: an
        instance whose confidence falls below it is discarded. Defaults to
        0.5.
    mask_threshold : float, optional
        Mask binarisation cutoff, passed to
        ``post_process_instance_segmentation`` as ``mask_threshold``. It
        decides which pixels of a kept instance belong to the object, and
        is deliberately a separate knob from ``score_threshold``: the two
        apply to unrelated quantities, and reusing the score cutoff here
        would reshape every mask. A ``score_threshold`` of 0 would then
        leave every pixel above the cutoff, turning each mask into the
        whole image. Defaults to 0.5, SAM 3's own default.
    """

    def __init__(
        self,
        model_source: str,
        device: Optional[str] = None,
        score_threshold: float = 0.5,
        mask_threshold: float = 0.5,
    ) -> None:
        self.model_source = model_source
        self._requested_device = device
        self.score_threshold = score_threshold
        self.mask_threshold = mask_threshold
        self._model = None
        self._processor = None
        self._device: Optional[str] = None

    def _ensure_loaded(self) -> None:
        """Load the model and processor on first use, once.

        Raises
        ------
        RuntimeError
            If ``Sam3Model`` or ``Sam3Processor`` fail to load. SAM 3 is a
            gated model, so the most common cause is a missing or
            unaccepted HuggingFace credential; the raised message names
            the model page and the required credential instead of
            surfacing a raw HTTP 401/403 from deep inside
            ``huggingface_hub``.
        """
        if self._model is not None:
            return

        import torch
        from transformers import Sam3Model, Sam3Processor

        self._device = self._requested_device or (
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        try:
            model = Sam3Model.from_pretrained(self.model_source).to(self._device)
            processor = Sam3Processor.from_pretrained(self.model_source)
        except Exception as error:
            raise RuntimeError(
                f"Could not load SAM 3 from '{self.model_source}'. SAM 3 is "
                "a gated HuggingFace model: add a HuggingFace credential in "
                f"DashAI and accept the model terms at {SAM3_MODEL_PAGE_URL}, "
                f"then try again. Original error: {error}"
            ) from error

        self._model = model
        self._processor = processor

    def segment(self, image: "PILImage", prompt: str) -> List[SegmentInstance]:
        """Detect every instance of ``prompt`` in ``image`` with SAM 3.

        Parameters
        ----------
        image : PIL.Image.Image
            Image to segment.
        prompt : str
            Text describing the concept to find, for example ``"cow"``.

        Returns
        -------
        list of SegmentInstance
            One entry per detected instance whose mask has at least one
            true pixel; instances with an entirely false mask are dropped,
            since they have no bounding box and would otherwise crop to a
            zero size image later. Masks are boolean and match ``image``'s
            size exactly. Bounding boxes are the tight box of the mask's
            own true pixels, in ``(x0, y0, x1, y1)`` order with ``x1`` and
            ``y1`` exclusive (the PIL crop convention), which guarantees
            they are ordered, within bounds, and consistent with the mask
            by construction.

        Raises
        ------
        RuntimeError
            If the model or processor cannot be loaded (see
            :meth:`_ensure_loaded`), or if SAM 3 returns a mask whose shape
            does not match ``image``'s size.
        """
        import torch

        self._ensure_loaded()

        width, height = image.size

        inputs = self._processor(images=image, text=prompt, return_tensors="pt").to(
            self._device
        )

        with torch.no_grad():
            outputs = self._model(**inputs)

        results = self._processor.post_process_instance_segmentation(
            outputs,
            threshold=self.score_threshold,
            mask_threshold=self.mask_threshold,
            target_sizes=inputs.get("original_sizes").tolist(),
        )[0]

        raw_masks = results["masks"]
        raw_scores = results["scores"]

        instances: List[SegmentInstance] = []
        for index in range(len(raw_masks)):
            # Hazard: mask dtype. post_process_instance_segmentation already
            # binarises with mask_threshold, but the tensor itself may still
            # arrive as float or uint8. Cast explicitly: the converter's
            # _select does `int(instance.mask.sum())`, so a float mask would
            # sum probabilities instead of counting pixels and silently
            # mis-threshold min_area_fraction.
            mask = raw_masks[index].detach().cpu().numpy().astype(bool)

            # Hazard: mask resolution. target_sizes above should already
            # resize the mask to the source image; assert rather than
            # assume, since a mismatch would otherwise surface much later,
            # deep inside render_segment, with a far less obvious error.
            if mask.shape != (height, width):
                raise RuntimeError(
                    f"SAM 3 returned a mask of shape {mask.shape}, expected "
                    f"{(height, width)} to match the source image. This "
                    "indicates target_sizes did not match the image handed "
                    "to the processor."
                )

            # Hazard: degenerate masks. An all-false mask has no bounding
            # box; keeping it would later pass _select when
            # min_area_fraction is 0 and then crop to a zero size image,
            # failing deep inside PIL.
            if not mask.any():
                continue

            # Hazard: bounding box. The box returned by the model is not
            # used directly. Instead, the bbox is derived as the tight box
            # of the mask's own true pixels, which is always ordered
            # (x0 < x1, y0 < y1), always within the image bounds, always
            # exclusive on x1/y1, and always consistent with the mask that
            # render_segment will actually crop, by construction rather
            # than by trusting the model's own box.
            row_indices = np.where(mask.any(axis=1))[0]
            col_indices = np.where(mask.any(axis=0))[0]
            y0, y1 = int(row_indices[0]), int(row_indices[-1]) + 1
            x0, x1 = int(col_indices[0]), int(col_indices[-1]) + 1

            score = float(raw_scores[index].detach().cpu().item())

            instances.append(
                SegmentInstance(mask=mask, score=score, bbox=(x0, y0, x1, y1))
            )

        return instances
