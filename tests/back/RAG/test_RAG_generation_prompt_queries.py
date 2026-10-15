"""Tests for the optional ``{queries}`` placeholder in generation prompts.

The query-transformation stage may produce several search queries before
retrieval. When it does, the RAG pipeline renders them into the generation
prompt through an optional ``{queries}`` placeholder. When the stage is
disabled, the physical line carrying the placeholder is removed so no dangling
"Search queries used for retrieval:" section survives.

These tests are pure: they build the real default/custom generation prompts and
assert the rendered text, no pipeline or database involved.
"""

from __future__ import annotations

import pytest

from DashAI.back.models.RAG.prompts.generation.custom_RAG_generation_prompt import (
    CustomRAGGenerationPrompt,
)
from DashAI.back.models.RAG.prompts.generation.default_QA_RAG_generation_prompt import (
    TEMPLATES as QA_TEMPLATES,
)
from DashAI.back.models.RAG.prompts.generation.default_QA_RAG_generation_prompt import (
    DefaultQARAGGenerationPrompt,
)
from DashAI.back.models.RAG.prompts.generation.default_RAG_generation_prompt import (
    TEMPLATES as DEFAULT_TEMPLATES,
)
from DashAI.back.models.RAG.prompts.generation.default_RAG_generation_prompt import (
    DefaultRAGGenerationPrompt,
)
from DashAI.back.models.RAG.prompts.generation.RAG_generation_prompt import (
    RAGGenerationPrompt,
)

#: The exact header rendered for each language.
QUERIES_HEADERS = {
    "en": "Search queries used for retrieval",
    "es": "Consultas de búsqueda utilizadas para recuperar",
    "pt": "Consultas de pesquisa utilizadas para recuperar",
}


def _default(language: str = "en") -> DefaultRAGGenerationPrompt:
    return DefaultRAGGenerationPrompt(
        language=language, template=DEFAULT_TEMPLATES[language]
    )


def _qa(language: str = "en") -> DefaultQARAGGenerationPrompt:
    return DefaultQARAGGenerationPrompt(
        language=language, template=QA_TEMPLATES[language]
    )


# ===================================================================
# abstract contract
# ===================================================================


class TestAbstractContract:
    """The base class declares the optional placeholder and a helper."""

    def test_optional_placeholder_declared(self):
        assert "{queries}" in RAGGenerationPrompt.optional_placeholders

    def test_required_placeholders_unchanged(self):
        assert RAGGenerationPrompt.required_placeholders == ["{input}", "{chunks}"]

    def test_render_queries_none_drops_line(self):
        rendered = RAGGenerationPrompt.render_queries(
            "before\nSearch queries used for retrieval: {queries}\nafter",
            None,
        )
        assert rendered == "before\nafter"

    def test_render_queries_value_replaces(self):
        rendered = RAGGenerationPrompt.render_queries(
            "Search queries used for retrieval: {queries}",
            "q1; q2",
        )
        assert rendered == "Search queries used for retrieval: q1; q2"


# ===================================================================
# default RAG generation prompt
# ===================================================================


class TestDefaultRAGGenerationPromptQueries:
    """Default generation prompt rendering with and without queries."""

    @pytest.mark.parametrize("language", ["en", "es", "pt"])
    def test_queries_rendered_per_language(self, language):
        prompt = _default(language)
        rendered = prompt.format(input="hello", chunks="ctx", queries="q1; q2")
        assert f"{QUERIES_HEADERS[language]}: q1; q2" in rendered

    @pytest.mark.parametrize("language", ["en", "es", "pt"])
    def test_queries_none_drops_the_line(self, language):
        prompt = _default(language)
        rendered = prompt.format(input="hello", chunks="ctx", queries=None)
        assert "{queries}" not in rendered
        assert QUERIES_HEADERS[language] not in rendered

    def test_absent_kwarg_behaves_like_none(self):
        prompt = _default("en")
        rendered = prompt.format(input="hello", chunks="ctx")
        assert "{queries}" not in rendered
        assert QUERIES_HEADERS["en"] not in rendered

    def test_backward_compatible_without_queries_token(self):
        old_template = "User: {input}\nDocs: {chunks}"
        prompt = DefaultRAGGenerationPrompt(language="en", template=old_template)
        rendered = prompt.format(input="hi", chunks="ctx", queries="q1")
        assert rendered == "User: hi\nDocs: ctx"

    def test_metadata_declares_optional_placeholder(self):
        metadata = DefaultRAGGenerationPrompt.metadata
        assert "{queries}" in metadata["optional_placeholders"]
        assert "{queries}" in metadata["placeholder_descriptions"]

    def test_template_contains_the_queries_line(self):
        for language in ("en", "es", "pt"):
            assert "{queries}" in DEFAULT_TEMPLATES[language]


# ===================================================================
# default QA RAG generation prompt
# ===================================================================


class TestDefaultQARAGGenerationPromptQueries:
    """QA generation prompt rendering with and without queries."""

    @pytest.mark.parametrize("language", ["en", "es", "pt"])
    def test_queries_rendered_per_language(self, language):
        prompt = _qa(language)
        rendered = prompt.format(input="hello", chunks="ctx", queries="q1; q2")
        assert f"{QUERIES_HEADERS[language]}: q1; q2" in rendered

    @pytest.mark.parametrize("language", ["en", "es", "pt"])
    def test_queries_none_drops_the_line(self, language):
        prompt = _qa(language)
        rendered = prompt.format(input="hello", chunks="ctx", queries=None)
        assert "{queries}" not in rendered
        assert QUERIES_HEADERS[language] not in rendered

    def test_backward_compatible_without_queries_token(self):
        old_template = "Q: {input}\nC: {chunks}"
        prompt = DefaultQARAGGenerationPrompt(language="en", template=old_template)
        rendered = prompt.format(input="hi", chunks="ctx", queries=None)
        assert rendered == "Q: hi\nC: ctx"

    def test_metadata_declares_optional_placeholder(self):
        metadata = DefaultQARAGGenerationPrompt.metadata
        assert "{queries}" in metadata["optional_placeholders"]
        assert "{queries}" in metadata["placeholder_descriptions"]

    def test_template_contains_the_queries_line(self):
        for language in ("en", "es", "pt"):
            assert "{queries}" in QA_TEMPLATES[language]


# ===================================================================
# custom generation prompt
# ===================================================================


class TestCustomRAGGenerationPromptQueries:
    """Custom templates decide where ``{queries}`` goes."""

    def test_mid_sentence_placeholder_renders(self):
        template = "Answer {input} using docs {chunks}.\nQueries: {queries}"
        prompt = CustomRAGGenerationPrompt(template=template)
        rendered = prompt.format(input="X", chunks="C", queries="q1; q2")
        assert "Queries: q1; q2" in rendered

    def test_absent_queries_drops_only_that_line(self):
        template = "Answer {input} using docs {chunks}.\nQueries: {queries}"
        prompt = CustomRAGGenerationPrompt(template=template)
        rendered = prompt.format(input="X", chunks="C", queries=None)
        assert "Queries:" not in rendered
        assert "{queries}" not in rendered
        assert "Answer X using docs C." in rendered

    def test_template_without_queries_is_unchanged(self):
        template = "Answer {input} using docs {chunks}."
        prompt = CustomRAGGenerationPrompt(template=template)
        rendered = prompt.format(input="X", chunks="C", queries="q1")
        assert rendered == "Answer X using docs C."

    def test_format_without_queries_kwarg_works(self):
        template = "Answer {input} using docs {chunks}.\nQueries: {queries}"
        prompt = CustomRAGGenerationPrompt(template=template)
        rendered = prompt.format(input="X", chunks="C")
        assert "Queries:" not in rendered

    def test_metadata_exposes_optional_placeholder(self):
        assert "{queries}" in CustomRAGGenerationPrompt.optional_placeholders
        metadata = CustomRAGGenerationPrompt.metadata
        assert "{queries}" in metadata["optional_placeholders"]


# ===================================================================
# input/chunk text carrying placeholder tokens
# ===================================================================


class TestInputContainingPlaceholderTokens:
    """Optional tokens resolve first; required substitution is single-pass."""

    def test_default_input_with_queries_token_when_disabled(self):
        prompt = _default("en")
        rendered = prompt.format(
            input="please show {queries} literally", chunks="ctx", queries=None
        )
        assert "please show {queries} literally" in rendered
        assert QUERIES_HEADERS["en"] not in rendered

    def test_default_input_with_input_token_not_re_expanded(self):
        prompt = _default("en")
        rendered = prompt.format(
            input="literal {input} token", chunks="ctx", queries="q1"
        )
        assert "literal {input} token" in rendered
        assert QUERIES_HEADERS["en"] in rendered

    def test_default_chunk_with_queries_token_survives(self):
        prompt = _default("en")
        rendered = prompt.format(
            input="hi", chunks="chunk says {queries}", queries=None
        )
        assert "chunk says {queries}" in rendered
        assert QUERIES_HEADERS["en"] not in rendered

    def test_qa_input_with_queries_token_when_disabled(self):
        prompt = _qa("en")
        rendered = prompt.format(input="literal {queries}", chunks="ctx", queries=None)
        assert "literal {queries}" in rendered
        assert QUERIES_HEADERS["en"] not in rendered

    def test_custom_input_with_queries_token_when_disabled(self):
        template = "Answer {input} using docs {chunks}.\nQueries: {queries}"
        prompt = CustomRAGGenerationPrompt(template=template)
        rendered = prompt.format(input="literal {queries}", chunks="C", queries=None)
        assert "Answer literal {queries} using docs C." in rendered
        assert "Queries:" not in rendered
