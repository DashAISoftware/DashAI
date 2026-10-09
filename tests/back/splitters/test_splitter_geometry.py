"""The split shape every splitter declares so the frontend can draw it.

The session sidebar previews the splits a configuration will produce. Which
picture it draws is read from ``geometry`` rather than guessed from the schema
parameters, because guessing gets it wrong without saying so: two splitters can
both take ``n_splits`` and still lay their folds out differently, and a preview
that assumed contiguous blocks would draw a confident picture of a split that
never happens.

A splitter whose shape has no renderer keeps the ``unknown`` default, and the
frontend draws nothing instead of drawing a lie. These tests pin the values the
renderers exist for.
"""

import pytest

from DashAI.back.initial_components import get_initial_components
from DashAI.back.splitters.base_splitter import BaseSplitter
from DashAI.back.splitters.fold_splitter import FoldSplitter
from DashAI.back.splitters.holdout import HoldoutSplitter
from DashAI.back.splitters.k_fold import KFoldSplitter
from DashAI.back.splitters.leave_one_out import LeaveOneOutSplitter
from DashAI.back.splitters.repeated_k_fold import RepeatedKFoldSplitter
from DashAI.back.splitters.rolling_origin import RollingOriginSplitter
from DashAI.back.splitters.temporal_holdout import TemporalHoldoutSplitter

RENDERED_GEOMETRIES = {
    "partitions",
    "sequential_partitions",
    "blocked_folds",
    "expanding_window",
}


def _offered_splitters():
    """Collect the splitters a session can actually be pointed at.

    Read from the registration list rather than from the class tree: the tree
    also holds the shared bases, which are never offered and have nothing to
    declare.

    Returns
    -------
    list
        The registered splitter classes.
    """
    return [
        component
        for component in get_initial_components()
        if isinstance(component, type) and issubclass(component, BaseSplitter)
    ]


@pytest.mark.parametrize("splitter", _offered_splitters(), ids=lambda s: s.__name__)
def test_every_splitter_declares_a_geometry_the_frontend_can_draw(splitter):
    assert splitter.get_metadata()["geometry"] in RENDERED_GEOMETRIES


def test_a_splitter_that_declares_nothing_is_not_drawn():
    assert BaseSplitter.GEOMETRY == "unknown"
    assert BaseSplitter.GEOMETRY not in RENDERED_GEOMETRIES


@pytest.mark.parametrize(
    ("splitter", "geometry"),
    [
        (HoldoutSplitter, "partitions"),
        (TemporalHoldoutSplitter, "sequential_partitions"),
        (KFoldSplitter, "blocked_folds"),
        (LeaveOneOutSplitter, "blocked_folds"),
        (RepeatedKFoldSplitter, "blocked_folds"),
        (RollingOriginSplitter, "expanding_window"),
    ],
)
def test_splitters_report_the_shape_they_actually_produce(splitter, geometry):
    assert splitter.get_metadata()["geometry"] == geometry


def test_the_series_splitters_are_not_drawn_as_shuffled_ones():
    shuffling = HoldoutSplitter.get_metadata()["geometry"]

    for splitter in (TemporalHoldoutSplitter, RollingOriginSplitter):
        assert splitter.get_metadata()["geometry"] != shuffling


def test_folds_inherit_their_geometry_rather_than_repeating_it():
    assert FoldSplitter.GEOMETRY == "blocked_folds"
    assert "geometry" not in vars(KFoldSplitter)


def test_geometry_is_added_next_to_what_the_metadata_already_carried():
    metadata = KFoldSplitter.get_metadata()

    assert metadata["partitioning"] == "folds"
    assert "compatibleInnerSplitters" in metadata
    assert metadata["geometry"] == "blocked_folds"
