"""Declarative rules that span several fields of a component schema.

A field constraint (``int_field(ge=1)``) describes one value in isolation. Some
constraints are relations instead: the holdout proportions must sum to one,
``chunk_overlap`` must stay under ``chunk_size``, ``random_state`` is
meaningless when shuffling is off. Those cannot be expressed by any per-field
keyword, and writing them as a ``@model_validator`` body leaves no trace in the
JSON Schema, so the frontend has to re-implement them by hand and drift.

This module makes such a relation *data*. A schema declares::

    class HoldoutSplitterSchema(BaseSchema):
        train: schema_field(float_field(ge=0, le=1), placeholder=0.6, ...)
        ...

        rules = [
            Check(
                Approx(Sum("train", "validation", "test"), 1.0, tol=1e-6),
                id="holdout.proportions_sum_to_one",
                targets=["train", "validation", "test"],
                message=MultilingualString(en="...", es="..."),
                bindings={"sum": Sum("train", "validation", "test")},
            ),
            Relevance("random_state", when=IsTrue(F("shuffle")), effect="disable"),
        ]

and ``BaseSchema`` turns that single declaration into two enforcers: an
inherited ``@model_validator(mode="after")`` that runs on the server, and an
``x-dashai-rules`` entry in the served JSON Schema that the browser replays
with the same semantics, before submit and with no network round trip.

Three properties are deliberate and load-bearing:

* **No grammar.** An expression is a closed set of AST node shapes, not a
  string in a language, so there is no parser to keep in parity between Python
  and JavaScript. Operators where the two runtimes disagree (``//``, ``%``,
  string coercion, implicit truthiness of non-booleans) are left out on
  purpose. ``tests/fixtures/rule_conformance.json`` pins the agreement.

* **Three-valued verdicts.** A rule whose expression reads a field that is
  absent, null or not yet coercible is ``PENDING``, not failed. Mid-edit is the
  normal state of a form, and a rule that fires while the user is still typing
  is worse than no rule. ``PENDING`` also stops a rule from being silently
  treated as satisfied.

* **Python objects, never expression strings.** The wire format is an
  implementation detail. If this algebra turns out too tight, it can be swapped
  for CEL or JSONLogic behind this same authoring API without touching a single
  plugin.

Notes
-----
Relevance is evaluated on the server only to *exclude* a field from the checks
that reference it. It cannot un-validate the field's own constraints, because
pydantic validates fields before any ``mode="after"`` validator runs and no
schema field carries a default. Its main job is to drive the renderer, which
disables, hides or omits the field.
"""

from __future__ import annotations

import difflib
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Union

from DashAI.back.core.utils import MultilingualString

__all__ = [
    "And",
    "Approx",
    "Check",
    "Ctx",
    "Eq",
    "F",
    "Expr",
    "In",
    "IsFalse",
    "IsNull",
    "IsTrue",
    "Len",
    "Lt",
    "Lte",
    "Ne",
    "Not",
    "Or",
    "Relevance",
    "Rule",
    "RuleDeclarationError",
    "RuleViolationError",
    "Sum",
    "collect_field_names",
    "rules_to_wire",
]

#: Effects a ``Relevance`` rule can ask the renderer for.
RELEVANCE_EFFECTS = ("disable", "hide", "omit")

#: Comparison operators the algebra admits. Deliberately no ``//`` or ``%``:
#: Python floors and JavaScript truncates, which is exactly the kind of silent
#: divergence a two-runtime rule layer dies of.
COMPARISONS = ("lt", "lte", "gt", "gte", "eq", "ne")


class RuleDeclarationError(TypeError):
    """Raised at class-definition time when a rule cannot be trusted.

    A misspelled field name, an unknown effect or a rule without targets is a
    dead constraint: it would never fire and nobody would notice. Failing at
    import turns that into a loud error at app boot or plugin install.
    """


class RuleViolationError(ValueError):
    """A rule that evaluated to ``False``.

    Carries enough structure for an endpoint to build a per-field error payload
    instead of stringifying a pydantic ``ValidationError`` into an HTTP detail.

    Attributes
    ----------
    rule_id : str
        Stable, machine-readable id of the rule that failed.
    targets : list of str
        Field names the message should be rendered under.
    message : MultilingualString
        The already-interpolated message, still multilingual so it can ride the
        existing server-side ``localize()`` path.
    """

    def __init__(
        self,
        rule_id: str,
        targets: Sequence[str],
        message: MultilingualString,
    ) -> None:
        self.rule_id = rule_id
        self.targets = list(targets)
        self.message = message
        super().__init__(message.get("en"))

    def as_payload(self) -> Dict[str, Any]:
        """Return the violation as a JSON-ready dict of multilingual parts."""
        return {
            "rule_id": self.rule_id,
            "targets": list(self.targets),
            "message": self.message,
        }


# --------------------------------------------------------------------------- #
# Expressions
# --------------------------------------------------------------------------- #


class Expr:
    """Base class for every node of the expression algebra.

    Subclasses only have to implement :meth:`to_ast`. The comparison operators
    are overloaded so a rule reads like the relation it encodes
    (``F("train") > 0``); ``==`` and ``!=`` are deliberately *not* overloaded,
    because silently returning an ``Expr`` from ``__eq__`` breaks equality and
    hashing everywhere else. Use :func:`Eq` and :func:`Ne` instead.
    """

    def to_ast(self) -> Dict[str, Any]:  # pragma: no cover - abstract
        raise NotImplementedError

    # -- arithmetic ------------------------------------------------------- #
    def __add__(self, other: Any) -> "Expr":
        return _Binary("add", self, _lift(other))

    def __radd__(self, other: Any) -> "Expr":
        return _Binary("add", _lift(other), self)

    def __sub__(self, other: Any) -> "Expr":
        return _Binary("sub", self, _lift(other))

    def __rsub__(self, other: Any) -> "Expr":
        return _Binary("sub", _lift(other), self)

    def __mul__(self, other: Any) -> "Expr":
        return _Binary("mul", self, _lift(other))

    def __rmul__(self, other: Any) -> "Expr":
        return _Binary("mul", _lift(other), self)

    # -- comparison ------------------------------------------------------- #
    def __lt__(self, other: Any) -> "Expr":
        return _Compare("lt", self, _lift(other))

    def __le__(self, other: Any) -> "Expr":
        return _Compare("lte", self, _lift(other))

    def __gt__(self, other: Any) -> "Expr":
        return _Compare("gt", self, _lift(other))

    def __ge__(self, other: Any) -> "Expr":
        return _Compare("gte", self, _lift(other))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.to_ast()})"


def _lift(value: Any) -> Expr:
    """Wrap a plain Python value as a literal node, passing Exprs through."""
    if isinstance(value, Expr):
        return value
    if isinstance(value, (bool, int, float, str)) or value is None:
        return _Literal(value)
    if isinstance(value, (list, tuple)):
        return _Literal([_unwrap_literal(item) for item in value])
    raise RuleDeclarationError(
        f"{value!r} ({type(value).__name__}) cannot appear in a rule expression. "
        "Allowed literals are bool, int, float, str, None and lists of those."
    )


def _unwrap_literal(value: Any) -> Any:
    if isinstance(value, Expr):
        raise RuleDeclarationError(
            "A list literal cannot contain expressions; use In(...) over a "
            "context reference instead."
        )
    return value


class _Literal(Expr):
    def __init__(self, value: Any) -> None:
        self.value = value

    def to_ast(self) -> Dict[str, Any]:
        return {"n": "lit", "v": self.value}


class F(Expr):
    """A reference to a sibling field of the same schema.

    Parameters
    ----------
    name : str
        Field name. Checked against the schema's own fields at class-definition
        time, so a typo raises :class:`RuleDeclarationError` at import.
    """

    def __init__(self, name: str) -> None:
        if not isinstance(name, str) or not name:
            raise RuleDeclarationError("F() needs a non-empty field name.")
        self.name = name

    def to_ast(self) -> Dict[str, Any]:
        return {"n": "field", "f": self.name}


class Ctx(Expr):
    """A reference to a fact the schema cannot carry.

    The valid domain of some fields lives outside the component: the columns of
    the selected dataset, its row count, the target task, the splitters an
    outer splitter is compatible with. Those arrive as a context payload
    fetched once per dataset or component selection, never per keystroke.

    A rule reading a context key that was not supplied evaluates to
    ``PENDING``, so it never passes by accident when the context is missing.
    """

    def __init__(self, key: str) -> None:
        if not isinstance(key, str) or not key:
            raise RuleDeclarationError("Ctx() needs a non-empty key.")
        self.key = key

    def to_ast(self) -> Dict[str, Any]:
        return {"n": "ctx", "k": self.key}


class _Binary(Expr):
    def __init__(self, op: str, left: Expr, right: Expr) -> None:
        self.op = op
        self.left = left
        self.right = right

    def to_ast(self) -> Dict[str, Any]:
        return {"n": self.op, "a": self.left.to_ast(), "b": self.right.to_ast()}


class _Compare(Expr):
    def __init__(self, op: str, left: Expr, right: Expr) -> None:
        if op not in COMPARISONS:
            raise RuleDeclarationError(f"Unknown comparison {op!r}.")
        self.op = op
        self.left = left
        self.right = right

    def to_ast(self) -> Dict[str, Any]:
        return {
            "n": "cmp",
            "op": self.op,
            "a": self.left.to_ast(),
            "b": self.right.to_ast(),
        }


class _Nary(Expr):
    def __init__(self, node: str, operands: Iterable[Any]) -> None:
        self.node = node
        self.operands = [_lift(operand) for operand in operands]
        if not self.operands:
            raise RuleDeclarationError(f"{node} needs at least one operand.")

    def to_ast(self) -> Dict[str, Any]:
        return {"n": self.node, "of": [item.to_ast() for item in self.operands]}


class _Unary(Expr):
    def __init__(self, node: str, operand: Any) -> None:
        self.node = node
        self.operand = _lift(operand)

    def to_ast(self) -> Dict[str, Any]:
        return {"n": self.node, "of": self.operand.to_ast()}


def _name_or_expr(value: Union[str, Expr]) -> Expr:
    """Turn a bare field name into a reference, passing expressions through."""
    return F(value) if isinstance(value, str) else _lift(value)


class Sum(_Nary):
    """Sum of several fields. ``Sum("train", "test")`` reads better than ``F + F``."""

    def __init__(self, *fields: Union[str, Expr]) -> None:
        if not fields:
            raise RuleDeclarationError("Sum() needs at least one field.")
        super().__init__("sum", [_name_or_expr(item) for item in fields])


class Approx(Expr):
    """``abs(a - b) <= tol``, written without ``abs()``.

    A first-class node rather than something an author composes, because
    per-runtime math libraries are exactly where two implementations drift:
    standard CEL has no ``abs()`` either. The tolerance also ends up living in
    one place, instead of the four different values this codebase used to carry
    for the same relation.
    """

    def __init__(self, left: Any, right: Any, tol: float = 1e-6) -> None:
        if not isinstance(tol, (int, float)) or isinstance(tol, bool) or tol < 0:
            raise RuleDeclarationError("Approx(tol=) must be a non-negative number.")
        self.left = _lift(left)
        self.right = _lift(right)
        self.tol = float(tol)

    def to_ast(self) -> Dict[str, Any]:
        return {
            "n": "approx",
            "a": self.left.to_ast(),
            "b": self.right.to_ast(),
            "tol": self.tol,
        }


class And(_Nary):
    """Logical conjunction. Python cannot overload ``and``, hence the node."""

    def __init__(self, *operands: Any) -> None:
        super().__init__("and", operands)


class Or(_Nary):
    """Logical disjunction."""

    def __init__(self, *operands: Any) -> None:
        super().__init__("or", operands)


class Not(_Unary):
    """Logical negation."""

    def __init__(self, operand: Any) -> None:
        super().__init__("not", operand)


class IsNull(_Unary):
    """True when the operand is absent or null. Never pending itself.

    This is the escape hatch for "has the user filled this in", which is a
    question the pending verdict deliberately refuses to answer implicitly.
    """

    def __init__(self, operand: Any) -> None:
        super().__init__("is_null", operand)


class IsTrue(_Unary):
    """True when the operand is exactly the boolean ``True``.

    Strict on purpose: no truthiness, so ``0``, ``""`` and ``[]`` are not falsy
    in one runtime and something else in the other.
    """

    def __init__(self, operand: Any) -> None:
        super().__init__("is_true", operand)


class IsFalse(_Unary):
    """True when the operand is exactly the boolean ``False``."""

    def __init__(self, operand: Any) -> None:
        super().__init__("is_false", operand)


class Len(_Unary):
    """Length of a list or string."""

    def __init__(self, operand: Any) -> None:
        super().__init__("len", operand)


class In(_Binary):
    """Membership of a value in a list, typically a context-supplied domain."""

    def __init__(self, needle: Any, haystack: Any) -> None:
        super().__init__("in", _lift(needle), _lift(haystack))


class Eq(_Compare):
    """Equality. A node rather than ``==`` so ``Expr`` keeps normal equality."""

    def __init__(self, left: Any, right: Any) -> None:
        super().__init__("eq", _lift(left), _lift(right))


class Ne(_Compare):
    """Inequality."""

    def __init__(self, left: Any, right: Any) -> None:
        super().__init__("ne", _lift(left), _lift(right))


class Lt(_Compare):
    """``left < right``, with bare field names allowed: ``Lt("overlap", "size")``."""

    def __init__(self, left: Union[str, Expr], right: Union[str, Expr]) -> None:
        super().__init__("lt", _name_or_expr(left), _name_or_expr(right))


class Lte(_Compare):
    """``left <= right``, with bare field names allowed."""

    def __init__(self, left: Union[str, Expr], right: Union[str, Expr]) -> None:
        super().__init__("lte", _name_or_expr(left), _name_or_expr(right))


# --------------------------------------------------------------------------- #
# Rules
# --------------------------------------------------------------------------- #


class Rule:
    """Base class for the rule kinds a schema can declare."""

    kind: str = ""

    def to_ast(self) -> Dict[str, Any]:  # pragma: no cover - abstract
        raise NotImplementedError

    def field_names(self) -> List[str]:  # pragma: no cover - abstract
        raise NotImplementedError


class Check(Rule):
    """A relation between fields that must hold for the value to be valid.

    Parameters
    ----------
    expr : Expr
        The predicate. ``True`` passes, ``False`` fails, ``PENDING`` is neither.
    id : str
        Stable, machine-readable identifier, conventionally
        ``"<component>.<relation>"``. It appears in the error payload so a
        message change never breaks a client that keys on the rule.
    targets : sequence of str
        The fields the message is rendered under. A relation between three
        fields should name all three, so the user sees the problem wherever
        they are looking.
    message : MultilingualString
        Shown to the user. Rides the existing server-side ``localize()`` path,
        so constraint messages get the same five languages as labels.
    bindings : mapping of str to Expr, optional
        Named sub-expressions interpolated into ``message`` with ``{name}``.
        Evaluated by whichever runtime is reporting, so the message can quote
        the offending value without a format string crossing the wire.
    requires_ctx : bool
        Declares that the rule reads :class:`Ctx`. Such a rule is skipped, and
        reported as unvalidated, when no context is available, rather than
        silently passing.
    """

    kind = "check"

    def __init__(
        self,
        expr: Expr,
        *,
        id: str,
        targets: Sequence[str],
        message: MultilingualString,
        bindings: Optional[Mapping[str, Expr]] = None,
        requires_ctx: bool = False,
    ) -> None:
        if not isinstance(expr, Expr):
            raise RuleDeclarationError(
                f"Check() needs an expression, got {type(expr).__name__}. "
                "Did you write a bare Python comparison such as `a == b`? Use Eq(a, b)."
            )
        if not isinstance(id, str) or not id:
            raise RuleDeclarationError("Check(id=) must be a non-empty string.")
        if not targets:
            raise RuleDeclarationError(
                f"Check(id={id!r}) has no targets. A rule whose message has "
                "nowhere to render is a dead constraint."
            )
        if not isinstance(message, MultilingualString):
            raise RuleDeclarationError(
                f"Check(id={id!r}) needs a MultilingualString message so the "
                "error can be localized like every other user-facing string."
            )
        self.expr = expr
        self.id = id
        self.targets = list(targets)
        self.message = message
        self.bindings = dict(bindings or {})
        self.requires_ctx = bool(requires_ctx)
        for name, binding in self.bindings.items():
            if not isinstance(binding, Expr):
                raise RuleDeclarationError(
                    f"Check(id={id!r}) binding {name!r} must be an expression."
                )

    def to_ast(self) -> Dict[str, Any]:
        return {
            "kind": "check",
            "id": self.id,
            "targets": list(self.targets),
            "message": self.message,
            "expr": self.expr.to_ast(),
            "bindings": {
                name: binding.to_ast() for name, binding in self.bindings.items()
            },
            "requires_ctx": self.requires_ctx,
        }

    def field_names(self) -> List[str]:
        names = list(self.targets)
        names.extend(collect_field_names(self.expr.to_ast()))
        for binding in self.bindings.values():
            names.extend(collect_field_names(binding.to_ast()))
        return names


class Relevance(Rule):
    """Declares when a field is meaningful at all.

    ``random_state`` has no effect when ``shuffle`` is off. Today that fact
    lives in prose inside the field's description, in five languages, enforced
    nowhere. As a rule it drives the renderer and excludes the field from the
    checks that reference it.

    Parameters
    ----------
    field : str
        The field whose relevance is conditional.
    when : Expr
        The field is relevant while this evaluates to ``True``. A ``PENDING``
        verdict leaves the field relevant, which is the safe direction: a field
        is never hidden because something else has not been filled in yet.
    effect : {"disable", "hide", "omit"}
        ``disable`` keeps the control visible but inert, which is right when
        the value still means something to a reader. ``hide`` removes it.
        ``omit`` additionally drops the key from the submitted payload, which
        some backends distinguish by presence.
    reason : MultilingualString, optional
        Why the field is inert, shown next to the disabled control instead of
        leaving the user guessing.
    """

    kind = "relevance"

    def __init__(
        self,
        field: str,
        *,
        when: Expr,
        effect: str = "disable",
        reason: Optional[MultilingualString] = None,
    ) -> None:
        if not isinstance(field, str) or not field:
            raise RuleDeclarationError("Relevance() needs a field name.")
        if not isinstance(when, Expr):
            raise RuleDeclarationError(
                f"Relevance({field!r}) needs an expression for `when`."
            )
        if effect not in RELEVANCE_EFFECTS:
            raise RuleDeclarationError(
                f"Relevance({field!r}) effect {effect!r} is not one of "
                f"{RELEVANCE_EFFECTS}."
            )
        if reason is not None and not isinstance(reason, MultilingualString):
            raise RuleDeclarationError(
                f"Relevance({field!r}) reason must be a MultilingualString."
            )
        self.field = field
        self.when = when
        self.effect = effect
        self.reason = reason

    def to_ast(self) -> Dict[str, Any]:
        ast: Dict[str, Any] = {
            "kind": "relevance",
            "field": self.field,
            "when": self.when.to_ast(),
            "effect": self.effect,
        }
        if self.reason is not None:
            ast["reason"] = self.reason
        return ast

    def field_names(self) -> List[str]:
        return [self.field, *collect_field_names(self.when.to_ast())]


# --------------------------------------------------------------------------- #
# Helpers used by BaseSchema
# --------------------------------------------------------------------------- #


def collect_field_names(ast: Any) -> List[str]:
    """Collect every field name referenced anywhere inside an expression AST."""
    found: List[str] = []
    if isinstance(ast, dict):
        if ast.get("n") == "field":
            found.append(ast["f"])
        for value in ast.values():
            found.extend(collect_field_names(value))
    elif isinstance(ast, list):
        for item in ast:
            found.extend(collect_field_names(item))
    return found


def validate_rules(
    rules: Sequence[Rule],
    *,
    owner: str,
    known: Iterable[str],
    unreadable: Iterable[str] = (),
) -> None:
    """Check a schema's rules against the fields it actually declares.

    Parameters
    ----------
    rules : sequence of Rule
        The schema's own rules, before merging with its parents'.
    owner : str
        The schema class name, for the error message.
    known : iterable of str
        The field names the schema declares.
    unreadable : iterable of str
        Fields whose value the algebra cannot read, so an expression over them
        can only ever be pending. Today that is the optimizer fields: their
        value is the ``{optimize, fixed_value, lower_bound, upper_bound}``
        envelope rather than a number, and the arithmetic and comparison nodes
        refuse a non-number by design.

    Raises
    ------
    RuleDeclarationError
        If a rule is not a :class:`Rule`, references a field the schema does not
        have, duplicates a rule id, or reads a field whose value the algebra
        cannot judge. The message suggests the closest real field name, because
        the overwhelmingly common cause is a typo.
    """
    known_names = set(known)
    unreadable_names = set(unreadable)
    seen_ids: Dict[str, int] = {}
    for index, rule in enumerate(rules):
        if not isinstance(rule, Rule):
            raise RuleDeclarationError(
                f"{owner}.rules[{index}] is {type(rule).__name__}, not a Check "
                "or a Relevance."
            )
        if isinstance(rule, Check):
            seen_ids[rule.id] = seen_ids.get(rule.id, 0) + 1
        for name in rule.field_names():
            if name not in known_names:
                hint = difflib.get_close_matches(name, sorted(known_names), n=1)
                suggestion = f" Did you mean {hint[0]!r}?" if hint else ""
                raise RuleDeclarationError(
                    f"{owner}.rules[{index}] references {name!r}, which is not a "
                    f"field of {owner}.{suggestion}"
                )
        # A rule that reads a value the algebra cannot judge is not a rule, it
        # is a permanently pending one. Reported rather than passed, so nothing
        # is validated wrongly, but nobody reads a pending report either, so it
        # fails here instead of never firing.
        read = _reads_of(rule)
        blocked = sorted(read & unreadable_names)
        if blocked:
            raise RuleDeclarationError(
                f"{owner}.rules[{index}] reads {blocked}, whose value is the "
                "optimizer envelope ({'optimize', 'fixed_value', 'lower_bound', "
                "'upper_bound'}) rather than a number, so the rule could only "
                "ever be pending and would never fire.\n"
                "Until an optimizable hyperparameter is a declared type instead "
                "of a shape carried by its placeholder, a constraint on one has "
                "to stay in a validator. A Relevance rule *targeting* the field "
                "is fine: it reads its condition, not the field's own value."
            )
    duplicates = sorted(name for name, count in seen_ids.items() if count > 1)
    if duplicates:
        raise RuleDeclarationError(
            f"{owner} declares more than one Check with id {duplicates!r}. Rule "
            "ids identify a violation to clients, so they must be unique."
        )


def _reads_of(rule: Rule) -> set:
    """Field names a rule's expressions read, as opposed to the ones it targets.

    The distinction matters: ``Relevance("season_length", when=...)`` targets a
    field it never reads, so it is judgeable even when that field's own value is
    one the algebra cannot handle.
    """
    if isinstance(rule, Check):
        asts = [rule.expr.to_ast()] + [b.to_ast() for b in rule.bindings.values()]
    elif isinstance(rule, Relevance):
        asts = [rule.when.to_ast()]
    else:  # pragma: no cover - a future rule kind must say what it reads
        asts = []
    found = set()
    for ast in asts:
        found.update(collect_field_names(ast))
    return found


def rules_to_wire(rules: Sequence[Rule]) -> List[Dict[str, Any]]:
    """Serialize rules for the JSON Schema.

    Only lists and dicts are emitted, never tuples: ``localize()`` walks dicts
    and lists, so a ``MultilingualString`` reached through a tuple would survive
    into the response and make the components endpoint fail to serialize.
    """
    return [rule.to_ast() for rule in rules]
