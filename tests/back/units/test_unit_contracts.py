"""A contract audit over every registered unit, enforced as a test.

The individual unit tests check behaviour; this one checks that the *declared*
contract matches the code. Undeclared context reads are the recurring mistake in
this design: they never break the job that happens to wire the context by hand,
so they survive every end-to-end test and only surface when something reuses the
unit — which is the whole point of having units.
"""

import ast
import pathlib
import re

import pytest

UNITS_DIR = pathlib.Path(__file__).resolve().parents[3] / "DashAI" / "back" / "units"

#: Keys a unit reads that its own execution produces, so they need no declaration.
SELF_PRODUCED = {"dataset"}


def _unit_modules():
    for path in sorted(UNITS_DIR.glob("*.py")):
        if path.name in {"__init__.py", "base_unit.py", "context.py"}:
            continue
        yield path


def _string_literals(node):
    return {
        element.value
        for element in ast.walk(node)
        if isinstance(element, ast.Constant) and isinstance(element.value, str)
    }


def _all_classes():
    """Every class defined under ``units/``, by name.

    Built first so a unit that inherits from another unit can be resolved: the
    audit reads source rather than importing, so a base class is just a name
    until something maps it back to a definition.
    """
    classes = {}
    for path in _unit_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes[node.name] = node
    return classes


_CLASSES = _all_classes()


def _is_unit(node):
    """A class deriving from ``BaseUnit``, directly or through another unit."""
    for base in node.bases:
        if not isinstance(base, ast.Name):
            continue
        if base.id == "BaseUnit":
            return True
        parent = _CLASSES.get(base.id)
        if parent is not None and parent is not node and _is_unit(parent):
            return True
    return False


def _unit_class(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and _is_unit(node):
            return node
    return None


def _lineage(cls):
    """The class and the units it inherits from, nearest first.

    Everything below reads the whole lineage rather than one class body. A unit
    that extends another one inherits both its declarations and the code that
    honours them, so auditing only its own body would report that it promises
    keys it never writes -- which is the same blindness a shared helper causes,
    arriving by a different road.
    """
    chain = [cls]
    for base in cls.bases:
        if not isinstance(base, ast.Name):
            continue
        parent = _CLASSES.get(base.id)
        if parent is not None and parent is not cls and _is_unit(parent):
            chain.extend(_lineage(parent))
    return chain


def _declared(cls, name):
    # Nearest declaration wins: a subclass that redeclares PROVIDES replaces
    # what it inherited rather than adding to it, the way Python resolves it.
    for ancestor in _lineage(cls):
        for node in ancestor.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == name for t in node.targets
            ):
                return _string_literals(node.value)
    return set()


def _context_calls(cls, methods):
    """Every ``ctx.<method>("key")`` literal in the class and what it extends."""
    keys = set()
    for ancestor in _lineage(cls):
        keys |= _context_calls_in(ancestor, methods)
    return keys


def _context_calls_in(cls, methods):
    keys = set()
    for node in ast.walk(cls):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in methods
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "ctx"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            keys.add(node.args[0].value)
    return keys


def _session_names(cls):
    """Names bound by ``with session_factory() as <name>:`` inside the class."""
    names = set()
    for node in ast.walk(cls):
        if not isinstance(node, (ast.With, ast.AsyncWith)):
            continue
        for item in node.items:
            call = item.context_expr
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and "session" in call.func.id.lower()
                and isinstance(item.optional_vars, ast.Name)
            ):
                names.add(item.optional_vars.id)
    return names


def _parsed_units():
    units = []
    for path in _unit_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        cls = _unit_class(tree)
        if cls is not None:
            units.append((path.name, cls))
    return units


UNITS = _parsed_units()


def test_the_audit_actually_found_the_units():
    """Guards the audit itself: a broken parser would make it vacuously pass."""
    assert {name for name, _ in UNITS} >= {
        "load_dataset_unit.py",
        "apply_converter_unit.py",
        "save_dataset_unit.py",
    }


@pytest.mark.parametrize(("name", "cls"), UNITS, ids=[name for name, _ in UNITS])
def test_every_context_key_a_unit_reads_is_declared_in_requires(name, cls):
    read = _context_calls(cls, {"require", "get", "has"})
    declared = _declared(cls, "REQUIRES") | _declared(cls, "PROVIDES") | SELF_PRODUCED

    undeclared = read - declared
    assert not undeclared, (
        f"{name} reads {sorted(undeclared)} from the context without declaring "
        "them in REQUIRES. A caller inspecting the contract cannot know they "
        "are needed, and a missing value reads as 'not applicable' instead of "
        "'wiring mistake'."
    )


@pytest.mark.parametrize(("name", "cls"), UNITS, ids=[name for name, _ in UNITS])
def test_a_unit_does_not_require_a_key_it_never_reads(name, cls):
    """The mirror of the test above, and just as load-bearing.

    ``__call__`` demands every key in ``REQUIRES`` unconditionally, so a key
    listed but never read is not harmless documentation: it rejects any upstream
    that does not happen to publish it. ``PrepareExplanationDataUnit`` used to
    require ``dataset_id`` — left over from an error message that moved to the
    job — which would have made it impossible to compose after
    ``BuildManualInputUnit``, whose ``PROVIDES`` is just ``("dataset",)``.

    It passed every end-to-end test because the one job wiring it happened to
    run a loader that publishes the id first. That is exactly the class of
    mistake this file exists to catch.
    """
    required = _declared(cls, "REQUIRES")
    read = _context_calls(cls, {"require", "get", "has"})

    unread = required - read
    assert not unread, (
        f"{name} declares {sorted(unread)} in REQUIRES but never reads them. "
        "Every declared key is demanded before the unit runs, so an unused one "
        "only narrows what the unit can be composed after."
    )


@pytest.mark.parametrize(("name", "cls"), UNITS, ids=[name for name, _ in UNITS])
def test_every_key_a_unit_promises_is_actually_written(name, cls):
    written = _context_calls(cls, {"put", "put_ref"})
    promised = _declared(cls, "PROVIDES")

    unwritten = promised - written
    assert not unwritten, (
        f"{name} promises {sorted(unwritten)} in PROVIDES but never writes it."
    )


@pytest.mark.parametrize(("name", "cls"), UNITS, ids=[name for name, _ in UNITS])
def test_a_unit_does_not_use_the_context_as_its_own_scratchpad(name, cls):
    """A key written and read by the same unit, and promised to nobody.

    That is instance state wearing a context key's clothes: two units of the
    same class in one context would overwrite each other. It belongs on
    ``self``, memoized, the way the registry lookups are.
    """
    written = _context_calls(cls, {"put", "put_ref"})
    read = _context_calls(cls, {"require", "get", "has"})
    promised = _declared(cls, "PROVIDES")

    scratch = (written & read) - promised - SELF_PRODUCED
    assert not scratch, (
        f"{name} writes and reads {sorted(scratch)} without promising it. "
        "Keep per-instance state on the unit, not in the shared context."
    )


def test_no_unit_requires_a_key_that_no_unit_provides():
    """Every declared input has to have a declared producer.

    This is what makes a static graph validator decidable. As long as some key
    has no producer anywhere in the palette, "nothing supplies this key" is
    ambiguous: it could be an edge the user forgot to draw, or a constant the
    engine is expected to inject. A validator cannot tell those apart, and the
    consequences are not symmetric -- a wrongly injected id is read as a
    legitimate value and fails silently.

    ``run_id`` was the only such key: four units required it and none published
    it, because in a job it arrived through ``self.kwargs``. It lives in unit
    configuration now, where the schema validates it. The rule that keeps it
    that way: a key in ``REQUIRES`` is something an upstream unit produces; a
    constant the caller chooses is configuration.
    """
    required = {}
    provided = set()
    for name, cls in UNITS:
        provided |= _declared(cls, "PROVIDES")
        for key in _declared(cls, "REQUIRES"):
            required.setdefault(key, []).append(name)

    orphans = {key: names for key, names in required.items() if key not in provided}
    assert not orphans, (
        "These keys are required but no unit provides them: "
        f"{ {key: sorted(names) for key, names in sorted(orphans.items())} }. "
        "A key with no producer makes 'nothing supplies this' ambiguous for the "
        "graph validator. Put caller-chosen constants in the unit's config, not "
        "in the context."
    )


@pytest.mark.parametrize(("name", "cls"), UNITS, ids=[name for name, _ in UNITS])
def test_a_unit_does_not_write_domain_rows(name, cls):
    """Units read the database; jobs and endpoints write it.

    A unit that persists an application entity cannot be reused by a caller
    that has no such entity to persist against -- and it is the caller, not the
    unit, that owns transaction boundaries and status transitions. Several units
    do open a session, always read-only (``db.get`` / ``db.query``); the ones
    whose verb is "save" write to disk and publish the path.

    The one place a unit reaches a write is indirect and named:
    ``EvaluateModelUnit`` calls ``BaseModel.calculate_metrics``, which persists
    through a session of its own. That is why that unit needs a real ``Run``
    row and refuses to run without one.
    """
    # Whatever the unit bound its session to, rather than a fixed list of
    # names: a unit that writes through ``as s:`` would otherwise slip past.
    sessions = {"db", "session", "sess"} | _session_names(cls)

    writes = set()
    for node in ast.walk(cls):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"add", "add_all", "delete", "commit", "flush"}
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in sessions
        ):
            writes.add(f"{node.func.value.id}.{node.func.attr}")

    assert not writes, (
        f"{name} writes to the database ({sorted(writes)}). Transaction "
        "boundaries and status transitions belong to the caller, and a unit "
        "that persists an application entity cannot be reused by a caller that "
        "has none."
    )


# --- The configuration side of the contract ---------------------------------
#
# Until now this file audited only the context. Configuration went unchecked,
# and it could not be checked here: telling a user-facing field from an
# engine-supplied one meant reading a flag off the emitted JSON schema, which
# needs the imported class. Splitting the two declarations apart put both within
# reach of the AST.

#: Names that usually belong to plumbing: an id, a path, a prefix. Not a
#: definition, a net -- a new field shaped like this has to be classified rather
#: than land in a form by default.
_PLUMBING_SHAPED = re.compile(r"(_id|_path|_prefix)$|^path$")

#: Fields a user does choose, but that a plain text input cannot render: they
#: need to select an entity, or to type a row. They stay in the schema, because
#: needing a purpose-built widget is a rendering problem and hiding them would
#: answer the wrong question. The value records what each one needs, so the day
#: a node form is built it can tell "do not show this" from "show this
#: differently" instead of rediscovering the distinction.
NEEDS_A_WIDGET = {
    ("save_dataset_to_path_unit.py", "path"): "directory picker",
    ("load_dataset_unit.py", "dataset_id"): "dataset selector",
    ("load_dataset_unit.py", "notebook_id"): "notebook selector",
    ("load_datafile_dataset_unit.py", "datafile_id"): "datafile selector",
    ("load_run_model_unit.py", "run_id"): "run selector",
    ("load_trained_model_unit.py", "run_id"): "run selector",
    ("run_exploration_unit.py", "explorer_id"): "exploration selector",
    ("save_exploration_unit.py", "explorer_id"): "exploration selector",
    ("generate_global_explanation_unit.py", "explainer_id"): "explainer selector",
    ("generate_local_explanation_unit.py", "explainer_id"): "explainer selector",
    ("generate_local_explanation_unit.py", "instance_dataset_id"): "dataset selector",
    ("build_manual_input_unit.py", "manual_input_data"): "typed row editor",
    ("generate_local_explanation_unit.py", "manual_input_data"): "typed row editor",
}


def _schema_fields(tree):
    """Names annotated in the module's ``*Schema`` class, from the AST."""
    names = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.ClassDef) and node.name.endswith("Schema")):
            continue
        for statement in node.body:
            if isinstance(statement, ast.AnnAssign) and isinstance(
                statement.target, ast.Name
            ):
                names.add(statement.target.id)
    return names


def _config_reads(cls):
    reads = set()
    for ancestor in _lineage(cls):
        reads |= _config_reads_in(ancestor)
    return reads


def _config_reads_in(cls):
    """Every ``self.config["key"]`` and ``self.config.get("key")`` in the class."""
    keys = set()
    for node in ast.walk(cls):
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "config"
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        ):
            keys.add(node.slice.value)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "config"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            keys.add(node.args[0].value)
    return keys


#: (filename, unit class node, module tree) for every unit.
UNITS_WITH_TREES = []
for _path in _unit_modules():
    _tree = ast.parse(_path.read_text(encoding="utf-8"))
    _cls = _unit_class(_tree)
    if _cls is not None:
        UNITS_WITH_TREES.append((_path.name, _cls, _tree))


_IDS = [name for name, _, _ in UNITS_WITH_TREES]


@pytest.mark.parametrize(("name", "cls", "tree"), UNITS_WITH_TREES, ids=_IDS)
def test_every_config_key_a_unit_reads_is_declared(name, cls, tree):
    """In the schema if a user fills it in, in RUNTIME_PARAMS if not.

    An undeclared key is a raw ``KeyError`` waiting for the first caller that
    builds the unit from its declarations instead of copying an existing call.
    """
    read = _config_reads(cls)
    declared = _schema_fields(tree) | _declared(cls, "RUNTIME_PARAMS")

    undeclared = read - declared
    assert not undeclared, (
        f"{name} reads {sorted(undeclared)} from its configuration without "
        "declaring it. Put it in the schema if a user chooses it, or in "
        "RUNTIME_PARAMS if whatever runs the unit supplies it."
    )


@pytest.mark.parametrize(("name", "cls", "tree"), UNITS_WITH_TREES, ids=_IDS)
def test_a_runtime_param_is_not_also_in_the_schema(name, cls, tree):
    """The two answers are mutually exclusive.

    A name in both would be exposed to the front and overridden by the caller
    at once -- a field the user is invited to fill in and whose value is then
    discarded.
    """
    overlap = _declared(cls, "RUNTIME_PARAMS") & _schema_fields(tree)
    assert not overlap, f"{name} declares {sorted(overlap)} twice."


@pytest.mark.parametrize(("name", "cls", "tree"), UNITS_WITH_TREES, ids=_IDS)
def test_a_runtime_param_is_actually_read(name, cls, tree):
    """A declared name nothing reads is a promise to nobody."""
    unread = _declared(cls, "RUNTIME_PARAMS") - _config_reads(cls)
    assert not unread, (
        f"{name} declares {sorted(unread)} in RUNTIME_PARAMS but never reads it."
    )


@pytest.mark.parametrize(("name", "cls", "tree"), UNITS_WITH_TREES, ids=_IDS)
def test_a_plumbing_shaped_field_is_classified_one_way_or_the_other(name, cls, tree):
    """A new field named like plumbing cannot default into a form.

    The net has a known hole: ``session_splits`` and
    ``trust_inherited_metadata`` are runtime params and match nothing, which is
    why the exact set in ``tests/back/api/test_units_api.py`` exists as well.
    What this catches is the common case -- a new ``*_id`` or ``*_path`` added
    without anyone deciding what it is.
    """
    runtime = _declared(cls, "RUNTIME_PARAMS")

    unclassified = [
        field
        for field in _schema_fields(tree)
        if _PLUMBING_SHAPED.search(field)
        and field not in runtime
        and (name, field) not in NEEDS_A_WIDGET
    ]

    assert not unclassified, (
        f"{name} has schema fields named like plumbing that nobody classified: "
        f"{sorted(unclassified)}. Move them to RUNTIME_PARAMS if whatever runs "
        "the unit supplies them, or add them to NEEDS_A_WIDGET with the widget "
        "they need."
    )


def test_every_entry_in_the_widget_registry_still_exists():
    """Guards the registry itself: a stale entry would make it decorative."""
    declared = {
        (name, field)
        for name, _, tree in UNITS_WITH_TREES
        for field in _schema_fields(tree)
    }

    missing = sorted(set(NEEDS_A_WIDGET) - declared)
    assert not missing, missing
