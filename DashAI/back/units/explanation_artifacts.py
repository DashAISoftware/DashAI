"""Shared helpers for the two explanation-generating units.

Not a unit: no configuration, no context, nothing to declare. It lives here
rather than in ``job/`` because importing from a job into a unit would invert
the dependency.
"""

import logging
from typing import Any, Tuple

from DashAI.back.job.base_job import JobError

log = logging.getLogger(__name__)


def build_explainer(scope: str, selected: dict, trained_model: Any) -> Any:
    """Resolve an explainer component and bind it to a trained model.

    Shared by the two scope-specific build units: building is identical either
    way, only the registry the component comes from differs.

    Takes and returns plain values instead of touching the context. That keeps
    every context write inside the unit itself, where the contract audit can
    see it — a ``ctx.put`` hidden in a helper is invisible to the static check
    and would let a broken ``PROVIDES`` through.

    Parameters
    ----------
    scope : str
        ``"global"`` or ``"local"``. Only decorates the error messages, which
        are user-visible and worded per scope.
    selected : dict
        The ``{"component": ..., "params": ...}`` value of the unit's field.
    trained_model : Any
        The model the explainer explains.

    Returns
    -------
    Any
        The instantiated explainer.

    Raises
    ------
    JobError
        If the component is not registered or cannot be instantiated.
    """
    from kink import di

    component_registry = di["component_registry"]

    explainer_name = selected["component"]

    try:
        explainer_class = component_registry[explainer_name]["class"]
    except Exception as e:
        log.exception(e)
        raise JobError(
            f"Unable to find the {scope} explainer with name "
            f"{explainer_name} in registry.",
        ) from e

    try:
        return explainer_class(model=trained_model, **(selected.get("params") or {}))
    except Exception as e:
        log.exception(e)
        raise JobError(
            f"Unable to instantiate {scope} explainer.",
        ) from e


def dump_explanation(explanation: Any, plots: Any, prefix: str, key: int) -> Tuple:
    """Pickle an explanation and its plots under the explanations directory.

    Both files are named after the explanation they belong to, so re-running
    one overwrites its own artifacts and never another's.

    Parameters
    ----------
    explanation : Any
        Whatever the explainer's ``explain``/``explain_instance`` returned.
    plots : Any
        The normalized artifacts produced from that explanation.
    prefix : str
        ``"global"`` or ``"local"``: the two scopes keep separate file names
        because their ids come from separate tables and would otherwise clash.
    key : int
        Identifier of the explanation row.

    Returns
    -------
    Tuple[str, str]
        The explanation path and the plot path.

    Raises
    ------
    JobError
        If either file cannot be written.
    """
    import os
    import pickle

    from kink import di

    config = di["config"]

    plots_name = "plot" if prefix == "global" else "plots"

    try:
        explanation_path = os.path.join(
            config["EXPLANATIONS_PATH"], f"{prefix}_explanation_{key}.pickle"
        )
        with open(explanation_path, "wb") as file:
            pickle.dump(explanation, file)

        plot_path = os.path.join(
            config["EXPLANATIONS_PATH"],
            f"{prefix}_explanation_{plots_name}_{key}.pickle",
        )
        with open(plot_path, "wb") as file:
            pickle.dump(plots, file)

    except Exception as e:
        log.exception(e)
        raise JobError(
            "Explanation file saving failed",
        ) from e

    return explanation_path, plot_path
