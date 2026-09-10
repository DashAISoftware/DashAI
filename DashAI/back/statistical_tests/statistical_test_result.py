from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PairwiseResult:
    """Result for a single pairwise comparison in a post-hoc test."""

    run_1: int
    run_2: int
    p_value: float
    significant: bool
    statistic: Optional[float] = field(default=None)


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
