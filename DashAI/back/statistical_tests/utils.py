from enum import Enum
from typing import Optional

import numpy as np
from statsmodels.stats.multitest import multipletests

from DashAI.back.statistical_tests.statistical_test_result import PairwiseResult

# Scores are metric values (roughly on [0, 1]), so anything below this is
# floating-point noise rather than a real difference between folds.
NUMERICAL_TOLERANCE = 1e-12

# Rank-based tests (Wilcoxon, Friedman, Nemenyi) only look at orderings, so a
# floating-point difference such as 0.5 vs 0.5000000000000002 repeated on every
# fold reads as a consistent "win" and can produce a significant result. They
# round scores to this precision first so those differences become ties,
# which these tests handle by design (mid-ranks and tie correction).
RANK_TEST_DECIMALS = 4

# Parametric tests use magnitudes and assume continuous data: rounding to
# RANK_TEST_DECIMALS would add quantization error and could turn stable runs
# into constant ones. Where they need it, they round only enough to drop
# floating-point noise, which has no statistical effect.
FLOAT_NOISE_DECIMALS = 12


class UndefinedTestError(ValueError):
    """The test is mathematically undefined for the given scores.

    Raised for degenerate inputs such as constant scores or constant paired
    differences. It is a problem with the submitted data, not a server fault,
    so the API reports it as 400. It subclasses ValueError so existing
    ``except ValueError`` handlers keep working.

    Args:
        message: Full explanation, shown when the whole test fails.
        summary: Short reason, shown in a table row when only one pairwise
            comparison fails. Defaults to the full message.
    """

    def __init__(self, message: str, summary: Optional[str] = None):
        super().__init__(message)
        self.summary = summary or message


class CorrectionMethod(Enum):
    """Enum for correction methods used in statistical tests."""

    HOLM = "holm"
    BONFERRONI = "bonferroni"
    BENJAMINI_HOCHBERG = "fdr_bh"


def correct_p_values(
    p_values: list[float], method: CorrectionMethod, alpha: float = 0.05
) -> list[dict]:
    """Corrects p-values for multiple comparisons using the specified method.

    Args:
        p_values (list): List of p-values to correct.
        method (CorrectionMethod): The correction method to use.

    Returns:
        list[dict]: List of corrected p-values with additional information.
    """
    return multipletests(p_values, alpha=alpha, method=method.value)[1]


def has_zero_variance(values) -> bool:
    """Return whether the values are constant up to floating-point noise.

    An exact ``== 0`` check is not enough: subtracting two score vectors that
    differ by a constant leaves a variance of ~1e-34 instead of 0, which makes
    t statistics explode to ~1e15 instead of being reported as undefined.

    Args:
        values: Sequence with at least two numeric values.

    Returns:
        bool: True if the sample standard deviation is negligible.
    """
    return bool(np.std(values, ddof=1) <= NUMERICAL_TOLERANCE)


def check_constant_differences(differences, run_1, run_2) -> bool:
    """Detect paired differences that are the same on every fold.

    A t-test is undefined when the paired differences have zero variance.
    If every difference is zero the runs are identical, which the caller
    reports as "no difference". If they share a non-zero value, one model
    beats the other by exactly the same margin on every fold; the test cannot
    quantify that, so an explanatory error is raised.

    Args:
        differences: Fold-wise differences between the scores of both runs.
        run_1: Identifier of the first run, used in the error message.
        run_2: Identifier of the second run, used in the error message.

    Returns:
        bool: True if both runs have identical scores on every fold, False if
        the differences vary (the test is well defined).

    Raises:
        UndefinedTestError: If the differences are constant and non-zero.
    """
    if not has_zero_variance(differences):
        return False

    mean_difference = float(np.mean(differences))
    if abs(mean_difference) <= NUMERICAL_TOLERANCE:
        return True

    raise UndefinedTestError(
        "The scores of runs differ by exactly the same amount "
        "on every fold. The paired differences have "
        "zero variance, so the t-test is undefined. Consider the Wilcoxon "
        "signed-rank test instead.",
        summary=(
            "Same difference on every fold (zero variance), so the t-test is undefined."
        ),
    )


def build_corrected_pairwise_results(
    pairs: list[tuple], correction_method: str, alpha: float
) -> tuple[list[PairwiseResult], bool]:
    """Correct the p-values of the computable pairs and build their results.

    Pairs that could not be computed are kept, in their original position,
    with their error instead of a p-value, and are left out of the
    correction so they do not change the adjusted p-values of the others.

    Args:
        pairs: One ``(run_1, run_2, statistic, p_value, error)`` tuple per
            comparison, where ``error`` is None for computable pairs and
            ``statistic`` / ``p_value`` are None for the rest.
        correction_method: Name of a CorrectionMethod member (e.g. "holm").
        alpha: Significance level.

    Returns:
        tuple[list[PairwiseResult], bool]: The pairwise results and whether
        any computable pair is significant.

    Raises:
        UndefinedTestError: If no pair could be computed.
    """
    valid = [index for index, pair in enumerate(pairs) if pair[4] is None]
    if not valid:
        reasons = dict.fromkeys(pair[4] for pair in pairs)  # unique, in order
        raise UndefinedTestError(
            "None of the pairs of models could be compared. " + " ".join(reasons)
        )

    corrected_p_values = correct_p_values(
        p_values=[pairs[index][3] for index in valid],
        method=CorrectionMethod[correction_method.upper()],
        alpha=alpha,
    )
    corrected_by_index = dict(zip(valid, corrected_p_values, strict=True))

    pairwise = []
    for index, (run_1, run_2, statistic, _, error) in enumerate(pairs):
        if error is not None:
            pairwise.append(
                PairwiseResult(
                    run_1=run_1,
                    run_2=run_2,
                    p_value=None,
                    significant=False,
                    error=error,
                )
            )
            continue

        p_value = float(corrected_by_index[index])
        pairwise.append(
            PairwiseResult(
                run_1=run_1,
                run_2=run_2,
                statistic=statistic,
                p_value=p_value,
                significant=p_value < alpha,
            )
        )

    overall_significant = any(pair.significant for pair in pairwise)
    return pairwise, overall_significant


def check_defined_result(statistic: float, p_value: float, test_name: str) -> None:
    """Raise instead of returning a NaN result.

    NaN compares as False against alpha, so it would silently be reported as
    "not significant". Infinite statistics are valid (e.g. zero within-group
    variance with different group means) and are left untouched.

    Args:
        statistic: Test statistic returned by the test.
        p_value: P-value returned by the test.
        test_name: Display name of the test, used in the error message.

    Raises:
        UndefinedTestError: If the statistic or the p-value is NaN.
    """
    if np.isnan(statistic) or np.isnan(p_value):
        raise UndefinedTestError(
            f"{test_name} is undefined for the given scores (the result is NaN). "
            "Check that the scores are valid numbers and are not constant."
        )
