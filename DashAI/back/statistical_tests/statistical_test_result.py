from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PairwiseResult:
    """Result for a single pairwise comparison in a post-hoc test."""

    run_1: int
    run_2: int
    # None when the comparison could not be computed (see ``error``)
    p_value: Optional[float]
    significant: bool
    statistic: Optional[float] = field(default=None)
    # Short reason shown in place of the p-value when this pair is undefined
    error: Optional[str] = field(default=None)


@dataclass
class StatisticalTestResult:
    """
    Result of a statistical test, including post-hoc pairwise
    comparisons if applicable.
    """

    statistic: float
    p_value: float
    significant: bool
    alpha: float
    details: dict
    # Populated by post-hoc tests (Nemenyi, Tukey HSD)
    # None for pairwise tests (Wilcoxon, paired t-test)
    posthoc: Optional[list[PairwiseResult]] = field(default=None)
