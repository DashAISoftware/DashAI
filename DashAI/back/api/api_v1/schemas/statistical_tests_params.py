"""Schemas for statistical tests endpoints."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    p_value: float
    significant: bool


class StatisticalTestResponse(BaseModel):
    """Response schema for statistical test results."""

    test_name: str
    statistic: Optional[float] = None
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

    statistic: Optional[float] = None
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
