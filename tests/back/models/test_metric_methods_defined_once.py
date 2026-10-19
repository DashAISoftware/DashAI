"""The scoring methods of a model are defined once, on ``BaseModel``.

``test_base_model_defines_compute_metrics_exactly_once`` guards ``BaseModel``
against a second ``compute_metrics`` in its own body. It cannot see a subclass:
when clustering split ``BaseModel`` into ``SupervisedModel`` and
``ClusteringModel``, ``SupervisedModel`` arrived with a copy of the whole
scoring block taken from an older ``BaseModel``. The merge was clean, and the
copy overrode the one every unit relies on -- a ``compute_metrics`` that
answered ``{}`` where the units expect ``None``, and a ``calculate_metrics``
that no longer handed back what it wrote. Nothing failed at import, because an
override is legal Python and ``@final`` is not enforced at runtime.

Parsed rather than introspected, for the same reason as the original guard:
``getattr`` sees one attribute however many classes define it.
"""

import ast
from pathlib import Path

import pytest

import DashAI.back.models as models_package

SCORING_METHODS = (
    "compute_metrics",
    "calculate_metrics",
    "_score_split",
    "_save_metrics",
)

MODELS_DIR = Path(models_package.__file__).parent


def _definitions(name: str) -> list:
    """Every ``Class.method`` under ``DashAI/back/models`` with that name."""
    found = []
    for path in sorted(MODELS_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if (
                    isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and item.name == name
                ):
                    relative = path.relative_to(MODELS_DIR).as_posix()
                    found.append(f"{relative}::{node.name}")
    return found


def test_the_audit_actually_finds_the_model_modules():
    """Guards the parser: the assertion below means nothing on an empty walk."""
    assert (MODELS_DIR / "base_model.py").exists()
    assert len(list(MODELS_DIR.rglob("*.py"))) > 50


@pytest.mark.parametrize("name", SCORING_METHODS)
def test_a_scoring_method_is_defined_only_on_base_model(name):
    assert _definitions(name) == ["base_model.py::BaseModel"]
