import logging
from dataclasses import asdict
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from kink import di, inject
from sqlalchemy import exc, select

from DashAI.back.api.api_v1.schemas.explainers_params import (
    GlobalExplainerParams,
    LocalExplainerParams,
    ValidateDatasetParams,
    ValidDatasetsParams,
)
from DashAI.back.core.artifacts import (
    Artifact,
    ArtifactGroup,
    GroupedArtifacts,
    PlotOverrideBody,
    apply_plot_overrides,
)
from DashAI.back.core.enums.status import ExplainerStatus
from DashAI.back.dependencies.database.models import (
    Dataset,
    GlobalExplainer,
    LocalExplainer,
    ModelSession,
    Run,
)
from DashAI.back.splitters.splits_payload import run_splits

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

    from DashAI.back.dependencies.registry.component_registry import ComponentRegistry

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


def _resolve_story_explainer(
    explainer_name: str,
    parameters: dict | None,
    component_registry: "ComponentRegistry",
):
    """Instantiate an explainer to compute stories, without its trained model.

    ``story()`` only needs the explanation dict already computed by the job
    and the explainer's own configuration parameters, never the trained
    model, so this avoids reloading it just to narrate an existing plot.

    Parameters
    ----------
    explainer_name : str
        Registered component name of the explainer (e.g. ``"KernelShap"``).
    parameters : dict or None
        The explainer's configuration parameters, as stored in the database.
    component_registry : ComponentRegistry
        Registry used to resolve ``explainer_name`` to its class.

    Returns
    -------
    BaseGlobalExplainer or BaseLocalExplainer or None
        The explainer instance, or ``None`` if it could not be built (logged,
        never raised: a story is a nice-to-have, not required to see a plot).
    """
    try:
        explainer_class = component_registry[explainer_name]["class"]
        return explainer_class(model=None, **(parameters or {}))
    except Exception as e:
        log.warning("Could not build '%s' to compute its story: %s", explainer_name, e)
        return None


def _as_group_target(value) -> ArtifactGroup:
    """Coerce a raw group into a real (unvalidated) ``ArtifactGroup``.

    ``explainer_job.py`` always runs ``plot()``'s output through
    ``normalize_artifacts`` *before* pickling it, so ``value`` is normally
    a wire-format dict (``{"title": ..., "artifacts": [...]}``), not the
    live ``ArtifactGroup`` ``plot()`` returned. Global explainers'
    ``story()`` implementations tell a group from a lone top-level artifact
    via ``isinstance(x, ArtifactGroup)``, so a generic ``.title``-only shim
    would silently fail that check — ``model_construct`` builds a real
    instance (skipping validation, since we only need ``.title`` and the
    dict's artifacts may carry stray keys like ``"index"`` anyway).

    Parameters
    ----------
    value : ArtifactGroup or dict
        The raw group, as loaded straight from the pickle.

    Returns
    -------
    ArtifactGroup
        ``value`` unchanged if already one, otherwise a group exposing the
        dict's ``"title"``.
    """
    if isinstance(value, ArtifactGroup):
        return value
    title = value.get("title") if isinstance(value, dict) else None
    return ArtifactGroup.model_construct(title=title, artifacts=[])


def _as_artifact_target(value) -> Artifact:
    """Coerce a raw top-level (ungrouped) item into a real ``Artifact``.

    Mirrors :func:`_as_group_target` for the lone-artifact case (e.g. the
    single bar chart a regression permutation-importance explainer
    returns, with no "Top N" selector around it).

    Parameters
    ----------
    value : Artifact or dict
        The raw artifact, as loaded straight from the pickle.

    Returns
    -------
    Artifact
        ``value`` unchanged if already one, otherwise an artifact exposing
        the dict's ``"title"``.
    """
    if isinstance(value, Artifact):
        return value
    title = value.get("title") if isinstance(value, dict) else None
    return Artifact.model_construct(title=title)


def _attach_one_story(
    explainer, explanation: dict, raw_output, wire_item: dict
) -> None:
    """Call ``explainer.story()`` for one artifact and embed it in its wire dict.

    Parameters
    ----------
    explainer : BaseGlobalExplainer or BaseLocalExplainer
        The explainer instance to narrate with.
    explanation : dict
        The explanation dictionary passed through to ``story()``.
    raw_output : Artifact or ArtifactGroup
        The artifact/group identifying what to narrate — already coerced
        by :func:`_as_group_target`/:func:`_as_artifact_target`.
    wire_item : dict
        The corresponding wire-format dict; mutated in place with a
        ``"story"`` key holding ``{"en": ..., "es": ..., ...}`` or ``None``.
    """
    try:
        story = explainer.story(explanation, raw_output)
    except Exception as e:
        log.warning("Story generation failed: %s", e)
        story = None
    wire_item["story"] = asdict(story) if story is not None else None


def _is_grouped_raw(value) -> bool:
    """Match ``normalize_artifacts``' own notion of "already grouped".

    True for a live ``GroupedArtifacts`` instance, but also — the normal
    case, since ``explainer_job.py`` always normalizes before pickling —
    for a wire-format dict (``{"type": "grouped", ...}``).

    Parameters
    ----------
    value : Any
        A raw item from a pickled ``plot()``/``explain*`` result.

    Returns
    -------
    bool
        Whether ``normalize_artifacts`` would treat this as a grouped item.
    """
    return isinstance(value, GroupedArtifacts) or (
        isinstance(value, dict) and value.get("type") == "grouped"
    )


def _attach_stories(
    normalized: list,
    raw: list,
    explanation: dict,
    explainer,
    create_grouped: bool = False,
) -> None:
    """Attach a per-language ``"story"`` dict to every matching wire artifact.

    Walks ``raw`` (the pickled artifacts/groups returned by ``plot()``,
    normally already wire-format dicts — see :func:`_as_story_target`) and
    ``normalized`` (their wire-format counterparts, in the same order) in
    lockstep, so each can be passed to ``explainer.story()`` alongside the
    artifact it actually describes. A no-op if ``explainer`` is ``None`` (it
    couldn't be built). Never raises: a group whose raw shape does not match
    what ``story()`` expects just gets no story, handled inside
    :func:`_attach_one_story`.

    Parameters
    ----------
    normalized : list
        Wire-format dicts from ``normalize_artifacts``; mutated in place.
    raw : list
        The pickled artifacts/groups ``normalized`` was built from.
    explanation : dict
        The explanation dictionary passed through to ``story()``.
    explainer : BaseGlobalExplainer or BaseLocalExplainer or None
        The explainer instance to narrate with.
    create_grouped : bool
        Must match the flag passed to ``normalize_artifacts``: when ``True``
        and ``raw`` is a flat list of leaf artifacts, ``normalized`` was
        collapsed into a single synthetic grouped item (one group per leaf).
    """
    if explainer is None:
        return

    # Mirror normalize_artifacts' own wrapping: explanations persisted before
    # explainer_job.py started normalizing prior to pickling (58c6262dc) still
    # have `raw` in this bare, unwrapped shape on disk.
    if isinstance(raw, (str, dict, Artifact, GroupedArtifacts)):
        raw = [raw]

    if create_grouped and raw and not _is_grouped_raw(raw[0]):
        wire_groups = normalized[0].get("groups", []) if normalized else []
        for raw_leaf, wire_group in zip(raw, wire_groups, strict=True):
            _attach_one_story(
                explainer, explanation, _as_artifact_target(raw_leaf), wire_group
            )
        return

    for raw_item, wire_item in zip(raw, normalized, strict=True):
        if _is_grouped_raw(raw_item):
            raw_groups = (
                raw_item.groups
                if isinstance(raw_item, GroupedArtifacts)
                else raw_item.get("groups", [])
            )
            wire_groups = wire_item.get("groups", [])
            for raw_group, wire_group in zip(raw_groups, wire_groups, strict=True):
                _attach_one_story(
                    explainer, explanation, _as_group_target(raw_group), wire_group
                )
        else:
            _attach_one_story(
                explainer, explanation, _as_artifact_target(raw_item), wire_item
            )


@router.get("/global")
@inject
async def get_global_explainers(
    run_id: int = None,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Returns the global explainers in the database.

    Parameters
    ----------
    run_id: int, optional
        Run id to select the global explanations to retrieve.
        If not provided, returns all global explainers.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A list of dicts containing global explainers.

    Raises
    ------
    HTTPException
        If there's a database error.
    """
    with session_factory() as db:
        try:
            if run_id is not None:
                # Filter by run_id
                global_explainers = db.scalars(
                    select(GlobalExplainer).where(GlobalExplainer.run_id == run_id)
                ).all()
            else:
                # Return all global explainers
                global_explainers = db.scalars(select(GlobalExplainer)).all()

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return global_explainers


@router.get("/global/{explainer_id}")
@inject
async def get_global_explanation(
    explainer_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Returns the global explanation associated with id explainer_id.

    Parameters
    ----------
    explaniner_id: int
        Id to select the global explanation to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A JSON with the explanation.

    Raises
    ------
    HTTPException
        If there is no global explanation associated with the explanation_id in the
        database.
    """
    import pickle

    with session_factory() as db:
        try:
            global_explainer = db.scalars(
                select(GlobalExplainer).where(GlobalExplainer.id == explainer_id)
            ).all()

            if not global_explainer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer not found",
                )

            if global_explainer[0].status != ExplainerStatus.FINISHED:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explaination not found",
                )

            explanation_path = global_explainer[0].explanation_path

            with open(explanation_path, "rb") as file:
                explanation = pickle.load(file)

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return explanation


@router.get("/global/plot/{explainer_id}")
@inject
async def get_global_explanation_plot(
    explainer_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Returns the global explanation plot associated with id explainer_id.

    Parameters
    ----------
    explaniner_id: int
        Id to select the global explanation plot to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.
    component_registry : ComponentRegistry
        Registry used to resolve the explainer's class, needed to compute a
        story for explainers that implement one.

    Returns
    -------
    List[dict]
        A list of artifact dicts (``{"type", "payload", "title"}``) with the
        explanation plots. Explainers that implement ``story()`` also carry a
        ``"story"`` key (``{"en": ..., "es": ..., ...}`` or ``None``),
        computed fresh on every call rather than persisted.

    Raises
    ------
    HTTPException
        If there is no global explanation associated with the explanation_id in the
        database.
    """
    import pickle

    from DashAI.back.core.artifacts import normalize_artifacts

    with session_factory() as db:
        try:
            global_explainer = db.scalars(
                select(GlobalExplainer).where(GlobalExplainer.id == explainer_id)
            ).all()

            if not global_explainer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer not found",
                )

            if global_explainer[0].status != ExplainerStatus.FINISHED:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explaination plot not found",
                )

            plot_path = global_explainer[0].plot_path
            plot_overrides = global_explainer[0].plot_overrides
            explanation_path = global_explainer[0].explanation_path
            explainer_name = global_explainer[0].explainer_name
            parameters = global_explainer[0].parameters

            with open(plot_path, "rb") as file:
                plot = pickle.load(file)
            with open(explanation_path, "rb") as file:
                explanation = pickle.load(file)

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    artifacts = apply_plot_overrides(normalize_artifacts(plot), plot_overrides)
    story_explainer = _resolve_story_explainer(
        explainer_name, parameters, component_registry
    )
    try:
        _attach_stories(artifacts, plot, explanation, story_explainer)
    except Exception as e:
        log.warning("Skipping stories, raw/normalized shapes didn't match: %s", e)
    return artifacts


@router.post("/global", status_code=status.HTTP_201_CREATED)
@inject
async def upload_global_explainer(
    params: GlobalExplainerParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Endpoint to create a global explainer

    Parameters
    ----------
    run_id: int
        Id of the run associated with the explainer
    explainer_name: str
        Selected explainer
    parameters: dict
        Explainer configuration parameters
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    dict
        Dict with the new global explainer.

    Raises
    ------
    HTTPException
        If the explainer cannot be saved to the database.
    """
    with session_factory() as db:
        try:
            run: Run = db.get(Run, params.run_id)
            if not run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
                )

            explainer = GlobalExplainer(
                run_id=params.run_id,
                explainer_name=params.explainer_name,
                parameters=params.parameters,
            )

            db.add(explainer)
            db.commit()
            db.refresh(explainer)

            return explainer

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.delete("/global/{explainer_id}")
@inject
async def delete_global_explainer(
    explainer_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Delete the global explainer with id explanation_id from the database and its
    associated explanation file.

    Parameters
    ----------
    explainer_id : int
        Id of the global explainer to delete.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Raises
    ------
    HTTPException
        If the global explanation with id explanation_id is not registered in the DB.
    """
    import os

    with session_factory() as db:
        try:
            global_explainer = db.get(GlobalExplainer, explainer_id)
            if not global_explainer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer not found",
                )

            if global_explainer.explanation_path is not None:
                os.remove(global_explainer.explanation_path)

            if global_explainer.plot_path is not None:
                os.remove(global_explainer.plot_path)

            db.delete(global_explainer)
            db.commit()

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get("/local")
@inject
async def get_local_explainers(
    run_id: int = None,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Returns the local explainers in the database.

    Parameters
    ----------
    run_id: int, optional
        Run id to select the local explanations to retrieve.
        If not provided, returns all local explainers.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A list of dicts containing local explainers.

    Raises
    ------
    HTTPException
        If there's a database error.
    """
    with session_factory() as db:
        try:
            if run_id is not None:
                # Filter by run_id
                local_explainers = db.scalars(
                    select(LocalExplainer).where(LocalExplainer.run_id == run_id)
                ).all()
            else:
                # Return all local explainers
                local_explainers = db.scalars(select(LocalExplainer)).all()

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return local_explainers


@router.get("/local/{explainer_id}")
@inject
async def get_local_explanation(
    explainer_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Returns the local explanation associated with id explainer_id.

    Parameters
    ----------
    explaniner_id: int
        Id to select the local explanation to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A JSON with the explanation.

    Raises
    ------
    HTTPException
        If there is no local explanation associated with the explanation_id in the
        database.
    """
    import pickle

    with session_factory() as db:
        try:
            local_explainer = db.scalars(
                select(LocalExplainer).where(LocalExplainer.id == explainer_id)
            ).all()

            if not local_explainer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer not found",
                )

            if local_explainer[0].status != ExplainerStatus.FINISHED:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explanation not found",
                )

            explanation_path = local_explainer[0].explanation_path

            with open(explanation_path, "rb") as file:
                explanation = pickle.load(file)

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return explanation


@router.get("/local/plot/{explainer_id}")
@inject
async def get_local_explanation_plot(
    explainer_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Returns the local explanation plot associated with id explainer_id.

    Parameters
    ----------
    explaniner_id: int
        Id to select the local explanation plot to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.
    component_registry : ComponentRegistry
        Registry used to resolve the explainer's class, needed to compute a
        story for explainers that implement one.

    Returns
    -------
    List[dict]
        A list of artifact dicts (``{"type", "payload", "title"}``) with the
        explanation plots, typically one per explained instance. Explainers
        that implement ``story()`` also carry a ``"story"`` key (``{"en":
        ..., "es": ..., ...}`` or ``None``), computed fresh on every call
        rather than persisted.

    Raises
    ------
    HTTPException
        If there is no local explanation associated with the explanation_id in the
        database.
    """
    import pickle

    from DashAI.back.core.artifacts import normalize_artifacts

    with session_factory() as db:
        try:
            local_explainer = db.scalars(
                select(LocalExplainer).where(LocalExplainer.id == explainer_id)
            ).all()

            if not local_explainer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer not found",
                )

            if local_explainer[0].status != ExplainerStatus.FINISHED:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explanation plot not found",
                )

            plots_path = local_explainer[0].plots_path
            plot_overrides = local_explainer[0].plot_overrides
            explanation_path = local_explainer[0].explanation_path
            explainer_name = local_explainer[0].explainer_name
            parameters = local_explainer[0].parameters

            with open(plots_path, "rb") as file:
                plots = pickle.load(file)
            with open(explanation_path, "rb") as file:
                explanation = pickle.load(file)

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    artifacts = apply_plot_overrides(
        normalize_artifacts(plots, create_grouped=True), plot_overrides
    )
    story_explainer = _resolve_story_explainer(
        explainer_name, parameters, component_registry
    )
    try:
        _attach_stories(
            artifacts, plots, explanation, story_explainer, create_grouped=True
        )
    except Exception as e:
        log.warning("Skipping stories, raw/normalized shapes didn't match: %s", e)
    return artifacts


@router.put("/{scope}/plot/{explainer_id}/override")
@inject
async def save_plot_override(
    scope: str,
    explainer_id: int,
    body: PlotOverrideBody,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Persist an edited plotly figure for one artifact of an explanation.

    Parameters
    ----------
    scope : str
        Either "global" or "local".
    explainer_id : int
        Id of the explainer whose plot is being edited.
    body : PlotOverrideBody
        The artifact index and the edited plotly figure.
    session_factory : Callable[..., ContextManager[Session]]
        Factory yielding a SQLAlchemy session.

    Returns
    -------
    dict
        ``{"status": "ok"}`` on success.

    Raises
    ------
    HTTPException
        If the scope is invalid or the explainer does not exist.
    """
    import json

    if scope not in ("global", "local"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid scope"
        )
    model = GlobalExplainer if scope == "global" else LocalExplainer
    with session_factory() as db:
        explainer = db.get(model, explainer_id)
        if explainer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Explainer not found"
            )
        overrides = dict(explainer.plot_overrides or {})
        figure = body.figure
        overrides[str(body.index)] = (
            figure if isinstance(figure, str) else json.dumps(figure)
        )
        explainer.plot_overrides = overrides
        db.commit()
    return {"status": "ok"}


@router.delete("/{scope}/plot/{explainer_id}/override/{index}")
@inject
async def delete_plot_override(
    scope: str,
    explainer_id: int,
    index: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Remove a stored plot override, reverting to the computed figure.

    Parameters
    ----------
    scope : str
        Either "global" or "local".
    explainer_id : int
        Id of the explainer.
    index : int
        Artifact index whose override is removed.
    session_factory : Callable[..., ContextManager[Session]]
        Factory yielding a SQLAlchemy session.

    Returns
    -------
    dict
        ``{"status": "ok"}``.

    Raises
    ------
    HTTPException
        If the scope is invalid or the explainer does not exist.
    """
    if scope not in ("global", "local"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid scope"
        )
    model = GlobalExplainer if scope == "global" else LocalExplainer
    with session_factory() as db:
        explainer = db.get(model, explainer_id)
        if explainer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Explainer not found"
            )
        overrides = dict(explainer.plot_overrides or {})
        overrides.pop(str(index), None)
        explainer.plot_overrides = overrides or None
        db.commit()
    return {"status": "ok"}


@router.post("/local", status_code=status.HTTP_201_CREATED)
@inject
async def upload_local_explainer(
    params: LocalExplainerParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Endpoint to create a local explainer

    Parameters
    ----------
    run_id: int
        Id of the run associated with the explainer
    explainer_name: str
        Selected explainer
    dataset_id: int
        Id of the dataset with the instances to be explained.
    parameters: dict
        Explainer configuration parameters
    parameters: dict
        Explainer fit configuration parameters
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    dict
        Dict with the new local explainer.

    Raises
    ------
    HTTPException
        If the explainer cannot be saved to the database.
    """
    with session_factory() as db:
        try:
            run: Run = db.get(Run, params.run_id)
            if not run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
                )

            explainer = LocalExplainer(
                run_id=params.run_id,
                explainer_name=params.explainer_name,
                dataset_id=params.dataset_id,
                parameters=params.parameters,
                fit_parameters=params.fit_parameters,
                scope=params.scope,
            )

            db.add(explainer)
            db.commit()
            db.refresh(explainer)

            return explainer

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.delete("/local/{explainer_id}")
@inject
async def delete_local_explainer(
    explainer_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Deletes the local explainer with id explanation_id from the database and its
    associated explanation file.

    Parameters
    ----------
    explainer_id : int
        Id of the local explainer to delete.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Raises
    ------
    HTTPException
        If the local explanation with id explanation_id is not registered in the DB.
    """
    import os

    with session_factory() as db:
        try:
            local_explainer = db.get(LocalExplainer, explainer_id)
            if not local_explainer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer not found",
                )

            if local_explainer.explanation_path is not None:
                os.remove(local_explainer.explanation_path)

            if local_explainer.plots_path is not None:
                os.remove(local_explainer.plots_path)

            db.delete(local_explainer)
            db.commit()

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.patch("/")
async def update_explainer() -> None:
    """Update explainer.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.post("/local/validate-dataset")
@inject
async def validate_dataset(
    params: ValidateDatasetParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

    with session_factory() as db:
        try:
            run: Run = db.get(Run, params.run_id)
            if not run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Run not found",
                )
            model_session: ModelSession = db.get(ModelSession, run.model_session_id)
            if not model_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Model session not found",
                )

            dataset: Dataset = db.get(Dataset, params.dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )

            instances = load_dataset(f"{dataset.file_path}/dataset")
            if not instances:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Error while loading the dataset.",
                )

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    validation_response = {}
    input_columns = model_session.input_columns
    output_columns = model_session.output_columns
    required_columns = input_columns + output_columns

    instances_columns = list(instances.features)

    # Check all required columns are present
    missing = [c for c in required_columns if c not in instances_columns]
    if missing:
        validation_response["dataset_status"] = "invalid"
        validation_response["missing_columns"] = missing
        return validation_response

    # Check column types match the original training dataset
    with session_factory() as db:
        try:
            training_dataset: Dataset = db.get(Dataset, model_session.dataset_id)
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    if training_dataset:
        training_instances = load_dataset(f"{training_dataset.file_path}/dataset")
        if training_instances:
            training_types = {
                col: type(t).__name__ for col, t in training_instances.types.items()
            }
            new_types = {col: type(t).__name__ for col, t in instances.types.items()}
            type_mismatches = {
                col: {"expected": training_types[col], "got": new_types[col]}
                for col in required_columns
                if col in training_types
                and col in new_types
                and training_types[col] != new_types[col]
            }
            if type_mismatches:
                validation_response["dataset_status"] = "invalid"
                validation_response["type_mismatches"] = type_mismatches
                return validation_response

    validation_response["dataset_status"] = "valid"
    return validation_response


@router.get("/explainable-splits/{run_id}")
@inject
async def get_explainable_splits(
    run_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Retrieve the dataset partitions of a run that an explainer may target.

    The available partitions depend on how the run was evaluated, so they are
    resolved here rather than assumed by the caller: a holdout run exposes its
    train, test and validation partitions, while a cross-validation run exposes
    its train partition and the rows it reserved as a test set, which are the
    only ones the saved model never saw.

    Parameters
    ----------
    run_id : int
        Id of the run to be explained.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
    component_registry : ComponentRegistry
        Registry used to resolve the splitter that produced the run.

    Returns
    -------
    dict
        A ``splits`` list of ``{"name", "rows"}`` entries, empty when the run has
        no data an explainer may use.

    Raises
    ------
    HTTPException
        If the run does not exist in the database.
    """
    with session_factory() as db:
        try:
            run: Run = db.get(Run, run_id)
            if not run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Run not found",
                )
            model_session: ModelSession = db.get(ModelSession, run.model_session_id)
            if not model_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Model session not found",
                )
            split_indexes = run.split_indexes
            session_splits = model_session.splits
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    try:
        return {"splits": run_splits(session_splits, split_indexes, component_registry)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e


@router.post("/local/valid-datasets")
@inject
async def valid_datasets(
    params: ValidDatasetsParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Return the ids of every dataset that can be explained by a run's model.

    A dataset is valid when it has all the model's input and output columns and
    their types match the training dataset. The run, model session and training
    dataset are loaded once and every dataset is checked in a single request so
    the frontend does not have to validate them one at a time.

    Parameters
    ----------
    params : ValidDatasetsParams
        The run whose model the datasets must be compatible with.

    Returns
    -------
    dict
        ``{"valid_dataset_ids": [...]}`` with the ids of the valid datasets.
    """
    from DashAI.back.dataloaders.classes.dashai_dataset import get_columns_spec

    with session_factory() as db:
        try:
            run: Run = db.get(Run, params.run_id)
            if not run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Run not found",
                )
            model_session: ModelSession = db.get(ModelSession, run.model_session_id)
            if not model_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Model session not found",
                )
            training_dataset: Dataset = db.get(Dataset, model_session.dataset_id)
            datasets = db.scalars(select(Dataset)).all()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    required_columns = model_session.input_columns + model_session.output_columns

    training_types = {}
    if training_dataset:
        try:
            training_spec = get_columns_spec(f"{training_dataset.file_path}/dataset")
            training_types = {
                col: spec.get("type") for col, spec in training_spec.items()
            }
        except Exception as e:
            log.warning(f"Could not read training dataset schema: {e}")

    valid_dataset_ids = []
    for dataset in datasets:
        try:
            columns_spec = get_columns_spec(f"{dataset.file_path}/dataset")
        except Exception as e:
            log.warning(f"Could not read dataset {dataset.id} schema: {e}")
            continue

        if any(col not in columns_spec for col in required_columns):
            continue

        type_mismatch = any(
            col in training_types
            and training_types[col] != columns_spec[col].get("type")
            for col in required_columns
        )
        if type_mismatch:
            continue

        valid_dataset_ids.append(dataset.id)

    return {"valid_dataset_ids": valid_dataset_ids}
