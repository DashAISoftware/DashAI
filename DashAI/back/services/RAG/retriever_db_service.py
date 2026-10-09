"""Service layer for retriever-related database operations.

Encapsulates all SQLAlchemy persistence logic for retriever models,
bridge records, embedding models, and embedding matrices. This service
is consumed by retriever factories and orchestration code; retriever
instances themselves never touch the database.
"""

from typing import Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from DashAI.back.dependencies.database.models import (
    RAGDenseRetriever as DenseRetrieverDBModel,
)
from DashAI.back.dependencies.database.models import (
    RAGEmbeddingMatrix as EmbeddingMatrixDBModel,
)
from DashAI.back.dependencies.database.models import (
    RAGEmbeddingModel as EmbeddingDBModel,
)
from DashAI.back.dependencies.database.models import (
    RAGRetriever as RetrieverDBModel,
)
from DashAI.back.dependencies.database.models import (
    RAGRetrieverChild,
)
from DashAI.back.dependencies.database.models import (
    RAGSparseRetriever as SparseRetrieverDBModel,
)


class RetrieverDBService:
    """All database operations for retriever models.

    This class owns every SQL query, INSERT, and DB-model construction
    related to retrievers. Factories and higher-level orchestration code
    use it as a collaborator; retriever instances never touch it.

    Every public method is expected to handle SQLAlchemy exceptions so
    that callers can react to persistence failures uniformly.
    """

    def __init__(self, db: Session):
        self.db = db

    # ── Bridge / identity helpers ──────────────────────────────────────

    def create_bridge(
        self, class_name: str, pipeline_id: int, commit: bool = True
    ) -> RetrieverDBModel:
        """Insert a new canonical identity record in RAG_retriever.

        Every retriever (unit or composite) gets one bridge record.

        Args:
            class_name: Retriever component class name.
            pipeline_id: FK to the owning pipeline.
            commit: When ``True``, commit and refresh; otherwise only flush.

        Returns:
            The persisted bridge record with its auto-generated id.
        """
        bridge_record = RetrieverDBModel(
            class_name=class_name,
            pipeline_id=pipeline_id,
        )
        try:
            self.db.add(bridge_record)
            if commit:
                self.db.commit()
                self.db.refresh(bridge_record)
            else:
                self.db.flush()
        except SQLAlchemyError:
            self.db.rollback()
            raise
        return bridge_record

    def find_bridge_for_sub_table(
        self,
        sub_db_model: SparseRetrieverDBModel | DenseRetrieverDBModel,
        class_name: str,
    ) -> Optional[RetrieverDBModel]:
        """Given a sub-table detail record, find its parent bridge record.

        Args:
            sub_db_model: A dense or sparse sub-table record.
            class_name: Expected class name for validation.

        Returns:
            The matching bridge record, or ``None`` if not found or mismatch.
        """
        try:
            bridge = self.db.query(RetrieverDBModel).get(sub_db_model.bridge_id)
        except SQLAlchemyError:
            raise
        if bridge is not None and bridge.class_name == class_name:
            return bridge
        return None

    # ── Sparse retriever ───────────────────────────────────────────────

    def find_sparse(
        self,
        class_name: str,
        parameters: Dict[str, object],
        chunk_set_id: int,
    ) -> Optional[SparseRetrieverDBModel]:
        """Look up an existing sparse retriever record by its natural key.

        Parameters
        ----------
        class_name : str
            Concrete retriever class name (e.g. "TFIDFRetriever").
        parameters : dict
            Schema parameters, sorted for deterministic JSON serialisation.
        chunk_set_id : int
            Which chunk set this retriever was trained on.

        Returns
        -------
        SparseRetrieverDBModel or None
        """
        parameters = dict(sorted(parameters.items()))
        try:
            return (
                self.db.query(SparseRetrieverDBModel)
                .filter_by(
                    class_name=class_name,
                    parameters=parameters,
                    chunk_set_id=chunk_set_id,
                )
                .first()
            )
        except SQLAlchemyError:
            raise

    def save_sparse(
        self,
        class_name: str,
        parameters: Dict[str, object],
        storage_folder: str,
        bridge_id: int,
        chunk_set_id: int,
        commit: bool = True,
    ) -> SparseRetrieverDBModel:
        """Persist a new sparse retriever record and link it to its bridge.

        Args:
            class_name: Retriever component class name.
            parameters: Schema parameters.
            storage_folder: On-disk folder for the sparse model.
            bridge_id: FK to the bridge record.
            chunk_set_id: FK to the chunk set.
            commit: When ``True``, commit and refresh; otherwise only flush.

        Returns:
            The persisted sparse retriever record.
        """
        parameters = dict(sorted(parameters.items()))
        record = SparseRetrieverDBModel(
            bridge_id=bridge_id,
            chunk_set_id=chunk_set_id,
            class_name=class_name,
            parameters=parameters,
            storage_folder=storage_folder,
        )
        try:
            self.db.add(record)
            if commit:
                self.db.commit()
                self.db.refresh(record)
            else:
                self.db.flush()
        except SQLAlchemyError:
            self.db.rollback()
            raise
        return record

    def find_sparse_by_bridge_id(
        self, bridge_id: int
    ) -> Optional[SparseRetrieverDBModel]:
        """Look up a sparse retriever sub-table record by its bridge_id.

        Args:
            bridge_id: FK to the bridge record.

        Returns:
            The sparse detail record, or ``None`` if not found.
        """
        try:
            return (
                self.db.query(SparseRetrieverDBModel)
                .filter_by(bridge_id=bridge_id)
                .first()
            )
        except SQLAlchemyError:
            raise

    # ── Dense retriever ────────────────────────────────────────────────

    def find_dense(
        self,
        class_name: str,
        parameters: Dict[str, object],
        chunk_set_id: int,
    ) -> Optional[DenseRetrieverDBModel]:
        """Look up an existing dense retriever record by its natural key.

        Args:
            class_name: Retriever component class name.
            parameters: Schema parameters.
            chunk_set_id: FK to the chunk set.

        Returns:
            The dense detail record, or ``None`` if not found.
        """
        parameters = dict(sorted(parameters.items()))
        try:
            return (
                self.db.query(DenseRetrieverDBModel)
                .filter_by(
                    class_name=class_name,
                    parameters=parameters,
                    chunk_set_id=chunk_set_id,
                )
                .first()
            )
        except SQLAlchemyError:
            raise

    def save_dense(
        self,
        class_name: str,
        parameters: Dict[str, object],
        bridge_id: int,
        chunk_set_id: int,
        embedding_model_id: int,
        commit: bool = True,
    ) -> DenseRetrieverDBModel:
        """Persist a new dense retriever record and link it to its bridge.

        Args:
            class_name: Retriever component class name.
            parameters: Schema parameters.
            bridge_id: FK to the bridge record.
            chunk_set_id: FK to the chunk set.
            embedding_model_id: FK to the embedding model.
            commit: When ``True``, commit and refresh; otherwise only flush.

        Returns:
            The persisted dense retriever record.
        """
        parameters = dict(sorted(parameters.items()))
        record = DenseRetrieverDBModel(
            bridge_id=bridge_id,
            chunk_set_id=chunk_set_id,
            class_name=class_name,
            parameters=parameters,
            embedding_model_id=embedding_model_id,
        )
        try:
            self.db.add(record)
            if commit:
                self.db.commit()
                self.db.refresh(record)
            else:
                self.db.flush()
        except SQLAlchemyError:
            self.db.rollback()
            raise
        return record

    def find_dense_by_bridge_id(
        self, bridge_id: int
    ) -> Optional[DenseRetrieverDBModel]:
        """Look up a dense retriever sub-table record by its bridge_id.

        Args:
            bridge_id: FK to the bridge record.

        Returns:
            The dense detail record, or ``None`` if not found.
        """
        try:
            return (
                self.db.query(DenseRetrieverDBModel)
                .filter_by(bridge_id=bridge_id)
                .first()
            )
        except SQLAlchemyError:
            raise

    # ── Composite retriever ────────────────────────────────────────────

    def save_composite(
        self,
        class_name: str,
        pipeline_id: int,
        child_bridge_ids: List[int],
        commit: bool = True,
    ) -> RetrieverDBModel:
        """Persist a composite bridge record and its child links.

        Parameters
        ----------
        class_name : str
            "SequentialRetriever" or "ParallelRetriever".
        pipeline_id : int
            Owning pipeline.
        child_bridge_ids : list[int]
            Ordered list of child bridge ids (RAG_retriever.id).
        commit : bool
            When ``True``, commit and refresh; otherwise skip final commit.

        Returns
        -------
        RetrieverDBModel
            The persisted bridge record.
        """
        bridge_record = RetrieverDBModel(
            class_name=class_name,
            pipeline_id=pipeline_id,
        )
        try:
            self.db.add(bridge_record)
            self.db.flush()
            for order, child_id in enumerate(child_bridge_ids):
                self.db.add(
                    RAGRetrieverChild(
                        parent_id=bridge_record.id,
                        child_id=child_id,
                        child_order=order,
                    )
                )
            if commit:
                self.db.commit()
                self.db.refresh(bridge_record)
        except SQLAlchemyError:
            self.db.rollback()
            raise
        return bridge_record

    # ── Embedding model / matrix ───────────────────────────────────────

    def find_or_create_embedding_model(
        self,
        class_name: str,
        parameters: Dict[str, object],
        commit: bool = True,
    ) -> EmbeddingDBModel:
        """Return an existing EmbeddingDBModel record or create one.

        This is idempotent: the same (class_name, parameters) pair
        always resolves to the same record.

        Args:
            class_name: Embedding model component class name.
            parameters: Embedding model parameters.

        Returns:
            The existing or newly created embedding model record.
        """
        parameters = dict(sorted(parameters.items()))
        try:
            existing = (
                self.db.query(EmbeddingDBModel)
                .filter_by(
                    class_name=class_name,
                    parameters=parameters,
                )
                .first()
            )
        except SQLAlchemyError:
            raise
        if existing is not None:
            return existing
        record = EmbeddingDBModel(
            class_name=class_name,
            parameters=parameters,
        )
        try:
            self.db.add(record)
            if commit:
                self.db.commit()
                self.db.refresh(record)
            else:
                self.db.flush()
        except SQLAlchemyError:
            self.db.rollback()
            raise
        return record

    # NOTE: All embedding matrices are loaded into memory via np.load()
    # for simplicity -- not suitable for very large document collections.
    def find_embedding_matrices(
        self,
        doc_ids: List[int],
        chunk_set_id: int,
        embedding_model_id: int,
    ) -> Dict[int, EmbeddingMatrixDBModel]:
        """Return existing embedding matrices keyed by document_id.

        Only matrices that actually exist in the database are returned.

        Args:
            doc_ids: List of document ids to look up.
            chunk_set_id: FK to the chunk set.
            embedding_model_id: FK to the embedding model.

        Returns:
            Dict mapping document_id to existing matrix records.
        """
        result: Dict[int, EmbeddingMatrixDBModel] = {}
        for doc_id in doc_ids:
            try:
                matrix = (
                    self.db.query(EmbeddingMatrixDBModel)
                    .filter_by(
                        document_id=doc_id,
                        chunk_set_id=chunk_set_id,
                        embedding_model_id=embedding_model_id,
                    )
                    .first()
                )
            except SQLAlchemyError:
                raise
            if matrix is not None:
                result[doc_id] = matrix
        return result

    def find_embedding_matrix(
        self,
        document_id: int,
        chunk_set_id: int,
        embedding_model_id: int,
    ) -> Optional[EmbeddingMatrixDBModel]:
        """Look up a single embedding matrix record.

        Args:
            document_id: FK to the document.
            chunk_set_id: FK to the chunk set.
            embedding_model_id: FK to the embedding model.

        Returns:
            The matrix record, or ``None`` if not found.
        """
        try:
            return (
                self.db.query(EmbeddingMatrixDBModel)
                .filter_by(
                    document_id=document_id,
                    chunk_set_id=chunk_set_id,
                    embedding_model_id=embedding_model_id,
                )
                .first()
            )
        except SQLAlchemyError:
            raise

    def save_embedding_matrix(
        self,
        document_id: int,
        chunk_set_id: int,
        embedding_model_id: int,
        storage_folder: str,
        matrix_shape: List[int],
        commit: bool = True,
    ) -> EmbeddingMatrixDBModel:
        """Persist a new embedding matrix record.

        Args:
            document_id: FK to the document.
            chunk_set_id: FK to the chunk set.
            embedding_model_id: FK to the embedding model.
            storage_folder: On-disk path to the matrix directory.
            matrix_shape: Shape of the numpy array as ``[rows, cols]``.
            commit: When ``True``, commit and refresh; otherwise only flush.

        Returns:
            The persisted embedding matrix record.
        """
        record = EmbeddingMatrixDBModel(
            document_id=document_id,
            chunk_set_id=chunk_set_id,
            embedding_model_id=embedding_model_id,
            storage_folder=storage_folder,
            matrix_shape=matrix_shape,
        )
        try:
            self.db.add(record)
            if commit:
                self.db.commit()
                self.db.refresh(record)
            else:
                self.db.flush()
        except SQLAlchemyError:
            self.db.rollback()
            raise
        return record

    # ── Deletion helpers ───────────────────────────────────────────────

    def delete_embedding_matrices_by_ids(self, matrix_ids: List[int]) -> None:
        """Bulk-delete embedding matrices by their primary keys.

        Args:
            matrix_ids: List of primary keys to delete.
        """
        try:
            self.db.query(EmbeddingMatrixDBModel).filter(
                EmbeddingMatrixDBModel.id.in_(matrix_ids)
            ).delete(synchronize_session="fetch")
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise

    def delete_embedding_model(self, embedding_model_id: int) -> None:
        """Delete a single embedding model record by its primary key.

        Args:
            embedding_model_id: Primary key of the embedding model to delete.
        """
        try:
            model = (
                self.db.query(EmbeddingDBModel).filter_by(id=embedding_model_id).first()
            )
            if model is not None:
                self.db.delete(model)
                self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise

    def delete_dense_detail(self, bridge_id: int) -> None:
        """Delete the dense retriever sub-table row linked by bridge_id.

        Args:
            bridge_id: FK to the bridge record whose detail should be deleted.
        """
        try:
            detail = (
                self.db.query(DenseRetrieverDBModel)
                .filter_by(bridge_id=bridge_id)
                .first()
            )
            if detail is not None:
                self.db.delete(detail)
                self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise

    def delete_sparse_detail(self, bridge_id: int) -> None:
        """Delete the sparse retriever sub-table row linked by bridge_id.

        Args:
            bridge_id: FK to the bridge record whose detail should be deleted.
        """
        try:
            detail = (
                self.db.query(SparseRetrieverDBModel)
                .filter_by(bridge_id=bridge_id)
                .first()
            )
            if detail is not None:
                self.db.delete(detail)
                self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise

    def delete_bridge(self, bridge_id: int) -> None:
        """Delete a bridge record (RAG_retriever row) by its primary key.

        Args:
            bridge_id: Primary key of the bridge record to delete.
        """
        try:
            bridge = self.db.query(RetrieverDBModel).get(bridge_id)
            if bridge is not None:
                self.db.delete(bridge)
                self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise
