import logging

from beartype.typing import List, Union
from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from kink import di, inject
from sqlalchemy.orm import Session, sessionmaker

from DashAI.back.api.api_v1.schemas import exploration_params as schemas
from DashAI.back.dependencies.database.models import Dataset, Exploration, Explorer

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


# validations
def validate_exploration_params(
    params: schemas.ExplorationCreate,
    session: Session,
):
    """
    Function to validate exploration parameters.
    It validates:
    - The `dataset_id` and `columns` against the dataset.
    """
    dataset = session.query(Dataset).get(params.dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    return True


@router.get("/", response_model=List[schemas.Exploration])
@inject
async def get_explorations(
    dataset_id: Union[int, None] = None,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
    skip: int = 0,
    limit: int = 0,
):
    """
    Get all explorations.
    """
    db: Session
    with session_factory() as db:
        if dataset_id is not None:
            explorations = db.query(Exploration).filter(
                Exploration.dataset_id == dataset_id
            )
        else:
            explorations = db.query(Exploration)

        if skip > 0:
            explorations = explorations.offset(skip)
        if limit > 0:
            explorations = explorations.limit(limit)

        return explorations.all()


@router.get("/{exploration_id}/", response_model=schemas.Exploration)
async def get_exploration_by_id(
    exploration_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """
    Get an exploration by id.
    """
    db: Session
    with session_factory() as db:
        exploration = db.query(Exploration).get(exploration_id)
        if exploration is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exploration not found",
            )
        return exploration


@router.get("/dataset/{dataset_id}/", response_model=List[schemas.Exploration])
async def get_explorations_by_dataset_id(
    dataset_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
    skip: int = 0,
    limit: int = 0,
):
    """
    Get all explorations by dataset.
    """
    db: Session
    with session_factory() as db:
        explorations = db.query(Exploration).filter(
            Exploration.dataset_id == dataset_id
        )

        if skip > 0:
            explorations = explorations.offset(skip)
        if limit > 0:
            explorations = explorations.limit(limit)

        return explorations.all()


@router.post(
    "/", response_model=schemas.Exploration, status_code=status.HTTP_201_CREATED
)
@inject
async def create_exploration(
    params: schemas.ExplorationCreate,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """
    Create an exploration.
    """
    db: Session
    with session_factory() as db:
        exploration = Exploration(**params.model_dump())
        validate_exploration_params(exploration, db)

        db.add(exploration)
        db.commit()
        db.refresh(exploration)
        return exploration


@router.patch("/{exploration_id}/", response_model=schemas.Exploration)
@inject
async def update_exploration(
    exploration_id: int,
    params: schemas.ExplorationBase,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """
    Update an exploration by id.
    """
    db: Session
    with session_factory() as db:
        exploration = db.query(Exploration).get(exploration_id)
        if exploration is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exploration not found",
            )

        params_dict = params.model_dump()
        for key, value in params_dict.items():
            setattr(exploration, key, value)

        db.commit()
        db.refresh(exploration)
        return exploration


@router.delete("/{exploration_id}/", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_exploration(
    exploration_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """
    Delete an exploration by id.
    """
    db: Session
    with session_factory() as db:
        exploration = db.query(Exploration).get(exploration_id)
        if exploration is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exploration not found",
            )

        # delete explorers and their results
        explorers = db.query(Explorer).filter(Explorer.exploration_id == exploration_id)
        for explorer in explorers:
            db.delete(explorer)
            explorer.delete_result()

        db.delete(exploration)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
