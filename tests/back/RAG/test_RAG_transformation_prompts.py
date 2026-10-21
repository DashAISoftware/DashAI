"""Unit tests for the transformation prompt classes.

Verifies placeholder contracts, default templates, custom templates and the
optional-line semantics of ``{n_max}``.
"""

from __future__ import annotations

import pytest

from DashAI.back.models.RAG.exceptions import RAGPromptTemplateError
from DashAI.back.models.RAG.prompts.transformation import (
    CustomQueryDecompositionPrompt,
    CustomQueryExpansionPrompt,
    CustomQueryRewritingPrompt,
    DefaultQueryDecompositionPrompt,
    DefaultQueryExpansionPrompt,
    DefaultQueryRewritingPrompt,
    QueryDecompositionPrompt,
    QueryExpansionPrompt,
    QueryRewritingPrompt,
    QueryTransformationPrompt,
)
from DashAI.back.models.RAG.prompts.transformation import (
    default_query_decomposition_prompt as dec_mod,
)
from DashAI.back.models.RAG.prompts.transformation import (
    default_query_expansion_prompt as exp_mod,
)
from DashAI.back.models.RAG.prompts.transformation import (
    default_query_rewriting_prompt as rw_mod,
)

# ===================================================================
# placeholder declarations
# ===================================================================


class TestPlaceholderDeclarations:
    """Class-level placeholder attributes match the contract."""

    def test_base_contract(self):
        assert QueryTransformationPrompt.required_placeholders == [
            "{input}",
            "{history}",
        ]
        assert QueryTransformationPrompt.optional_placeholders == []

    def test_rewriting_contract(self):
        assert QueryRewritingPrompt.required_placeholders == ["{input}", "{history}"]
        assert QueryRewritingPrompt.optional_placeholders == []

    def test_expansion_contract(self):
        assert QueryExpansionPrompt.required_placeholders == [
            "{input}",
            "{history}",
            "{n}",
        ]
        assert QueryExpansionPrompt.optional_placeholders == []

    def test_decomposition_contract(self):
        assert QueryDecompositionPrompt.required_placeholders == [
            "{input}",
            "{history}",
        ]
        assert QueryDecompositionPrompt.optional_placeholders == ["{n_max}"]


# ===================================================================
# default templates
# ===================================================================


class TestDefaultTemplates:
    """Default templates are valid in every language."""

    @pytest.mark.parametrize("lang", ["en", "es", "pt"])
    def test_rewriting_templates_validate(self, lang):
        template = rw_mod.TEMPLATES[lang]
        assert DefaultQueryRewritingPrompt.validate_template(template)

    @pytest.mark.parametrize("lang", ["en", "es", "pt"])
    def test_expansion_templates_validate(self, lang):
        template = exp_mod.TEMPLATES[lang]
        assert DefaultQueryExpansionPrompt.validate_template(template)

    @pytest.mark.parametrize("lang", ["en", "es", "pt"])
    def test_decomposition_templates_validate(self, lang):
        template = dec_mod.TEMPLATES[lang]
        assert DefaultQueryDecompositionPrompt.validate_template(template)

    def test_templates_expose_function_call_contract(self):
        for template in rw_mod.TEMPLATES.values():
            assert '"rewrite_query"' in template
            assert '"arguments"' in template
            assert '"query"' in template
        for template in exp_mod.TEMPLATES.values():
            assert '"expand_query"' in template
            assert '"arguments"' in template
            assert '"queries"' in template
        for template in dec_mod.TEMPLATES.values():
            assert '"decompose_query"' in template
            assert '"arguments"' in template
            assert '"queries"' in template

    def test_templates_have_no_markdown_fences(self):
        for module in (rw_mod, exp_mod, dec_mod):
            for template in module.TEMPLATES.values():
                assert "```" not in template

    def test_templates_request_progress_narrative(self):
        """Every default template asks for a user message and a justification."""
        for module in (rw_mod, exp_mod, dec_mod):
            for template in module.TEMPLATES.values():
                assert '"message"' in template
                assert '"justification"' in template


# ===================================================================
# format rendering
# ===================================================================


class TestFormatRendering:
    """``format`` substitutes placeholders and handles optional lines."""

    def test_rewriting_replaces_input_and_history(self):
        prompt = DefaultQueryRewritingPrompt(language="en")
        rendered = prompt.format(input="Hello world", history="user: hi")
        assert "Hello world" in rendered
        assert "user: hi" in rendered
        assert "{input}" not in rendered
        assert "{history}" not in rendered

    def test_rewriting_accepts_empty_history(self):
        prompt = DefaultQueryRewritingPrompt(language="en")
        rendered = prompt.format(input="Hello", history="")
        assert "Hello" in rendered
        assert "{history}" not in rendered

    def test_expansion_replaces_n(self):
        prompt = DefaultQueryExpansionPrompt(language="en")
        rendered = prompt.format(input="Hello", history="", n=4)
        assert "{n}" not in rendered
        assert "exactly 4 concise" in rendered

    def test_decomposition_optional_line_replaced_when_set(self):
        prompt = DefaultQueryDecompositionPrompt(language="en")
        rendered = prompt.format(input="Hello", history="", n_max=2)
        assert "more than 2 sub-queries" in rendered
        assert "{n_max}" not in rendered

    def test_decomposition_optional_line_dropped_when_none(self):
        prompt = DefaultQueryDecompositionPrompt(language="en")
        rendered = prompt.format(input="Hello", history="", n_max=None)
        assert "Do not produce more than" not in rendered
        assert "{n_max}" not in rendered
        # The rest of the template survives the line removal.
        assert "decompose_query" in rendered
        assert "Hello" in rendered


# ===================================================================
# custom templates
# ===================================================================


class TestCustomTemplates:
    """Custom prompts validate their template on construction."""

    def test_custom_rewriting_rejects_missing_placeholder(self):
        with pytest.raises(RAGPromptTemplateError):
            CustomQueryRewritingPrompt(template="no placeholders here")

    def test_custom_rewriting_renders_when_valid(self):
        prompt = CustomQueryRewritingPrompt(template="Q: {input}\nH: {history}")
        rendered = prompt.format(input="a", history="b")
        assert rendered == "Q: a\nH: b"

    def test_custom_expansion_rejects_missing_n(self):
        with pytest.raises(RAGPromptTemplateError):
            CustomQueryExpansionPrompt(template="{input} {history}")

    def test_custom_decomposition_allows_missing_optional(self):
        prompt = CustomQueryDecompositionPrompt(template="{input} || {history}")
        rendered = prompt.format(input="q", history="h")
        assert rendered == "q || h"


# ===================================================================
# default prompt overrides
# ===================================================================


class TestDefaultOverrides:
    """Template overrides are validated and unknown languages rejected."""

    def test_override_missing_required_placeholder_raises(self):
        with pytest.raises(RAGPromptTemplateError):
            DefaultQueryRewritingPrompt(language="en", template="only {input}")

    def test_unknown_language_raises(self):
        with pytest.raises(RAGPromptTemplateError):
            DefaultQueryRewritingPrompt(language="klingon")

    def test_override_with_all_placeholders_accepted(self):
        prompt = DefaultQueryRewritingPrompt(
            language="en", template="{input} -- {history}"
        )
        assert prompt.format(input="a", history="b") == "a -- b"


# ===================================================================
# metadata
# ===================================================================


class TestMetadata:
    """metadata dicts agree with the class attributes."""

    def test_default_metadata_matches_anchor_and_templates(self):
        cases = [
            (DefaultQueryRewritingPrompt, rw_mod.TEMPLATES, QueryRewritingPrompt),
            (DefaultQueryExpansionPrompt, exp_mod.TEMPLATES, QueryExpansionPrompt),
            (
                DefaultQueryDecompositionPrompt,
                dec_mod.TEMPLATES,
                QueryDecompositionPrompt,
            ),
        ]
        for cls, templates, anchor in cases:
            metadata = cls.get_metadata()
            assert metadata["type"] == "transformation"
            assert metadata["required_placeholders"] == anchor.required_placeholders
            assert metadata["optional_placeholders"] == anchor.optional_placeholders
            assert metadata["templates"] == templates
            assert "{input}" in metadata["placeholder_descriptions"]
            assert "{history}" in metadata["placeholder_descriptions"]

    def test_custom_metadata_has_no_templates(self):
        customs = (
            CustomQueryRewritingPrompt,
            CustomQueryExpansionPrompt,
            CustomQueryDecompositionPrompt,
        )
        for cls in customs:
            metadata = cls.get_metadata()
            assert metadata["type"] == "transformation"
            assert "templates" not in metadata
            assert "{input}" in metadata["placeholder_descriptions"]
            assert "{history}" in metadata["placeholder_descriptions"]
