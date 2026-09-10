import logging
from typing import TYPE_CHECKING, Any, Dict, List

import numpy as np

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    enum_field,
    int_field,
    list_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.exceptions import RAGRetrieverError
from DashAI.back.models.RAG.retrievers.cross_encoder.cross_encoder_retriever import (
    CrossEncoderRetriever,
)

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder

log = logging.getLogger(__name__)

# ── Supported cross-encoder models ────────────────────────────────────────────

CROSS_ENCODER_MODELS: Dict[str, Dict[str, Any]] = {
    # ── MS MARCO passage ranking ──────────────────────────────────────────
    "cross-encoder/ms-marco-MiniLM-L-6-v2": {
        "languages": ["en"],
        "max_length": 512,
        "description": "MiniLM-L6 cross-encoder fine-tuned on MS MARCO. "
        "Good accuracy/speed trade-off.",
    },
    "cross-encoder/ms-marco-MiniLM-L-12-v2": {
        "languages": ["en"],
        "max_length": 512,
        "description": "Larger MiniLM-L12 variant for MS MARCO re-ranking.",
    },
    "cross-encoder/ms-marco-MiniLM-L-4-v2": {
        "languages": ["en"],
        "max_length": 512,
        "description": "Fast MiniLM-L4 variant for MS MARCO re-ranking.",
    },
    "cross-encoder/ms-marco-TinyBERT-L-2-v2": {
        "languages": ["en"],
        "max_length": 512,
        "description": "Lightweight TinyBERT cross-encoder for MS MARCO. "
        "Fastest option with acceptable accuracy.",
    },
    "cross-encoder/ms-marco-electra-base": {
        "languages": ["en"],
        "max_length": 512,
        "description": "ELECTRA-base cross-encoder fine-tuned on MS MARCO.",
    },
    # ── MS MARCO multilingual ─────────────────────────────────────────────
    "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1": {
        "languages": [
            "en",
            "es",
            "fr",
            "de",
            "it",
            "pt",
            "nl",
            "ar",
            "zh",
            "ja",
            "ko",
            "ru",
            "hi",
            "vi",
            "id",
            "multi",
        ],
        "max_length": 512,
        "description": "Multilingual MiniLM cross-encoder for MS MARCO re-ranking. "
        "Supports 14+ languages.",
    },
    # ── Semantic Textual Similarity (STS) ─────────────────────────────────
    "cross-encoder/stsb-roberta-base": {
        "languages": ["en"],
        "max_length": 512,
        "description": "RoBERTa-base cross-encoder fine-tuned on STS benchmark.",
    },
    "cross-encoder/stsb-distilroberta-base": {
        "languages": ["en"],
        "max_length": 512,
        "description": "Distilled RoBERTa cross-encoder for STS tasks.",
    },
    "cross-encoder/stsb-TinyBERT-L-4": {
        "languages": ["en"],
        "max_length": 512,
        "description": "Lightweight TinyBERT cross-encoder for STS tasks.",
    },
    "cross-encoder/stsb-roberta-large": {
        "languages": ["en"],
        "max_length": 512,
        "description": "RoBERTa-large cross-encoder for STS tasks. "
        "Highest accuracy at the cost of inference speed.",
    },
    # ── Quora duplicate question detection ────────────────────────────────
    "cross-encoder/quora-distilroberta-base": {
        "languages": ["en"],
        "max_length": 512,
        "description": "Distilled RoBERTa cross-encoder fine-tuned on Quora "
        "duplicate questions.",
    },
    "cross-encoder/quora-roberta-base": {
        "languages": ["en"],
        "max_length": 512,
        "description": "RoBERTa-base cross-encoder fine-tuned on Quora "
        "duplicate questions.",
    },
    # ── Natural Language Inference (NLI) ─────────────────────────────────
    "cross-encoder/nli-distilroberta-base": {
        "languages": ["en"],
        "max_length": 512,
        "score_index": 1,  # label 1 = entailment (relevance signal)
        "description": "Distilled RoBERTa cross-encoder for NLI tasks "
        "(SNLI + MultiNLI).",
    },
    "cross-encoder/nli-roberta-base": {
        "languages": ["en"],
        "max_length": 512,
        "score_index": 1,  # label 1 = entailment (relevance signal)
        "description": "RoBERTa-base cross-encoder for NLI tasks.",
    },
    "cross-encoder/nli-deberta-v3-base": {
        "languages": ["en"],
        "max_length": 512,
        "score_index": 1,  # label 1 = entailment (relevance signal)
        "description": "DeBERTa-v3 cross-encoder for NLI tasks.",
    },
    "cross-encoder/nli-MiniLM2-L6-H768": {
        "languages": ["en"],
        "max_length": 512,
        "score_index": 1,  # label 1 = entailment (relevance signal)
        "description": "MiniLM2 cross-encoder for NLI tasks. Compact and fast.",
    },
    "cross-encoder/nli-deberta-v3-xsmall": {
        "languages": ["en"],
        "max_length": 512,
        "score_index": 1,  # label 1 = entailment (relevance signal)
        "description": "Extra-small DeBERTa-v3 cross-encoder for NLI tasks. "
        "Fastest NLI option.",
    },
}

CROSS_ENCODER_MODEL_NAMES = list(CROSS_ENCODER_MODELS.keys())


# ── Schema ────────────────────────────────────────────────────────────────────


class SentenceTransformerCrossEncoderRetrieverSchema(BaseSchema):
    """Schema for :class:`SentenceTransformerCrossEncoderRetriever`.

    Attributes:
        model_name: Identifier of the pre-trained cross-encoder model.
        top_k: Final number of chunks to return after re-ranking. The
            candidate set size is determined by the child retriever's own
            ``top_k``.
        children: Exactly one child retriever whose candidates are re-ranked.
    """

    model_name: schema_field(
        enum_field(enum=CROSS_ENCODER_MODEL_NAMES),
        placeholder="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description=MultilingualString(
            en="Pre-trained SentenceTransformer cross-encoder model to use.",
            es="Modelo cross-encoder pre-entrenado de SentenceTransformer a usar.",
            pt="Modelo cross-encoder pré-treinado de SentenceTransformer a usar.",
            de="Vorab trainiertes SentenceTransformer-Cross-Encoder-Modell,"
            " das verwendet werden soll.",
            zh="要使用的预训练 SentenceTransformer 交叉编码器模型。",
        ),
    )  # type: ignore

    top_k: schema_field(
        int_field(gt=0),
        placeholder=5,
        description=MultilingualString(
            en="Final number of chunks to return after re-ranking. The "
            "candidate set size is determined by the child retriever's "
            "own top_k.",
            es="Número final de fragmentos a devolver tras el reordenamiento. "
            "El tamaño del conjunto candidato lo define el top_k propio "
            "del recuperador hijo.",
            pt="Número final de fragmentos a devolver após o reordenamento. "
            "O tamanho do conjunto candidato é definido pelo top_k do "
            "próprio recuperador filho.",
            de="Endgültige Anzahl der nach der Neubewertung zurückzugebenden"
            " Chunks. Die Größe des Kandidatensatzes wird durch den eigenen"
            " top_k des Kind-Retrievers bestimmt.",
            zh="重新排序后最终要返回的块数量。候选集大小由子检索器自身的 top_k 决定。",
        ),
    )  # type: ignore

    children: schema_field(
        list_field(component_field(parent="RetrieverModel"), min_items=1, max_items=1),
        placeholder=[],
        description=MultilingualString(
            en="The child retriever whose candidates will be re-ranked.",
            es="El recuperador hijo cuyos candidatos serán reordenados.",
            pt="O recuperador filho cujos candidatos serão reordenados.",
            de="Der Kind-Retriever, dessen Kandidaten neu bewertet werden.",
            zh="其候选将被重新排序的子检索器。",
        ),
    )  # type: ignore


# ── Concrete class ────────────────────────────────────────────────────────────


class SentenceTransformerCrossEncoderRetriever(CrossEncoderRetriever):
    """Cross-encoder re-ranker powered by SentenceTransformer models.

    Retrieves candidates from a single child retriever and re-ranks them
    using a `SentenceTransformer CrossEncoder
    <https://sbert.net/docs/cross_encoder/pretrained_models.html>`_
    model that scores ``(query, chunk)`` pairs jointly.

    The child retriever (the ranker) defines how many candidates are
    fetched via its own ``top_k``; this cross-encoder only selects
    ``top_k`` of them after re-ranking.

    Example usage::

        # Retrieve 15 candidates with BM25 (child's own top_k), keep top 5
        # after cross-encoding
        config = {
            "model_name": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "top_k": 5,
            "children": [
                {
                    "component": "BM25Retriever",
                    "params": {"...": "...", "top_k": 15},
                }
            ],
        }
    """

    SCHEMA = SentenceTransformerCrossEncoderRetrieverSchema

    DISPLAY_NAME: str = MultilingualString(
        en="SentenceTransformer Cross-Encoder",
        es="Cross-Encoder de SentenceTransformer",
        pt="Cross-Encoder de SentenceTransformer",
        de="SentenceTransformer-Cross-Encoder",
        zh="SentenceTransformer 交叉编码器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Cross-encoder re-ranker using SentenceTransformer models. "
        "Re-scores candidates from a child retriever for improved accuracy.",
        es="Reordenador cross-encoder usando modelos de SentenceTransformer. "
        "Reevalúa candidatos de un recuperador hijo para mejorar la precisión.",
        pt="Reordenador cross-encoder usando modelos de SentenceTransformer. "
        "Reavalia candidatos de um recuperador filho para melhorar a precisão.",
        de="Cross-Encoder-Reranker mit SentenceTransformer-Modellen. "
        "Bewertet Kandidaten eines Kind-Retrievers neu, um die Genauigkeit "
        "zu verbessern.",
        zh="使用 SentenceTransformer 模型的交叉编码器重排序器。"
        "对子检索器的候选重新评分以提高准确性。",
    )
    COLOR: str = "#FF5722"
    ICON: str = "Shuffle"

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Return UI metadata including the declarative operation summary."""
        return {
            **super().get_metadata(),
            "operation_summary": {
                "kind": "rerank",
                "fields": [{"param": "model_name", "label": ""}],
            },
        }

    def __init__(self, **kwargs):
        """Initialize the SentenceTransformer cross-encoder retriever.

        Pops ``model_name`` from *kwargs* and stores it for later loading.
        Remaining kwargs are forwarded to :class:`CrossEncoderRetriever`.

        Args:
            **kwargs: Must contain ``model_name``, ``top_k``, and
                ``children`` (exactly one child).
        """
        self.model_name: str = kwargs.pop("model_name")
        super().__init__(**kwargs)
        self.params["model_name"] = self.model_name
        self._ce_model: "CrossEncoder | None" = None

    def load(self, filename: str = "") -> None:
        """Download and load the cross-encoder model from HuggingFace Hub.

        The model is lazily loaded — resource acquisition only occurs when
        this method is called, not during ``__init__``. The *filename*
        argument is accepted for signature compatibility with
        :class:`RetrieverModel` but ignored: the model is always loaded
        from HuggingFace by ``self.model_name``.

        Args:
            filename: Optional filename override. Ignored.
        """
        if self._ce_model is not None:
            return
        if self.model_name not in CROSS_ENCODER_MODELS:
            raise RAGRetrieverError(
                f"Unknown cross-encoder model '{self.model_name}'. "
                "Choose one from CROSS_ENCODER_MODELS."
            )

        from sentence_transformers import CrossEncoder
        from torch import nn

        model_config = CROSS_ENCODER_MODELS.get(self.model_name, {})
        max_length = model_config.get("max_length", 512)
        try:
            self._ce_model = CrossEncoder(
                self.model_name,
                max_length=max_length,
                activation_fn=nn.Identity(),
            )
            log.info("Loaded cross-encoder model: %s", self.model_name)
        except Exception as exc:
            raise RAGRetrieverError(
                f"Failed to load cross-encoder model '{self.model_name}': {exc}"
            ) from exc

    def _cross_score(self, query: str, chunks: List[Chunk]) -> List[float]:
        """Score candidate chunks using the cross-encoder.

        Constructs ``(query, chunk_text)`` pairs for every candidate and
        runs a single ``predict`` call.  The returned scores are raw logits
        where higher values indicate higher relevance.

        Args:
            query: The search query string.
            chunks: Candidate chunks to score.

        Returns:
            A list of relevance scores (higher = more relevant), one per
            chunk, in the same order as *chunks*.

        Raises:
            RAGRetrieverError: If the model has not been loaded.
        """
        if self._ce_model is None:
            raise RAGRetrieverError(
                "Cross-encoder model not loaded. "
                "Call load() before retrieve() or score_chunks()."
            )
        if not chunks:
            return []
        pairs: List[tuple[str, str]] = [(query, chunk.text) for chunk in chunks]
        try:
            scores = self._ce_model.predict(
                pairs,
                show_progress_bar=False,
            )
            scores = np.asarray(scores)
            model_config = CROSS_ENCODER_MODELS.get(self.model_name, {})
            score_index = model_config.get("score_index")
            if scores.ndim == 2:
                if score_index is None:
                    raise RAGRetrieverError(
                        f"Model '{self.model_name}' returned multi-column scores but "
                        "no score_index is configured."
                    )
                scores = scores[:, score_index]
            return scores.tolist()
        except Exception as exc:
            raise RAGRetrieverError(f"Cross-encoder prediction failed: {exc}") from exc

    def inject_infra(
        self,
        env_RAG_path: str,  # noqa: N803
        chunks: Dict[int, Dict[int, Chunk]],
        persistence: Any,
    ) -> None:
        """Inject runtime infrastructure and load the cross-encoder model.

        Stores the runtime infrastructure on this retriever (the child
        retriever is injected separately, before this call) and lazily
        downloads/loads the cross-encoder model.

        Args:
            env_RAG_path: Root directory path for RAG data.
            chunks: Nested dictionary mapping document IDs to chunk IDs to
                :class:`Chunk` instances.
            persistence: Persistence object.
        """
        super().inject_infra(env_RAG_path, chunks, persistence)
        self.load()
