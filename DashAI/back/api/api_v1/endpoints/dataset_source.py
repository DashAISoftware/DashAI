"""Dataset source API endpoints."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import HTTPException
from kink import di
from pydantic import BaseModel

if TYPE_CHECKING:
    from DashAI.back.dependencies.registry import ComponentRegistry

log = logging.getLogger(__name__)
router = APIRouter()


def _get_source(source_name: str, registry: "ComponentRegistry"):
    """Retrieve and instantiate a DatasetSource from the registry.

    Parameters
    ----------
    source_name : str
        Registered class name of the DatasetSource.
    registry : ComponentRegistry
        The component registry to look up.

    Returns
    -------
    BaseDatasetSource
        Instantiated source object.

    Raises
    ------
    HTTPException
        404 if source_name is not found in the DatasetSource registry.
    """
    sources = registry._registry.get("DatasetSource", {})
    if source_name not in sources:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DatasetSource '{source_name}' not found.",
        )
    return sources[source_name]["class"]()


@router.get("/{source_name}/search")
async def search_datasets(
    source_name: str,
    q: str = Query(default="", description="Search query"),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str = Query(default="", description="Pagination cursor from previous page"),
    tags: list[str] = Query(default=[]),
    registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
) -> Dict[str, Any]:
    """Search for datasets in a registered source.

    Parameters
    ----------
    source_name : str
        Registered DatasetSource class name.
    q : str
        Search query string.
    limit : int
        Maximum number of results (1-100).
    cursor : str
        Opaque pagination token returned by the previous call.  Empty string
        means first page.
    tags : list[str]
        Repeated tag filter strings (e.g. ``?tags=nlp&tags=tabular``).  Passed
        through to the datasource via ``**filters``.
    registry : ComponentRegistry
        Injected component registry.

    Returns
    -------
    dict
        ``{"results": [...], "next_cursor": str | null}``
    """
    source = _get_source(source_name, registry)
    page = source.search(q, limit=limit, cursor=cursor or None, tags=tags)
    return {
        "results": [
            {
                "id": e.id,
                "name": e.name,
                "description": e.description,
                "tags": e.tags,
                "size_bytes": e.size_bytes,
                "url": e.url,
                "source": e.source,
            }
            for e in page.entries
        ],
        "next_cursor": page.next_cursor,
    }


@router.get("/{source_name}/{dataset_id:path}/info")
async def get_dataset_info(
    source_name: str,
    dataset_id: str,
    registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
) -> Dict[str, Any]:
    """Return full metadata for a single dataset (description, tags, etc.).

    Parameters
    ----------
    source_name : str
        Registered DatasetSource class name.
    dataset_id : str
        Source-specific dataset identifier (URL-encoded).
    registry : ComponentRegistry
        Injected component registry.

    Returns
    -------
    dict
        DatasetEntry fields, or empty dict if the source has no enrichment.
    """
    source = _get_source(source_name, registry)
    decoded_id = unquote(dataset_id)
    entry = source.get_info(decoded_id)
    if entry is None:
        return {}
    return {
        "id": entry.id,
        "description": entry.description,
        "tags": entry.tags,
        "size_bytes": entry.size_bytes,
    }


class PreviewRequest(BaseModel):
    """Request body for previewing a dataset with dataloader params.

    Parameters
    ----------
    dataloader : str | None
        Name of the DataLoader to use for parsing the file.
    params : dict
        DataLoader parameters (e.g., separator for CSV).
    n_rows : int
        Number of rows to sample (1-500).
    datafile_id : int | None
        If set, use this pre-downloaded local file instead of fetching from source.
    selected_file : str | None
        Relative filename inside the datafile directory.
    """

    dataloader: str | None = None
    params: Dict[str, Any] = {}
    n_rows: int = 100
    datafile_id: int | None = None
    selected_file: str | None = None


@router.post("/{source_name}/{dataset_id:path}/preview")
async def preview_dataset_with_params(
    source_name: str,
    dataset_id: str,
    body: PreviewRequest,
    registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
    session_factory=Depends(lambda: di["session_factory"]),
) -> Dict[str, Any]:
    """Fetch a sample preview using a DataLoader and params.

    If ``hub_download_id`` is provided the already-downloaded local file is
    used directly; no redownload from the source occurs.

    Parameters
    ----------
    source_name : str
        Registered DatasetSource class name.
    dataset_id : str
        Source-specific dataset identifier (URL-encoded).
    body : PreviewRequest
        DataLoader name, params, row count, and optional datafile_id.
    registry : ComponentRegistry
        Injected component registry.
    session_factory
        Injected DB session factory (used when datafile_id is set).

    Returns
    -------
    dict
        ``{"sample": [...], "inferred_types": {...}, "preview_row_count": int}``.
    """
    from DashAI.back.types.inf.type_inference import infer_types

    _get_source(source_name, registry)  # validate source exists
    decoded_id = unquote(dataset_id)
    n_rows = max(1, min(body.n_rows, 500))

    try:
        if body.datafile_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="datafile_id is required.",
            )

        from DashAI.back.core.enums.status import DatafileStatus
        from DashAI.back.dependencies.database.models import Datafile

        with session_factory() as db:
            hub_row = db.get(Datafile, body.datafile_id)
        if hub_row is None or hub_row.status != DatafileStatus.READY:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hub download not ready or not found.",
            )
        if body.selected_file:
            file_path = str(Path(hub_row.local_path) / body.selected_file)
        else:
            base_path = Path(hub_row.local_path)
            files = sorted(
                str(p)
                for p in base_path.rglob("*")
                if p.is_file()
                and not any(
                    part.startswith(".") for part in p.relative_to(base_path).parts
                )
            )
            if not files:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No files found in hub download directory.",
                )
            file_path = files[0]
        work_dir = str(Path(file_path).parent)
        dataloader_name = body.dataloader
        if not dataloader_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="dataloader is required.",
            )

        dl_registry = registry._registry.get("DataLoader", {})
        if dataloader_name not in dl_registry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"DataLoader '{dataloader_name}' not found.",
            )

        dataloader = dl_registry[dataloader_name]["class"]()
        params = body.params or {}

        try:
            preview_df = dataloader.load_preview(
                filepath_or_buffer=file_path,
                params=params,
                n_rows=n_rows,
            )
        except NotImplementedError:
            dataset = dataloader.load_data(
                filepath_or_buffer=file_path,
                temp_path=work_dir,
                params=params,
                n_sample=n_rows,
            )
            preview_df = dataset.to_pandas().head(n_rows)

    except HTTPException:
        raise
    except Exception as exc:
        log.exception("Error fetching preview for %s/%s", source_name, decoded_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch preview from source: {exc}",
        ) from exc

    if preview_df.empty:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Source returned no data for dataset '{decoded_id}'.",
        )

    inferred = infer_types(preview_df, method="DashAIPtype")
    sample = preview_df.to_dict(orient="records")

    return {
        "sample": sample,
        "inferred_types": inferred,
        "preview_row_count": len(preview_df),
    }


class ImportRequest(BaseModel):
    """Request body for the dataset import endpoint.

    Parameters
    ----------
    dataset_id : int
        ID of a pre-created Dataset DB record to populate.
    params : dict
        Parameters including ``inferred_types`` and ``column_renames``.
    """

    dataset_id: int
    params: Dict[str, Any] = {}


@router.post(
    "/{source_name}/{dataset_id:path}/import", status_code=status.HTTP_201_CREATED
)
async def import_dataset(
    source_name: str,
    dataset_id: str,
    body: ImportRequest,
    registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
    job_queue=Depends(lambda: di["job_queue"]),
) -> Dict[str, Any]:
    """Enqueue a DatasetJob to import a dataset from an external source.

    Parameters
    ----------
    source_name : str
        Registered DatasetSource class name.
    dataset_id : str
        Source-specific dataset identifier (URL-encoded).
    body : ImportRequest
        Contains the DashAI dataset_id and params. ``params`` may include
        ``compute_metadata: bool`` (default True). When False, ``DatasetJob``
        only computes base metadata (column names, row count, NaN counts),
        extended EDA fields (correlations, stats, quality) are omitted.
    registry : ComponentRegistry
        Injected component registry.
    job_queue : BaseJobQueue
        Injected job queue.

    Returns
    -------
    dict
        ``{"job_id": int, "dataset_id": int}``: the enqueued job and dataset IDs.
    """
    from DashAI.back.job.dataset_job import DatasetJob

    _get_source(source_name, registry)  # validates source exists, raises 404 if not

    job = DatasetJob(
        kwargs={
            "dataset_id": body.dataset_id,
            "source_name": source_name,
            "dataset_source_id": unquote(dataset_id),
            "params": body.params,
        }
    )
    job.set_status_as_delivered()
    result = job_queue.put(job)
    # huey.api.Result has .id (task UUID string); plain int in other modes
    job_id = getattr(result, "id", result)

    return {"job_id": job_id, "dataset_id": body.dataset_id}
