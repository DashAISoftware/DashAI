import logging

from sqlalchemy.orm import Session

from DashAI.back.dependencies.database.models import (
    RAGChunkingModel,
    RAGChunkSet,
    RAGChunkSetDocument,
    RAGDenseRetriever,
    RAGEmbeddingMatrix,
    RAGEmbeddingModel,
    RAGPipeline,
    RAGRetriever,
    RAGRetrieverChild,
    RAGSparseRetriever,
)
from DashAI.back.models.RAG.RAG_constants import COMPOSITE_RETRIEVER_NAMES
from DashAI.back.services.RAG.deferred_fs import remove_after_commit, remove_now
from DashAI.back.services.RAG.retriever_db_service import RetrieverDBService

log = logging.getLogger(__name__)


class CleanupService:
    """Cascade deletion of RAG resources when a session is deleted or updated.

    Responsible for removing orphaned retriever models, chunking models,
    embedding matrices, and storage folders when a generative session is
    deleted or its parameters are updated. Order of operations is critical:
    retrievers must be cleaned up BEFORE chunking models.
    """

    def __init__(self, db: Session):
        self.db = db
        self._retriever_db = RetrieverDBService(db)

    def cleanup_orphaned_resources(
        self,
        session_id: int,
        old_parameters: dict,
        new_parameters: dict | None = None,
    ) -> None:
        """Main entry point. Called on session DELETE or parameter UPDATE.

        Order MUST be: retriever cleanup BEFORE chunking cleanup.
        (Retriever cleanup queries chunking_model_id from DB — if chunking
        models are deleted first, the query returns None.)

        Args:
            session_id: The generative session being deleted or updated.
            old_parameters: The session's parameters before the change.
            new_parameters: The session's parameters after the change, or
                ``None`` on full session deletion.
        """
        try:
            if not old_parameters:
                return

            def _component_changed(key: str) -> bool:
                if new_parameters is None:
                    return True
                return old_parameters.get(key) != new_parameters.get(key)

            documents_ids = sorted(old_parameters.get("documents") or [])

            # ── Retriever cleanup (MUST run BEFORE chunking) ──
            retriever_model_params = old_parameters.get("retriever_model") or {}
            retriever_component_name = retriever_model_params.get("component", "")

            # The retriever rows deleted below hang off this session's chunk
            # set, which no other session can share now that documents belong
            # to one session. Rows keyed by configuration alone -- the chunking
            # model here, the embedding model in _cleanup_dense_retriever --
            # *are* shared, and are guarded where they are deleted.
            should_cleanup_retriever = bool(retriever_model_params) and (
                _component_changed("retriever_model")
            )

            if should_cleanup_retriever:
                if retriever_component_name in COMPOSITE_RETRIEVER_NAMES:
                    self._cleanup_composite_retriever(old_parameters, session_id)
                else:
                    self._cleanup_unit_retriever(
                        old_parameters,
                        documents_ids,
                        retriever_model_params,
                        session_id,
                    )

            # ── Chunking model cleanup (AFTER retriever) ──
            chunking_model_params = old_parameters.get("chunking_model") or {}

            should_cleanup_chunking = bool(chunking_model_params) and (
                _component_changed("chunking_model")
            )

            if should_cleanup_chunking:
                # Ask this session's own pipeline which row it was using, rather
                # than looking one up by class name and params. Chunking rows
                # are stored with their params key-sorted while a session's
                # parameters keep whatever order the client sent, so a JSON
                # comparison silently misses the very row it means to match.
                self._drop_chunking_model_if_unused(session_id)

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # ── Private helpers ──

    @staticmethod
    def _delete_path(path_value: str | None) -> None:
        """Delete a filesystem path immediately, if it exists.

        Prefer queueing the path with
        :func:`~DashAI.back.services.RAG.deferred_fs.remove_after_commit` when
        it is tied to rows being deleted in a transaction.

        Args:
            path_value: Absolute path to delete. Silently skipped if
                ``None`` or the path does not exist.
        """
        remove_now(path_value)

    def _drop_chunking_model_if_unused(self, session_id: int) -> None:
        """Release the chunking model a session's pipeline points at.

        The row is shared: it is keyed by configuration, so every session that
        settled on the same chunking uses one record -- the common case, since
        a new session takes the backend defaults. It may only go once no other
        pipeline references it.

        Parameters
        ----------
        session_id : int
        """
        pipeline = (
            self.db.query(RAGPipeline).filter_by(session_id=session_id).one_or_none()
        )
        if pipeline is None or pipeline.chunking_model_id is None:
            return

        chunking_model_id = pipeline.chunking_model_id
        # Release this session's claim first, so the count below sees the truth.
        pipeline.chunking_model_id = None
        self.db.flush()

        still_used = (
            self.db.query(RAGPipeline)
            .filter(RAGPipeline.chunking_model_id == chunking_model_id)
            .count()
        )
        if still_used:
            return
        record = self.db.get(RAGChunkingModel, chunking_model_id)
        if record is not None:
            self.db.delete(record)

    def _embedding_model_in_use(
        self, embedding_model_id: int, *, exclude_dense_retriever_id: int | None = None
    ) -> bool:
        """Whether anything still references an embedding model.

        Parameters
        ----------
        embedding_model_id : int
        exclude_dense_retriever_id : int | None
            A dense retriever being deleted in the same transaction, which
            should not count as a live reference.

        Returns
        -------
        bool
        """
        retrievers = self.db.query(RAGDenseRetriever).filter(
            RAGDenseRetriever.embedding_model_id == embedding_model_id
        )
        if exclude_dense_retriever_id is not None:
            retrievers = retrievers.filter(
                RAGDenseRetriever.id != exclude_dense_retriever_id
            )
        if retrievers.count():
            return True
        return bool(
            self.db.query(RAGEmbeddingMatrix)
            .filter(RAGEmbeddingMatrix.embedding_model_id == embedding_model_id)
            .count()
        )

    def _find_pipeline_id(self, session_id: int) -> int | None:
        """Find pipeline DB record ID for a session.

        Args:
            session_id: Generative session identifier.

        Returns:
            The pipeline record id, or ``None`` if no pipeline exists.
        """
        pipeline = self.db.query(RAGPipeline).filter_by(session_id=session_id).first()
        return pipeline.id if pipeline else None

    def _cleanup_composite_retriever(
        self,
        old_parameters: dict,
        session_id: int,
    ) -> None:
        """Cascade-delete a composite retriever and its children.

        Finds the composite bridge record, recursively deletes child
        retrievers (sparse detail storage folders, dense detail records),
        then removes the parent bridge record.

        Args:
            old_parameters: Session parameters containing the retriever
                component name.
            session_id: Generative session identifier.
        """
        pipeline_id = self._find_pipeline_id(session_id)
        if pipeline_id is None:
            return

        retriever_component_name = old_parameters.get("retriever_model", {}).get(
            "component"
        )

        composite_bridges = (
            self.db.query(RAGRetriever)
            .filter(
                RAGRetriever.pipeline_id == pipeline_id,
                RAGRetriever.class_name == retriever_component_name,
            )
            .all()
        )

        for bridge in composite_bridges:
            child_links = (
                self.db.query(RAGRetrieverChild)
                .filter_by(parent_id=bridge.id)
                .order_by(RAGRetrieverChild.child_order)
                .all()
            )
            for link in child_links:
                child_bridge = self.db.query(RAGRetriever).get(link.child_id)
                if child_bridge is None:
                    continue
                if child_bridge.sparse_detail:
                    self._delete_path(child_bridge.sparse_detail.storage_folder)
                    self.db.delete(child_bridge.sparse_detail)
                elif child_bridge.dense_detail:
                    self.db.delete(child_bridge.dense_detail)
            self.db.delete(bridge)

    def _cleanup_unit_retriever(
        self,
        old_parameters: dict,
        documents_ids: list,
        retriever_model_params: dict,
        session_id: int,
    ) -> None:
        """Cascade-delete a unit retriever (dense or sparse).

        Determines retriever type by inspecting the bridge relationship
        (``dense_detail`` vs ``sparse_detail``) rather than parameter heuristics.

        Args:
            old_parameters: Session parameters dict.
            documents_ids: Document ids associated with the session.
            retriever_model_params: The ``retriever_model`` parameter dict.
            session_id: Generative session identifier.
        """
        pipeline_id = self._find_pipeline_id(session_id)
        if pipeline_id is None:
            return

        bridge = (
            self.db.query(RAGRetriever)
            .filter(
                RAGRetriever.pipeline_id == pipeline_id,
                RAGRetriever.class_name == retriever_model_params.get("component"),
            )
            .first()
        )
        if bridge is None:
            return

        if bridge.dense_detail is not None:
            self._cleanup_dense_retriever(bridge, documents_ids)
        elif bridge.sparse_detail is not None:
            self._cleanup_sparse_retriever(bridge)
        self.db.delete(bridge)

    def _cleanup_dense_retriever(
        self,
        bridge: RAGRetriever,
        documents_ids: list,
    ) -> None:
        """Cascade-delete a dense retriever and its embedding resources.

        Removes embedding matrix storage folders, deletes matrix DB records,
        the embedding model record, and the dense detail record.

        Args:
            bridge: The bridge record for the dense retriever.
            documents_ids: Document ids whose embeddings to delete.
        """
        dense_retriever = bridge.dense_detail
        chunk_set_id = dense_retriever.chunk_set_id
        embedding_model_id = dense_retriever.embedding_model_id

        embedding_matrices = (
            self.db.query(RAGEmbeddingMatrix)
            .filter(
                RAGEmbeddingMatrix.chunk_set_id == chunk_set_id,
                RAGEmbeddingMatrix.embedding_model_id == embedding_model_id,
                RAGEmbeddingMatrix.document_id.in_(documents_ids),
            )
            .all()
        )

        matrix_ids = []
        for matrix in embedding_matrices:
            self._delete_path(matrix.storage_folder)
            matrix_ids.append(matrix.id)

        if matrix_ids:
            self.db.query(RAGEmbeddingMatrix).filter(
                RAGEmbeddingMatrix.id.in_(matrix_ids)
            ).delete(synchronize_session="fetch")

        # Embedding models are also keyed by configuration alone, so another
        # session's dense retriever or embedding matrix may still need this row.
        embedding_model = self.db.get(RAGEmbeddingModel, embedding_model_id)
        if embedding_model is not None and not self._embedding_model_in_use(
            embedding_model_id, exclude_dense_retriever_id=dense_retriever.id
        ):
            self.db.delete(embedding_model)

        self.db.delete(dense_retriever)

    def _cleanup_sparse_retriever(
        self,
        bridge: RAGRetriever,
    ) -> None:
        """Cascade-delete a sparse retriever and its storage folder.

        Removes the on-disk storage folder and the sparse detail DB record.

        Args:
            bridge: The bridge record for the sparse retriever.
        """
        sparse_retriever = bridge.sparse_detail
        self._delete_path(sparse_retriever.storage_folder)
        self.db.delete(sparse_retriever)

    def invalidate_document_artifacts(
        self,
        document_id: int,
        *,
        commit: bool = True,
    ) -> None:
        """Delete every chunk set that contains a legacy document.

        Kept only for the legacy document service, removed with it.

        Parameters
        ----------
        document_id : int
            Document whose chunk sets are deleted.
        commit : bool
            When ``False`` the caller owns the transaction and commits it.
        """
        chunk_set_ids = {
            row[0]
            for row in self.db.query(RAGChunkSetDocument.chunk_set_id)
            .filter(RAGChunkSetDocument.document_id == document_id)
            .all()
        }
        for chunk_set_id in chunk_set_ids:
            self._invalidate_chunk_set(chunk_set_id)
        if commit:
            self.db.commit()

    def invalidate_session_artifacts(
        self, session_id: int, *, commit: bool = True
    ) -> None:
        """Delete every chunk set a session owns, with what was fitted on it.

        Chunk sets carry their owning ``session_id``, so this never reaches the
        index of another session, even one using the same Data documents.

        Parameters
        ----------
        session_id : int
            The generative session whose indexes are discarded.
        commit : bool
            When ``False`` the caller owns the transaction and commits it.
        """
        chunk_set_ids = [
            row[0]
            for row in self.db.query(RAGChunkSet.id)
            .filter(RAGChunkSet.session_id == session_id)
            .all()
        ]
        for chunk_set_id in chunk_set_ids:
            self._invalidate_chunk_set(chunk_set_id)
        if commit:
            self.db.commit()

    def invalidate_legacy_artifacts(self, *, commit: bool = True) -> int:
        """Delete the chunk sets built before chunk sets had an owner.

        They indexed rows of the legacy ``document`` table, which no longer
        exist, so nothing can use them again.

        Parameters
        ----------
        commit : bool
            When ``False`` the caller owns the transaction and commits it.

        Returns
        -------
        int
            Number of chunk sets deleted.
        """
        chunk_set_ids = [
            row[0]
            for row in self.db.query(RAGChunkSet.id)
            .filter(RAGChunkSet.session_id.is_(None))
            .all()
        ]
        for chunk_set_id in chunk_set_ids:
            self._invalidate_chunk_set(chunk_set_id)
        if commit:
            self.db.commit()
        return len(chunk_set_ids)

    def _invalidate_chunk_set(self, chunk_set_id: int) -> None:
        """Delete one chunk set and everything fitted on it.

        Removes the composite retrievers built over its retrievers, its sparse
        and dense retrievers, its embedding matrices (and their embedding model
        once nothing else uses it) and the chunk set itself, whose chunks and
        membership rows go with it. Storage folders are queued with
        ``remove_after_commit``.

        Parameters
        ----------
        chunk_set_id : int
            The chunk set to delete.
        """
        document_ids = [
            row[0]
            for row in self.db.query(RAGChunkSetDocument.document_id)
            .filter(RAGChunkSetDocument.chunk_set_id == chunk_set_id)
            .all()
        ]
        sparse_links = (
            self.db.query(RAGSparseRetriever, RAGRetriever)
            .join(RAGRetriever, RAGSparseRetriever.bridge_id == RAGRetriever.id)
            .filter(RAGSparseRetriever.chunk_set_id == chunk_set_id)
            .all()
        )
        dense_links = (
            self.db.query(RAGDenseRetriever, RAGRetriever)
            .join(RAGRetriever, RAGDenseRetriever.bridge_id == RAGRetriever.id)
            .filter(RAGDenseRetriever.chunk_set_id == chunk_set_id)
            .all()
        )

        child_bridge_ids = {bridge.id for _, bridge in sparse_links + dense_links}
        if child_bridge_ids:
            parent_ids = {
                link.parent_id
                for link in self.db.query(RAGRetrieverChild)
                .filter(RAGRetrieverChild.child_id.in_(child_bridge_ids))
                .all()
            }
            for parent_id in parent_ids:
                parent = self.db.get(RAGRetriever, parent_id)
                if parent is not None:
                    self.db.delete(parent)

        for sparse_detail, bridge in sparse_links:
            remove_after_commit(self.db, sparse_detail.storage_folder)
            self.db.delete(sparse_detail)
            self.db.delete(bridge)

        for dense_detail, bridge in dense_links:
            embedding_model_id = dense_detail.embedding_model_id
            matrices = (
                self.db.query(RAGEmbeddingMatrix)
                .filter(
                    RAGEmbeddingMatrix.chunk_set_id == chunk_set_id,
                    RAGEmbeddingMatrix.embedding_model_id == embedding_model_id,
                    RAGEmbeddingMatrix.document_id.in_(document_ids),
                )
                .all()
            )
            for matrix in matrices:
                remove_after_commit(self.db, matrix.storage_folder)
                self.db.delete(matrix)
            if not self._embedding_model_in_use(
                embedding_model_id, exclude_dense_retriever_id=dense_detail.id
            ):
                embedding_model = self.db.get(RAGEmbeddingModel, embedding_model_id)
                if embedding_model is not None:
                    self.db.delete(embedding_model)
            self.db.delete(dense_detail)
            self.db.delete(bridge)

        chunk_set = self.db.get(RAGChunkSet, chunk_set_id)
        if chunk_set is not None:
            self.db.delete(chunk_set)
