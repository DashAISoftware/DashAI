import numpy as np
import pytest

from DashAI.back.exploration.complexity_measures import (
    MEASURE_NAMES,
    borderline_points,
    compute_class_overlap,
    fisher_discriminant_ratio,
    intra_extra_nn_ratio,
)


def _separable(seed=0, per_class=40):
    """Two blobs far enough apart that no point sits on the boundary."""
    rng = np.random.default_rng(seed)
    X = np.vstack(
        [
            rng.normal(0.0, 0.2, (per_class, 2)),
            rng.normal(10.0, 0.2, (per_class, 2)),
        ]
    )
    y = np.array([0] * per_class + [1] * per_class)
    return X, y


def _noise(seed=0, samples=80):
    """Labels drawn independently of the features, so nothing is learnable."""
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 1.0, (samples, 3)), rng.integers(0, 2, samples)


# --- range and direction ---


@pytest.mark.parametrize(
    "measure",
    [fisher_discriminant_ratio, borderline_points, intra_extra_nn_ratio],
)
def test_measures_stay_in_the_unit_interval(measure):
    for builder in (_separable, _noise):
        X, y = builder()
        value = measure(X, y)
        assert 0.0 <= value <= 1.0


@pytest.mark.parametrize(
    "measure",
    [fisher_discriminant_ratio, borderline_points, intra_extra_nn_ratio],
)
def test_separable_data_scores_lower_than_noise(measure):
    """Lower must mean easier, which is the convention the whole module uses."""
    easy = measure(*_separable())
    hard = measure(*_noise())
    assert easy < hard


# --- F1 ---


def test_f1_is_zero_when_a_feature_separates_perfectly():
    X = np.array([[0.0], [0.0], [1.0], [1.0]])
    y = np.array([0, 0, 1, 1])
    # No within-class spread and different means: an infinite ratio, so F1 = 0.
    assert fisher_discriminant_ratio(X, y) == 0.0


def test_f1_finds_the_single_informative_feature_among_noise():
    rng = np.random.default_rng(1)
    informative = np.r_[np.zeros(40), np.ones(40) * 8]
    X = np.column_stack([informative, rng.normal(0.0, 1.0, (80, 5))])
    y = np.array([0] * 40 + [1] * 40)
    assert fisher_discriminant_ratio(X, y) < 0.01


def test_f1_is_one_when_the_classes_share_a_mean_and_spread():
    X = np.array([[0.0], [1.0], [0.0], [1.0]])
    y = np.array([0, 0, 1, 1])
    # Identical means cancel the numerator, so the ratio is 0 and F1 is 1.
    assert fisher_discriminant_ratio(X, y) == pytest.approx(1.0)


# --- N1 ---


def test_n1_is_small_for_well_separated_blobs():
    # Only the pair of points bridging the two blobs can be borderline.
    assert borderline_points(*_separable()) <= 2 / 80


def test_n1_flags_every_point_when_classes_alternate():
    # Points alternate along a line, so every tree edge joins two classes.
    X = np.arange(10, dtype=float).reshape(-1, 1)
    y = np.array([0, 1] * 5)
    assert borderline_points(X, y) == 1.0


def test_n1_handles_coincident_points():
    """Duplicate rows give a zero distance, which must not break the tree."""
    X = np.array([[0.0], [0.0], [0.0], [5.0], [5.0], [5.0]])
    y = np.array([0, 0, 0, 1, 1, 1])
    assert 0.0 <= borderline_points(X, y) <= 1.0


# --- N2 ---


def test_n2_is_small_for_well_separated_blobs():
    assert intra_extra_nn_ratio(*_separable()) < 0.05


def test_n2_skips_classes_with_a_single_member():
    X = np.array([[0.0], [0.1], [0.2], [9.0]])
    y = np.array([0, 0, 0, 1])
    # The lone member of class 1 has no same-class neighbour; the rest do.
    assert 0.0 <= intra_extra_nn_ratio(X, y) <= 1.0


def test_n2_raises_when_no_point_has_a_same_class_neighbour():
    X = np.array([[0.0], [1.0]])
    y = np.array([0, 1])
    with pytest.raises(ValueError, match="same-class and a different-class"):
        intra_extra_nn_ratio(X, y)


# --- validation ---


@pytest.mark.parametrize(
    "measure",
    [fisher_discriminant_ratio, borderline_points, intra_extra_nn_ratio],
)
def test_measures_reject_a_single_class(measure):
    with pytest.raises(ValueError, match="At least two classes"):
        measure(np.zeros((6, 2)), np.zeros(6))


@pytest.mark.parametrize(
    "measure",
    [fisher_discriminant_ratio, borderline_points, intra_extra_nn_ratio],
)
def test_measures_reject_mismatched_lengths(measure):
    with pytest.raises(ValueError, match="same number of rows"):
        measure(np.zeros((6, 2)), np.zeros(5))


def test_measures_reject_an_empty_matrix():
    with pytest.raises(ValueError, match="empty"):
        fisher_discriminant_ratio(np.zeros((0, 2)), np.zeros(0))


# --- compute_class_overlap ---


def test_compute_class_overlap_reports_every_measure():
    X, y = _separable()
    summary = compute_class_overlap(X, y, random_state=0)
    assert set(summary["measures"]) == set(MEASURE_NAMES)
    assert summary["n_samples"] == 80
    assert summary["n_features"] == 2
    assert summary["n_classes"] == 2
    assert summary["n_dropped_rows"] == 0


def test_compute_class_overlap_drops_rows_with_missing_values():
    X, y = _separable()
    X = X.astype(float)
    X[0, 0] = np.nan
    X[7, 1] = np.nan
    summary = compute_class_overlap(X, y, random_state=0)
    assert summary["n_dropped_rows"] == 2
    assert summary["n_samples"] == 78


def test_compute_class_overlap_subsamples_above_the_budget():
    rng = np.random.default_rng(2)
    X = rng.normal(0.0, 1.0, (300, 2))
    y = rng.integers(0, 2, 300)
    summary = compute_class_overlap(X, y, max_samples=60, random_state=0)
    assert summary["n_samples"] == 300
    # F1 keeps the full sample; only the distance-based measures are reduced.
    assert summary["n_samples_used_for_distances"] <= 66


def test_compute_class_overlap_is_reproducible_with_a_seed():
    rng = np.random.default_rng(3)
    X = rng.normal(0.0, 1.0, (200, 2))
    y = rng.integers(0, 2, 200)
    first = compute_class_overlap(X, y, max_samples=50, random_state=7)
    second = compute_class_overlap(X, y, max_samples=50, random_state=7)
    assert first["measures"] == second["measures"]


def test_compute_class_overlap_is_scale_invariant_for_distance_measures():
    """Min-max scaling means a unit change must not move N1 or N2."""
    X, y = _separable()
    plain = compute_class_overlap(X, y, random_state=0)["measures"]
    stretched = compute_class_overlap(X * 1000.0, y, random_state=0)["measures"]
    assert plain["N1"] == pytest.approx(stretched["N1"])
    assert plain["N2"] == pytest.approx(stretched["N2"])


def test_compute_class_overlap_supports_more_than_two_classes():
    rng = np.random.default_rng(4)
    X = np.vstack(
        [
            rng.normal(0.0, 0.3, (30, 2)),
            rng.normal(6.0, 0.3, (30, 2)),
            rng.normal(12.0, 0.3, (30, 2)),
        ]
    )
    y = np.array([0] * 30 + [1] * 30 + [2] * 30)
    summary = compute_class_overlap(X, y, random_state=0)
    assert summary["n_classes"] == 3
    assert all(value < 0.1 for value in summary["measures"].values())


def test_compute_class_overlap_accepts_string_labels():
    X, y = _separable()
    labels = np.where(y == 0, "cat", "dog")
    summary = compute_class_overlap(X, labels, random_state=0)
    assert summary["n_classes"] == 2
