import logging
from typing import TYPE_CHECKING, Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from kink import di, inject
from sqlalchemy import exc

from DashAI.back.api.api_v1.schemas.pipelines_params import (
    DatasetFilterParams,
    PipelineCreateParams,
    PipelineUpdateParams,
    ValidateNodeParams,
    ValidatePipelineParams,
)
from DashAI.back.core.artifacts import normalize_artifacts
from DashAI.back.dependencies.database.models import Dataset, Pipeline
from DashAI.back.pipeline.validator.nodes_definitions import NODES
from DashAI.back.pipeline.validator.pipeline_validator import PipelineValidator
from DashAI.back.pipeline.validator.validator import VALIDATOR_MAP

if TYPE_CHECKING:
    from sqlalchemy.orm import Session, sessionmaker

    from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
    from DashAI.back.exploration.base_explorer import BaseExplorer

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
@inject
async def get_pipelines(
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Retrieve all pipelines.

    Parameters
    ----------
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[Pipeline]
        A list of all pipelines stored in the database.
    """
    with session_factory() as db:
        try:
            pipelines = db.query(Pipeline).all()
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    return pipelines


@router.get("/nodes")
async def get_nodes() -> List[Dict[str, Any]]:
    """Retrieve pipeline node definitions."""
    try:
        type_to_name = {node.type: node.name for node in NODES}
        nodes_with_next = []
        for node in NODES:
            node_dict = node.model_dump()
            node_dict["next"] = [type_to_name.get(s, s) for s in node.successors]
            nodes_with_next.append(node_dict)
        return nodes_with_next

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load node definitions",
        ) from e


@router.get("/predict_summary")
@inject
async def pipeline_predict_summary(
    pred_name: str = Query(...),
    config: Dict[str, Any] = Depends(lambda: di["config"]),
) -> Dict[str, Any]:
    """Retrieve prediction summary statistics.

    Parameters
    ----------
    pred_name : str
        Name of the prediction file to analyze.

    Returns
    -------
    Dict[str, Any]
        Summary statistics including total data points, data type,
        class distribution (if applicable), and sample data.

    Raises
    ------
    HTTPException
        400: Invalid JSON format or invalid class value.
        404: Prediction file not found.
        500: Internal server error.
    """
    import json
    import os

    sqlite_local = os.path.expanduser(config["LOCAL_PATH"])
    path = os.path.join(sqlite_local, "pipelines", "predictions", pred_name)
    summary = {}

    try:
        with open(path, "r") as f:
            try:
                data = json.load(f)["prediction"]
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=400, detail="Invalid JSON format"
                ) from e

            summary["total_data_points"] = len(data)

            if isinstance(data[0], str):
                summary["data_type"] = "string"
            else:
                summary["data_type"] = "numeric"
                class_set = set(data)
                classes = [str(item) for item in class_set]
                summary["Unique_classes"] = len(classes)
                class_distribution = []
                id = 1
                for class_name in classes:
                    try:
                        occurrences = data.count(int(class_name))
                    except ValueError as e:
                        raise HTTPException(
                            status_code=400, detail=f"Invalid class value: {class_name}"
                        ) from e
                    distribution = {
                        "id": id,
                        "Class": class_name,
                        "Ocurrences": occurrences,
                        "Percentage": round(occurrences / len(data) * 100, 2),
                    }
                    id += 1
                    class_distribution.append(distribution)
                summary["class_distribution"] = class_distribution

            sample_data = [
                {"id": idx, "value": value} for idx, value in enumerate(data[:50], 1)
            ]
            summary["sample_data"] = sample_data
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="Prediction not found") from e
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e)) from e
    return summary


@router.get("/{pipeline_id}")
@inject
async def get_pipeline(
    pipeline_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Retrieve a specific pipeline by ID.

    Parameters
    ----------
    pipeline_id : int
        ID of the pipeline to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Pipeline
        The requested pipeline.

    Raises
    ------
    HTTPException
        404: Pipeline not found.
        500: Internal database error.
    """
    logger.debug("Retrieving pipeline with id %s", pipeline_id)
    with session_factory() as db:
        try:
            pipeline = db.get(Pipeline, pipeline_id)
            if not pipeline:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline not found",
                )
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    return pipeline


@router.get("/{pipeline_id}/dataexploration/results/")
@inject
async def get_pipeline_dataexploration_results(
    pipeline_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Get results for all Data Exploration steps of a pipeline.

    Parameters
    ----------
    pipeline_id : int
        ID of the pipeline to retrieve exploration results from.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
    component_registry : ComponentRegistry
        Registry containing available exploration components.

    Returns
    -------
    dict
        Dictionary containing exploration results for each exploration step.

    Raises
    ------
    HTTPException
        400: Pipeline has no valid Data Exploration step or exploration type not found.
        404: Pipeline not found.
        500: Database error or error retrieving results.
    """
    db: Session = session_factory()

    try:
        pipeline = db.get(Pipeline, pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pipeline with id {pipeline_id} not found",
            )
    except exc.SQLAlchemyError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving pipeline from the database",
        ) from e

    dataexploration = pipeline.exploration
    if not dataexploration or not isinstance(dataexploration, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pipeline has no valid Data Exploration step",
        )

    results = {}

    for exploration_id, exploration_info in dataexploration.items():
        exploration_type = exploration_info["exploration_type"]
        exploration_path = exploration_info["path"]
        parameters = exploration_info.get("parameters", {})
        name = exploration_info.get("name")

        try:
            explorer_component_class = component_registry[exploration_type]["class"]
        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(f"Exploration type '{exploration_type}' not found in registry"),
            ) from e

        try:
            explorer_instance: BaseExplorer = explorer_component_class(**parameters)
            result = explorer_instance.get_results(
                exploration_path=exploration_path,
                options={},
            )
            results[exploration_id] = {
                "exploration_type": exploration_type,
                "results": normalize_artifacts(result),
                "name": name,
            }
        except Exception as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(f"Error while getting results for '{exploration_type}'"),
            ) from e

    return results


@router.post("/", status_code=status.HTTP_201_CREATED)
@inject
async def create_pipeline(
    params: PipelineCreateParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Create a new pipeline.

    Parameters
    ----------
    params : PipelineCreateParams
        Parameters containing pipeline name, steps, and edges.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.

    Returns
    -------
    Pipeline
        The newly created pipeline.

    Raises
    ------
    HTTPException
        400: Empty pipeline (no steps provided).
        500: Internal database error.
    """
    logger.debug("Creating a new pipeline with params: %s", params)
    if not params.steps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty pipeline",
        )

    with session_factory() as db:
        try:
            steps_dict = [
                step.model_dump() if hasattr(step, "model_dump") else step
                for step in params.steps or []
            ]

            new_pipeline = Pipeline(
                name=params.name,
                steps=steps_dict,
                edges=params.edges,
                exploration=None,
                train=None,
                prediction=None,
            )
            db.add(new_pipeline)
            db.commit()
            db.refresh(new_pipeline)

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    return new_pipeline


@router.put("/{pipeline_id}")
@inject
async def update_pipeline(
    pipeline_id: int,
    params: PipelineUpdateParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Update a specific pipeline.

    Parameters
    ----------
    pipeline_id : int
        ID of the pipeline to update.
    params : PipelineUpdateParams
        Parameters containing updated pipeline name, steps, and edges.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.

    Returns
    -------
    Pipeline
        The updated pipeline.

    Raises
    ------
    HTTPException
        400: Empty pipeline (no steps provided).
        404: Pipeline not found.
        500: Internal database error.
    """
    if not params.steps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty pipeline",
        )

    with session_factory() as db:
        try:
            pipeline = db.get(Pipeline, pipeline_id)
            if not pipeline:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline not found",
                )

            pipeline.exploration = None
            pipeline.train = None
            pipeline.prediction = None

            steps_dict = [
                step.model_dump() if hasattr(step, "model_dump") else step
                for step in params.steps or []
            ]

            pipeline.name = params.name or pipeline.name
            pipeline.steps = steps_dict or pipeline.steps
            pipeline.edges = params.edges or pipeline.edges

            db.commit()
            db.refresh(pipeline)

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    return pipeline


@router.delete("/{pipeline_id}")
@inject
async def delete_pipeline(
    pipeline_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Delete a specific pipeline.

    Parameters
    ----------
    pipeline_id : int
        ID of the pipeline to delete.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.

    Returns
    -------
    dict
        Confirmation message that the pipeline was deleted successfully.

    Raises
    ------
    HTTPException
        404: Pipeline not found.
        500: Internal database error.
    """
    logger.debug("Deleting pipeline with id %s", pipeline_id)
    with session_factory() as db:
        try:
            pipeline = db.get(Pipeline, pipeline_id)
            if not pipeline:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline not found",
                )

            db.delete(pipeline)
            db.commit()
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    return {"message": "Pipeline deleted successfully"}


@router.post("/validate_node")
@inject
async def validate_node(
    params: ValidateNodeParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Validate a single node configuration.

    Parameters
    ----------
    params : ValidateNodeParams
        Parameters containing node type and configuration.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.

    Returns
    -------
    dict
        Validation results for the node configuration.

    Raises
    ------
    HTTPException
        400: Unknown node type.
    """
    validator_class = VALIDATOR_MAP.get(params.type)
    if not validator_class:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown node type: {params.type}",
        )

    with session_factory() as db:
        validator = validator_class(params.config, db)
        return validator.validate()


@router.post("/validate_pipeline")
@inject
async def validate_pipeline(
    params: ValidatePipelineParams,
):
    """Validate a pipeline configuration.

    Parameters
    ----------
    params : ValidatePipelineParams
        Parameters containing nodes and edges.

    Returns
    -------
    dict
        Validation results for the pipeline configuration.
    """
    validator = PipelineValidator(params.nodes, params.edges)
    return validator.validate()


@router.post("/filter_models")
async def filter_models_endpoint(
    params: DatasetFilterParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Filter pipelines to find compatible models for a given dataset.

    Parameters
    ----------
    params : DatasetFilterParams
        Parameters containing dataset ID and optional pipeline ID to exclude.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.

    Returns
    -------
    List[Pipeline]
        List of pipelines with compatible models for the given dataset.

    Raises
    ------
    HTTPException
        404: Dataset not found.
        500: Error filtering pipelines.
    """
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import get_columns_spec

    try:
        with session_factory() as db:
            base_dataset = db.get(Dataset, params.dataset_id)
            if not base_dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )

            base_spec = get_columns_spec(str(Path(base_dataset.file_path, "dataset")))

            pipelines = db.query(Pipeline).all()

            compatible_pipelines = []

            for pipeline in pipelines:
                if params.pipeline_id and pipeline.id == params.pipeline_id:
                    continue

                if not pipeline.train:
                    continue

                steps = pipeline.steps
                dataset_path = None
                dataset_spec = None

                for step in steps:
                    if step["type"] == "DataSelector":
                        dataset_path = step["config"]["file_path"]
                        dataset_spec = get_columns_spec(
                            str(Path(dataset_path, "dataset"))
                        )

                if dataset_spec == base_spec:
                    compatible_pipelines.append(pipeline)

            return compatible_pipelines

    except Exception as e:
        logger.exception("Error filtering pipelines: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=("An error occurred while filtering pipelines"),
        ) from e
