"""The shape of the metadata the frontend reads to filter dataset columns.

``get_metadata()`` is a wire contract, not an internal dict: the browser decides
which explorers and converters a dataset can use by reading it. Nothing pinned
that shape, and it drifted, twice at once:

* ``restricted_dtypes`` was renamed to ``non_allowed_dtypes`` and the old key is
  popped on the way out. One frontend consumer kept reading the old name with no
  fallback, so it threw on every render and the exploration wizard showed an
  error with zero explorers to choose from.
* ``allowed_dtypes`` is normalized here so that ``["*"]`` and absent both become
  ``[]``, meaning "no restriction". The same consumer tested
  ``allowed_dtypes.includes("*")`` to detect that case. Since ``"*"`` can no
  longer arrive, the test was always false, every unrestricted explorer was
  filtered against an empty allow-list, and all of them were disabled.

So this file asserts what the payload contains and, just as importantly, what it
must not contain. The browser's half of the same contract is in
``DashAI/front/src/utils/columnEligibility.test.js``, and both sides read one
implementation each.
"""

from typing import Any, Dict, List, Tuple

import pytest

from DashAI.back.dependencies.config_builder import get_initial_components

#: Keys DashAI/front/src/utils/columnEligibility.js reads. Removing or renaming
#: one of these is a breaking change for the column pickers, whatever the
#: backend thinks of it.
KEYS_THE_FRONTEND_READS = (
    "allowed_types",
    "allowed_dtypes",
    "non_allowed_dtypes",
    "input_cardinality",
)

#: Renamed keys. A component that resurrects one is talking to a consumer that
#: no longer exists.
RETIRED_KEYS = ("restricted_dtypes",)


def _components_with_metadata() -> List[Tuple[str, Dict[str, Any]]]:
    rows = []
    for component in get_initial_components():
        if not hasattr(component, "get_metadata"):
            continue
        try:
            metadata = component.get_metadata()
        except Exception:
            continue
        if not isinstance(metadata, dict):
            continue
        rows.append((component.__name__, metadata))
    return rows


METADATA = _components_with_metadata()

#: Components whose metadata takes part in column filtering, i.e. the ones the
#: pickers judge. A component with no dtype metadata at all is not one of them.
FILTERING = [
    (name, metadata)
    for name, metadata in METADATA
    if "allowed_dtypes" in metadata or "non_allowed_dtypes" in metadata
]


def test_there_are_components_to_check():
    assert len(METADATA) > 100, len(METADATA)
    assert len(FILTERING) > 20, len(FILTERING)


@pytest.mark.parametrize(("name", "metadata"), FILTERING, ids=[n for n, _ in FILTERING])
def test_every_key_the_frontend_reads_is_present(name: str, metadata: Dict[str, Any]):
    missing = [key for key in KEYS_THE_FRONTEND_READS if key not in metadata]
    assert not missing, (
        f"{name} serves metadata without {missing}. The column pickers read "
        "those keys directly, so an absent one is either a crash or a "
        "restriction that silently never applies."
    )


@pytest.mark.parametrize(("name", "metadata"), METADATA, ids=[n for n, _ in METADATA])
def test_no_component_serves_a_retired_key(name: str, metadata: Dict[str, Any]):
    present = [key for key in RETIRED_KEYS if key in metadata]
    assert not present, (
        f"{name} serves {present}, which no consumer reads any more. Serving a "
        "retired key is how the two sides drift back apart."
    )


@pytest.mark.parametrize(("name", "metadata"), FILTERING, ids=[n for n, _ in FILTERING])
def test_no_restriction_is_spelled_as_an_empty_list(
    name: str, metadata: Dict[str, Any]
):
    """``"*"`` is normalized away here, so the browser can never receive it."""
    allowed = metadata["allowed_dtypes"]
    assert isinstance(allowed, list), (name, allowed)
    assert "*" not in allowed, (
        f"{name} serves allowed_dtypes={allowed!r}. The wildcard is normalized "
        "to an empty list before serving, and a consumer testing for it would "
        "read 'no restriction' as 'nothing allowed'."
    )


@pytest.mark.parametrize(("name", "metadata"), FILTERING, ids=[n for n, _ in FILTERING])
def test_the_blacklist_is_always_a_list(name: str, metadata: Dict[str, Any]):
    refused = metadata["non_allowed_dtypes"]
    assert isinstance(refused, list), (name, refused)


@pytest.mark.parametrize(("name", "metadata"), FILTERING, ids=[n for n, _ in FILTERING])
def test_cardinality_is_usable(name: str, metadata: Dict[str, Any]):
    cardinality = metadata["input_cardinality"]
    assert isinstance(cardinality, dict), (name, cardinality)
    assert cardinality.keys() <= {"min", "max", "exact"}, (name, cardinality)
    assert "exact" in cardinality or "min" in cardinality, (
        f"{name} declares input_cardinality={cardinality!r}, which tells a "
        "picker nothing about how many columns it needs."
    )
    if "min" in cardinality and "max" in cardinality:
        assert cardinality["min"] <= cardinality["max"], (name, cardinality)


@pytest.mark.parametrize(("name", "metadata"), FILTERING, ids=[n for n, _ in FILTERING])
def test_allowed_types_are_serialized_names(name: str, metadata: Dict[str, Any]):
    """The browser compares these against the strings a column reports."""
    for entry in metadata["allowed_types"]:
        assert isinstance(entry, str), (
            f"{name} serves a non-string in allowed_types ({entry!r}). The "
            "column table compares it against a column's own type name, so a "
            "class here can never match anything."
        )


def test_the_declared_blacklists_are_the_ones_we_think_they_are():
    """A named list, so growing it is a decision rather than an accident.

    Two of these are converters, and the notebook's converter picker used to
    ignore the blacklist entirely, so SMOTE was offered for datasets whose
    columns the backend would then refuse.
    """
    with_blacklist = sorted(
        name for name, metadata in FILTERING if metadata["non_allowed_dtypes"]
    )
    assert with_blacklist == [
        "CorrelationMatrixExplorer",
        "CovarianceMatrixExplorer",
        "ECDFPlotExplorer",
        "MultiColumnBoxPlotExplorer",
        "ParallelCordinatesExplorer",
        "SMOTEConverter",
        "SMOTEENNConverter",
        "ScatterMatrixExplorer",
        "ScatterPlotExplorer",
    ], with_blacklist
