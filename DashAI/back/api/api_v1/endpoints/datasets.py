import asyncio
import hashlib
import io
import json
import logging
import os
import time
import zipfile
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from kink import di, inject
from sqlalchemy import exc, select

from DashAI.back.api.api_v1.schemas.datasets_params import Dataset as DatasetSchema
from DashAI.back.api.api_v1.schemas.datasets_params import (
    DatasetBulkDeleteParams,
    DatasetColumnEncoderParams,
    DatasetCreateParams,
    DatasetRenameColumnParams,
    DatasetUpdateParams,
)
from DashAI.back.dependencies.database.models import Dataset, Folder, ModelSession

if TYPE_CHECKING:
    import pyarrow as pa
    from sqlalchemy.orm.session import sessionmaker

    from DashAI.back.dependencies.registry import ComponentRegistry


def _build_image_preview_sample(
    extract_dir: str, image_extensions: set, max_rows: int = 5
) -> tuple:
    """Walk an extracted imagefolder directory and return sample rows,
    total count, and whether class subdirectories exist.

    Returns
    -------
    tuple of (list[dict], int, bool)
        (sample_rows, total_images, has_labels)
    """
    import os

    samples = []
    total = 0
    labels_seen = set()
    for root, dirs, files in os.walk(extract_dir):
        dirs[:] = [
            d for d in dirs if not d.startswith("__MACOSX") and not d.startswith(".")
        ]
        for f in sorted(files):
            if f.startswith("."):
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext not in image_extensions:
                continue
            total += 1
            label = os.path.basename(root)
            labels_seen.add(label)
            if len(samples) >= max_rows:
                continue
            filepath = os.path.join(root, f)
            try:
                with open(filepath, "rb") as fh:
                    img_bytes = fh.read()
                if len(img_bytes) == 0:
                    continue
                thumb = _image_bytes_to_thumbnail_data_uri(img_bytes)
                if thumb == "[Image]":
                    continue
                samples.append({"image": thumb, "_label": label})
            except Exception:
                continue

    has_labels = len(labels_seen) > 1

    if has_labels:
        for s in samples:
            s["label"] = s.pop("_label")
    else:
        for s in samples:
            s.pop("_label", None)

    return samples, total, has_labels


def _image_bytes_to_thumbnail_data_uri(img_bytes: bytes, max_size: int = 64) -> str:
    """Convert raw image bytes to a small base64 data URI thumbnail."""
    import base64
    import io

    from PIL import Image

    try:
        img = Image.open(io.BytesIO(img_bytes))
        if img.mode in ("CMYK", "YCbCr", "LAB", "HSV"):
            img = img.convert("RGB")
        elif img.mode in ("LA", "PA"):
            img = img.convert("RGBA")
        img.thumbnail((max_size, max_size))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        logger.warning(
            "Failed to generate thumbnail (len=%d, head=%r): %s",
            len(img_bytes),
            img_bytes[:16],
            e,
        )
        return "[Image]"


logger = logging.getLogger(__name__)
router = APIRouter()

_SEED_MANIFEST_PATH = (
    Path(__file__).parent.parent.parent.parent / "seeds" / "manifest.json"
)


def _load_seed_tasks() -> dict:
    try:
        with _SEED_MANIFEST_PATH.open() as f:
            return {name: meta.get("task") for name, meta in json.load(f).items()}
    except Exception:
        return {}


_SEED_TASKS: dict = _load_seed_tasks()


# ---------------------------------------------------------------------------
# Cache for filtered + sorted PyArrow tables
# ---------------------------------------------------------------------------
_CACHE_MAX_SIZE = 20
_CACHE_TTL_SECONDS = 300  # 5 minutes


class _FilteredTableCache:
    """LRU cache for filtered/sorted PyArrow tables with TTL eviction."""

    def __init__(self, max_size: int = _CACHE_MAX_SIZE, ttl: int = _CACHE_TTL_SECONDS):
        self._store: OrderedDict[str, tuple[float, "pa.Table", int]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl

    @staticmethod
    def _make_key(path: str, filter_model: str | None, sort_model: str | None) -> str:
        raw = f"{path}|{filter_model or ''}|{sort_model or ''}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, path: str, filter_model: str | None, sort_model: str | None):
        key = self._make_key(path, filter_model, sort_model)
        entry = self._store.get(key)
        if entry is None:
            return None
        ts, table, total = entry
        if time.time() - ts > self._ttl:
            del self._store[key]
            return None
        arrow_file_path = f"{path}/dataset/data.arrow"
        try:
            if os.path.getmtime(arrow_file_path) > ts:
                del self._store[key]
                return None
        except OSError:
            pass
        self._store.move_to_end(key)
        return table, total

    def put(
        self,
        path: str,
        filter_model: str | None,
        sort_model: str | None,
        table: "pa.Table",
        total: int,
    ):
        key = self._make_key(path, filter_model, sort_model)
        self._store[key] = (time.time(), table, total)
        self._store.move_to_end(key)
        while len(self._store) > self._max_size:
            self._store.popitem(last=False)

    def invalidate(self):
        """Invalidate all cache entries on dataset mutation."""
        self._store.clear()


_filtered_table_cache = _FilteredTableCache()


def _load_and_filter_table(
    path: str,
    filter_model: str | None,
    sort_model: str | None,
) -> tuple["pa.Table", int, bool]:
    """Load arrow file, apply filters and sorting.

    Returns (table, total, was_filtered).
    """

    import json

    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.ipc as ipc

    from DashAI.back.dataloaders.classes.dashai_dataset import get_dataset_info

    arrow_file_path = f"{path}/dataset/data.arrow"
    with pa.OSFile(arrow_file_path, "rb") as source:
        reader = ipc.RecordBatchFileReader(source)
        batches = [reader.get_batch(i) for i in range(reader.num_record_batches)]
        table = pa.Table.from_batches(batches)

    filter_dict = None
    if filter_model:
        try:
            filter_dict = json.loads(filter_model)
        except Exception:
            filter_dict = None

    if filter_dict and "items" in filter_dict:
        for item in filter_dict["items"]:
            col = item.get("field") or item.get("columnField")
            op = item.get("operator") or item.get("operatorValue")
            val = item.get("value")
            if col and op:
                col_type = table[col].type

                def cast_value(v, col_type=col_type):
                    if pa.types.is_integer(col_type):
                        try:
                            return int(v)
                        except Exception:
                            return v
                    elif pa.types.is_floating(col_type):
                        try:
                            return float(v)
                        except Exception:
                            return v
                    elif pa.types.is_boolean(col_type):
                        if isinstance(v, bool):
                            return v
                        if str(v).lower() in ["true", "1"]:
                            return True
                        if str(v).lower() in ["false", "0"]:
                            return False
                        return v
                    return v

                if op == "equals" and val is not None:
                    table = table.filter(pc.equal(table[col], cast_value(val)))
                elif op == "lessThan" and val is not None:
                    table = table.filter(pc.less(table[col], cast_value(val)))
                elif op == "lessThanOrEqualTo" and val is not None:
                    table = table.filter(pc.less_equal(table[col], cast_value(val)))
                elif op == "greaterThan" and val is not None:
                    table = table.filter(pc.greater(table[col], cast_value(val)))
                elif op == "greaterThanOrEqualTo" and val is not None:
                    table = table.filter(pc.greater_equal(table[col], cast_value(val)))
                elif op == "contains" and val is not None:
                    if not pa.types.is_string(col_type):
                        as_str = pc.utf8_lower(pc.cast(table[col], pa.string()))
                    else:
                        as_str = pc.utf8_lower(table[col])
                    mask = pc.match_substring(as_str, str(val).lower())
                    table = table.filter(mask)
                elif op == "doesNotContain" and val is not None:
                    if not pa.types.is_string(col_type):
                        as_str = pc.utf8_lower(pc.cast(table[col], pa.string()))
                    else:
                        as_str = pc.utf8_lower(table[col])
                    mask = pc.invert(pc.match_substring(as_str, str(val).lower()))
                    table = table.filter(mask)
                elif op == "startsWith" and val is not None:
                    if not pa.types.is_string(col_type):
                        as_str = pc.utf8_lower(pc.cast(table[col], pa.string()))
                    else:
                        as_str = pc.utf8_lower(table[col])
                    mask = pc.match_substring_regex(as_str, f"^{str(val).lower()}")
                    table = table.filter(mask)
                elif op == "endsWith" and val is not None:
                    if not pa.types.is_string(col_type):
                        as_str = pc.utf8_lower(pc.cast(table[col], pa.string()))
                    else:
                        as_str = pc.utf8_lower(table[col])
                    mask = pc.match_substring_regex(as_str, f"{str(val).lower()}$")
                    table = table.filter(mask)
                elif op == "isEmpty":
                    if pa.types.is_string(col_type):
                        mask = pc.or_(pc.equal(table[col], ""), pc.is_null(table[col]))
                    else:
                        mask = pc.is_null(table[col])
                    table = table.filter(mask)
                elif op == "isNotEmpty":
                    if pa.types.is_string(col_type):
                        mask = pc.and_(
                            pc.invert(pc.equal(table[col], "")),
                            pc.invert(pc.is_null(table[col])),
                        )
                    else:
                        mask = pc.invert(pc.is_null(table[col]))
                    table = table.filter(mask)
                elif op == "isAnyOf" and val is not None:
                    values = (
                        val
                        if isinstance(val, list)
                        else [v.strip() for v in str(val).split(",")]
                    )
                    casted_values = [cast_value(v) for v in values]
                    mask = pc.is_in(table[col], value_set=pa.array(casted_values))
                    table = table.filter(mask)
                elif (
                    op == "between"
                    and val is not None
                    and isinstance(val, list)
                    and len(val) == 2
                ):
                    min_val, max_val = val
                    if min_val not in (None, ""):
                        table = table.filter(
                            pc.greater_equal(table[col], cast_value(min_val))
                        )
                    if max_val not in (None, ""):
                        table = table.filter(
                            pc.less_equal(table[col], cast_value(max_val))
                        )

    filtered = (
        filter_dict and filter_dict.get("items") and len(filter_dict["items"]) > 0
    )

    if sort_model:
        try:
            sort_list = json.loads(sort_model)
            sort_keys = [
                (item["id"], "descending" if item.get("desc") else "ascending")
                for item in sort_list
                if "id" in item
            ]
            if sort_keys:
                table = table.sort_by(sort_keys)
        except Exception as e:
            logger.error("Error parsing sort_model: %s", e)

    if filtered:
        total = table.num_rows
    else:
        try:
            total = get_dataset_info(f"{path}/dataset")["total_rows"]
        except Exception:
            total = table.num_rows

    return table, total, bool(filtered)


# Server-side filtering and pagination
@router.get("/filter/")
async def filter_dataset_file(
    path: str,
    page: int = 0,
    page_size: int = 10,
    filter_model: str = Query(None, alias="filterModel"),
    sort_model: str = Query(None, alias="sortModel"),
):
    """
    Fetch filtered and paginated dataset rows based on the provided
    filterModel from the frontend. Uses an in-memory cache so that
    pagination over the same filter+sort combination avoids re-reading
    and re-filtering the Arrow file.
    """
    import pyarrow as pa

    cached = _filtered_table_cache.get(path, filter_model, sort_model)
    if cached is not None:
        table, total = cached
    else:
        table, total, _ = _load_and_filter_table(path, filter_model, sort_model)
        _filtered_table_cache.put(path, filter_model, sort_model, table, total)

    start = page * page_size
    paged_table = table.slice(start, page_size)

    image_cols = {
        col
        for col in paged_table.schema.names
        if pa.types.is_struct(paged_table.schema.field(col).type)
        or pa.types.is_large_binary(paged_table.schema.field(col).type)
        or pa.types.is_binary(paged_table.schema.field(col).type)
    }

    rows = []
    for i in range(paged_table.num_rows):
        row = {}
        for col in paged_table.schema.names:
            val = paged_table[col][i].as_py()
            if col in image_cols:
                if isinstance(val, dict):
                    img_bytes = val.get("bytes", b"")
                elif isinstance(val, bytes):
                    img_bytes = val
                else:
                    img_bytes = b""
                row[col] = (
                    _image_bytes_to_thumbnail_data_uri(img_bytes)
                    if img_bytes
                    else "[Image]"
                )
            else:
                row[col] = val
        rows.append(row)

    return JSONResponse(content={"rows": rows, "total": total})


@router.post("/", response_model=DatasetSchema, status_code=status.HTTP_201_CREATED)
@inject
async def create_dataset(
    params: DatasetCreateParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Create a new dataset entry in the database with NOT_STARTED status.

    Parameters
    ----------
    params : DatasetCreateParams
        A schema containing the dataset creation parameters.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.

    Returns
    -------
    Dataset
        The newly created dataset with NOT_STARTED status.
    """
    with session_factory() as db:
        try:
            existing = db.query(Dataset).filter(Dataset.name == params.name).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A dataset with the name '{params.name}' already exists",
                )

            dataset = Dataset(
                name=params.name,
                file_path="",
            )
            db.add(dataset)
            db.commit()
            db.refresh(dataset)
            return dataset

        except HTTPException:
            raise
        except exc.IntegrityError as e:
            logger.exception(e)
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A dataset with the name '{params.name}' already exists",
            ) from e
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get("/")
@inject
async def get_datasets(
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Retrieve a list of the stored datasets in the database.

    Parameters
    ----------
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A list of dictionaries representing the found datasets.
        Each dictionary contains information about the dataset, including its name,
        type, description, and creation date.
        If no datasets are found, an empty list will be returned.
    """
    logger.debug("Retrieving all datasets.")
    with session_factory() as db:
        try:
            datasets = db.query(Dataset).all()

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    result = []
    for ds in datasets:
        data = jsonable_encoder(ds)
        data["task"] = _SEED_TASKS.get(ds.name)
        result.append(data)
    return result


@router.get("/{dataset_id}")
@inject
async def get_dataset(
    dataset_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Retrieve the dataset associated with the provided ID.

    Parameters
    ----------
    dataset_id : int
        ID of the dataset to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Dict
        A Dict containing the requested dataset details.
    """
    logger.debug("Retrieving dataset with id %s", dataset_id)
    with session_factory() as db:
        try:
            dataset = db.get(Dataset, dataset_id)

            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return dataset


@router.get("/{dataset_id}/sample")
@inject
async def get_sample(
    dataset_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Return a sample of 10 rows from the dataset with id dataset_id from the
    database.

    If a column is not JSON serializable, it will be converted to a list of
    strings.

    Parameters
    ----------
    dataset_id : int
        id of the dataset to query.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Dict
        A Dict with a sample of 10 rows
    """
    import os

    import pyarrow as pa
    import pyarrow.ipc as ipc

    from DashAI.back.core.enums.status import DatasetStatus

    with session_factory() as db:
        try:
            dataset = db.get(Dataset, dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )
            if dataset.status != DatasetStatus.FINISHED:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Dataset is not in finished state",
                )
            file_path = dataset.file_path

            arrow_path = os.path.join(file_path, "dataset", "data.arrow")

            with pa.OSFile(arrow_path, "rb") as source:
                reader = ipc.open_file(source)
                batch = reader.get_batch(0)
                sample_size = min(10, batch.num_rows)
                sample_batch = batch.slice(0, sample_size)
                sample = sample_batch.to_pydict()

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
        try:
            jsonable_encoder(sample)
        except ValueError:
            for key, value in sample.items():
                try:
                    jsonable_encoder({key: value})
                except ValueError:
                    value = list(map(str, value))
                sample[key] = value
    return sample


@router.get("/sample/file")
@inject
async def get_sample_by_file(
    path: str,
):
    """Return a sample of 10 rows from the dataset file

    If a column is not JSON serializable, it will be converted to a list of
    strings.

    Parameters
    ----------
    params : dict
        A dictionary containing the parameters for the request.

    Returns
    -------
    Dict
        A Dict with a sample of 10 rows
    """
    import os

    import pyarrow as pa
    import pyarrow.ipc as ipc

    try:
        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found",
            )

        arrow_path = os.path.join(path, "dataset", "data.arrow")

        with pa.OSFile(arrow_path, "rb") as source:
            reader = ipc.open_file(source)
            batch = reader.get_batch(0)
            sample_size = min(10, batch.num_rows)
            sample_batch = batch.slice(0, sample_size)
            sample = sample_batch.to_pydict()

    except exc.SQLAlchemyError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e
    try:
        jsonable_encoder(sample)
    except ValueError:
        for key, value in sample.items():
            try:
                jsonable_encoder({key: value})
            except ValueError:
                value = list(map(str, value))
            sample[key] = value
    return sample


@router.get("/file/info")
@inject
async def get_info_by_file(
    path: str,
):
    """Return the dataset with id dataset_id from the database.

    Parameters
    ----------
    path : str
        The file path of the dataset.

    Returns
    -------
    JSON
        JSON with the specified dataset id.
    """
    from DashAI.back.dataloaders.classes.dashai_dataset import get_dataset_info

    try:
        info = get_dataset_info(f"{path}/dataset")
    except exc.SQLAlchemyError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error",
        ) from e
    return info


@router.get("/{dataset_id}/info")
@inject
async def get_info(
    dataset_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Return the dataset with id dataset_id from the database.

    Parameters
    ----------
    dataset_id : int
        id of the dataset to query.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    JSON
        JSON with the specified dataset id.
    """
    from DashAI.back.core.enums.status import DatasetStatus
    from DashAI.back.dataloaders.classes.dashai_dataset import get_dataset_info

    with session_factory() as db:
        try:
            dataset = db.get(Dataset, dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )

            if dataset.status != DatasetStatus.FINISHED:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Dataset is not in finished state",
                )

            info = get_dataset_info(f"{dataset.file_path}/dataset")
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    return info


@router.get("/{dataset_id}/model-sessions-exist")
@inject
async def get_model_sessions_exist(
    dataset_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Get a boolean indicating if there are model sessions associated with the dataset.

    Parameters
    ----------
    dataset_id : int
        id of the dataset to query.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    bool
        True if there are model sessions associated with the dataset, False otherwise.
    """
    from DashAI.back.core.enums.status import DatasetStatus

    with session_factory() as db:
        try:
            dataset = db.get(Dataset, dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )

            if dataset.status != DatasetStatus.FINISHED:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Dataset is not in finished state",
                )

            # Check if there are any model sessions associated with the dataset
            model_sessions_exist = (
                db.query(ModelSession)
                .filter(ModelSession.dataset_id == dataset_id)
                .first()
                is not None
            )

            return model_sessions_exist

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get("/{dataset_id}/types")
@inject
async def get_types(
    dataset_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Return the dataset with id dataset_id from the database.

    Parameters
    ----------
    dataset_id : int
        id of the dataset to query.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Dict
        Dict containing column names and types.
    """
    from DashAI.back.core.enums.status import DatasetStatus
    from DashAI.back.dataloaders.classes.dashai_dataset import get_columns_spec

    with session_factory() as db:
        try:
            dataset = db.get(Dataset, dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )
            if dataset.status != DatasetStatus.FINISHED:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Dataset is not in finished state",
                )
            columns_spec = get_columns_spec(f"{dataset.file_path}/dataset")
            if not columns_spec:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Error while loading column types.",
                )
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    return columns_spec


@router.get("/types/file")
@inject
async def get_types_by_file_path(
    path: str,
):
    """Return the dataset with the specified file path.

    Parameters
    ----------
    path : str
        Path to the dataset file.

    Returns
    -------
    Dict
        Dict containing column names and types.
    """
    from DashAI.back.dataloaders.classes.dashai_dataset import get_columns_spec

    try:
        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found",
            )
        columns_spec = get_columns_spec(f"{path}/dataset")
        if not columns_spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Error while loading column types.",
            )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error",
        ) from e
    return columns_spec


@router.post("/copy", status_code=status.HTTP_201_CREATED)
@inject
async def copy_dataset(
    dataset: Dict[str, int],
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    config: Dict[str, Any] = Depends(lambda: di["config"]),
):
    """Copy an existing dataset to create a new one.

    Parameters
    ----------
    dataset_id : int
        ID of the dataset to copy.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.
    config : Dict[str, Any]
        A dictionary containing the application configuration, including the path
        where datasets are stored.

    Returns
    -------
    Dataset
        The newly created dataset.
    """
    import shutil

    from DashAI.back.core.enums.status import DatasetStatus

    dataset_id = dataset["dataset_id"]
    logger.debug(f"Copying dataset with ID {dataset_id}.")

    with session_factory() as db:
        # Retrieve the existing dataset
        original_dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not original_dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original dataset not found.",
            )
        if original_dataset.status != DatasetStatus.FINISHED:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Original dataset is not in finished state",
            )

        # Create a new folder for the copied dataset
        new_name = f"{original_dataset.name}_copy"
        new_folder_path = config["DATASETS_PATH"] / new_name
        try:
            shutil.copytree(original_dataset.file_path, new_folder_path)
        except FileExistsError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A dataset with the name '{new_name}' already exists.",
            ) from None
        except Exception as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to copy dataset files.",
            ) from e

        # Save metadata for the new dataset
        try:
            new_dataset = Dataset(
                name=new_name,
                file_path=str(new_folder_path),
            )
            db.add(new_dataset)
            db.commit()
            db.refresh(new_dataset)
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            shutil.rmtree(new_folder_path, ignore_errors=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error.",
            ) from e

    logger.debug(f"Dataset copied successfully to '{new_name}'.")
    return new_dataset


@router.delete("/")
@inject
async def delete_datasets(
    params: DatasetBulkDeleteParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Delete multiple datasets, in a single transaction.

    Parameters
    ----------
    params : DatasetBulkDeleteParams
        The IDs of the datasets to delete. IDs that do not match an existing
        dataset are silently skipped rather than failing the whole request.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Response with code 204 NO_CONTENT
    """
    logger.debug("Deleting datasets with ids %s", params.ids)
    file_paths = []
    with session_factory() as db:
        try:
            for dataset_id in params.ids:
                dataset = db.get(Dataset, dataset_id)
                if not dataset:
                    continue
                file_paths.append(dataset.file_path)
                db.delete(dataset)

            db.commit()

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    _filtered_table_cache.invalidate()

    import shutil

    for file_path in file_paths:
        shutil.rmtree(file_path, ignore_errors=True)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{dataset_id}")
@inject
async def delete_dataset(
    dataset_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Delete the dataset associated with the provided ID from the database.

    Parameters
    ----------
    dataset_id : int
        ID of the dataset to be deleted.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Response with code 204 NO_CONTENT
    """
    logger.debug("Deleting dataset with id %s", dataset_id)
    with session_factory() as db:
        try:
            dataset = db.get(Dataset, dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )

            db.delete(dataset)
            db.commit()

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    _filtered_table_cache.invalidate()

    try:
        import shutil

        shutil.rmtree(dataset.file_path, ignore_errors=True)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except OSError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete directory",
        ) from e


@router.patch("/{dataset_id}")
@inject
async def update_dataset(
    dataset_id: int,
    params: DatasetUpdateParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Updates the name and/or folder of a dataset with the provided ID.

    Parameters
    ----------
    dataset_id : int
        ID of the dataset to update.
    params : DatasetUpdateParams
        A dictionary containing the new values for the dataset.
        name : str
            New name for the dataset.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Dict
        A dictionary containing the updated dataset record.
    """
    with session_factory() as db:
        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
            )

        if params.name is not None:
            if not params.name.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Name cannot be empty",
                )
            new_name = params.name.strip()
            if new_name != dataset.name:
                exists = db.execute(
                    select(Dataset.id).where(
                        Dataset.name == new_name, Dataset.id != dataset_id
                    )
                ).scalar()
                if exists:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Dataset name already exists",
                    )
                dataset.name = new_name

        if "folder_id" in params.model_fields_set:
            if params.folder_id is not None:
                folder = db.get(Folder, params.folder_id)
                if folder is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Folder not found",
                    )
            dataset.folder_id = params.folder_id

        try:
            db.commit()
            db.refresh(dataset)
            return dataset
        except exc.IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Dataset name already exists",
            ) from e
        except exc.SQLAlchemyError as e:
            db.rollback()
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.patch("/{dataset_id}/columns/rename")
@inject
async def rename_dataset_column(
    dataset_id: int,
    params: DatasetRenameColumnParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Rename a column in a dataset.

    Parameters
    ----------
    dataset_id : int
        ID of the dataset to update.
    params : DatasetRenameColumnParams
        Parameters containing old_name and new_name for the column.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Dict
        A dictionary with a success message and updated column types.
    """
    import json
    import os

    import pyarrow as pa
    import pyarrow.ipc as ipc

    from DashAI.back.core.enums.status import DatasetStatus
    from DashAI.back.dataloaders.classes.dashai_dataset import get_columns_spec

    with session_factory() as db:
        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
            )

        if dataset.status != DatasetStatus.FINISHED:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Dataset is not in finished state or being modified",
            )

        # Lock the dataset to prevent concurrent modifications
        try:
            dataset.set_status_as_started()
            db.commit()
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error locking dataset for modification",
            ) from e

        old_name = params.old_name.strip()
        new_name = params.new_name.strip()
        if not old_name or not new_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Column names cannot be empty",
            )
        if old_name == new_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="New column name must be different from old name",
            )

        dataset_path = f"{dataset.file_path}/dataset"
        arrow_file_path = f"{dataset_path}/data.arrow"
        try:
            from DashAI.back.types.utils import (
                get_types_from_arrow_metadata,
                save_types_in_arrow_metadata,
            )

            with pa.OSFile(arrow_file_path, "rb") as source:
                reader = ipc.open_file(source)
                table = reader.read_all()
            if old_name not in table.schema.names:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Column '{old_name}' not found in dataset",
                )
            if new_name in table.schema.names and new_name != old_name:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Column '{new_name}' already exists",
                )

            column_index = table.schema.get_field_index(old_name)
            types_dict = get_types_from_arrow_metadata(table.schema)
            new_fields = []
            for i, field in enumerate(table.schema):
                if i == column_index:
                    new_fields.append(pa.field(new_name, field.type, field.nullable))
                else:
                    new_fields.append(field)

            new_schema = pa.schema(new_fields)

            renamed_table = pa.table(
                {
                    new_name if name == old_name else name: table[name]
                    for name in table.schema.names
                },
                schema=new_schema,
            )
            if old_name in types_dict:
                types_dict[new_name] = types_dict.pop(old_name)

            types_serialized = {col: types_dict[col].to_string() for col in types_dict}
            renamed_table = save_types_in_arrow_metadata(
                renamed_table, types_serialized
            )

            with pa.OSFile(arrow_file_path, "wb") as sink:
                writer = ipc.new_file(sink, renamed_table.schema)
                writer.write_table(renamed_table)
                writer.close()

            _filtered_table_cache.invalidate()

            splits_path = f"{dataset_path}/splits.json"
            if os.path.exists(splits_path):
                with open(splits_path, "r", encoding="utf-8") as f:
                    splits_data = json.load(f)
                # Update column_names in split file
                splits_data["column_names"] = [
                    new_name if name == old_name else name
                    for name in splits_data["column_names"]
                ]
                # Update nan entries
                splits_data["nan"][new_name] = splits_data["nan"].pop(old_name)

                # Update general info (absent when compute_metadata=False)
                if "general_info" in splits_data:
                    splits_data["general_info"]["dtypes"][new_name] = splits_data[
                        "general_info"
                    ]["dtypes"].pop(old_name)

                # Update quality info nan per ratio
                if "quality_info" in splits_data:
                    splits_data["quality_info"]["nan_ratio_per_column"][new_name] = (
                        splits_data["quality_info"]["nan_ratio_per_column"].pop(
                            old_name
                        )
                    )

                # Update numeric_stats if column is numerical
                if old_name in splits_data.get("numeric_stats", {}):
                    splits_data["numeric_stats"][new_name] = splits_data[
                        "numeric_stats"
                    ].pop(old_name)

                    # Update correlations
                    if "correlations" in splits_data:
                        correlations = splits_data["correlations"]

                        # Rename the main key if needed
                        if old_name in correlations:
                            correlations[new_name] = correlations.pop(old_name)

                        # Rename inner keys
                        for _, corr_values in correlations.items():
                            if old_name in corr_values:
                                corr_values[new_name] = corr_values.pop(old_name)

                # Update categorical_stats columns if column is categorical
                elif old_name in splits_data.get("categorical_stats", {}):
                    splits_data["categorical_stats"][new_name] = splits_data[
                        "categorical_stats"
                    ].pop(old_name)

                # Update text_stats columns if column is textual
                elif old_name in splits_data.get("text_stats", {}):
                    splits_data["text_stats"][new_name] = splits_data["text_stats"].pop(
                        old_name
                    )

                with open(splits_path, "w", encoding="utf-8") as f:
                    json.dump(
                        splits_data,
                        f,
                        indent=2,
                        sort_keys=True,
                        ensure_ascii=False,
                    )

            dataset.last_modified = datetime.now(timezone.utc)
            dataset.set_status_as_finished()
            db.commit()
            db.refresh(dataset)
            updated_columns = get_columns_spec(dataset_path)
            return {
                "message": f"Column '{old_name}' renamed to '{new_name}' successfully",
                "old_name": old_name,
                "new_name": new_name,
                "columns": updated_columns,
            }
        except HTTPException:
            # Release the lock before re-raising
            dataset.set_status_as_finished()
            db.commit()
            raise
        except Exception as e:
            # Release the lock and mark as finished on error
            dataset.set_status_as_finished()
            db.commit()
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error renaming column: {str(e)}",
            ) from e


@router.patch("/{dataset_id}/columns/{column_name}/encoder")
@inject
async def update_column_encoder(
    dataset_id: int,
    column_name: str,
    params: DatasetColumnEncoderParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Update the encoder preference for a single Categorical column.

    Parameters
    ----------
    dataset_id : int
        ID of the dataset to update.
    column_name : str
        Name of the column to update.
    params : DatasetColumnEncoderParams
        Parameters containing the new encoder value.

    Returns
    -------
    Dict
        Updated column types dict (same shape as GET /types).
    """
    import os

    import pyarrow as pa
    import pyarrow.ipc as ipc

    from DashAI.back.core.enums.status import DatasetStatus
    from DashAI.back.dataloaders.classes.dashai_dataset import get_columns_spec
    from DashAI.back.types.categorical import Categorical
    from DashAI.back.types.utils import (
        get_types_from_arrow_metadata,
        save_types_in_arrow_metadata,
    )

    with session_factory() as db:
        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
            )

        if dataset.status != DatasetStatus.FINISHED:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Dataset is not in finished state",
            )

        try:
            dataset.set_status_as_started()
            db.commit()
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error locking dataset for modification",
            ) from e

        data_filepath = os.path.join(dataset.file_path, "dataset", "data.arrow")

        try:
            with pa.OSFile(data_filepath, "rb") as source:
                reader = pa.ipc.open_file(source)
                table = reader.read_all()
                schema = reader.schema

            if column_name not in table.schema.names:
                dataset.set_status_as_finished()
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Column '{column_name}' not found in dataset",
                )

            types_dict = get_types_from_arrow_metadata(schema)

            col_type = types_dict.get(column_name)
            if not isinstance(col_type, Categorical):
                dataset.set_status_as_finished()
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Column '{column_name}' is not a Categorical column",
                )

            col_type.encoder = params.encoder
            types_serialized = {col: t.to_string() for col, t in types_dict.items()}

            updated_table = save_types_in_arrow_metadata(table, types_serialized)
            sink = pa.BufferOutputStream()
            with ipc.new_file(sink, updated_table.schema) as writer:
                writer.write_table(updated_table)

            with open(data_filepath, "wb") as f:
                f.write(sink.getvalue().to_pybytes())

            dataset.set_status_as_finished()
            db.commit()

        except HTTPException:
            raise
        except Exception as e:
            logger.exception(e)
            try:
                dataset.set_status_as_finished()
                db.commit()
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating encoder: {str(e)}",
            ) from e

        dataset_file_path = dataset.file_path

    return get_columns_spec(os.path.join(dataset_file_path, "dataset"))


@router.get("/file/")
async def get_dataset_file(
    path: str,
    page: int = 0,
    page_size: int = 10,
):
    """Fetch the dataset file associated with the provided file path.

    Parameters
    ----------
    path : str
        The folder path of the dataset to retrieve.
    page: int
        The page number to retrieve.
    page_size: int
        The number of items per page.

    Returns
    -------
    JSONResponse
        A JSON response containing the dataset rows and total row count.
    """
    import pyarrow as pa
    import pyarrow.ipc as ipc

    from DashAI.back.dataloaders.classes.dashai_dataset import get_dataset_info

    arrow_file_path = f"{path}/dataset/data.arrow"
    rows = []

    start = page * page_size
    end = start + page_size
    rows_collected = 0

    with pa.OSFile(arrow_file_path, "rb") as source:
        reader = ipc.RecordBatchFileReader(source)

        current_index = 0
        for i in range(reader.num_record_batches):
            batch = reader.get_batch(i)
            batch_start = current_index
            batch_end = current_index + batch.num_rows
            current_index = batch_end

            # Skip batches before the page start
            if batch_end <= start:
                continue
            if batch_start >= end:
                break  # already got all needed rows

            slice_start = max(0, start - batch_start)
            slice_end = min(batch.num_rows, end - batch_start)
            sliced_batch = batch.slice(slice_start, slice_end - slice_start)

            image_cols = {
                col
                for col in sliced_batch.schema.names
                if pa.types.is_struct(sliced_batch.schema.field(col).type)
                or pa.types.is_large_binary(sliced_batch.schema.field(col).type)
                or pa.types.is_binary(sliced_batch.schema.field(col).type)
            }

            for j in range(sliced_batch.num_rows):
                row = {}
                for col in sliced_batch.schema.names:
                    val = sliced_batch[col][j].as_py()
                    if col in image_cols:
                        if isinstance(val, dict):
                            img_bytes = val.get("bytes", b"")
                        elif isinstance(val, bytes):
                            img_bytes = val
                        else:
                            img_bytes = b""
                        row[col] = (
                            _image_bytes_to_thumbnail_data_uri(img_bytes)
                            if img_bytes
                            else "[Image]"
                        )
                    else:
                        row[col] = val
                rows.append(row)
                rows_collected += 1
                if rows_collected >= page_size:
                    break

            if rows_collected >= page_size:
                break

    total_rows = get_dataset_info(f"{path}/dataset")["total_rows"]

    return JSONResponse(content={"rows": rows, "total": total_rows})


def _build_image_zip(table: "pa.Table") -> io.BytesIO:
    """Build a ZIP buffer from an image dataset table.

    Uses ZIP_STORED (no compression) because image formats (JPEG, PNG) are
    already compressed, so DEFLATE gains nothing but wastes significant CPU time.
    """
    import pyarrow as pa

    label_col = next(
        (
            col
            for col in table.column_names
            if not pa.types.is_struct(table.schema.field(col).type)
            and (
                pa.types.is_string(table.schema.field(col).type)
                or pa.types.is_large_string(table.schema.field(col).type)
                or pa.types.is_dictionary(table.schema.field(col).type)
            )
        ),
        None,
    )

    image_cols = [
        col
        for col in table.column_names
        if pa.types.is_struct(table.schema.field(col).type)
    ]

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_STORED) as zf:
        seen_paths: set = set()
        for col in image_cols:
            arr_col = table.column(col)
            label_arr = table.column(label_col) if label_col else None
            for i in range(table.num_rows):
                val = arr_col[i].as_py()
                if not (isinstance(val, dict) and val.get("bytes")):
                    continue
                img_bytes = val["bytes"]
                raw_path = val.get("path") or ""
                raw_ext = os.path.splitext(raw_path)[1].lstrip(".").lower()
                ext = raw_ext if raw_ext else "png"
                orig_fname = os.path.basename(raw_path) or f"{col}_{i}.{ext}"

                if label_arr is not None:
                    label_val = str(label_arr[i].as_py())
                    entry = f"{label_val}/{orig_fname}"
                else:
                    entry = f"images/{orig_fname}"

                if entry in seen_paths:
                    stem, dot_ext = os.path.splitext(orig_fname)
                    entry_base = (
                        f"{label_val}/{stem}"
                        if label_arr is not None
                        else f"images/{stem}"
                    )
                    entry = f"{entry_base}_{i}{dot_ext}"
                seen_paths.add(entry)
                zf.writestr(entry, img_bytes)

    zip_buffer.seek(0)
    return zip_buffer


def _iter_buffer(buf: io.BytesIO, chunk_size: int = 65536):
    """Yield a BytesIO in fixed-size chunks for StreamingResponse."""
    while True:
        chunk = buf.read(chunk_size)
        if not chunk:
            break
        yield chunk


async def _build_export_response(
    table: "pa.Table", dataset_name: str
) -> StreamingResponse:
    """Build a StreamingResponse for dataset export.

    For image datasets (struct columns), produces a ZIP in ImageFolder format:
    ``<label>/<original_filename>``. For tabular datasets, produces a plain CSV.

    The CPU-bound work (ZIP/CSV construction) runs in a thread-pool executor so
    it does not block FastAPI's async event loop.

    Parameters
    ----------
    table : pa.Table
        The (possibly filtered) Arrow table to export.
    dataset_name : str
        Used as the base filename in the Content-Disposition header.

    Returns
    -------
    StreamingResponse
        ZIP (image datasets) or CSV (tabular datasets).
    """
    import pyarrow as pa
    import pyarrow.csv as csv

    image_cols = [
        col
        for col in table.column_names
        if pa.types.is_struct(table.schema.field(col).type)
    ]

    loop = asyncio.get_event_loop()

    if image_cols:
        zip_buffer = await loop.run_in_executor(None, _build_image_zip, table)
        return StreamingResponse(
            _iter_buffer(zip_buffer),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={dataset_name}.zip"},
        )
    else:
        drop_cols = [
            col
            for col in table.column_names
            if pa.types.is_binary(table.schema.field(col).type)
            or pa.types.is_large_binary(table.schema.field(col).type)
        ]
        if drop_cols:
            table = table.drop(drop_cols)

        def _build_csv():
            output = io.BytesIO()
            csv.write_csv(table, output)
            output.seek(0)
            return output

        csv_buffer = await loop.run_in_executor(None, _build_csv)
        return StreamingResponse(
            _iter_buffer(csv_buffer),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={dataset_name}.csv"},
        )


@router.get("/export/csv")
async def export_dataset_as_csv(
    path: str,
    filter_model: Optional[str] = None,
    sort_model: Optional[str] = None,
):
    """Export a dataset as CSV or ZIP, with optional filtering and sorting.

    Parameters
    ----------
    path : str
        The folder path of the dataset to export.
    filter_model : str, optional
        JSON-encoded MUI filter model (same format as ``/filter/``).
    sort_model : str, optional
        JSON-encoded MUI sort model (same format as ``/filter/``).

    Returns
    -------
    StreamingResponse
        CSV for tabular datasets; ZIP in ImageFolder format for image datasets.
    """
    import os

    try:
        arrow_file_path = f"{path}/dataset/data.arrow"
        if not os.path.exists(arrow_file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset file not found",
            )
        table, _total, _was_filtered = _load_and_filter_table(
            path, filter_model, sort_model
        )
        dataset_name = os.path.basename(path.rstrip("/"))
        return await _build_export_response(table, dataset_name)
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file not found",
        ) from e
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting dataset to CSV",
        ) from e


@router.get("/{dataset_id}/export/csv")
@inject
async def export_dataset_csv_by_id(
    dataset_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Export the entire dataset as a CSV or ZIP file by dataset ID.

    Parameters
    ----------
    dataset_id : int
        ID of the dataset to export.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.

    Returns
    -------
    StreamingResponse
        CSV for tabular datasets; ZIP in ImageFolder format for image datasets.
    """
    import os

    from DashAI.back.core.enums.status import DatasetStatus

    logger.debug("Exporting dataset with id %s to CSV", dataset_id)
    with session_factory() as db:
        try:
            dataset = db.get(Dataset, dataset_id)

            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )
            if dataset.status != DatasetStatus.FINISHED:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Dataset is not in finished state",
                )

            file_path = dataset.file_path
            arrow_file_path = f"{file_path}/dataset/data.arrow"

            if not os.path.exists(arrow_file_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset file not found",
                )

            table, _total, _was_filtered = _load_and_filter_table(file_path, None, None)
            return await _build_export_response(table, dataset.name)

        except HTTPException:
            raise
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
        except Exception as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error exporting dataset as CSV",
            ) from e


@router.post("/preview_with_types")
@inject
async def preview_with_types(
    file: UploadFile = File(...),
    params: str = Form(None),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """
    Load preview AND infer types in a single call.

    Parameters
    ----------
    file : UploadFile
        The file uploaded by the user.
    params : str
        JSON string with parameters for the dataloader.
    component_registry: ComponentRegistry
        Registry that provides metadata and class references for the
        components available in DashAI.

    Returns
    -------
    dict
        A dictionary containing:
        - sample: First 10 rows of the dataset
        - schema: Column types from Arrow
        - inferred_types: Detailed type inference (DashAI types)
        - preview_row_count: Number of rows used for inference
    """
    import contextlib
    import json
    import os
    import shutil
    import tempfile

    import numpy as np
    import pyarrow as pa

    from DashAI.back.types.inf.type_inference import infer_types
    from DashAI.back.types.utils import arrow_to_dashai_schema

    try:
        parsed_params = json.loads(params) if params else {}

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file.filename
        ) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            previewed_bytes = len(content)
            tmp_file_path = tmp_file.name

        try:
            inference_rows = parsed_params.get("inference_rows", 1000)
            use_native_types = parsed_params.get("use_native_types", False)
            dataloader_name = parsed_params.get("dataloader_name")

            if not dataloader_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="dataloader_name is required in params.",
                )

            if dataloader_name not in component_registry:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Dataloader {dataloader_name} not found in registry.",
                )

            dataloader_cls = component_registry[dataloader_name]["class"]
            dataloader = dataloader_cls()

            native_types = None
            should_use_native = (
                use_native_types and dataloader_cls.SUPPORTS_NATIVE_TYPES
            )

            if file.filename.endswith(".zip"):
                allowed_exts = dataloader_cls.SUPPORTED_EXTENSIONS
                extract_dir = tempfile.mkdtemp()
                try:
                    with zipfile.ZipFile(tmp_file_path, "r") as zf:
                        zf.extractall(extract_dir)

                    image_extensions = {
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".bmp",
                        ".gif",
                        ".tiff",
                        ".webp",
                    }
                    matched_file = None
                    has_images = False
                    for root, dirs, files in os.walk(extract_dir):
                        dirs[:] = [
                            d
                            for d in dirs
                            if not d.startswith("__MACOSX") and not d.startswith(".")
                        ]
                        for f in files:
                            if f.startswith("."):
                                continue
                            ext = os.path.splitext(f)[1].lower()
                            if ext in allowed_exts:
                                matched_file = os.path.join(root, f)
                                break
                            if ext in image_extensions:
                                has_images = True
                        if matched_file:
                            break

                    if matched_file is None and has_images:
                        sample_rows, total_images, has_labels = (
                            _build_image_preview_sample(
                                extract_dir, image_extensions, max_rows=5
                            )
                        )
                        shutil.rmtree(extract_dir, ignore_errors=True)
                        os.unlink(tmp_file_path)

                        schema = {
                            "image": {"type": "Image", "dtype": "struct"},
                        }
                        inferred_types = {
                            "image": {"type": "Image", "dtype": "struct"},
                        }
                        if has_labels:
                            schema["label"] = {
                                "type": "Categorical",
                                "dtype": "string",
                            }
                            inferred_types["label"] = {
                                "type": "Categorical",
                                "dtype": "string",
                                "encoder": "one_hot",
                            }

                        return {
                            "sample": sample_rows,
                            "schema": schema,
                            "inferred_types": inferred_types,
                            "preview_row_count": total_images,
                            "types_inferred": False,
                            "previewed_bytes": previewed_bytes,
                        }

                    if matched_file is None:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=(
                                f"ZIP does not contain any file supported by "
                                f"{dataloader_name}."
                            ),
                        )

                    loaded_dataset = dataloader.load_preview(
                        filepath_or_buffer=matched_file,
                        params=parsed_params,
                        n_rows=inference_rows,
                    )

                    if should_use_native:
                        native_types = dataloader.extract_native_types(
                            matched_file, parsed_params
                        )

                finally:
                    with contextlib.suppress(Exception):
                        shutil.rmtree(extract_dir, ignore_errors=True)

            else:
                loaded_dataset = dataloader.load_preview(
                    filepath_or_buffer=tmp_file_path,
                    params=parsed_params,
                    n_rows=inference_rows,
                )

                if should_use_native:
                    native_types = dataloader.extract_native_types(
                        tmp_file_path, parsed_params
                    )

            sample_df = loaded_dataset.head(100)

            table = pa.Table.from_pandas(loaded_dataset)
            arrow_schema = arrow_to_dashai_schema(table)

            if native_types is not None:
                inferred_types = native_types
            else:
                methods = parsed_params.get("methods", ["DashAIPtype"])
                inferred_types = {}

                for method in methods:
                    method_types = infer_types(loaded_dataset, method=method)
                    inferred_types.update(method_types)

            sample_df = sample_df.replace({np.nan: None, np.inf: None, -np.inf: None})
            sample = sample_df.to_dict(orient="records")

            return {
                "sample": sample,
                "schema": arrow_schema,
                "inferred_types": inferred_types,
                "preview_row_count": len(loaded_dataset),
                "types_inferred": True,
                "previewed_bytes": previewed_bytes,
            }

        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load preview with types: {str(e)}",
        ) from e


@router.post("/validate_type_changes")
@inject
async def validate_type_changes(
    file: UploadFile = File(...),
    type_changes: str = Form(...),
    params: str = Form(None),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """
    Validate proposed type changes for dataset columns.
    """
    import json
    import os
    import tempfile

    from DashAI.back.types.type_validation import validate_multiple_type_changes

    try:
        parsed_params = json.loads(params) if params else {}
        parsed_type_changes = json.loads(type_changes)

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file.filename
        ) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            dataloader_name = parsed_params.get("dataloader_name")

            if not dataloader_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="dataloader_name is required in params.",
                )

            if dataloader_name not in component_registry:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Dataloader {dataloader_name} not found",
                )

            dataloader = component_registry[dataloader_name]["class"]()

            sample_df = dataloader.load_preview(
                filepath_or_buffer=tmp_file_path, params=parsed_params, n_rows=1000
            )

            all_valid, errors, resolved_dtypes = validate_multiple_type_changes(
                sample_df, parsed_type_changes
            )

            return {
                "valid": all_valid,
                "errors": errors,
                # A Date column's strptime format is detected from the data, so
                # the frontend learns it here rather than choosing it.
                "resolved_dtypes": resolved_dtypes,
            }

        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate type changes: {str(e)}",
        ) from e
