import json
import sys

import numpy as np
import pandas as pd
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.models.clustering_model import ClusteringModel
from DashAI.back.models.faiss.faiss_dbscan_clustering import FaissDBSCANClustering
from DashAI.back.models.faiss.faiss_kmeans_clustering import FaissKMeansClustering
from DashAI.back.models.scikit_learn.agglomerative_clustering import (
    AgglomerativeClustering,
)
from DashAI.back.models.scikit_learn.dbscan_clustering import DBSCANClustering
from DashAI.back.models.scikit_learn.gaussian_mixture_clustering import (
    GaussianMixtureClustering,
)
from DashAI.back.models.scikit_learn.hdbscan_clustering import HDBSCANClustering
from DashAI.back.models.scikit_learn.kmeans_clustering import KMeansClustering
from DashAI.back.models.scikit_learn.spectral_clustering import SpectralClustering

ALL_MODELS = [
    KMeansClustering,
    DBSCANClustering,
    HDBSCANClustering,
    AgglomerativeClustering,
    GaussianMixtureClustering,
    SpectralClustering,
    FaissKMeansClustering,
    FaissDBSCANClustering,
]

# The number of groups is not a shared parameter: centroid based models are
# told how many to look for, density based ones work it out from the data.
# Pairing each model with the arguments that ask it for three keeps the
# recovery test below honest instead of asserting each algorithm's default.
ASKED_FOR_THREE = [
    (KMeansClustering, {"n_clusters": 3, "random_state": 0}),
    (AgglomerativeClustering, {"n_clusters": 3}),
    (GaussianMixtureClustering, {"n_components": 3, "random_state": 0}),
    (SpectralClustering, {"n_clusters": 3, "random_state": 0}),
    (FaissKMeansClustering, {"n_clusters": 3, "random_state": 0}),
    (DBSCANClustering, {}),
    (HDBSCANClustering, {}),
    (FaissDBSCANClustering, {}),
]

CENTRES = [(0.0, 0.0), (10.0, 10.0), (-10.0, 10.0)]

# FAISS trains its own k-means index and wants roughly forty points per
# centroid before it stops warning and starts converging, so the fixture is
# sized for the strictest model rather than the cheapest one.
PER_CENTRE = 100


def _blobs(per_centre=PER_CENTRE, spread=0.1, seed=0):
    """Three tight, far apart blobs that every model here can recover.

    The centres sit a hundred times the spread apart, so the grouping is not a
    matter of judgement: any algorithm that fails this is broken rather than
    merely differently tuned.
    """
    rng = np.random.default_rng(seed)
    points = np.vstack(
        [rng.normal(loc=c, scale=spread, size=(per_centre, 2)) for c in CENTRES]
    )
    return to_dashai_dataset(pd.DataFrame({"x": points[:, 0], "y": points[:, 1]}))


def _truth(per_centre=PER_CENTRE):
    """Which blob each row of ``_blobs`` was drawn from."""
    return np.repeat(range(len(CENTRES)), per_centre)


# --- the shared contract -----------------------------------------------------


@pytest.mark.parametrize("model_class", ALL_MODELS)
def test_every_model_assigns_one_label_per_row(model_class):
    x = _blobs()

    model = model_class()
    model.train(x)
    labels = np.asarray(model.get_cluster_labels(x))

    assert labels.shape == (len(CENTRES) * PER_CENTRE,)
    assert np.issubdtype(labels.dtype, np.integer)


@pytest.mark.parametrize("model_class", ALL_MODELS)
def test_every_model_is_declared_for_the_clustering_task(model_class):
    assert model_class.COMPATIBLE_COMPONENTS == ["ClusteringTask"]
    assert issubclass(model_class, ClusteringModel)


@pytest.mark.parametrize("model_class", ALL_MODELS)
def test_every_model_reports_fit_attributes_the_converter_can_serialise(model_class):
    """The report reaches the explorers as JSON, so a numpy array would break it."""
    model = model_class()
    model.train(_blobs())

    json.dumps(model.get_fit_attributes())


@pytest.mark.parametrize("model_class", ALL_MODELS)
def test_every_model_round_trips_through_save_and_load(model_class, tmp_path):
    x = _blobs()
    model = model_class()
    model.train(x)
    expected = list(np.asarray(model.get_cluster_labels(x)))

    path = tmp_path / "model.joblib"
    model.save(str(path))
    restored = model_class.load(str(path))

    assert list(np.asarray(restored.get_cluster_labels(x))) == expected


@pytest.mark.parametrize(("model_class", "params"), ASKED_FOR_THREE)
def test_every_model_recovers_three_separated_blobs(model_class, params):
    x = _blobs()
    truth = _truth()

    model = model_class(**params)
    model.train(x)
    labels = np.asarray(model.get_cluster_labels(x))

    clustered = labels[labels != -1]
    assert len(set(clustered.tolist())) == 3

    # Every row of a blob lands in one cluster, and no two blobs share it.
    per_blob = [set(labels[truth == k].tolist()) for k in range(len(CENTRES))]
    assert all(len(group) == 1 for group in per_blob)
    assert len({group.pop() for group in per_blob}) == 3


# --- what the converter relies on --------------------------------------------


def test_the_registry_finds_every_algorithm_once_its_module_is_imported():
    """``Clustering`` builds its dropdown from this, with no manual list."""
    registry = ClusteringModel.get_registry()

    for model_class in ALL_MODELS:
        assert registry[model_class.__name__] is model_class


def test_the_registry_leaves_out_the_abstract_adapters():
    """Only classes carrying their own SCHEMA are concrete algorithms."""
    registry = ClusteringModel.get_registry()

    assert "SklearnLikeClusterer" not in registry
    assert "FaissLikeClusterer" not in registry


# --- the behaviours each family is chosen for --------------------------------


def test_dbscan_calls_a_far_away_point_noise_rather_than_its_own_cluster():
    frame = _blobs().to_pandas()
    frame.loc[len(frame)] = {"x": 500.0, "y": 500.0}
    x = to_dashai_dataset(frame)

    model = DBSCANClustering()
    model.train(x)
    labels = np.asarray(model.get_cluster_labels(x))

    assert labels[-1] == -1
    assert (labels[:-1] != -1).all()


def test_kmeans_reports_its_centres_and_inertia_after_fitting():
    model = KMeansClustering(n_clusters=3, random_state=0)
    model.train(_blobs())

    attributes = model.get_fit_attributes()

    assert len(attributes["cluster_centers"]) == 3
    # Inertia is the summed squared distance to each centre. With 300 points
    # drawn around two axes at a spread of 0.1, that is 300 * 2 * 0.1 ** 2.
    assert attributes["inertia"] == pytest.approx(6.0, rel=0.3)


# --- the macOS deadlock ------------------------------------------------------


def test_faiss_is_pinned_to_one_thread_on_macos(monkeypatch):
    """FAISS and torch each ship an OpenMP runtime, and two of them in one
    process deadlock on macOS. That hung a CI job for six hours inside
    FaissKMeansClustering.train while the scikit-learn clusterers beside it
    finished in under a second.
    """
    faiss = FaissKMeansClustering._import_faiss()
    before = faiss.omp_get_max_threads()
    try:
        monkeypatch.setattr(sys, "platform", "darwin")

        FaissKMeansClustering._import_faiss()

        assert faiss.omp_get_max_threads() == 1
    finally:
        faiss.omp_set_num_threads(before)


def test_faiss_keeps_its_threads_everywhere_else(monkeypatch):
    """The adapter exists to accelerate large datasets, so only macOS pays."""
    faiss = FaissKMeansClustering._import_faiss()
    before = faiss.omp_get_max_threads()
    monkeypatch.setattr(sys, "platform", "linux")

    FaissKMeansClustering._import_faiss()

    assert faiss.omp_get_max_threads() == before
