"""Helpers to read the ``splits`` payload stored in a model session.

The payload is written by the frontend as a flat object: the selected
splitter's schema parameters at the top level, plus the meta keys
``splitter_name``, ``splitType`` and ``splitted_indexes``. Sessions created
before the splitter forms were generated from the component schemas used a
different set of keys, so every reader normalizes the payload first.
"""

import json
from typing import Any, Dict, List, Optional, Tuple, Type

# Before fold splitters existed the payload named no splitter at all: every
# split was a holdout split.
DEFAULT_SPLITTER_NAME = "HoldoutSplitter"

INDEX_KEY_BY_SPLIT = {
    "train": "train_indexes",
    "test": "test_indexes",
    "validation": "val_indexes",
}

META_KEYS = ("splitter_name", "splitType", "splitted_indexes", "seed")


def normalize_splits_payload(splits_data: Dict[str, Any]) -> Dict[str, Any]:
    """Translate a legacy splits payload into the current contract.

    Four legacy shapes are handled:

    - No ``splitter_name``, from before fold splitters existed.
    - ``seed`` instead of the schema's ``random_state``.
    - ``holdout`` instead of ``test_size``, which is what the reserved
      proportion was called when fold splitters first got one.
    - ``train`` / ``test`` / ``validation`` holding index lists instead of
      proportions, which is how manual and predefined holdout splits used to
      be stored.

    Parameters
    ----------
    splits_data : dict
        The payload as stored in ``ModelSession.splits``.

    Returns
    -------
    dict
        A new dictionary following the current contract. The input is left
        untouched.
    """
    normalized = dict(splits_data)

    if not isinstance(normalized.get("splitter_name"), str):
        normalized["splitter_name"] = DEFAULT_SPLITTER_NAME

    if "random_state" not in normalized and "seed" in normalized:
        normalized["random_state"] = normalized["seed"]

    if "test_size" not in normalized and "holdout" in normalized:
        normalized["test_size"] = normalized["holdout"]

    index_lists = {
        split: normalized[split]
        for split in INDEX_KEY_BY_SPLIT
        if isinstance(normalized.get(split), list)
    }
    if index_lists:
        splitted_indexes = dict(normalized.get("splitted_indexes") or {})
        for split, indexes in index_lists.items():
            splitted_indexes.setdefault(INDEX_KEY_BY_SPLIT[split], indexes)
            del normalized[split]
        normalized["splitted_indexes"] = splitted_indexes
        normalized.setdefault("splitType", "manual")

    return normalized


def schema_placeholder_defaults(splitter_cls: Type) -> Dict[str, Any]:
    """Collect the placeholder value declared for each schema parameter.

    The frontend seeds its form with these values, so filling them in makes a
    partial payload (for example a manual split, which carries no
    proportions) validate exactly as the form would have submitted it.

    Parameters
    ----------
    splitter_cls : type
        A splitter class exposing ``get_schema``.

    Returns
    -------
    dict
        Parameter name to placeholder value, skipping parameters that declare
        no placeholder.
    """
    properties = splitter_cls.get_schema().get("properties", {})
    return {
        name: prop["placeholder"]
        for name, prop in properties.items()
        if "placeholder" in prop
    }


def splitter_class_for(session_splits: Dict[str, Any], component_registry) -> Type:
    """Resolve the splitter class that produced a run.

    Parameters
    ----------
    session_splits : dict
        The ``ModelSession.splits`` payload, already parsed.
    component_registry : ComponentRegistry
        Registry used to resolve the splitter by name.

    Returns
    -------
    type
        The splitter class named by the payload.

    Raises
    ------
    ValueError
        If the payload names a splitter that is not registered.
    """
    splitter_name = normalize_splits_payload(session_splits)["splitter_name"]
    if splitter_name not in component_registry:
        raise ValueError(f"Splitter {splitter_name} does not exist in the registry.")
    return component_registry[splitter_name]["class"]


def explainable_indexes(
    splitter_class: Type, split_indexes: Dict[str, Any]
) -> Tuple[List[int], List[int], List[int]]:
    """Resolve the rows an explainer may use for a run of a given splitter.

    The partitions and their names come from the splitter itself; this maps them
    onto the three slots the explainers' dataset dictionary is built from.

    Parameters
    ----------
    splitter_class : type
        The splitter that produced the run.
    split_indexes : dict
        The ``Run.split_indexes`` payload, already parsed.

    Returns
    -------
    tuple[list[int], list[int], list[int]]
        Row indexes for the train, evaluation and validation slots. Splitters
        without a validation partition return an empty third list.

    Raises
    ------
    ValueError
        If the run has no rows in the partition explanations are measured on.
    """
    try:
        partitions = splitter_class.explainable_partitions(split_indexes)
    except (KeyError, NotImplementedError, TypeError) as e:
        raise ValueError(
            "The run's split indexes do not match the splitter that produced "
            "it, so there is no data to explain."
        ) from e

    training = splitter_class.TRAINING_PARTITION
    unseen = {
        name: indexes
        for name, indexes in partitions.items()
        if name != training and indexes
    }
    if not unseen:
        raise ValueError(
            "The run has no rows outside the data the model was fitted on (its "
            "test partition is empty), so there is nothing to explain."
        )

    # Explanations are measured on the test partition, falling back to whichever
    # unseen partition the run actually filled: a holdout run configured without
    # a test partition is explained on validation.
    evaluation = unseen.get("test") or next(iter(unseen.values()))

    return partitions.get(training, []), evaluation, partitions.get("val", [])


def _parse_payload(payload: Any) -> Dict[str, Any]:
    """Return a splits payload as a dictionary, decoding it when stored as text.

    Parameters
    ----------
    payload : Any
        A ``ModelSession.splits`` or ``Run.split_indexes`` value, which the
        database may hold either as a dict or as its JSON encoding.

    Returns
    -------
    dict
        The decoded payload, or an empty dictionary when there is none.
    """
    if isinstance(payload, str):
        return json.loads(payload) if payload else {}
    return payload or {}


def run_splits(
    session_splits: Any, split_indexes: Any, component_registry
) -> List[Dict[str, Any]]:
    """Describe the dataset partitions of a run that a later job may target.

    Which partitions exist depends on how the run was evaluated, so the
    splitter that produced it decides the list and its names. Both explaining
    and predicting on the training dataset offer the same set: the partitions
    the saved model was measured on, plus the whole dataset.

    Parameters
    ----------
    session_splits : Any
        The ``ModelSession.splits`` payload, as a dict or its JSON encoding.
    split_indexes : Any
        The ``Run.split_indexes`` payload, as a dict or its JSON encoding.
    component_registry : ComponentRegistry
        Registry used to resolve the splitter by name.

    Returns
    -------
    list[dict]
        One ``{"name", "rows"}`` entry per partition, empty when the run has no
        partition worth offering.

    Raises
    ------
    ValueError
        If the payload names a splitter that is not registered.
    """
    splitter_class = splitter_class_for(
        _parse_payload(session_splits), component_registry
    )
    return splitter_class.explainable_splits(_parse_payload(split_indexes))


def run_split_indexes(
    session_splits: Any, split_indexes: Any, component_registry, split: str
) -> Optional[List[int]]:
    """Resolve the rows one named partition of a run holds.

    Parameters
    ----------
    session_splits : Any
        The ``ModelSession.splits`` payload, as a dict or its JSON encoding.
    split_indexes : Any
        The ``Run.split_indexes`` payload, as a dict or its JSON encoding.
    component_registry : ComponentRegistry
        Registry used to resolve the splitter by name.
    split : str
        Name of the partition, as reported by :func:`run_splits`. ``"all"``
        stands for the whole dataset.

    Returns
    -------
    list[int] or None
        The row indexes of the partition, or None when ``split`` covers the
        whole dataset and no selection is needed.

    Raises
    ------
    ValueError
        If the splitter is not registered, or if it declares no partition by
        that name.
    """
    if not split or split == "all":
        return None

    splitter_class = splitter_class_for(
        _parse_payload(session_splits), component_registry
    )
    try:
        partitions = splitter_class.explainable_partitions(
            _parse_payload(split_indexes)
        )
    except (KeyError, NotImplementedError, TypeError) as e:
        raise ValueError(
            "The run's split indexes do not match the splitter that produced it."
        ) from e

    if split not in partitions:
        raise ValueError(f"{split} is not a partition of this run.")
    return list(partitions[split])


def predictable_splits(
    session_splits: Any,
    split_indexes: Any,
    component_registry,
    *,
    task_name: str,
    evaluation_strategy: str,
) -> List[Dict[str, Any]]:
    """Describe the partitions of a run its saved model can be asked to predict.

    For most tasks that is every partition the run has, plus the whole dataset:
    a fitted classifier will label the rows it was trained on. A model of a
    task that predicts forward only cannot. It reads a date and answers how far
    past the end of training it lies, so every partition inside the window the
    kept model was fitted through is dropped, and so is the whole dataset entry
    that contains them.

    Which rows those are comes from the evaluation strategy, since strategies
    differ on what the kept model is allowed to learn from: a holdout run fits
    on its training partition, while the folds of a rolling origin run walk
    through everything outside the reserved tail. The comparison is made on row
    indexes, which run in time order for every splitter a forward-only task can
    use.

    Parameters
    ----------
    session_splits : Any
        The ``ModelSession.splits`` payload, as a dict or its JSON encoding.
    split_indexes : Any
        The ``Run.split_indexes`` payload, as a dict or its JSON encoding.
    component_registry : ComponentRegistry
        Registry used to resolve the splitter, task and strategy by name.
    task_name : str
        The ``ModelSession.task_name`` of the run.
    evaluation_strategy : str
        The ``ModelSession.evaluation_strategy`` of the run.

    Returns
    -------
    list[dict]
        One ``{"name", "rows"}`` entry per partition that can be predicted,
        empty when there is none.

    Raises
    ------
    ValueError
        If the payload names a splitter that is not registered.
    """
    splits = run_splits(session_splits, split_indexes, component_registry)

    task_class = _registered_class(component_registry, task_name)
    if not getattr(task_class, "PREDICTS_FORWARD_ONLY", False):
        return splits

    strategy_class = _registered_class(component_registry, evaluation_strategy)
    fitted_partitions = getattr(strategy_class, "FINAL_FIT_PARTITIONS", ("train",))

    splitter_class = splitter_class_for(
        _parse_payload(session_splits), component_registry
    )
    try:
        partitions = splitter_class.explainable_partitions(
            _parse_payload(split_indexes)
        )
    except (KeyError, NotImplementedError, TypeError):
        return []

    fitted = [
        index for name in fitted_partitions for index in partitions.get(name) or []
    ]
    if not fitted:
        return []

    last_fitted = max(fitted)
    return [
        {"name": name, "rows": len(indexes)}
        for name, indexes in partitions.items()
        if indexes and min(indexes) > last_fitted
    ]


def _registered_class(component_registry, name: str) -> Optional[Type]:
    """Return a registered component class, or None when it is not installed.

    A run whose task or strategy came from a plugin that has since been removed
    still has to describe itself as well as it can, so a missing name is not an
    error here.

    Parameters
    ----------
    component_registry : ComponentRegistry
        Registry used to resolve the component by name.
    name : str
        Name of the component to resolve.

    Returns
    -------
    type or None
        The registered class, or None when the registry does not have it.
    """
    try:
        if name not in component_registry:
            return None
        return component_registry[name]["class"]
    except (KeyError, TypeError):
        return None
