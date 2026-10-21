"""Unit tests for the retrieval sufficiency prompt family.

Verifies the anchor's placeholder contract, the language-driven default
templates, custom-template validation, the optional-line semantics and the JSON
rendering of the retriever/document catalogs.
"""

from __future__ import annotations

import json

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

OPTIONAL_PLACEHOLDERS = [
    "{children_catalog}",
    "{pool_size}",
    "{topk}",
    "{retriever.description}",
    "{documents.names}",
    "{documents.description}",
]

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
        assert RetrievalSufficiencyPrompt.optional_placeholders == (
            OPTIONAL_PLACEHOLDERS
        )

    def test_default_prompt_inherits_contract(self):
        assert DefaultRetrievalSufficiencyPrompt.required_placeholders == [
            "{input}",
            "{chunks}",
        ]
        assert DefaultRetrievalSufficiencyPrompt.optional_placeholders == (
            OPTIONAL_PLACEHOLDERS
        )


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

    def test_templates_expose_function_call_contract(self):
        for template in sufficiency_mod.TEMPLATES.values():
            assert '"sufficient"' in template
            assert '"call_retrievers"' in template
            assert '"request_chunks"' in template
            assert '"discard"' in template
            assert "evaluate_retrieval_sufficiency" in template
            assert "```" not in template

    def test_templates_reference_supported_placeholders(self):
        for template in sufficiency_mod.TEMPLATES.values():
            for placeholder in (
                "{input}",
                "{chunks}",
                "{topk}",
                "{retriever.description}",
                "{documents.names}",
                "{documents.description}",
                "{pool_size}",
            ):
                assert placeholder in template

    def test_templates_drop_legacy_verdict_fields(self):
        for template in sufficiency_mod.TEMPLATES.values():
            assert '"top_k":' not in template
            assert '"children":' not in template


# ===================================================================
# format rendering
# ===================================================================


def _catalog() -> dict:
    return {
        1: {"class": "BM25Retriever", "params": {"k1": 1.5, "b": 0.75}},
        2: {"class": "DenseEmbeddingRetriever", "params": {"top_k": 5}},
    }


def _documents() -> list[dict]:
    return [{"document_id": 1, "name": "alpha.pdf", "chunks": 4, "pages": 2}]


def _chunks() -> list[dict]:
    return [
        {"document_id": 1, "position": 0, "text": "first chunk"},
        {"document_id": 2, "position": 3, "text": "second chunk"},
    ]


class TestFormatRendering:
    """``format`` substitutes placeholders and drops optional lines."""

    def test_replaces_required_and_optional(self):
        prompt = DefaultRetrievalSufficiencyPrompt(language="en")
        rendered = prompt.format(
            input="What is DashAI?",
            chunks=_chunks(),
            children_catalog=_catalog(),
            pool_size=5,
            top_k=10,
            retrievers=_catalog(),
            documents=_documents(),
        )
        assert "What is DashAI?" in rendered
        assert "[1] (document_id=1, position=0) first chunk" in rendered
        assert "[2] (document_id=2, position=3) second chunk" in rendered
        assert "Candidate pool size: 5 chunks" in rendered
        assert "Maximum retrievable chunks: 10" in rendered
        assert "alpha.pdf" in rendered
        assert '"class": "BM25Retriever"' in rendered
        assert '"document_id": 1' in rendered
        for token in OPTIONAL_PLACEHOLDERS:
            assert token not in rendered

    def test_dict_values_render_as_indented_json(self):
        prompt = DefaultRetrievalSufficiencyPrompt(language="en")
        rendered = prompt.format(
            input="Q?",
            chunks="chunk",
            retrievers={1: {"class": "X"}},
            documents=[{"document_id": 2, "name": "beta.pdf"}],
        )
        assert json.dumps({1: {"class": "X"}}, ensure_ascii=False, indent=2) in rendered
        assert (
            json.dumps(
                [{"document_id": 2, "name": "beta.pdf"}],
                ensure_ascii=False,
                indent=2,
            )
            in rendered
        )
        assert "beta.pdf" in rendered

    def test_missing_document_name_falls_back_in_the_prompt(self):
        """The prompt owns the ``document {id}`` display fallback."""
        prompt = DefaultRetrievalSufficiencyPrompt(language="en")
        rendered = prompt.format(
            input="Q?",
            chunks="chunk",
            documents=[{"document_id": 7, "name": None, "chunks": 1, "pages": 0}],
        )
        assert "document 7" in rendered

    def test_malformed_chunk_payload_raises(self):
        """A structured chunk missing a required key fails loudly."""
        prompt = CustomRetrievalSufficiencyPrompt(template="{input}|{chunks}")

        with pytest.raises(RAGPromptTemplateError, match="missing required keys"):
            prompt.format(
                input="q",
                chunks=[{"document_id": 1, "position": 0}],
            )

    def test_non_mapping_chunk_payload_raises(self):
        """A non-mapping chunk payload fails loudly."""
        prompt = CustomRetrievalSufficiencyPrompt(template="{input}|{chunks}")

        with pytest.raises(RAGPromptTemplateError, match="must be a mapping"):
            prompt.format(input="q", chunks=["not a mapping"])

    def test_truncated_chunk_text_gets_an_ellipsis(self):
        """Long chunk text is truncated and marked with an ellipsis."""
        prompt = CustomRetrievalSufficiencyPrompt(template="{input}|{chunks}")

        rendered = prompt.format(
            input="q",
            chunks=[{"document_id": 1, "position": 0, "text": "x" * 500}],
        )

        assert "x" * 400 + "..." in rendered

    def test_preformatted_chunks_are_kept_verbatim(self):
        prompt = CustomRetrievalSufficiencyPrompt(template="{input}||{chunks}")
        rendered = prompt.format(input="q", chunks="[9] already rendered")
        assert rendered == "q||[9] already rendered"

    def test_preformatted_retrievers_are_kept_verbatim(self):
        prompt = CustomRetrievalSufficiencyPrompt(
            template="{input}|{chunks}|{retriever.description}"
        )
        rendered = prompt.format(input="q", chunks="c", retrievers="1: BM25Retriever")
        assert rendered == "q|c|1: BM25Retriever"

    def test_children_catalog_is_an_alias_for_the_retriever_description(self):
        prompt = CustomRetrievalSufficiencyPrompt(
            template="{input}|{chunks}|{children_catalog}|{retriever.description}"
        )
        rendered = prompt.format(input="q", chunks="c", retrievers={1: {"class": "R"}})
        catalog_json = json.dumps({1: {"class": "R"}}, ensure_ascii=False, indent=2)
        assert rendered == f"q|c|{catalog_json}|{catalog_json}"

    def test_optional_lines_dropped_when_none(self):
        prompt = DefaultRetrievalSufficiencyPrompt(language="en")
        rendered = prompt.format(input="Q?", chunks="some chunk")
        for token in OPTIONAL_PLACEHOLDERS:
            assert token not in rendered
        assert "Documents:" not in rendered
        assert "Document description" not in rendered
        assert "Maximum retrievable chunks" not in rendered
        assert "Retriever catalog" not in rendered
        assert "Candidate pool size" not in rendered

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

    def test_custom_renders_document_names_and_topk(self):
        prompt = CustomRetrievalSufficiencyPrompt(
            template="{input}|{chunks}|{documents.names}|{topk}"
        )
        rendered = prompt.format(
            input="a",
            chunks="b",
            documents=[
                {"document_id": 1, "name": "alpha"},
                {"document_id": 2, "name": "beta"},
            ],
            top_k=7,
        )
        assert rendered == "a|b|alpha, beta|7"
