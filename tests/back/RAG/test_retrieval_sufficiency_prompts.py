"""Unit tests for the retrieval sufficiency prompt family.

Verifies the anchor's placeholder contract, the language-driven default
templates, custom-template validation and the optional-line semantics of
``{children_catalog}`` and ``{pool_size}``.
"""

from __future__ import annotations

import pytest

from DashAI.back.models.RAG.exceptions import RAGPromptTemplateError
from DashAI.back.models.RAG.prompts.evaluation import (
    CustomRetrievalSufficiencyPrompt,
    DefaultRetrievalSufficiencyPrompt,
    RetrievalSufficiencyPrompt,
)
from DashAI.back.models.RAG.prompts.evaluation import (
    default_retrieval_sufficiency_prompt as sufficiency_mod,
)

# ===================================================================
# placeholder declarations
# ===================================================================


class TestPlaceholderDeclarations:
    """Class-level placeholder attributes match the fixed contract."""

    def test_anchor_contract(self):
        assert RetrievalSufficiencyPrompt.required_placeholders == [
            "{input}",
            "{chunks}",
        ]
        assert RetrievalSufficiencyPrompt.optional_placeholders == [
            "{children_catalog}",
            "{pool_size}",
        ]

    def test_default_prompt_inherits_contract(self):
        assert DefaultRetrievalSufficiencyPrompt.required_placeholders == [
            "{input}",
            "{chunks}",
        ]
        assert DefaultRetrievalSufficiencyPrompt.optional_placeholders == [
            "{children_catalog}",
            "{pool_size}",
        ]


# ===================================================================
# default templates
# ===================================================================


class TestDefaultTemplates:
    """Default templates validate and expose the strict JSON contract."""

    @pytest.mark.parametrize("lang", ["en", "es", "pt"])
    def test_templates_validate(self, lang):
        assert DefaultRetrievalSufficiencyPrompt.validate_template(
            sufficiency_mod.TEMPLATES[lang]
        )

    def test_templates_expose_json_contract(self):
        for template in sufficiency_mod.TEMPLATES.values():
            assert '"sufficient"' in template
            assert '"top_k"' in template
            assert "```" not in template

    def test_templates_reference_both_required_placeholders(self):
        for template in sufficiency_mod.TEMPLATES.values():
            assert "{input}" in template
            assert "{chunks}" in template


# ===================================================================
# format rendering
# ===================================================================


class TestFormatRendering:
    """``format`` substitutes placeholders and drops optional lines."""

    def test_replaces_required_and_optional(self):
        prompt = DefaultRetrievalSufficiencyPrompt(language="en")
        rendered = prompt.format(
            input="What is DashAI?",
            chunks="DashAI is a toolbox.",
            children_catalog="0: BM25Retriever",
            pool_size=5,
        )
        assert "What is DashAI?" in rendered
        assert "DashAI is a toolbox." in rendered
        assert "0: BM25Retriever" in rendered
        assert "Candidate pool size: 5 chunks" in rendered
        assert "{input}" not in rendered
        assert "{chunks}" not in rendered
        assert "{children_catalog}" not in rendered
        assert "{pool_size}" not in rendered

    def test_optional_lines_dropped_when_none(self):
        prompt = DefaultRetrievalSufficiencyPrompt(language="en")
        rendered = prompt.format(input="Q?", chunks="some chunk")
        assert "{children_catalog}" not in rendered
        assert "{pool_size}" not in rendered
        # The lines owning the optional tokens vanish entirely.
        assert "Child retriever catalog" not in rendered
        assert "Candidate pool size" not in rendered
        assert "indices selected from" not in rendered

    def test_catalog_instruction_dropped_when_absent(self):
        prompt = DefaultRetrievalSufficiencyPrompt(language="en")
        rendered = prompt.format(input="Q?", chunks="some chunk")
        # Without a catalog the ``children`` alternative must not be offered.
        assert '"children": [' not in rendered

    def test_default_prompt_picks_template_by_language(self):
        for lang in ("en", "es", "pt"):
            prompt = DefaultRetrievalSufficiencyPrompt(language=lang)
            assert prompt.template == sufficiency_mod.TEMPLATES[lang]

    def test_unknown_language_raises(self):
        with pytest.raises(RAGPromptTemplateError):
            DefaultRetrievalSufficiencyPrompt(language="klingon")


# ===================================================================
# custom templates
# ===================================================================


class TestCustomTemplates:
    """Custom prompts validate their template on construction."""

    def test_custom_missing_required_placeholder_raises(self):
        with pytest.raises(RAGPromptTemplateError):
            CustomRetrievalSufficiencyPrompt(template="no placeholders here")

    def test_custom_missing_chunks_raises(self):
        with pytest.raises(RAGPromptTemplateError):
            CustomRetrievalSufficiencyPrompt(template="only {input} present")

    def test_custom_valid_renders(self):
        prompt = CustomRetrievalSufficiencyPrompt(template="{input} || {chunks}")
        assert prompt.format(input="a", chunks="b") == "a || b"

    def test_custom_allows_absent_optional(self):
        prompt = CustomRetrievalSufficiencyPrompt(template="{input} || {chunks}")
        rendered = prompt.format(input="a", chunks="b", pool_size=None)
        assert rendered == "a || b"
