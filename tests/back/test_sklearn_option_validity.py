"""Every option a schema offers must be one the wrapped library accepts.

A dropdown that lists a value scikit-learn rejects is worse than a missing
feature: the option looks supported, the form validates it, the parameters get
persisted, and the run fails with an ``InvalidParameterError`` inside a Huey
worker minutes later. Several of these had been shipping for a while, in one
case as the *first* option in the list, because scikit-learn removed the value
and nothing here noticed.

The check is mechanical, so it belongs in the suite rather than in someone's
memory. scikit-learn declares ``_parameter_constraints`` on every estimator, so
for each registered component that wraps one we can construct the component with
each declared option and ask scikit-learn's own constraint whether the value
that reaches it is acceptable.

Constructing the component rather than reading the schema matters: several
components legitimately translate a form-friendly sentinel into something a form
cannot express. ``random_state="RandomState"`` becomes a real
``numpy.random.RandomState`` instance in six converters, ``unknown_value="np.nan"``
becomes ``float("nan")``, and ``MLPClassifier``'s ``hidden_layer_size`` becomes
the ``(n,)`` tuple sklearn wants. Those are correct and this test must not flag
them, which it does not, because it inspects the value after construction.
"""

from typing import Any, Dict, List, Optional, Tuple

import pytest
from sklearn.utils._param_validation import make_constraint

from DashAI.back.dependencies.config_builder import get_initial_components


def _sklearn_base(component: type) -> Optional[type]:
    """Return the wrapped scikit-learn estimator in a component's MRO."""
    for ancestor in getattr(component, "__mro__", [])[1:]:
        if ancestor.__module__.startswith("sklearn.") and hasattr(
            ancestor, "_parameter_constraints"
        ):
            return ancestor
    return None


def _accepted(constraints: List[Any], value: Any) -> bool:
    """Whether scikit-learn's own constraints admit ``value``."""
    for constraint in constraints:
        try:
            if make_constraint(constraint).is_satisfied_by(value):
                return True
        except Exception:
            # A constraint shape this sklearn version cannot express as an
            # object (``no_validation`` and friends) means anything goes.
            return True
    return False


def _enum_options(prop: Dict[str, Any]) -> List[Any]:
    """Every literal option a property offers, across its union branches."""
    branches = prop.get("anyOf") or [prop]
    options: List[Any] = []
    for branch in branches:
        options.extend(branch.get("enum", []))
    return options


def _cases() -> List[Tuple[str, str, Any]]:
    """(component, parameter, option) for every option of every sklearn wrapper."""
    cases = []
    for component in get_initial_components():
        base = _sklearn_base(component)
        if base is None or not hasattr(component, "get_schema"):
            continue
        try:
            properties = component.get_schema().get("properties", {})
        except Exception:
            continue
        for name, prop in properties.items():
            if name not in base._parameter_constraints:
                # A parameter the estimator does not take is either handled by
                # the wrapper (MinMaxScaler splits feature_range into two form
                # fields) or dead. Either way it is not this test's business.
                continue
            for option in _enum_options(prop):
                cases.append((component.__name__, name, option))
    return cases


CASES = _cases()

#: Options whose spelling is dictated by an upstream bug rather than by us.
#: ``TruncatedSVD``'s ``power_iteration_normalizer`` accepts ``"OR"`` and
#: rejects ``"QR"`` in scikit-learn 1.7, which is a typo in scikit-learn: the
#: algorithm is QR decomposition. The schema offers the correct spelling and the
#: converter translates it, so the option that reaches sklearn is the typo.
KNOWN_UPSTREAM_QUIRKS = {("TruncatedSVD", "power_iteration_normalizer", "QR")}


def test_the_registry_has_sklearn_wrappers_to_check():
    """Guard the guard: a silent zero here would make the suite meaningless."""
    assert len(CASES) > 100, len(CASES)
    assert len({name for name, _, _ in CASES}) > 20


@pytest.mark.parametrize(
    ("component_name", "parameter", "option"),
    CASES,
    ids=[f"{c}.{p}={o!r}" for c, p, o in CASES],
)
def test_every_offered_option_is_one_sklearn_accepts(
    component_name: str, parameter: str, option: Any
):
    """Construct the component with the option and check what sklearn receives.

    A failure here means a user can pick that option in the form and the run
    will die at fit time. The fix is to correct the enum, not to skip the case.
    """
    component = next(
        c
        for c in get_initial_components()
        if getattr(c, "__name__", None) == component_name
    )
    base = _sklearn_base(component)
    properties = component.get_schema()["properties"]

    kwargs = {
        name: (option if name == parameter else prop.get("placeholder"))
        for name, prop in properties.items()
    }
    # Component-valued parameters carry a {component, params} placeholder that
    # only the registry can resolve; they are never enum options anyway.
    kwargs = {k: v for k, v in kwargs.items() if not isinstance(v, dict)}

    instance = component(**kwargs)
    reaching_sklearn = getattr(instance, parameter)

    if (component_name, parameter, option) in KNOWN_UPSTREAM_QUIRKS:
        # The translation is the point: the schema offers "QR" and sklearn must
        # receive its own misspelling. If sklearn ever fixes the typo this
        # assertion flips and tells us to drop the translation.
        assert reaching_sklearn == "OR", reaching_sklearn
        return

    assert _accepted(base._parameter_constraints[parameter], reaching_sklearn), (
        f"{component_name}.{parameter} offers {option!r}, which reaches sklearn as "
        f"{reaching_sklearn!r} and {base.__name__} rejects it. A user picking this "
        f"option gets an InvalidParameterError at fit time, inside a worker."
    )
