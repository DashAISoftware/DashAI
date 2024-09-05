import logging
from typing import List

from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from kink import di, inject
from sqlalchemy.orm import Session, sessionmaker

from DashAI.back.api.api_v1.schemas import explorers_params as schemas
from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
from DashAI.back.dependencies.database.models import Dataset, Explorer

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()

# Validations


def validate_explorer_params(session: Session, explorer: Explorer):
    """
    Function to validate explorer parameters.
    It validates the `dataset_id` and `columns` against the dataset.
    """
    dataset = session.query(Dataset).get(explorer.dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    # TODO: validate exploration_type in registered explorers

    # validate columns against dataset columns
    dataset = load_dataset(f"{dataset.file_path}/dataset")
    columns = dataset["train"].column_names
    for col in explorer.columns:
        if col not in columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Column {col} not found in dataset",
            )

    return True


# GET
@router.get("/", response_model=List[schemas.Explorer])
@inject
async def get_explorers(
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
    skip: int = 0,
    limit: int = 15,
):
    db: Session
    with session_factory() as db:
        explorers = db.query(Explorer).offset(skip).limit(limit).all()
        return explorers


@router.get("/{explorer_id}/", response_model=schemas.Explorer)
@inject
async def get_explorer_by_id(
    explorer_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    db: Session
    with session_factory() as db:
        explorer = db.query(Explorer).get(explorer_id)
        if explorer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Explorer not found",
            )
        return explorer


@router.get("/dataset/{dataset_id}/", response_model=List[schemas.Explorer])
@inject
async def get_explorers_by_dataset_id(
    dataset_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    db: Session
    with session_factory() as db:
        explorers = db.query(Explorer).filter(Explorer.dataset_id == dataset_id).all()
        return explorers


# CREATE
@router.post("/", response_model=schemas.Explorer)
@inject
async def create_explorer(
    params: schemas.ExplorerCreate,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    db: Session
    with session_factory() as db:
        explorer = Explorer(**params.model_dump())
        _ = validate_explorer_params(session=db, explorer=explorer)

        db.add(explorer)
        db.commit()
        db.refresh(explorer)
        return explorer


@router.post("/dataset/{dataset_id}/", response_model=schemas.Explorer)
@inject
async def create_explorer_by_dataset_id(
    params: schemas.ExplorerBase,
    dataset_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    db: Session
    with session_factory() as db:
        explorer = Explorer(**params.model_dump(), dataset_id=dataset_id)
        _ = validate_explorer_params(session=db, explorer=explorer)

        db.add(explorer)
        db.commit()
        db.refresh(explorer)
        return explorer


@router.get("/dataset/{dataset_id}/describe/")
@inject
async def describe_dataset(
    dataset_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    db: Session
    with session_factory() as db:
        dataset: Dataset = db.query(Dataset).get(dataset_id)
        loaded_dataset = load_dataset(f"{dataset.file_path}/dataset")
        describe = loaded_dataset["train"].to_pandas().describe().to_dict()
        return describe


# DELETE
@router.delete("/{explorer_id}/")
@inject
async def delete_explorer(
    explorer_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
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
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
