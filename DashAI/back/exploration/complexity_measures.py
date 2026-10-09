"""Geometrical complexity measures for classification datasets.

This module implements a subset of the measures surveyed in Lorena et al.
(2019), "How Complex Is Your Classification Problem? A Survey on Measuring
Classification Complexity". They describe how hard a classification problem is
from the geometry of the data alone, without training any classifier.

Three measures are provided:

``F1``
    Maximum Fisher discriminant ratio. Feature-based: looks for the single most
    discriminative feature.
``N1``
    Fraction of borderline points, obtained from a minimum spanning tree.
    Neighbourhood-based: measures the size of the class boundary.
``N2``
    Ratio of intra-class to extra-class nearest neighbour distances.
    Neighbourhood-based: measures how tight classes are relative to their
    separation.

All three are normalised to ``[0, 1]`` where **lower means easier to
separate**, following the convention used in the survey.

This module intentionally has no DashAI imports. The measures are plain
functions over ``(x, y)`` arrays so they can be reused unchanged if the project
later introduces a dedicated data-metric component type.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from numpy import ndarray

# Measures computed by :func:`compute_class_overlap`, in reporting order.
MEASURE_NAMES: Tuple[str, ...] = ("F1", "N1", "N2")

# Above this many rows the pairwise distance matrix needed by N1 and N2 stops
# being practical, so the sample is reduced before computing them.
DEFAULT_MAX_SAMPLES: int = 2000


def _validate(x: "ndarray", y: "ndarray") -> None:
    """Check that the arrays can support a complexity measure.

    Parameters
    ----------
    x : ndarray
        Feature matrix of shape ``(n_samples, n_features)``.
    y : ndarray
        Class labels of shape ``(n_samples,)``.

    Raises
    ------
    ValueError
        If the shapes disagree, the matrix is empty, or fewer than two classes
        are present.
    """
    import numpy as np

    if x.ndim != 2:
        raise ValueError(f"x must be two-dimensional, got shape {x.shape}.")
    if len(x) != len(y):
        raise ValueError(
            "x and y must have the same number of rows, given: "
            f"len(x) = {len(x)} and len(y) = {len(y)}."
        )
    if len(x) == 0:
        raise ValueError("x is empty; no complexity measure can be computed.")
    if len(np.unique(y)) < 2:
        raise ValueError(
            "At least two classes are required to measure class overlap, found "
            f"{len(np.unique(y))}."
        )


def _drop_missing(x: "ndarray", y: "ndarray") -> Tuple["ndarray", "ndarray", int]:
    """Remove rows holding a missing value in any feature or in the label.

    Parameters
    ----------
    x : ndarray
        Feature matrix.
    y : ndarray
        Class labels.

    Returns
    -------
    Tuple[ndarray, ndarray, int]
        The filtered matrix, the filtered labels, and the number of rows that
        were dropped.
    """
    import numpy as np

    finite = np.isfinite(x).all(axis=1)
    labelled = np.array([value is not None and value == value for value in y])
    keep = finite & labelled
    return x[keep], y[keep], int((~keep).sum())


def _min_max_scale(x: "ndarray") -> "ndarray":
    """Scale every feature to ``[0, 1]``.

    Distance-based measures are not scale invariant, so features are put on a
    common range before N1 and N2 are computed. Constant features collapse to
    zero and therefore stop contributing to the distances.

    Parameters
    ----------
    x : ndarray
        Feature matrix.

    Returns
    -------
    ndarray
        The scaled matrix, as float.
    """
    x = x.astype(float, copy=True)
    minimum = x.min(axis=0)
    spread = x.max(axis=0) - minimum
    spread[spread == 0] = 1.0
    return (x - minimum) / spread


def _stratified_subsample(
    x: "ndarray", y: "ndarray", max_samples: int, random_state: Optional[int]
) -> Tuple["ndarray", "ndarray"]:
    """Reduce the sample while keeping the class proportions.

    Every class keeps at least two members whenever it had them, so that the
    intra-class nearest neighbour used by N2 still exists after subsampling.

    Parameters
    ----------
    x : ndarray
        Feature matrix.
    y : ndarray
        Class labels.
    max_samples : int
        Target number of rows. The result may be slightly larger when the
        per-class minimum forces it.
    random_state : Optional[int]
        Seed for the selection, or ``None`` for a non-deterministic draw.

    Returns
    -------
    Tuple[ndarray, ndarray]
        The reduced matrix and labels.
    """
    import numpy as np

    if len(x) <= max_samples:
        return x, y

    rng = np.random.default_rng(random_state)
    keep: List[int] = []
    classes, counts = np.unique(y, return_counts=True)
    ratio = max_samples / len(x)

    for label, count in zip(classes, counts, strict=True):
        indices = np.flatnonzero(y == label)
        quota = max(min(2, int(count)), int(round(int(count) * ratio)))
        keep.extend(rng.choice(indices, size=quota, replace=False).tolist())

    keep_array = np.array(sorted(keep))
    return x[keep_array], y[keep_array]


def fisher_discriminant_ratio(x: "ndarray", y: "ndarray") -> float:
    """Compute F1, the maximum Fisher discriminant ratio.

    For each feature the ratio contrasts the separation between class means
    against the spread inside the classes, weighted by class size. The measure
    keeps the largest ratio over all features, so it answers "is there at least
    one feature that separates these classes on its own?".

    The value is ``1 / (1 + max_ratio)``: it approaches 0 when some feature
    separates the classes cleanly and approaches 1 when no single feature does.

    Parameters
    ----------
    x : ndarray
        Feature matrix of shape ``(n_samples, n_features)``.
    y : ndarray
        Class labels of shape ``(n_samples,)``.

    Returns
    -------
    float
        F1 in ``[0, 1]``. Lower means easier to separate.
    """
    import numpy as np

    _validate(x, y)
    x = x.astype(float, copy=False)
    classes = np.unique(y)

    numerator = np.zeros(x.shape[1], dtype=float)
    denominator = np.zeros(x.shape[1], dtype=float)

    means = {}
    sizes = {}
    for label in classes:
        members = x[y == label]
        means[label] = members.mean(axis=0)
        sizes[label] = len(members)
        denominator += ((members - means[label]) ** 2).sum(axis=0)

    for position, first in enumerate(classes):
        for second in classes[position + 1 :]:
            weight = sizes[first] * sizes[second]
            numerator += weight * (means[first] - means[second]) ** 2

    # A zero denominator means the feature has no within-class spread at all.
    # If its class means still differ the feature separates perfectly, which is
    # an infinite ratio; if they do not, the feature carries no information.
    safe_denominator = np.where(denominator > 0, denominator, 1.0)
    ratios = np.where(
        denominator > 0,
        numerator / safe_denominator,
        np.where(numerator > 0, np.inf, 0.0),
    )

    best = float(np.max(ratios))
    if np.isinf(best):
        return 0.0
    return float(1.0 / (1.0 + best))


def borderline_points(x: "ndarray", y: "ndarray") -> float:
    """Compute N1, the fraction of points on a class boundary.

    A minimum spanning tree is built over the points using Euclidean distance.
    Every edge that joins two different classes marks both of its endpoints as
    borderline. N1 is the share of points marked this way, so it estimates how
    long and how populated the boundary between classes is.

    Parameters
    ----------
    x : ndarray
        Feature matrix, already scaled.
    y : ndarray
        Class labels.

    Returns
    -------
    float
        N1 in ``[0, 1]``. Lower means a smaller boundary, so easier to
        separate.
    """
    import numpy as np
    from scipy.sparse.csgraph import minimum_spanning_tree
    from scipy.spatial.distance import pdist, squareform

    _validate(x, y)
    distances = squareform(pdist(x.astype(float, copy=False)))

    # minimum_spanning_tree reads a zero as "no edge", so coincident points
    # would lose their edge. Nudging those zeros keeps the tree connected.
    off_diagonal = ~np.eye(len(x), dtype=bool)
    positive = distances[off_diagonal & (distances > 0)]
    epsilon = float(positive.min()) * 1e-6 if positive.size else 1e-12
    distances[off_diagonal & (distances == 0)] = epsilon

    tree = minimum_spanning_tree(distances).tocoo()
    borderline = set()
    for source, target in zip(tree.row, tree.col, strict=True):
        if y[source] != y[target]:
            borderline.add(int(source))
            borderline.add(int(target))

    return float(len(borderline) / len(x))


def intra_extra_nn_ratio(x: "ndarray", y: "ndarray") -> float:
    """Compute N2, the intra-class over extra-class nearest neighbour ratio.

    For every point the distance to its closest same-class neighbour is
    compared against the distance to its closest different-class neighbour.
    Summing both over the dataset gives a ratio that is small when classes are
    tight and far apart, and large when they interleave.

    The result is ``r / (1 + r)`` so that it stays in ``[0, 1]``.

    Points belonging to a class with a single member are skipped, since they
    have no same-class neighbour to measure against.

    Parameters
    ----------
    x : ndarray
        Feature matrix, already scaled.
    y : ndarray
        Class labels.

    Returns
    -------
    float
        N2 in ``[0, 1]``. Lower means easier to separate.

    Raises
    ------
    ValueError
        If no point has both a same-class and a different-class neighbour.
    """
    import numpy as np
    from scipy.spatial.distance import pdist, squareform

    _validate(x, y)
    distances = squareform(pdist(x.astype(float, copy=False)))
    np.fill_diagonal(distances, np.inf)

    intra_total = 0.0
    extra_total = 0.0
    measured = 0

    for index in range(len(x)):
        same = y == y[index]
        same[index] = False
        if not same.any():
            continue
        intra_total += float(distances[index][same].min())
        extra_total += float(distances[index][~same].min())
        measured += 1

    if measured == 0:
        raise ValueError(
            "No point has both a same-class and a different-class neighbour, "
            "so N2 cannot be computed."
        )
    if extra_total == 0:
        return 1.0

    ratio = intra_total / extra_total
    return float(ratio / (1.0 + ratio))


def compute_class_overlap(
    x: "ndarray",
    y: "ndarray",
    max_samples: int = DEFAULT_MAX_SAMPLES,
    random_state: Optional[int] = None,
) -> Dict[str, Any]:
    """Compute F1, N1 and N2 for a labelled dataset.

    Rows with a missing feature or label are dropped, features are scaled to
    ``[0, 1]`` for the two distance-based measures, and the sample is reduced
    when it exceeds ``max_samples``.

    Parameters
    ----------
    x : ndarray
        Numeric feature matrix of shape ``(n_samples, n_features)``.
    y : ndarray
        Class labels of shape ``(n_samples,)``.
    max_samples : int
        Row budget for N1 and N2, which both need a pairwise distance matrix.
        F1 always uses every available row, since it is linear in the sample.
    random_state : Optional[int]
        Seed used when the sample has to be reduced.

    Returns
    -------
    Dict[str, Any]
        Dictionary with the keys ``"measures"`` (one float per measure name),
        ``"n_samples"`` (rows kept after dropping missing values),
        ``"n_features"``, ``"n_classes"``, ``"n_dropped_rows"`` and
        ``"n_samples_used_for_distances"``.
    """
    import numpy as np

    x = np.asarray(x, dtype=float)
    y = np.asarray(y)

    _validate(x, y)
    x, y, dropped = _drop_missing(x, y)
    _validate(x, y)

    scaled = _min_max_scale(x)
    reduced_x, reduced_y = _stratified_subsample(scaled, y, max_samples, random_state)

    return {
        "measures": {
            "F1": fisher_discriminant_ratio(x, y),
            "N1": borderline_points(reduced_x, reduced_y),
            "N2": intra_extra_nn_ratio(reduced_x, reduced_y),
        },
        "n_samples": int(len(x)),
        "n_features": int(x.shape[1]),
        "n_classes": int(len(np.unique(y))),
        "n_dropped_rows": dropped,
        "n_samples_used_for_distances": int(len(reduced_x)),
    }
