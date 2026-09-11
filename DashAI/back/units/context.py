"""Execution context shared between atomic units."""

import copy
import json
from typing import Any, Dict, Optional


class UnitContractError(Exception):
    """Raised when a unit's declared contract is violated.

    Either a required key is missing from the context before execution, or a
    promised key is missing after it.
    """


class ExecutionContext:
    """State that crosses the boundary between atomic units.

    The context deliberately splits its state in two halves with different
    rules:

    * ``refs``: JSON serializable references (ids, paths, index lists). This is
      the only half that can cross a process boundary. Jobs are shipped to the
      Huey worker with dill and rebuild their dependencies from a fresh
      container, so anything that must survive that trip has to be expressible
      as plain data.
    * ``cache``: live objects (datasets, models, tasks). Never serialized;
      always derivable again from the refs.

    Keeping the halves apart is what allows the same unit to run in-process
    (cache hit, nothing is reloaded) or, in the future, as an independently
    enqueued job (refs travel, the heavy objects are derived again).

    Parameters
    ----------
    refs : Dict[str, Any], optional
        Initial JSON serializable references.
    """

    def __init__(self, refs: Optional[Dict[str, Any]] = None) -> None:
        self._refs: Dict[str, Any] = {}
        self._cache: Dict[str, Any] = {}

        for key, value in (refs or {}).items():
            self.put_ref(key, value)

    @property
    def refs(self) -> Dict[str, Any]:
        """A deep copy of the serializable references held by the context."""
        return copy.deepcopy(self._refs)

    def put_ref(self, key: str, value: Any) -> None:
        """Store a durable, JSON serializable reference.

        The value is deep-copied on the way in, so a mutable dict handed in
        by the caller (e.g. an ORM-attached ``dict`` column) is never aliased.
        Without this, a later in-place edit made through the context — such as
        ``ModelFactory.update_parameters`` rewriting a nested ``fixed_value``
        — would silently write through to the caller's object.

        Parameters
        ----------
        key : str
            Name of the reference.
        value : Any
            Value to store. Must be JSON serializable.

        Raises
        ------
        UnitContractError
            If the value cannot be serialized to JSON.
        """
        try:
            json.dumps(value)
        except (TypeError, ValueError) as e:
            raise UnitContractError(
                f"Context reference '{key}' is not JSON serializable "
                f"({type(value).__name__}). Only ids, paths and plain data can "
                "cross a unit boundary; store live objects with put() instead."
            ) from e

        self._refs[key] = copy.deepcopy(value)

    def put(self, key: str, value: Any) -> None:
        """Store a live object in the in-process cache.

        Parameters
        ----------
        key : str
            Name of the value.
        value : Any
            Any object. It is never serialized.
        """
        self._cache[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value, looking in the cache before the references.

        A live object from the cache is returned by reference — that is the
        point of the cache half. A reference is returned as a deep copy, so
        mutating what comes back never reaches into the context's own state
        or, transitively, into whatever object a ``put_ref`` call was given.

        Parameters
        ----------
        key : str
            Name of the value.
        default : Any, optional
            Returned when the key is absent from both halves.

        Returns
        -------
        Any
            The cached object, a copy of the stored reference, or ``default``.
        """
        if key in self._cache:
            return self._cache[key]
        if key in self._refs:
            return copy.deepcopy(self._refs[key])
        return default

    def require(self, key: str) -> Any:
        """Retrieve a value, failing when it is absent.

        See :meth:`get` for the copy-on-read guarantee for references.

        Parameters
        ----------
        key : str
            Name of the value.

        Returns
        -------
        Any
            The cached object or a copy of the stored reference.

        Raises
        ------
        UnitContractError
            If the key is present in neither half of the context.
        """
        if key in self._cache:
            return self._cache[key]
        if key in self._refs:
            return copy.deepcopy(self._refs[key])

        raise UnitContractError(
            f"Context key '{key}' is not available. "
            f"Present keys: {sorted(set(self._cache) | set(self._refs))}."
        )

    def has(self, key: str) -> bool:
        """Return whether a key is present in either half of the context."""
        return key in self._cache or key in self._refs

    def origin(self, key: str) -> Optional[str]:
        """Return which half holds a key, without copying anything.

        ``get`` and ``has`` merge the two halves on purpose, and ``refs``
        deep-copies the whole reference half, so neither can answer this
        cheaply. Something that moves a value from one context to another has
        to know: the two halves have incompatible rules, and picking the wrong
        one fails in both directions. Handing a live dataset to ``put_ref``
        raises, and handing ``put`` a dict that was a reference silently drops
        the copy-on-read guarantee the reference depended on.

        The cache is checked first, matching ``get`` and ``require``, so a key
        present in both halves has one answer rather than two.

        Parameters
        ----------
        key : str
            Name of the value.

        Returns
        -------
        Optional[str]
            ``"cache"``, ``"ref"``, or ``None`` when the key is absent.
        """
        if key in self._cache:
            return "cache"
        if key in self._refs:
            return "ref"
        return None

    def clear_cache(self) -> None:
        """Drop every live object, keeping the references.

        Called by the orchestrator before ``gc.collect()`` so datasets, splits
        and models become collectable as soon as the job is done.
        """
        self._cache.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the context to the references that can cross a process.

        Returns
        -------
        Dict[str, Any]
            A deep copy of the JSON serializable half of the context.
        """
        return self.refs

    @classmethod
    def from_dict(cls, refs: Dict[str, Any]) -> "ExecutionContext":
        """Rebuild a context from previously serialized references.

        Parameters
        ----------
        refs : Dict[str, Any]
            References as returned by :meth:`to_dict`.

        Returns
        -------
        ExecutionContext
            A context with an empty cache; live objects are derived on demand.
        """
        return cls(refs=refs)
