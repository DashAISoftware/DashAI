import logging
from typing import TYPE_CHECKING, Any, Dict, List

from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from kink import di, inject
from sqlalchemy import exc

from DashAI.back.api.api_v1.schemas.explorers_params import Explorer as ExplorerSchema
from DashAI.back.api.api_v1.schemas.explorers_params import (
    ExplorerBase,
    ExplorerCreate,
    ExplorerResultsOptions,
)
from DashAI.back.core.artifacts import PlotOverrideBody, apply_plot_overrides
from DashAI.back.core.enums.status import ExplorerStatus
from DashAI.back.dependencies.database.models import Dataset, Explorer, Notebook

if TYPE_CHECKING:
    from sqlalchemy.orm import Session, sessionmaker

    from DashAI.back.dependencies.registry import ComponentRegistry
    from DashAI.back.exploration.base_explorer import BaseExplorer

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


# Validations
def validate_explorer_params(
    session: "Session",
    component_registry: "ComponentRegistry",
    explorer: Explorer,
    validate_columns: bool = True,
):
    """
    Function to validate explorer parameters.
    It validates:
    - The `exploration_type` against the registered explorers.
    - The `parameters` against the explorer schema.
    - The `dataset_id` and `columns` against the dataset.
    """
    from DashAI.back.dataloaders.classes.dashai_dataset import get_columns_spec

    # validate exploration_type in registered explorers
    if explorer.exploration_type not in component_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exploration type {explorer.exploration_type} not found",
        )

    # validate parameters with class method
    explorer_class: "BaseExplorer" = component_registry[explorer.exploration_type][
        "class"
    ]
    try:
        valid = explorer_class.validate_parameters(explorer.parameters)
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error while validating explorer parameters",
        ) from e

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid parameters for the explorer",
        )

    # validate dataset_id and columns against dataset
    notebook = session.query(Notebook).get(explorer.notebook_id)
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )

    dataset = session.query(Dataset).get(notebook.dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    if validate_columns:
        # validate columns against dataset columns
        dataset_path = f"{notebook.file_path}/dataset"
        columns_spec = get_columns_spec(dataset_path)

        try:
            valid = explorer_class.validate_columns(explorer, columns_spec)
        except Exception as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error while validating explorer columns",
            ) from e
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected columns do not satisfy the explorer's type "
                "constraints",
            )

    return True


def validate_explorer_finished(explorer: Explorer):
    """
    Function to validate if the explorer is finished.

    The exploration is readable when its stored artifacts are on disk, or,
    for explorations created before artifacts were persisted, when the raw
    result file is still there to build them from.
    """
    import pathlib

    from DashAI.back.exploration.artifact_store import has_stored_artifacts

    if explorer.status != ExplorerStatus.FINISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explorer is not finished",
        )

    if has_stored_artifacts(explorer):
        return True

    if (
        explorer.exploration_path is None
        or explorer.exploration_path == ""
        or not pathlib.Path(explorer.exploration_path).exists()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exploration path not found",
        )

    return True


def load_explorer_artifacts(
    explorer: Explorer,
    component_registry: "ComponentRegistry",
    session: "Session",
) -> List[Dict[str, Any]]:
    """Load the stored artifacts of an explorer, backfilling them if missing.

    Parameters
    ----------
    explorer : Explorer
        The explorer database record.
    component_registry : ComponentRegistry
        Registry used only when the artifacts still have to be built.
    session : Session
        Session owning ``explorer``, committed when a backfill happened.

    Returns
    -------
    List[Dict[str, Any]]
        The artifact wire dicts of the exploration.

    Raises
    ------
    HTTPException
        409: the exploration predates stored artifacts and its explorer is no
        longer registered.
        400: the artifacts could not be read or built.
    """
    from DashAI.back.exploration.artifact_store import (
        ensure_artifacts_from_registry,
        has_stored_artifacts,
    )

    had_artifacts = has_stored_artifacts(explorer)
    try:
        artifacts = ensure_artifacts_from_registry(explorer, component_registry)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Explorer {explorer.exploration_type} is not installed and this "
                "exploration has no stored results to render"
            ),
        ) from e
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error while getting explorer results",
        ) from e

    if not had_artifacts:
        session.commit()

    return artifacts


# GET
@router.get("/", response_model=List[ExplorerSchema])
@inject
async def get_explorers(
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    skip: int = 0,
    limit: int = 0,
):
    db: "Session"
    with session_factory() as db:
        explorers = db.query(Explorer)

        if skip > 0:
            explorers = explorers.offset(skip)
        if limit > 0:
            explorers = explorers.limit(limit)

        return explorers.all()


@router.get("/{explorer_id}/", response_model=ExplorerSchema)
@inject
async def get_explorer_by_id(
    explorer_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    db: "Session"
    with session_factory() as db:
        explorer = db.query(Explorer).get(explorer_id)
        if explorer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Explorer not found",
            )
        return explorer


@router.get("/exploration/{exploration_id}/", response_model=List[ExplorerSchema])
@inject
async def get_explorers_by_exploration_id(
    exploration_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    skip: int = 0,
    limit: int = 0,
):
    db: "Session"
    with session_factory() as db:
        explorers = db.query(Explorer).filter(Explorer.exploration_id == exploration_id)

        if skip > 0:
            explorers = explorers.offset(skip)
        if limit > 0:
            explorers = explorers.limit(limit)

        return explorers.all()


# CREATE
@router.post("/", response_model=ExplorerSchema, status_code=status.HTTP_201_CREATED)
@inject
async def create_explorer(
    params: ExplorerCreate,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    db: "Session"
    with session_factory() as db:
        explorer = Explorer(**params.model_dump())
        validate_explorer_params(
            session=db, component_registry=component_registry, explorer=explorer
        )

        db.add(explorer)
        db.commit()
        db.refresh(explorer)
        return explorer


# UPDATE
@router.patch("/{explorer_id}/", response_model=ExplorerSchema)
@inject
async def update_explorer(
    explorer_id: int,
    params: ExplorerBase,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    db: "Session"
    with session_factory() as db:
        explorer = db.query(Explorer).get(explorer_id)
        if explorer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Explorer not found",
            )

        params_dict = params.model_dump()
        for key, value in params_dict.items():
            setattr(explorer, key, value)

        validate_explorer_params(
            session=db,
            component_registry=component_registry,
            explorer=explorer,
            validate_columns=False,
        )

        db.commit()
        db.refresh(explorer)
        return explorer


# DELETE
@router.delete("/{explorer_id}/")
@inject
async def delete_explorer(
    explorer_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    db: Session
    with session_factory() as db:
        explorer = db.query(Explorer).get(explorer_id)
        if explorer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Explorer not found",
            )
        db.delete(explorer)
        explorer.delete_result()

        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)


# Obtain results
@router.post("/{explorer_id}/results/")
@inject
async def get_explorer_results(
    explorer_id: int,
    params: ExplorerResultsOptions,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    db: "Session"
    with session_factory() as db:
        try:
            explorer_info = db.query(Explorer).get(explorer_id)
            if explorer_info is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Explorer with id {explorer_id} not found",
                )
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error while loading the explorer info",
            ) from e

        # validate explorer status and result path
        validate_explorer_finished(explorer=explorer_info)

        # The artifacts were built when the exploration ran, so no explorer
        # class is involved here. Explorations created before artifacts were
        # persisted are backfilled on this first read.
        artifacts = load_explorer_artifacts(
            explorer=explorer_info,
            component_registry=component_registry,
            session=db,
        )
        # Stored user edits win over the computed figure, and are flagged so
        # the frontend renders them verbatim instead of re-theming them.
        artifacts = apply_plot_overrides(artifacts, explorer_info.plot_overrides)

    return artifacts


@router.put("/{explorer_id}/results/")
@inject
async def update_explorer_results(
    explorer_id: int,
    body: PlotOverrideBody,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Persist an edited plotly figure for one artifact of an exploration.

    The edit is stored on the explorer record keyed by artifact index. The
    stored artifacts file is left untouched, so the computed figure survives
    and ``delete_explorer_results_override`` can restore it.

    Parameters
    ----------
    explorer_id : int
        Id of the explorer whose plot is being edited.
    body : PlotOverrideBody
        The artifact index and the edited plotly figure.
    session_factory : Callable[..., ContextManager[Session]]
        Factory yielding a SQLAlchemy session.

    Returns
    -------
    dict
        A confirmation message.

    Raises
    ------
    HTTPException
        404 if the explorer does not exist.
    """
    import json

    db: "Session"
    with session_factory() as db:
        explorer = db.get(Explorer, explorer_id)
        if explorer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Explorer not found",
            )

        overrides = dict(explorer.plot_overrides or {})
        figure = body.figure
        overrides[str(body.index)] = (
            figure if isinstance(figure, str) else json.dumps(figure)
        )
        explorer.plot_overrides = overrides
        db.commit()

    return {"message": "Explorer results updated successfully"}


@router.delete("/{explorer_id}/results/override/{index}")
@inject
async def delete_explorer_results_override(
    explorer_id: int,
    index: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Remove a stored plot override, reverting to the computed figure.

    Parameters
    ----------
    explorer_id : int
        Id of the explorer.
    index : int
        Artifact index whose override is removed. Removing an index that has
        no override is a no-op.
    session_factory : Callable[..., ContextManager[Session]]
        Factory yielding a SQLAlchemy session.

    Returns
    -------
    dict
        A confirmation message.

    Raises
    ------
    HTTPException
        404 if the explorer does not exist.
    """
    db: "Session"
    with session_factory() as db:
        explorer = db.get(Explorer, explorer_id)
        if explorer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Explorer not found",
            )

        overrides = dict(explorer.plot_overrides or {})
        overrides.pop(str(index), None)
        explorer.plot_overrides = overrides or None
        db.commit()

    return {"message": "Explorer results restored successfully"}
