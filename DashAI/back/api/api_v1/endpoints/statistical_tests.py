"""Statistical tests endpoints"""

import logging
from typing import TYPE_CHECKING, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from kink import di, inject
from sqlalchemy import exc, select

from DashAI.back.api.api_v1.schemas.statistical_tests_params import (
    PairwiseResultResponse,
    StatisticalTestParams,
    StatisticalTestRead,
    StatisticalTestRequest,
    StatisticalTestResponse,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import StatisticalTest
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.statistical_tests.base_statistical_test import BaseStatisticalTest
from DashAI.back.statistical_tests.statistical_test_result import StatisticalTestResult

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


def _get_interpretation(
    metadata: Optional[Dict],
    significant: bool,
    accept_language: Optional[str] = None,
) -> Optional[str]:
    """Extract test interpretation from metadata based on result significance.

    Parameters
    ----------
    metadata : Optional[Dict]
        Test metadata containing interpretation MultilingualString
    significant : bool
        Whether the test result is significant
    accept_language : Optional[str]
        Language code from Accept-Language header (e.g., 'en', 'es', 'pt')

    Returns
    -------
    Optional[str]
        Localized interpretation message or None if not available
    """
    if not metadata or "interpretation" not in metadata:
        return None

    interpretation = metadata["interpretation"]
    if not isinstance(interpretation, MultilingualString):
        return None

    # Extract language code from header (e.g., 'en' from 'en-US')
    lang_code = "en"
    if accept_language:
        lang_code = accept_language.split("-")[0].lower()

    # Get the interpretation for the appropriate outcome (significant/not_significant)
    outcome = "significant" if significant else "not_significant"

    try:
        # interpretation is a MultilingualString where each language maps to a dict
        # with 'significant' and 'not_significant' keys
        lang_dict = interpretation.get(lang_code)
        if isinstance(lang_dict, dict) and outcome in lang_dict:
            return lang_dict[outcome]
    except (AttributeError, KeyError, TypeError):
        pass

    return None


@router.post(
    "/run",
    response_model=StatisticalTestResponse,
    status_code=status.HTTP_200_OK,
)
async def run_statistical_test(
    request: StatisticalTestRequest,
    accept_language: Optional[str] = Header(default=None),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
) -> StatisticalTestResponse:
    """Run a statistical test on fold metrics from selected runs.

    Automatically runs the appropriate post-hoc test (Nemenyi after Friedman,
    Tukey HSD after ANOVA) when the primary test is significant.
    PairwiseWilcoxon already includes pairwise comparisons with Holm correction
    and does not require a separate post-hoc step.

    Parameters
    ----------
    request : StatisticalTestRequest
        Request containing test name, metric, run IDs, fold metrics, alpha,
        and optional extra params (e.g. alternative hypothesis).

    Returns
    -------
    StatisticalTestResponse
        Test result including statistic, p-value, interpretation,
        and optional pairwise post-hoc results.

    Raises
    ------
    HTTPException
        400 if the test name is unknown or inputs are invalid.
        500 on internal error.
    """
    try:
        if not request.fold_metrics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fold_metrics cannot be empty",
            )

        # Resolve test class from registry
        try:
            test_instance: BaseStatisticalTest = component_registry[request.test_name][
                "class"
            ]()
        except KeyError as key_error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown statistical test: '{request.test_name}'. ",
            ) from key_error

        # Build scores dict keyed by run name for readability in results
        # Use run_id as key if no name mapping is available
        scores: Dict[str, List[float]] = {
            run_id: request.fold_metrics[str(run_id)]
            for run_id in request.run_ids
            if str(run_id) in request.fold_metrics
        }

        # Run the primary test, forwarding any extra params
        result: StatisticalTestResult = test_instance.run(
            scores=scores,
            alpha=request.alpha,
            **(request.params or {}),
        )

        # Run post-hoc automatically if the primary test is significant
        # and a post-hoc exists for this test
        posthoc = component_registry.get_related_components(request.test_name)

        posthoc_results = None
        if result.significant and posthoc:
            try:
                posthoc_instance: BaseStatisticalTest = posthoc[0]["class"]()

                # Pass precalculated omnibus values to avoid recomputing
                posthoc_result: StatisticalTestResult = posthoc_instance.run(
                    scores=scores,
                    alpha=request.alpha,
                    statistic=result.statistic,
                    p_value=result.p_value,
                )

                posthoc_results = [
                    PairwiseResultResponse(
                        run_1=pr.run_1,
                        run_1_name=request.run_names.get(str(pr.run_1), None),
                        run_2=pr.run_2,
                        run_2_name=request.run_names.get(str(pr.run_2), None),
                        p_value=pr.p_value,
                        significant=pr.significant,
                    )
                    for pr in posthoc_result.posthoc
                ]
            except Exception as e:
                log.warning(f"Post-hoc test failed, skipping: {str(e)}")

        # If the primary test saved results as posthoc (multiple pairwise comparisons)
        elif result.posthoc:
            posthoc_results = [
                PairwiseResultResponse(
                    run_1=pr.run_1,
                    run_1_name=request.run_names.get(str(pr.run_1), None),
                    run_2=pr.run_2,
                    run_2_name=request.run_names.get(str(pr.run_2), None),
                    p_value=pr.p_value,
                    significant=pr.significant,
                )
                for pr in result.posthoc
            ]

        log.info(
            f"Statistical test '{request.test_name}' completed: "
            f"p={result.p_value}, significant={result.significant}"
        )

        # Get test metadata for interpretation
        test_metadata = None
        try:
            test_component = component_registry[request.test_name]
            test_metadata = test_component.get("metadata")
        except (KeyError, AttributeError):
            pass

        # Extract interpretation based on result significance
        interpretation = _get_interpretation(
            test_metadata, result.significant, accept_language
        )

        details = {
            "run_names": request.run_names,
            "scores": scores,
        }

        return StatisticalTestResponse(
            test_name=request.test_name,
            statistic=result.statistic,
            p_value=result.p_value,
            significant=result.significant,
            alpha=result.alpha,
            details=details,
            posthoc=posthoc_results,
            interpretation=interpretation,
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error running statistical test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running statistical test: {str(e)}",
        ) from e


@router.post(
    "/save",
    response_model=List[StatisticalTestRead],
    status_code=status.HTTP_201_CREATED,
)
@inject
async def save_statistical_tests(
    items: List[StatisticalTestParams],
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Persist one or more statistical test results chosen by the user.

    Accepts a list so a single omnibus result ([1 item]) and a per-run batch
    (e.g. Shapiro, [N items]) share the same path. When more than one item is
    sent and no group_id is provided, a shared group_id is generated so the
    batch can be retrieved together.

    Parameters
    ----------
    items : List[StatisticalTestParams]
        Results to store (assembled client-side from the displayed result).
    session_factory : Callable[..., ContextManager[Session]]
        Factory that yields a context-managed SQLAlchemy session.

    Returns
    -------
    List[StatisticalTest]
        The persisted rows.

    Raises
    ------
    HTTPException
        400 if the list is empty, 500 on a database error.
    """
    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No results to save.",
        )

    with session_factory() as db:
        try:
            batch_group_id = uuid4().hex if len(items) > 1 else None

            rows = []
            for item in items:
                row = StatisticalTest(**item.model_dump())
                if batch_group_id and not row.group_id:
                    row.group_id = batch_group_id
                db.add(row)
                rows.append(row)

            db.commit()
            for row in rows:
                db.refresh(row)
            return rows
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get(
    "/saved",
    response_model=List[StatisticalTestRead],
)
@inject
async def list_saved_statistical_tests(
    model_session_id: Optional[int] = None,
    group_id: Optional[str] = None,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """List saved results, optionally filtered by model session or batch group.

    Parameters
    ----------
    model_session_id : Optional[int]
        If given, only results tied to that model session are returned.
    group_id : Optional[str]
        If given, only results of that batch are returned.
    session_factory : Callable[..., ContextManager[Session]]
        Factory that yields a context-managed SQLAlchemy session.

    Returns
    -------
    List[StatisticalTest]
        Stored results, most recent first.
    """
    with session_factory() as db:
        try:
            stmt = select(StatisticalTest)
            if model_session_id is not None:
                stmt = stmt.where(StatisticalTest.model_session_id == model_session_id)
            if group_id is not None:
                stmt = stmt.where(StatisticalTest.group_id == group_id)
            stmt = stmt.order_by(StatisticalTest.created.desc())
            return db.scalars(stmt).all()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.delete("/saved/{result_id}")
@inject
async def delete_saved_statistical_test(
    result_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Delete a saved statistical test result by id.

    Parameters
    ----------
    result_id : int
        ID of the stored result to delete.
    session_factory : Callable[..., ContextManager[Session]]
        Factory that yields a context-managed SQLAlchemy session.

    Returns
    -------
    dict
        {"deleted": True, "id": <result_id>}.

    Raises
    ------
    HTTPException
        404 if not found, 500 on a database error.
    """
    with session_factory() as db:
        try:
            row = db.get(StatisticalTest, result_id)
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Saved statistical test not found",
                )
            db.delete(row)
            db.commit()
            return {"deleted": True, "id": result_id}
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
