import numpy as np
import pandas as pd
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.metrics.clustering.calinski_harabasz import CalinskiHarabasz
from DashAI.back.metrics.clustering.davies_bouldin import DaviesBouldin
from DashAI.back.metrics.clustering.silhouette import Silhouette

ALL_METRICS = [Silhouette, CalinskiHarabasz, DaviesBouldin]


def _x(values):
    """A one column feature matrix, so distances are just differences."""
    return to_dashai_dataset(pd.DataFrame({"v": [float(v) for v in values]}))


def _two_groups(gap, per_group=20, spread=0.1, seed=0):
    """Two equally sized groups whose centres sit ``gap`` apart."""
    rng = np.random.default_rng(seed)
    left = rng.normal(loc=0.0, scale=spread, size=per_group)
    right = rng.normal(loc=gap, scale=spread, size=per_group)
    labels = np.repeat([0, 1], per_group)
    return _x(np.concatenate([left, right])), labels


# --- the shared contract -----------------------------------------------------


@pytest.mark.parametrize("metric", ALL_METRICS)
def test_every_metric_scores_features_against_labels(metric):
    """Internal indices take (x, labels), not the (y_true, y_pred) of the rest."""
    x, labels = _two_groups(gap=10.0)

    assert isinstance(metric.score(x, labels), float)


@pytest.mark.parametrize("metric", ALL_METRICS)
def test_every_metric_is_undefined_when_a_single_cluster_is_found(metric):
    assert metric.score(_x([1.0, 2.0, 3.0, 4.0]), np.array([0, 0, 0, 0])) is None


@pytest.mark.parametrize("metric", ALL_METRICS)
def test_every_metric_is_undefined_when_every_point_is_noise(metric):
    """The shape DBSCAN produces when its eps is too small for the data."""
    assert metric.score(_x([1.0, 2.0, 3.0, 4.0]), np.array([-1, -1, -1, -1])) is None


@pytest.mark.parametrize("metric", ALL_METRICS)
def test_every_metric_is_undefined_when_every_point_is_its_own_cluster(metric):
    assert metric.score(_x([1.0, 2.0, 3.0, 4.0]), np.array([0, 1, 2, 3])) is None


@pytest.mark.parametrize("metric", ALL_METRICS)
def test_every_metric_leaves_noise_out_of_the_score(metric):
    """Noise is not a cluster, so adding a noise row must not move the answer."""
    x, labels = _two_groups(gap=10.0)

    frame = x.to_pandas()
    frame.loc[len(frame)] = {"v": 500.0}
    with_noise = to_dashai_dataset(frame)
    labels_with_noise = np.append(labels, -1)

    assert metric.score(with_noise, labels_with_noise) == pytest.approx(
        metric.score(x, labels)
    )


@pytest.mark.parametrize("metric", ALL_METRICS)
def test_every_metric_declares_which_direction_is_better(metric):
    assert isinstance(metric.MAXIMIZE, bool)


# --- values that can be worked out by hand -----------------------------------


def test_silhouette_matches_a_hand_computed_value():
    # Two pairs on a line: {0, 1} and {10, 11}. For the point at 0 the distance
    # within its cluster is 1 and the mean distance to the other is 10.5, so its
    # silhouette is 9.5/10.5. The four points give 0.904762, 0.894737, 0.894737
    # and 0.904762, and the metric reports their mean.
    score = Silhouette.score(_x([0.0, 1.0, 10.0, 11.0]), np.array([0, 0, 1, 1]))

    assert score == pytest.approx(0.89975, abs=1e-5)


def test_silhouette_approaches_one_as_the_groups_separate():
    close, labels = _two_groups(gap=1.0)
    far, _ = _two_groups(gap=100.0)

    assert Silhouette.score(far, labels) > 0.99
    assert Silhouette.score(close, labels) < Silhouette.score(far, labels)


def test_silhouette_turns_negative_when_the_labels_are_shuffled_across_groups():
    """Points assigned to the far group score below zero, which is the point of
    a negative silhouette: it flags samples that sit in the wrong cluster."""
    x, labels = _two_groups(gap=100.0)
    crossed = np.tile([0, 1], len(labels) // 2)

    assert Silhouette.score(x, crossed) < 0


# --- the direction each index moves in ---------------------------------------


def test_calinski_harabasz_rises_with_separation():
    labels = np.repeat([0, 1], 20)

    close, _ = _two_groups(gap=1.0)
    far, _ = _two_groups(gap=100.0)

    assert CalinskiHarabasz.score(far, labels) > CalinskiHarabasz.score(close, labels)
    assert CalinskiHarabasz.MAXIMIZE is True


def test_davies_bouldin_falls_with_separation():
    labels = np.repeat([0, 1], 20)

    close, _ = _two_groups(gap=1.0)
    far, _ = _two_groups(gap=100.0)

    assert DaviesBouldin.score(far, labels) < DaviesBouldin.score(close, labels)
    assert DaviesBouldin.MAXIMIZE is False


# --- inputs the metrics must refuse ------------------------------------------


@pytest.mark.parametrize("metric", ALL_METRICS)
def test_every_metric_refuses_a_label_count_that_does_not_match_the_rows(metric):
    with pytest.raises(ValueError, match="must have the same length"):
        metric.score(_x([1.0, 2.0, 3.0]), np.array([0, 1]))


@pytest.mark.parametrize("metric", ALL_METRICS)
def test_every_metric_refuses_a_dataset_with_no_numeric_column(metric):
    x = to_dashai_dataset(pd.DataFrame({"name": ["a", "b", "c", "d"]}))

    with pytest.raises(ValueError, match="at least one numeric column"):
        metric.score(x, np.array([0, 0, 1, 1]))
