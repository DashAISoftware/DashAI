from enum import Enum

from statsmodels.stats.multitest import multipletests


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
