"""Dense embedding model implementations for the RAG module.

Exposes all concrete dense embedding classes (BERT, DistilBERT, E5,
HuggingFace, Instructor, LaBSE, OpenAI, RoBERTa, SentenceTransformer) for
registration in the DashAI component system.
"""

from DashAI.back.models.RAG.embeddings.dense.bert_embedding import BERTEmbedding
from DashAI.back.models.RAG.embeddings.dense.distilbert_embedding import DistilBERTEmbedding
from DashAI.back.models.RAG.embeddings.dense.e5_embedding import E5Embedding
from DashAI.back.models.RAG.embeddings.dense.huggingface_embedding import HuggingFaceEmbedding
from DashAI.back.models.RAG.embeddings.dense.instructor_embedding import InstructorEmbedding
from DashAI.back.models.RAG.embeddings.dense.labse_embedding import LaBSEmbedding
from DashAI.back.models.RAG.embeddings.dense.roberta_embedding import RoBERTaEmbedding
from DashAI.back.models.RAG.embeddings.dense.sentence_transformer_embedding import SentenceTransformerEmbedding

__all__ = [
    "BERTEmbedding",
    "DistilBERTEmbedding",
    "E5Embedding",
    "HuggingFaceEmbedding",
    "InstructorEmbedding",
    "LaBSEmbedding",
    "RoBERTaEmbedding",
    "SentenceTransformerEmbedding",
]
