"""Schemas for statistical tests endpoints."""

import math
from datetime import datetime
from typing import Annotated, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer


def _serialize_statistic(value: Optional[float]) -> Optional[Union[float, str]]:
    """Send infinite statistics as strings, since JSON has no infinity.

    By default Pydantic serializes inf as null, which hides valid results such
    as an ANOVA where every model is constant but the models differ. The
    frontend parses "Infinity" / "-Infinity" back with Number().
    """
    if value is not None and math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"
    return value


Statistic = Annotated[
    Optional[float], PlainSerializer(_serialize_statistic, when_used="json")
]


class StatisticalTestRequest(BaseModel):
    """Request schema for running a statistical test."""

    test_name: str
    metric_name: str
    metric_split: str
    run_ids: List[int]
    run_names: Dict[
        str, str
    ]  # Mapping of run_id to run_name (e.g. {"1": "Model A", "2": "Model B"})
    fold_metrics: Dict[str, List[float]]
    alpha: Optional[float] = 0.05
    # Extra kwargs forwarded to the test's run() method (e.g. alternative)
    params: Optional[Dict] = {}


class PairwiseResultResponse(BaseModel):
    """Single pairwise comparison result from a post-hoc test."""

    run_1: int
    run_1_name: Optional[str] = None
    run_2: int
    run_2_name: Optional[str] = None
    # None when the comparison could not be computed (see ``error``)
    p_value: Optional[float] = None
    significant: bool
    # Short reason shown in place of the p-value for an undefined pair
    error: Optional[str] = None


class StatisticalTestResponse(BaseModel):
    """Response schema for statistical test results."""

    test_name: str
    statistic: Statistic = None
    p_value: Optional[float] = None
    significant: bool
    alpha: float
    details: Optional[Dict] = None
    # Populated for post-hoc tests (Nemenyi, Tukey, PairwiseWilcoxon)
    posthoc: Optional[List[PairwiseResultResponse]] = None
    # Interpretation message from the test's metadata
    interpretation: Optional[str] = None


class StatisticalTestParams(BaseModel):
    """Result the user chose to save"""

    test_name: str
    metric_name: str
    metric_split: str
    alpha: float
    significant: bool

    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)

    run_ids: List[int] = []
    run_names: Dict[str, str] = {}

    statistic: Statistic = None
    p_value: Optional[float] = None
    interpretation: Optional[str] = None

    params: Optional[Dict] = None
    details: Optional[Dict] = None
    posthoc: Optional[List[Dict]] = None

    group_id: Optional[str] = None
    model_session_id: Optional[int] = None


class StatisticalTestRead(StatisticalTestParams):
    """A stored result returned by the API"""

    id: int
    created: datetime

    model_config = ConfigDict(from_attributes=True)
