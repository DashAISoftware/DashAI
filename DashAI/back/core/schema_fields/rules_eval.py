"""The Python half of the rule interpreter.

``DashAI/front/src/utils/ruleEngine.js`` is the other half. The two are kept in
agreement by ``tests/fixtures/rule_conformance.json``, generated here and
asserted by both test suites, because a rule layer whose two runtimes quietly
disagree is worse than no rule layer at all.

Everything in this module is a pure function of ``(ast, values, ctx)``. No
imports from the rest of dashAI beyond ``MultilingualString``, no I/O, no
registry, no ``eval``.

Semantics, stated once so the JavaScript side can be read against it:

``PENDING``
    A third verdict alongside true and false, returned whenever the expression
    depends on something not yet known: a field the caller did not supply, a
    field explicitly ``null``, a context key that was not fetched, or an operand
    of the wrong type. A ``Check`` with a ``PENDING`` verdict is not a failure
    and not a pass; the server skips it and reports it as unvalidated, and the
    browser shows nothing. Mid-edit is the normal state of a form.

Strict types
    ``and``/``or``/``not`` accept booleans only, arithmetic accepts numbers
    only, and a boolean is *not* a number even though Python says otherwise.
    ``eq``/``ne`` compare booleans only against booleans. Every one of those
    rules exists to close a place where CPython and JavaScript disagree.

Short circuit
    ``and`` returns false as soon as any operand is false, even when another is
    ``PENDING``; ``or`` returns true as soon as any operand is true. So a rule
    guarded by ``And(Not(IsNull(F("x"))), ...)`` behaves the way its author
    expects while ``x`` is empty.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

from DashAI.back.core.utils import MultilingualString

__all__ = [
    "PENDING",
    "RuleReport",
    "evaluate",
    "evaluate_rules",
    "format_value",
]


class _Pending:
    """Sentinel for the third verdict. Distinct from ``None``, which is a value."""

    _instance: Optional["_Pending"] = None

    def __new__(cls) -> "_Pending":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "PENDING"

    def __bool__(self) -> bool:
        raise TypeError(
            "PENDING has no truth value. Compare with `is PENDING` instead, so a "
            "rule that cannot be judged is never silently treated as satisfied."
        )


PENDING = _Pending()

_MISSING = object()


def _is_number(value: Any) -> bool:
    """True for real numbers only. A bool is not a number here, unlike in Python."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def format_value(value: Any) -> str:
    """Render a value for interpolation into a rule message.

    Pinned digit for digit against the JavaScript side, because a message that
    reads ``1.2000000000000002`` in one runtime and ``1.2`` in the other is a
    conformance failure the fixtures must catch. Floats are rounded to six
    decimal places and printed without a trailing ``.0``.
    """
    if value is PENDING or value is None:
        return "?"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            return str(value)
        rounded = float(f"{value:.6f}") if abs(value) < 1e21 else value
        if rounded == int(rounded) and abs(rounded) < 1e16:
            return str(int(rounded))
        return repr(rounded)
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ", ".join(format_value(item) for item in value)
    return str(value)


def evaluate(
    ast: Mapping[str, Any],
    values: Mapping[str, Any],
    ctx: Optional[Mapping[str, Any]] = None,
) -> Any:
    """Evaluate one expression AST node.

    Parameters
    ----------
    ast : mapping
        A node produced by ``Expr.to_ast()``.
    values : mapping
        The current field values. A missing key and an explicit ``None`` are
        treated the same way: ``PENDING``.
    ctx : mapping, optional
        Facts from outside the schema. ``None`` means no context was supplied,
        so every ``Ctx`` reference is ``PENDING``.

    Returns
    -------
    Any
        A Python value, or :data:`PENDING`.
    """
    node = ast.get("n")

    if node == "lit":
        return ast["v"]

    if node == "field":
        found = values.get(ast["f"], _MISSING)
        if found is _MISSING or found is None:
            return PENDING
        return found

    if node == "ctx":
        if ctx is None:
            return PENDING
        found = ctx.get(ast["k"], _MISSING)
        if found is _MISSING or found is None:
            return PENDING
        return found

    if node in ("add", "sub", "mul"):
        left = evaluate(ast["a"], values, ctx)
        right = evaluate(ast["b"], values, ctx)
        if not _is_number(left) or not _is_number(right):
            return PENDING
        if node == "add":
            return left + right
        if node == "sub":
            return left - right
        return left * right

    if node == "sum":
        total: float = 0
        for operand in ast["of"]:
            item = evaluate(operand, values, ctx)
            if not _is_number(item):
                return PENDING
            total = total + item
        return total

    if node == "approx":
        left = evaluate(ast["a"], values, ctx)
        right = evaluate(ast["b"], values, ctx)
        if not _is_number(left) or not _is_number(right):
            return PENDING
        difference = left - right
        if difference < 0:
            difference = -difference
        return difference <= ast["tol"]

    if node == "cmp":
        return _compare(ast["op"], ast, values, ctx)

    if node == "and":
        verdicts = [evaluate(operand, values, ctx) for operand in ast["of"]]
        if any(verdict is False for verdict in verdicts):
            return False
        if any(
            verdict is PENDING or not isinstance(verdict, bool) for verdict in verdicts
        ):
            return PENDING
        return True

    if node == "or":
        verdicts = [evaluate(operand, values, ctx) for operand in ast["of"]]
        if any(verdict is True for verdict in verdicts):
            return True
        if any(
            verdict is PENDING or not isinstance(verdict, bool) for verdict in verdicts
        ):
            return PENDING
        return False

    if node == "not":
        verdict = evaluate(ast["of"], values, ctx)
        if not isinstance(verdict, bool):
            return PENDING
        return not verdict

    if node == "is_null":
        verdict = evaluate(ast["of"], values, ctx)
        return verdict is PENDING or verdict is None

    if node == "is_true":
        verdict = evaluate(ast["of"], values, ctx)
        if verdict is PENDING:
            return PENDING
        return verdict is True

    if node == "is_false":
        verdict = evaluate(ast["of"], values, ctx)
        if verdict is PENDING:
            return PENDING
        return verdict is False

    if node == "in":
        needle = evaluate(ast["a"], values, ctx)
        haystack = evaluate(ast["b"], values, ctx)
        if needle is PENDING or not isinstance(haystack, list):
            return PENDING
        return any(_strict_equal(needle, item) for item in haystack)

    if node == "len":
        operand = evaluate(ast["of"], values, ctx)
        if not isinstance(operand, (list, str)):
            return PENDING
        return len(operand)

    raise ValueError(f"Unknown rule node {node!r}.")


def _compare(
    op: str,
    ast: Mapping[str, Any],
    values: Mapping[str, Any],
    ctx: Optional[Mapping[str, Any]],
) -> Any:
    left = evaluate(ast["a"], values, ctx)
    right = evaluate(ast["b"], values, ctx)
    if left is PENDING or right is PENDING:
        return PENDING

    if op in ("eq", "ne"):
        equal = _strict_equal(left, right)
        return equal if op == "eq" else not equal

    both_numbers = _is_number(left) and _is_number(right)
    both_strings = isinstance(left, str) and isinstance(right, str)
    if not both_numbers and not both_strings:
        return PENDING
    if op == "lt":
        return left < right
    if op == "lte":
        return left <= right
    if op == "gt":
        return left > right
    return left >= right


def _strict_equal(left: Any, right: Any) -> bool:
    """Equality that agrees with JavaScript's ``===`` for JSON scalars.

    Python considers ``True == 1``; JavaScript does not. Booleans therefore
    only ever equal booleans here.
    """
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left is right
    if _is_number(left) and _is_number(right):
        return left == right
    if type(left) is not type(right):
        return False
    return bool(left == right)


class RuleReport:
    """The outcome of evaluating a schema's whole rule set.

    Attributes
    ----------
    violations : list of dict
        One entry per failed check, as ``{rule_id, targets, message}`` where
        ``message`` is a :class:`MultilingualString` with its bindings already
        interpolated.
    pending : list of str
        Ids of checks that could not be judged. Reported rather than dropped,
        so "we did not validate this" is never mistaken for "this is valid".
    relevance : dict
        ``{field: {"relevant": bool, "effect": str, "reason": ...}}`` for every
        field a relevance rule marked irrelevant.
    """

    def __init__(
        self,
        violations: List[Dict[str, Any]],
        pending: List[str],
        relevance: Dict[str, Dict[str, Any]],
    ) -> None:
        self.violations = violations
        self.pending = pending
        self.relevance = relevance

    @property
    def ok(self) -> bool:
        """True when no check failed. Pending checks do not make a value invalid."""
        return not self.violations

    def irrelevant_fields(self) -> List[str]:
        """Fields a relevance rule marked as not meaningful right now."""
        return [name for name, state in self.relevance.items() if not state["relevant"]]


def evaluate_rules(
    rules: Sequence[Mapping[str, Any]],
    values: Mapping[str, Any],
    ctx: Optional[Mapping[str, Any]] = None,
) -> RuleReport:
    """Evaluate a serialized rule set against a set of values.

    Relevance is resolved first, because a check that references an irrelevant
    field must not run: with ``shuffle`` off, a rule about ``random_state`` is
    not merely satisfied, it is meaningless.

    Parameters
    ----------
    rules : sequence of mapping
        The ``x-dashai-rules`` payload, or ``rules_to_wire(...)`` output.
    values : mapping
        Current field values.
    ctx : mapping, optional
        Facts from outside the schema; ``None`` when none were supplied.

    Returns
    -------
    RuleReport
    """
    relevance: Dict[str, Dict[str, Any]] = {}
    for rule in rules:
        if rule.get("kind") != "relevance":
            continue
        verdict = evaluate(rule["when"], values, ctx)
        # PENDING leaves the field relevant: never hide a control because
        # something else has not been filled in yet.
        relevant = verdict is not False
        state: Dict[str, Any] = {"relevant": relevant, "effect": rule["effect"]}
        if rule.get("reason") is not None:
            state["reason"] = rule["reason"]
        relevance[rule["field"]] = state

    irrelevant = {name for name, state in relevance.items() if not state["relevant"]}

    violations: List[Dict[str, Any]] = []
    pending: List[str] = []
    for rule in rules:
        if rule.get("kind") != "check":
            continue
        if any(target in irrelevant for target in rule["targets"]):
            continue
        if rule.get("requires_ctx") and ctx is None:
            pending.append(rule["id"])
            continue
        verdict = evaluate(rule["expr"], values, ctx)
        if verdict is True:
            continue
        if verdict is False:
            violations.append(
                {
                    "rule_id": rule["id"],
                    "targets": list(rule["targets"]),
                    "message": _interpolate(rule, values, ctx),
                }
            )
        else:
            pending.append(rule["id"])

    return RuleReport(violations, pending, relevance)


def _interpolate(
    rule: Mapping[str, Any],
    values: Mapping[str, Any],
    ctx: Optional[Mapping[str, Any]],
) -> MultilingualString:
    """Fill a rule's ``{binding}`` placeholders in every language it declares."""
    message = rule["message"]
    bindings = rule.get("bindings") or {}
    if not bindings:
        return message
    rendered = {
        name: format_value(evaluate(expr, values, ctx))
        for name, expr in bindings.items()
    }
    if isinstance(message, MultilingualString):
        parts = {
            lang: _apply(getattr(message, lang), rendered)
            for lang in ("en", "es", "pt", "de", "zh")
        }
        return MultilingualString(**parts)
    # Already localized to a plain string by the API boundary.
    return _apply(message, rendered)


def _apply(text: Optional[str], rendered: Mapping[str, str]) -> Optional[str]:
    if not text:
        return text
    for name, value in rendered.items():
        text = text.replace("{" + name + "}", value)
    return text
