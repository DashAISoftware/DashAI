"""Integration test that runs the full ``RAGJob`` with a stub LLM.

``RAGJob`` orchestrates the complete RAG pipeline lifecycle: document
loading, chunking, retrieval, prompt formatting and LLM generation.  A
registered ``StubLLM`` replaces the real inference backend so the whole
pipeline can execute quickly and deterministically in a test.

Parametrised over ``(retriever, prompt)`` so both sparse retrievers
(``BM25Retriever`` / ``TFIDFRetriever``) and both default prompt classes
(``DefaultRAGGenerationPrompt`` / ``DefaultQARAGGenerationPrompt`` — note the
double ``GG`` in the QA class name) are exercised.  After ``RAGJob(...).run()``
the generative process must reach ``RunStatus.FINISHED`` and store a ``str``
output containing the stub answer.
"""

import contextlib
import os
import tempfile
import uuid

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import RunStatus
from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.dependencies.database.models import (
    GenerativeProcess,
    GenerativeSession,
    ProcessData,
)
from DashAI.back.job.RAG_job import RAGJob
from DashAI.back.models.RAG.prompts.generation.default_QA_RAG_generation_prompt import (
    TEMPLATES as QA_TEMPLATES,
)
from DashAI.back.models.RAG.prompts.generation.default_RAG_generation_prompt import (
    TEMPLATES,
)
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from tests.back.RAG.conftest import _create_test_document

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------
STUB_ANSWER = "stub answer"

DOC_TEXT = (
    "DashAI is a graphical toolbox for training, evaluating and deploying "
    "machine learning models. It provides a complete graphical interface "
    "that allows users to compare and use different machine learning "
    "algorithms without writing code. " * 50
)

_TEMPLATES_BY_PROMPT = {
    "DefaultRAGGenerationPrompt": TEMPLATES,
    "DefaultQARAGGenerationPrompt": QA_TEMPLATES,
}


# ---------------------------------------------------------------------------
# Stub LLM
# ---------------------------------------------------------------------------


class StubLLMSchema(BaseSchema):
    """Empty schema — the stub model accepts any (empty) parameter set."""


class StubLLM(TextToTextGenerationTaskModel):
    """Deterministic text-to-text model used to avoid real LLM inference."""

    SCHEMA = StubLLMSchema

    def __init__(self, **kwargs):
        """Store parameters without initialising the base class."""
        self.parameters = {}

    def generate(self, prompt):
        """Return a fixed stub answer."""
        return [STUB_ANSWER]


@pytest.fixture(scope="module", autouse=True)
def register_stub_llm(client: TestClient) -> None:
    """Register ``StubLLM`` in the app component registry before the job runs."""
    client.app.container["component_registry"].register_component(StubLLM)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _frontend_session_parameters(doc_id: int, retriever: str, prompt: str) -> dict:
    """Build RAG session parameters for the given retriever/prompt pair."""
    if retriever == "BM25Retriever":
        vectorizer = {
            "component": "BM25VectorizerModel",
            "params": {
                "strip_accents": None,
                "lowercase": True,
                "stop_words": None,
                "max_df": 1.0,
                "min_df": 0.0,
                "max_features": None,
            },
        }
        retriever_params = {
            "BM25Vectorizer": vectorizer,
            "k1": 1.5,
            "b": 0.75,
            "delta": 0.0,
            "similarity_function": "cosine",
            "top_k": 5,
        }
    else:
        vectorizer = {
            "component": "TFIDFVectorizerModel",
            "params": {
                "strip_accents": "None",
                "lowercase": True,
                "analyzer": "word",
                "stop_words": [],
                "ngram_range": [1, 1],
                "max_df": 1.0,
                "min_df": 0.0,
                "max_features": 1000,
                "norm": "l2",
                "use_idf": True,
                "smooth_idf": True,
                "sublinear_tf": False,
            },
        }
        retriever_params = {
            "TFIDFVectorizer": vectorizer,
            "similarity_function": "cosine",
            "top_k": 5,
        }

    templates = _TEMPLATES_BY_PROMPT[prompt]
    return {
        "documents": [doc_id],
        "chunking_model": {
            "component": "CharacterChunkModel",
            "params": {"chunk_size": 200, "chunk_overlap": 20},
        },
        "retriever_model": {"component": retriever, "params": retriever_params},
        "generation_model": {"component": "StubLLM", "params": {}},
        "prompt": {
            "component": prompt,
            "params": {"language": "en", "template": templates["en"]},
        },
    }


# ===================================================================
# RAGJob end-to-end flow
# ===================================================================


@pytest.mark.parametrize(
    ("retriever", "prompt"),
    [
        ("BM25Retriever", "DefaultRAGGenerationPrompt"),
        ("TFIDFRetriever", "DefaultQARAGGenerationPrompt"),
    ],
)
def test_rag_job_completes_full_flow(
    client: TestClient,
    retriever: str,
    prompt: str,
) -> None:
    """Running ``RAGJob`` on a valid session finishes with the stub output."""
    run_tag = uuid.uuid4().hex[:8]
    suffix = f"_{run_tag}_{retriever}"
    doc_id = _create_test_document(client, suffix=suffix)
    file_path = os.path.join(tempfile.gettempdir(), f"test_doc{suffix}.txt")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(DOC_TEXT)

        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            session = GenerativeSession(
                task_name="RAGTask",
                model_name="RAGPipeline",
                parameters=_frontend_session_parameters(doc_id, retriever, prompt),
                name=f"job_flow_{retriever}_{run_tag}",
                description=None,
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            process = GenerativeProcess(
                session_id=session.id,
                status=RunStatus.NOT_STARTED,
            )
            db.add(process)
            db.commit()
            db.refresh(process)
            process_id = process.id

            db.add(
                ProcessData(
                    process_id=process_id,
                    is_input=True,
                    data="Tell me about DashAI",
                    data_type="str",
                )
            )
            db.commit()

        RAGJob(generative_process_id=process_id).run()

        with session_factory() as db:
            process = db.get(GenerativeProcess, process_id)
            assert process is not None, "The generative process must still exist."
            assert process.status == RunStatus.FINISHED, (
                f"Expected the process to finish, got status {process.status}."
            )
            assert any(
                o.data_type == "str" and STUB_ANSWER in o.data for o in process.output
            ), (
                "Expected a str output containing the stub answer, "
                f"got outputs: {[o.data for o in process.output]!r}"
            )
    finally:
        with contextlib.suppress(OSError):
            os.remove(file_path)
