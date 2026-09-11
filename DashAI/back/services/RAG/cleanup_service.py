import logging

from sqlalchemy.orm import Session

from DashAI.back.dependencies.database.models import (
    RAGChunkingModel,
    RAGDenseRetriever,
    RAGEmbeddingMatrix,
    RAGEmbeddingModel,
    RAGPipeline,
    RAGRetriever,
    RAGRetrieverChild,
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
        """Delete all RAG artifacts associated with a document.

        When a document's extractor changes, all chunk sets, retrievers,
        embedding matrices, and on-disk artifacts that depend on it are
        deleted. The next pipeline run will recompute them automatically.

        Also closes the orphaned-artifacts gap on document deletion.

        The whole chunk set is deleted, including the chunks of sibling
        documents in the same set. Documents belong to exactly one session, so
        a chunk set does too: re-chunking the set is precisely what has to
        happen when one of its documents changes.

        Args:
            document_id: Document ID whose artifacts should be removed.
            commit: When ``False`` the caller owns the transaction and is
                responsible for committing (or rolling back). Use it to make
                the invalidation part of a larger unit of work.

        The artifact directories are queued with
        :func:`~DashAI.back.services.RAG.deferred_fs.remove_after_commit`, so
        they are removed when the transaction commits and left alone if it does
        not -- whoever owns that transaction.
        """
        from DashAI.back.dependencies.database.models import (
            RAGChunkSet,
            RAGChunkSetDocument,
            RAGDenseRetriever,
            RAGEmbeddingMatrix,
            RAGEmbeddingModel,
            RAGRetriever,
            RAGRetrieverChild,
            RAGSparseRetriever,
        )

        chunk_set_links = (
            self.db.query(RAGChunkSetDocument).filter_by(document_id=document_id).all()
        )
        chunk_set_ids = list({link.chunk_set_id for link in chunk_set_links})

        if not chunk_set_ids:
            return

        for chunk_set_id in chunk_set_ids:
            docs_in_chunk_set = (
                self.db.query(RAGChunkSetDocument)
                .filter_by(chunk_set_id=chunk_set_id)
                .all()
            )
            doc_ids_in_set = [d.document_id for d in docs_in_chunk_set]

            # 2. Sparse retrievers
            sparse_detail_links = (
                self.db.query(RAGSparseRetriever, RAGRetriever)
                .join(RAGRetriever, RAGSparseRetriever.bridge_id == RAGRetriever.id)
                .filter(RAGSparseRetriever.chunk_set_id == chunk_set_id)
                .all()
            )
            for sparse_detail, bridge in sparse_detail_links:
                remove_after_commit(self.db, sparse_detail.storage_folder)
                self.db.delete(bridge)
                self.db.delete(sparse_detail)

            # 3. Dense retrievers
            dense_detail_links = (
                self.db.query(RAGDenseRetriever, RAGRetriever)
                .join(RAGRetriever, RAGDenseRetriever.bridge_id == RAGRetriever.id)
                .filter(RAGDenseRetriever.chunk_set_id == chunk_set_id)
                .all()
            )
            for dense_detail, bridge in dense_detail_links:
                embedding_model_id = dense_detail.embedding_model_id

                for doc_id in doc_ids_in_set:
                    matrices = (
                        self.db.query(RAGEmbeddingMatrix)
                        .filter(
                            RAGEmbeddingMatrix.chunk_set_id == chunk_set_id,
                            RAGEmbeddingMatrix.embedding_model_id == embedding_model_id,
                            RAGEmbeddingMatrix.document_id == doc_id,
                        )
                        .all()
                    )
                    for matrix in matrices:
                        remove_after_commit(self.db, matrix.storage_folder)
                        self.db.delete(matrix)

                remaining = (
                    self.db.query(RAGDenseRetriever)
                    .filter(
                        RAGDenseRetriever.embedding_model_id == embedding_model_id,
                        RAGDenseRetriever.id != dense_detail.id,
                    )
                    .first()
                )
                if remaining is None:
                    emb_model = self.db.query(RAGEmbeddingModel).get(embedding_model_id)
                    if emb_model is not None:
                        self.db.delete(emb_model)

                self.db.delete(bridge)
                self.db.delete(dense_detail)

            # 4. Composite retrievers — find parents whose children
            # reference this chunk set via sparse/dense detail
            sparse_child_ids = (
                self.db.query(RAGSparseRetriever.bridge_id)
                .filter(RAGSparseRetriever.chunk_set_id == chunk_set_id)
                .all()
            )
            dense_child_ids = (
                self.db.query(RAGDenseRetriever.bridge_id)
                .filter(RAGDenseRetriever.chunk_set_id == chunk_set_id)
                .all()
            )
            child_bridge_ids = {row[0] for row in sparse_child_ids + dense_child_ids}
            if child_bridge_ids:
                orphaned_children = (
                    self.db.query(RAGRetrieverChild)
                    .filter(RAGRetrieverChild.child_id.in_(child_bridge_ids))
                    .all()
                )
                for child_link in orphaned_children:
                    parent_bridge = self.db.query(RAGRetriever).get(
                        child_link.parent_id
                    )
                    if parent_bridge is not None:
                        self.db.delete(parent_bridge)

            # 5. Delete chunk set
            chunk_set = self.db.query(RAGChunkSet).get(chunk_set_id)
            if chunk_set is not None:
                self.db.delete(chunk_set)

        if commit:
            self.db.commit()
