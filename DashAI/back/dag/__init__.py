"""A sequential DAG engine over the atomic units.

Nothing here imports from ``DashAI/back/pipeline/``. That subsystem does not
run — its nodes implement two of ``BaseJob``'s four abstract methods, so they
cannot even be instantiated — and it is replaced rather than repaired.

The engine is deliberately sequential. Its predecessor was concurrent, and the
concurrency was not buying what it cost: the most expensive node in a pipeline
was already serialised behind an exclusive lock, every context and database
write was wrapped in another, and SQLite answered the remaining concurrent
writes with "database is locked" often enough to need retries with exponential
backoff. Units open a database session each, which is safe in sequence and was
the source of that contention in parallel.
"""

from DashAI.back.dag.graph import Edge, Graph, GraphError, Node, connect, sinks
from DashAI.back.dag.validate import resolve_unit_class, validate

__all__ = [
    "Edge",
    "Graph",
    "GraphError",
    "Node",
    "connect",
    "resolve_unit_class",
    "sinks",
    "validate",
]
