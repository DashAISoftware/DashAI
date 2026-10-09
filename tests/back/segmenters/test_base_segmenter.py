"""Contract tests for the segmenter abstraction."""

import numpy as np
import pytest

from DashAI.back.segmenters.base_segmenter import BaseSegmenter, SegmentInstance


def test_segment_instance_holds_mask_score_and_bbox():
    mask = np.zeros((4, 4), dtype=bool)
    mask[1:3, 1:3] = True

    instance = SegmentInstance(mask=mask, score=0.9, bbox=(1, 1, 3, 3))

    assert instance.score == 0.9
    assert instance.bbox == (1, 1, 3, 3)
    assert instance.mask.sum() == 4


def test_base_segmenter_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseSegmenter()


def test_subclass_must_implement_segment():
    class _Incomplete(BaseSegmenter):
        pass

    with pytest.raises(TypeError):
        _Incomplete()


def test_instances_compare_by_identity_without_raising():
    """Lock in that a numpy field cannot make equality or hashing raise."""
    mask = np.zeros((4, 4), dtype=bool)
    first = SegmentInstance(mask=mask, score=0.9, bbox=(0, 0, 2, 2))
    second = SegmentInstance(mask=mask, score=0.9, bbox=(0, 0, 2, 2))

    assert first == first
    assert first != second
    assert hash(first) != hash(second)
