"""Unit tests for the context-local RAG progress channel helpers.

The helpers are deliberately small: a context variable holding the current
reporter, a whitespace/length normalizer for LLM-authored text and a
``report_progress`` call that only emits JSON-shaped payloads with the canonical
keys first. These tests pin that contract plus the no-op and reset semantics.
"""

from __future__ import annotations

from typing import Any

import pytest

from DashAI.back.models.RAG.progress_utils import (
    normalize_progress_text,
    progress_scope,
    report_progress,
    sanitize_text,
)


class TestNormalizeProgressText:
    """Only strings survive; whitespace is collapsed and capped."""

    def test_collapses_all_whitespace(self):
        assert normalize_progress_text("  hello \n\t world  ") == "hello world"

    def test_non_string_values_return_empty(self):
        assert normalize_progress_text(None) == ""
        assert normalize_progress_text(123) == ""
        assert normalize_progress_text(["text"]) == ""
        assert normalize_progress_text({"text": "x"}) == ""

    def test_empty_and_whitespace_only_return_empty(self):
        assert normalize_progress_text("") == ""
        assert normalize_progress_text("   \n\t ") == ""

    def test_length_cap_leaves_short_text_untouched(self):
        assert normalize_progress_text("short", max_length=10) == "short"

    def test_length_cap_truncates_with_ellipsis(self):
        capped = normalize_progress_text("x" * 50, max_length=10)

        assert len(capped) <= 10
        assert capped.endswith("...")

    def test_zero_length_cap_returns_empty_safely(self):
        assert normalize_progress_text("anything", max_length=0) == ""

    def test_invisible_format_characters_are_removed(self):
        assert normalize_progress_text("\u200b") == ""
        assert normalize_progress_text("a\u200bb") == "ab"
        assert sanitize_text("\ufeffhello\u202e") == "hello"

    def test_lone_surrogates_are_replaced(self):
        text = normalize_progress_text("\ud800 ok")

        assert "\ud800" not in text
        assert text.endswith("ok")
        assert isinstance(text.encode("utf-8"), bytes)


class TestProgressScope:
    """The reporter is context-local and always restored on exit."""

    def test_no_reporter_is_a_noop(self):
        events = []

        report_progress("retrieving", message="ignored")

        assert events == []

    def test_scope_reports_canonical_payload_order(self):
        events: list[dict[str, Any]] = []

        with progress_scope(events.append):
            report_progress(
                "retrieving",
                message="  Looking   around ",
                justification=" because it helps ",
                queries=["q1"],
            )

        assert events == [
            {
                "stage": "retrieving",
                "message": "Looking around",
                "justification": "because it helps",
                "queries": ["q1"],
            }
        ]
        assert list(events[0]) == ["stage", "message", "justification", "queries"]

    def test_empty_narrative_keys_are_omitted(self):
        events: list[dict[str, Any]] = []

        with progress_scope(events.append):
            report_progress("generating", message="", justification=None)

        assert events == [{"stage": "generating"}]

    def test_canonical_keys_cannot_be_overridden_by_extras(self):
        """The signature rejects canonical keys smuggled through ``extras``."""
        events: list[dict[str, Any]] = []

        with progress_scope(events.append), pytest.raises(TypeError):
            report_progress("retrieving", stage="overridden")

        assert events == []

    def test_statements_and_extras_keep_canonical_order(self):
        events: list[dict[str, Any]] = []

        with progress_scope(events.append):
            report_progress(
                "retrieving",
                message="message",
                justification="justification",
                queries=["q"],
                extra=1,
            )

        assert events == [
            {
                "stage": "retrieving",
                "message": "message",
                "justification": "justification",
                "queries": ["q"],
                "extra": 1,
            }
        ]
        assert list(events[0]) == [
            "stage",
            "message",
            "justification",
            "queries",
            "extra",
        ]

    def test_scope_resets_after_exit(self):
        events: list[dict[str, Any]] = []

        with progress_scope(events.append):
            report_progress("transforming", message="inside")

        report_progress("generating", message="outside")

        assert events == [{"stage": "transforming", "message": "inside"}]

    def test_nested_scope_restores_the_outer_reporter(self):
        outer: list[dict[str, Any]] = []
        inner: list[dict[str, Any]] = []

        with progress_scope(outer.append):
            report_progress("transforming", message="outer")
            with progress_scope(inner.append):
                report_progress("retrieving", message="inner")
            report_progress("generating", message="outer again")

        assert [event["stage"] for event in outer] == ["transforming", "generating"]
        assert [event["stage"] for event in inner] == ["retrieving"]

    def test_scope_resets_when_the_body_raises(self):
        events: list[dict[str, Any]] = []

        def explode() -> None:
            report_progress("transforming", message="inside")
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"), progress_scope(events.append):
            explode()

        report_progress("generating", message="outside")

        assert events == [{"stage": "transforming", "message": "inside"}]

    def test_reporter_exceptions_propagate(self):
        def boom(_payload: dict[str, Any]) -> None:
            raise RuntimeError("reporter exploded")

        with (
            progress_scope(boom),
            pytest.raises(RuntimeError, match="reporter exploded"),
        ):
            report_progress("retrieving", message="x")
