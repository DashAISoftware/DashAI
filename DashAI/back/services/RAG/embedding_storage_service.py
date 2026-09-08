"""Service for managing embedding matrix persistence on disk and in DB."""

import logging
import os
import shutil
from typing import List

import numpy as np

from DashAI.back.dependencies.database.models import RAGEmbeddingMatrix
from DashAI.back.models.RAG.exceptions import RAGEmbeddingLoadError
from DashAI.back.services.RAG.retriever_db_service import RetrieverDBService

logger = logging.getLogger(__name__)

EMBEDDINGS_DIRNAME = "embeddings"
EMBEDDINGS_FILENAME = "embeddings.npy"


class EmbeddingStorageService:
    """Manages embedding matrix persistence: numpy .npy files on disk + DB records.

    Embedding matrices are stored as .npy files in directories like:
    ``{env_RAG_path}/embeddings/doc_id-{doc_id}__chunk_set_id-{chunk_set_id}__
    embedding_model_id-{embedding_model_id}/embeddings.npy``
    """

    def __init__(self, env_RAG_path: str, db_service: RetrieverDBService):  # noqa: N803
        """Initialise with the base RAG directory path and DB service.

        Parameters
        ----------
        env_RAG_path : str
            Base RAG directory path from config.
        db_service : RetrieverDBService
            Service for database operations on retriever models.
        """
        self._env_RAG_path = env_RAG_path
        self._db_service = db_service

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    @staticmethod
    def build_matrix_dir_name(
        doc_id: int, chunk_set_id: int, embedding_model_id: int
    ) -> str:
        return (
            f"doc_id-{doc_id}__chunk_set_id-{chunk_set_id}__"
            f"embedding_model_id-{embedding_model_id}"
        )

    def _matrix_dir(
        self, doc_id: int, chunk_set_id: int, embedding_model_id: int
    ) -> str:
        """Build the directory path for a specific embedding matrix.

        Format: ``{env_RAG_path}/embeddings/doc_id-{doc_id}__
        chunk_set_id-{chunk_set_id}__embedding_model_id-{embedding_model_id}``
        """
        return os.path.join(
            self._env_RAG_path,
            EMBEDDINGS_DIRNAME,
            self.build_matrix_dir_name(doc_id, chunk_set_id, embedding_model_id),
        )

    def _matrix_path(
        self, doc_id: int, chunk_set_id: int, embedding_model_id: int
    ) -> str:
        """Full path to the ``embeddings.npy`` file.

        Delegates to :meth:`_matrix_dir` and appends the filename.
        """
        return os.path.join(
            self._matrix_dir(doc_id, chunk_set_id, embedding_model_id),
            EMBEDDINGS_FILENAME,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_embeddings(
        self,
        doc_id: int,
        chunk_set_id: int,
        embedding_model_id: int,
        embeddings: np.ndarray,
    ) -> RAGEmbeddingMatrix:
        """Save embeddings to disk and create / return a DB record.

        Steps
        -----
        1. Create the directory via :meth:`_matrix_dir`.
        2. Write the array to ``embeddings.npy`` with :func:`numpy.save`.
        3. Persist a matching ``RAGEmbeddingMatrix`` record through
           :meth:`RetrieverDBService.save_embedding_matrix`.

        Parameters
        ----------
        doc_id : int
            Owning document id.
        chunk_set_id : int
            Chunk set identifier.
        embedding_model_id : int
            Embedding model identifier.
        embeddings : np.ndarray
            2-D embedding matrix (num_chunks x embedding_dimension).

        Returns
        -------
        RAGEmbeddingMatrix
            The newly persisted database record.
        """
        matrix_dir = self._matrix_dir(doc_id, chunk_set_id, embedding_model_id)
        os.makedirs(matrix_dir, exist_ok=True)

        matrix_path = self._matrix_path(doc_id, chunk_set_id, embedding_model_id)
        np.save(matrix_path, embeddings)

        record = self._db_service.save_embedding_matrix(
            document_id=doc_id,
            chunk_set_id=chunk_set_id,
            embedding_model_id=embedding_model_id,
            storage_folder=matrix_dir,
            matrix_shape=list(embeddings.shape),
        )
        return record

    def load_embeddings(
        self, doc_id: int, chunk_set_id: int, embedding_model_id: int
    ) -> np.ndarray | None:
        """Load an embedding matrix from disk as a numpy array.

        Returns ``None`` when the file does not exist (not an error).

        Parameters
        ----------
        doc_id : int
            Owning document id.
        chunk_set_id : int
            Chunk set identifier.
        embedding_model_id : int
            Embedding model identifier.

        Returns
        -------
        np.ndarray or None
            The loaded embedding matrix, or ``None`` if not found.
        """
        matrix_path = self._matrix_path(doc_id, chunk_set_id, embedding_model_id)
        if not os.path.isfile(matrix_path):
            return None
        try:
            return np.load(matrix_path)
        except (IOError, OSError, ValueError) as exc:
            logger.warning("Failed to load embeddings from %s: %s", matrix_path, exc)
            raise RAGEmbeddingLoadError(
                f"Failed to load embeddings from {matrix_path}: {exc}"
            ) from exc

    def exists(self, doc_id: int, chunk_set_id: int, embedding_model_id: int) -> bool:
        """Check whether an ``embeddings.npy`` file exists on disk.

        Parameters
        ----------
        doc_id : int
            Owning document id.
        chunk_set_id : int
            Chunk set identifier.
        embedding_model_id : int
            Embedding model identifier.

        Returns
        -------
        bool
            ``True`` if the file exists, ``False`` otherwise.
        """
        return os.path.isfile(
            self._matrix_path(doc_id, chunk_set_id, embedding_model_id)
        )

    def delete_all_for_document(
        self, doc_id: int, matrices: List[RAGEmbeddingMatrix]
    ) -> None:
        """Delete embedding directories and DB records for a document.

        For each provided matrix record, the corresponding on-disk directory
        is removed recursively.  DB records are bulk-deleted via
        :meth:`RetrieverDBService.delete_embedding_matrices_by_ids`.

        Parameters
        ----------
        doc_id : int
            Document whose embeddings are being deleted.
        matrices : list[RAGEmbeddingMatrix]
            Embedding matrix records to delete.
        """
        matrix_ids = []
        for m in matrices:
            if m.document_id == doc_id:
                matrix_ids.append(m.id)
                self.delete_storage(m.storage_folder)
        if matrix_ids:
            self._db_service.delete_embedding_matrices_by_ids(matrix_ids)

    @staticmethod
    def delete_storage(storage_folder: str) -> None:
        """Recursively delete a storage directory if it exists.

        Uses :func:`shutil.rmtree` and silently ignores missing folders.

        Parameters
        ----------
        storage_folder : str
            Absolute path to the directory to remove.
        """
        if os.path.isdir(storage_folder):
            try:
                shutil.rmtree(storage_folder)
            except OSError as exc:
                logger.warning(
                    "Failed to remove storage folder %s: %s",
                    storage_folder,
                    exc,
                )
