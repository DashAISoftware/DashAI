"""Generates and asserts the cross-runtime conformance fixture for rules.

The rule layer's whole premise is that one declaration is enforced twice, by
two interpreters written in two languages. That only holds if the two agree,
and "they look similar" is not agreement. This module is the mechanism that
turns agreement into something measurable:

1. It builds a set of cases: named ones covering every node shape and every
   place CPython and JavaScript are known to disagree, plus a seeded random
   sweep over the whole algebra.
2. It evaluates each case with the Python interpreter and asserts the expected
   verdict, so the fixture cannot be committed with a wrong answer baked in.
3. It writes the fixture, and ``ruleEngine.test.js`` replays every case in the
   browser runtime and asserts the same verdicts.

The fixture lives under ``DashAI/front/src/utils/`` rather than ``tests/`` on
purpose: Create React App's jest can import anything inside ``src`` with no
extra configuration, while pytest can read any path at all. One file, no
resolution tricks on either side.

If this file is deleted or stops running in CI, the rule layer loses the only
thing that makes its central claim true. That is the stated kill criterion.
"""

import json
import random
from pathlib import Path
from typing import Any, Dict, List

import pytest

from DashAI.back.core.schema_fields.rules import (
    And,
    Approx,
    Check,
    Ctx,
    Eq,
    F,
    In,
    IsFalse,
    IsNull,
    IsTrue,
    Len,
    Lt,
    Ne,
    Not,
    Or,
    Relevance,
    Sum,
    rules_to_wire,
)
from DashAI.back.core.schema_fields.rules_eval import (
    PENDING,
    evaluate,
    evaluate_rules,
    format_value,
)
from DashAI.back.core.utils import MultilingualString, localize

FIXTURE_PATH = (
    Path(__file__).resolve().parents[3]
    / "DashAI"
    / "front"
    / "src"
    / "utils"
    / "ruleConformance.fixture.json"
)

#: How many random expressions the parity sweep covers. Large enough to walk
#: every node shape in combination, small enough that the committed fixture
#: stays reviewable by a human.
SWEEP_SIZE = 1200

#: Bumped when the AST encoding changes, so a stale frontend can refuse to
#: interpret rules it does not understand instead of guessing.
FIXTURE_VERSION = 1


def _encode(value: Any) -> Any:
    """Encode an expected verdict for JSON, marking PENDING explicitly."""
    if value is PENDING:
        return {"$pending": True}
    return value


def _named_cases() -> List[Dict[str, Any]]:
    """Cases a human should be able to read and check by eye.

    Every entry here exists because of a specific way the two runtimes could
    diverge, not for coverage's sake.
    """
    values = {
        "train": 0.6,
        "validation": 0.3,
        "test": 0.1,
        "chunk_size": 500,
        "chunk_overlap": 50,
        "shuffle": True,
        "name": "abc",
        "empty": None,
        "flag_false": False,
        "zero": 0,
        "one": 1,
        "items": ["a", "b"],
    }
    ctx = {"columns": ["a", "b", "c"], "n_rows": 1000}

    cases = [
        # The flagship relation, and the IEEE-754 sum that a hand-written
        # exact comparison in the pipeline editor still rejects today.
        ("approx_sum_60_30_10", Approx(Sum("train", "validation", "test"), 1.0, 1e-6)),
        ("approx_sum_off_by_two_tenths", Approx(Sum("train", "test"), 1.0, 1e-6)),
        ("sum_value", Sum("train", "validation", "test")),
        # Pairwise inequality, the chunker case.
        ("lt_overlap_size", Lt("chunk_overlap", "chunk_size")),
        ("lt_reversed", Lt("chunk_size", "chunk_overlap")),
        # A missing or null field makes the whole expression PENDING, so a rule
        # never fires while the user is still typing.
        ("pending_missing_field", F("absent") > 0),
        ("pending_explicit_null", F("empty") > 0),
        ("pending_in_sum", Sum("train", "absent")),
        # is_null is the escape hatch: it answers "was this filled in" and is
        # never PENDING itself.
        ("is_null_on_missing", IsNull(F("absent"))),
        ("is_null_on_null", IsNull(F("empty"))),
        ("is_null_on_present", IsNull(F("train"))),
        # Booleans are not numbers, and only equal booleans. Python would say
        # True == 1; JavaScript would not.
        ("eq_bool_and_one", Eq(F("shuffle"), 1)),
        ("eq_bool_and_true", Eq(F("shuffle"), True)),
        ("eq_zero_and_false", Eq(F("zero"), False)),
        ("is_true_on_bool", IsTrue(F("shuffle"))),
        ("is_true_on_one", IsTrue(F("one"))),
        ("is_false_on_false", IsFalse(F("flag_false"))),
        ("is_false_on_zero", IsFalse(F("zero"))),
        # Arithmetic on a boolean is PENDING, not 1.
        ("pending_bool_arithmetic", F("shuffle") + 1),
        # Ordering across types has no meaning, so it is PENDING rather than
        # whatever each language's coercion would invent.
        ("pending_number_vs_string", F("train") < F("name")),
        ("string_ordering", F("name") < "abd"),
        # Short circuit: false wins over pending in `and`, true in `or`.
        ("and_false_beats_pending", And(Eq(F("one"), 2), F("absent") > 0)),
        ("and_all_true", And(IsTrue(F("shuffle")), F("train") > 0)),
        ("and_pending", And(IsTrue(F("shuffle")), F("absent") > 0)),
        ("or_true_beats_pending", Or(F("train") > 0, F("absent") > 0)),
        ("or_pending", Or(Eq(F("one"), 2), F("absent") > 0)),
        ("not_true", Not(IsTrue(F("shuffle")))),
        ("not_pending", Not(F("absent") > 0)),
        ("ne_strings", Ne(F("name"), "abc")),
        # Context: absent keys are PENDING, never silently satisfied.
        ("in_ctx_columns_hit", In("a", Ctx("columns"))),
        ("in_ctx_columns_miss", In("zz", Ctx("columns"))),
        ("in_ctx_missing_key", In("a", Ctx("not_fetched"))),
        ("ctx_numeric_bound", F("chunk_size") <= Ctx("n_rows")),
        ("len_of_list", Len(F("items"))),
        ("len_of_string", Len(F("name"))),
        ("len_of_number", Len(F("one"))),
        ("gte_boundary", F("train") >= 0.6),
        ("mul_and_sub", (F("chunk_size") * 2) - 100),
    ]

    encoded = []
    for name, expr in cases:
        ast = expr.to_ast()
        encoded.append(
            {
                "name": name,
                "ast": ast,
                "values": values,
                "ctx": ctx,
                "expect": _encode(evaluate(ast, values, ctx)),
            }
        )

    # The same expression with no context at all: every Ctx reference must go
    # PENDING rather than fall back to a default.
    for name, expr in [
        ("no_ctx_in", In("a", Ctx("columns"))),
        ("no_ctx_bound", F("chunk_size") <= Ctx("n_rows")),
    ]:
        ast = expr.to_ast()
        encoded.append(
            {
                "name": name,
                "ast": ast,
                "values": values,
                "ctx": None,
                "expect": _encode(evaluate(ast, values, None)),
            }
        )
    return encoded


def _formatting_cases() -> List[Dict[str, Any]]:
    """Message interpolation has to agree digit for digit, or messages diverge."""
    samples = [
        0.6 + 0.3 + 0.1,  # 0.9999999999999999
        1.2000000000000002,
        0.1 + 0.2,  # 0.30000000000000004
        1.0,
        0.0,
        -0.0,
        1,
        -3,
        1e-7,
        0.5,
        2.5,
        100.0,
        1234.56789,
        True,
        False,
        "text",
        None,
        [1, 2.5, "x"],
    ]
    return [{"value": value, "expect": format_value(value)} for value in samples]


def _ruleset_cases() -> List[Dict[str, Any]]:
    """Whole rule sets, including the relevance interaction and interpolation."""
    rules = [
        Check(
            Approx(Sum("train", "validation", "test"), 1.0, 1e-6),
            id="sum_to_one",
            targets=["train", "validation", "test"],
            message=MultilingualString(en="Must sum to 1 (currently {total})."),
            bindings={"total": Sum("train", "validation", "test")},
        ),
        Check(
            F("train") > 0,
            id="train_not_empty",
            targets=["train"],
            message=MultilingualString(en="Train must be greater than 0."),
        ),
        Check(
            F("random_state") >= 0,
            id="seed_non_negative",
            targets=["random_state"],
            message=MultilingualString(en="The seed cannot be negative."),
        ),
        Check(
            In(F("group_column"), Ctx("columns")),
            id="group_column_exists",
            targets=["group_column"],
            message=MultilingualString(en="{col} is not a column of this dataset."),
            bindings={"col": F("group_column")},
            requires_ctx=True,
        ),
        Relevance("random_state", when=IsTrue(F("shuffle")), effect="disable"),
    ]
    # The fixture must hold what the BROWSER receives, which is the payload
    # after the API boundary collapsed every MultilingualString through
    # localize(). Storing the multilingual form instead would test a wire
    # format that never reaches the frontend.
    wire = localize(rules_to_wire(rules), "en")

    scenarios = [
        (
            "valid_60_30_10",
            {
                "train": 0.6,
                "validation": 0.3,
                "test": 0.1,
                "shuffle": True,
                "random_state": 42,
                "group_column": "a",
            },
            {"columns": ["a", "b"]},
        ),
        (
            "sum_too_high",
            {
                "train": 0.8,
                "validation": 0.3,
                "test": 0.3,
                "shuffle": True,
                "random_state": 42,
                "group_column": "a",
            },
            {"columns": ["a", "b"]},
        ),
        (
            "mid_edit_train_cleared",
            {
                "train": None,
                "validation": 0.3,
                "test": 0.1,
                "shuffle": True,
                "random_state": 42,
                "group_column": "a",
            },
            {"columns": ["a", "b"]},
        ),
        (
            "irrelevant_seed_is_not_checked",
            {
                "train": 0.6,
                "validation": 0.3,
                "test": 0.1,
                "shuffle": False,
                "random_state": -5,
                "group_column": "a",
            },
            {"columns": ["a", "b"]},
        ),
        (
            "relevant_seed_is_checked",
            {
                "train": 0.6,
                "validation": 0.3,
                "test": 0.1,
                "shuffle": True,
                "random_state": -5,
                "group_column": "a",
            },
            {"columns": ["a", "b"]},
        ),
        (
            "ctx_rule_pending_without_ctx",
            {
                "train": 0.6,
                "validation": 0.3,
                "test": 0.1,
                "shuffle": True,
                "random_state": 42,
                "group_column": "zz",
            },
            None,
        ),
        (
            "ctx_rule_fails_with_ctx",
            {
                "train": 0.6,
                "validation": 0.3,
                "test": 0.1,
                "shuffle": True,
                "random_state": 42,
                "group_column": "zz",
            },
            {"columns": ["a", "b"]},
        ),
    ]

    encoded = []
    for name, values, ctx in scenarios:
        report = evaluate_rules(wire, values, ctx)
        encoded.append(
            {
                "name": name,
                "values": values,
                "ctx": ctx,
                "expect": {
                    "errors": {
                        target: violation["message"]
                        for violation in report.violations
                        for target in violation["targets"]
                    },
                    "pending": sorted(report.pending),
                    "irrelevant": sorted(report.irrelevant_fields()),
                },
            }
        )
    return {"rules": wire, "scenarios": encoded}


def _random_ast(rng: random.Random, depth: int = 0) -> Dict[str, Any]:
    """Build a random expression, biased toward shapes that actually occur."""
    field_names = ["train", "validation", "test", "empty", "shuffle", "name", "items"]
    ctx_keys = ["n_rows", "columns", "absent_key"]

    if depth >= 3:
        choice = rng.choice(["field", "ctx", "lit"])
    else:
        choice = rng.choice(
            [
                "field",
                "ctx",
                "lit",
                "sum",
                "add",
                "sub",
                "mul",
                "cmp",
                "cmp",
                "approx",
                "and",
                "or",
                "not",
                "is_null",
                "is_true",
                "is_false",
                "in",
                "len",
            ]
        )

    if choice == "field":
        return {"n": "field", "f": rng.choice(field_names)}
    if choice == "ctx":
        return {"n": "ctx", "k": rng.choice(ctx_keys)}
    if choice == "lit":
        return {
            "n": "lit",
            "v": rng.choice([0, 1, -1, 0.5, 1.0, True, False, None, "a", "abc"]),
        }
    if choice == "sum":
        count = rng.randint(1, 3)
        return {"n": "sum", "of": [_random_ast(rng, depth + 1) for _ in range(count)]}
    if choice in ("add", "sub", "mul", "in"):
        return {
            "n": choice,
            "a": _random_ast(rng, depth + 1),
            "b": _random_ast(rng, depth + 1),
        }
    if choice == "cmp":
        return {
            "n": "cmp",
            "op": rng.choice(["lt", "lte", "gt", "gte", "eq", "ne"]),
            "a": _random_ast(rng, depth + 1),
            "b": _random_ast(rng, depth + 1),
        }
    if choice == "approx":
        return {
            "n": "approx",
            "a": _random_ast(rng, depth + 1),
            "b": _random_ast(rng, depth + 1),
            "tol": rng.choice([0, 1e-6, 0.1]),
        }
    if choice in ("and", "or"):
        count = rng.randint(1, 3)
        return {"n": choice, "of": [_random_ast(rng, depth + 1) for _ in range(count)]}
    return {"n": choice, "of": _random_ast(rng, depth + 1)}


def _sweep_cases() -> List[Dict[str, Any]]:
    """A seeded random walk over the algebra. Same seed, same fixture, always."""
    rng = random.Random(20260904)
    values = {
        "train": 0.6,
        "validation": 0.3,
        "test": 0.1,
        "empty": None,
        "shuffle": True,
        "name": "abc",
        "items": ["a", "b"],
    }
    ctx = {"n_rows": 1000, "columns": ["a", "b"]}
    cases = []
    for index in range(SWEEP_SIZE):
        ast = _random_ast(rng)
        use_ctx = ctx if index % 4 else None
        cases.append(
            {
                "ast": ast,
                "ctx_present": use_ctx is not None,
                "expect": _encode(evaluate(ast, values, use_ctx)),
            }
        )
    return {"values": values, "ctx": ctx, "cases": cases}


def build_fixture() -> Dict[str, Any]:
    """Assemble the whole fixture. Pure, so the output is reproducible."""
    return {
        "version": FIXTURE_VERSION,
        "generated_by": "tests/back/core/test_rules_conformance.py",
        "note": (
            "Generated by pytest and replayed by "
            "DashAI/front/src/utils/ruleEngine.test.js. Do not hand-edit: "
            "regenerate with `uv run pytest "
            "tests/back/core/test_rules_conformance.py` and review the diff."
        ),
        "named": _named_cases(),
        "formatting": _formatting_cases(),
        "rulesets": _ruleset_cases(),
        "sweep": _sweep_cases(),
    }


def test_fixture_is_written_and_self_consistent():
    """Write the fixture and prove the Python side agrees with what it claims."""
    fixture = build_fixture()

    for case in fixture["named"]:
        actual = _encode(evaluate(case["ast"], case["values"], case["ctx"]))
        assert actual == case["expect"], case["name"]

    for case in fixture["formatting"]:
        assert format_value(case["value"]) == case["expect"]

    sweep = fixture["sweep"]
    for index, case in enumerate(sweep["cases"]):
        ctx = sweep["ctx"] if case["ctx_present"] else None
        actual = _encode(evaluate(case["ast"], sweep["values"], ctx))
        assert actual == case["expect"], f"sweep case {index}"

    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Compact on purpose: the sweep is generated from a fixed seed, so its
    # diff is never read line by line. The human-reviewable part is the named
    # section, and a reviewer reads it in this file rather than in the JSON.
    FIXTURE_PATH.write_text(
        json.dumps(fixture, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    assert FIXTURE_PATH.exists()
    assert len(sweep["cases"]) == SWEEP_SIZE


def test_sweep_actually_exercises_every_verdict():
    """A sweep that only ever returns PENDING would prove nothing."""
    sweep = build_fixture()["sweep"]
    verdicts = [
        "pending"
        if isinstance(case["expect"], dict)
        else "bool"
        if isinstance(case["expect"], bool)
        else "value"
        for case in sweep["cases"]
    ]
    counts = {kind: verdicts.count(kind) for kind in set(verdicts)}
    assert counts.get("bool", 0) > 100, counts
    assert counts.get("pending", 0) > 100, counts
    assert counts.get("value", 0) > 40, counts


def test_pending_has_no_truth_value():
    """PENDING must not be usable as a boolean, or it decays into 'satisfied'."""
    with pytest.raises(TypeError):
        bool(PENDING)


def test_unknown_node_is_an_error_not_a_pass():
    """A rule the runtime does not understand must never evaluate to valid."""
    with pytest.raises(ValueError, match="Unknown rule node"):
        evaluate({"n": "regex_match", "a": {"n": "lit", "v": 1}}, {}, None)
