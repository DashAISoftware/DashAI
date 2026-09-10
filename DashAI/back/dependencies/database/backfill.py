import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

log = logging.getLogger(__name__)


def backfill_dataset_counts(session_factory: "sessionmaker") -> None:
    """Populate total_rows/total_columns for FINISHED datasets with NULL counts.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory from the DI container.
    """
    from DashAI.back.core.enums.status import DatasetStatus
    from DashAI.back.dependencies.database.models import Dataset

    with session_factory() as db:
        pending = (
            db.query(Dataset)
            .filter(
                Dataset.status == DatasetStatus.FINISHED,
                Dataset.total_rows == None,  # noqa: E711 (SQLAlchemy ORM requires == for column IS NULL)
            )
            .all()
        )
        updated = 0

        if not pending:
            log.debug("No datasets found that require backfilling.")
            return
        for ds in pending:
            try:
                from DashAI.back.dataloaders.classes.dashai_dataset import (
                    get_dataset_info,
                )

                info = get_dataset_info(f"{ds.file_path}/dataset")
                ds.total_rows = info["total_rows"]
                ds.total_columns = info["total_columns"]
                updated += 1
            except Exception as e:
                log.warning("Failed to backfill dataset %d: %s", ds.id, e)
        if updated:
            db.commit()
            log.debug("Backfilled counts for %d dataset(s).", updated)


def backfill_explorer_artifacts(session_factory: "sessionmaker") -> None:
    """Persist the render artifacts of explorations created before they existed.

    Explorations used to build their artifacts on every read request, which
    made them unreadable once their explorer class was removed from the
    registry. This backfill stores the artifacts of every finished exploration
    that still lacks them, while the explorer classes are installed. Explorers
    that are already gone are skipped: nothing can be recovered for them.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory from the DI container.
    """
    from kink import di

    from DashAI.back.core.enums.status import ExplorerStatus
    from DashAI.back.dependencies.database.models import Explorer
    from DashAI.back.exploration.artifact_store import (
        has_stored_artifacts,
        store_artifacts,
    )

    component_registry = di["component_registry"]

    with session_factory() as db:
        pending = (
            db.query(Explorer)
            .filter(
                Explorer.status == ExplorerStatus.FINISHED,
                Explorer.artifacts_path == None,  # noqa: E711 (SQLAlchemy ORM requires == for column IS NULL)
                Explorer.exploration_path != None,  # noqa: E711
            )
            .all()
        )

        if not pending:
            log.debug("No explorers found that require backfilling.")
            return

        updated = 0
        for explorer in pending:
            if has_stored_artifacts(explorer):
                continue
            try:
                explorer_class = component_registry[explorer.exploration_type]["class"]
                explorer_instance = explorer_class(**explorer.parameters)
                explorer.artifacts_path = store_artifacts(
                    explorer_instance, explorer.exploration_path, explorer.id
                )
                updated += 1
            except Exception as e:
                log.warning(
                    "Failed to backfill artifacts of explorer %d: %s", explorer.id, e
                )
        if updated:
            db.commit()
            log.debug("Backfilled artifacts for %d explorer(s).", updated)
