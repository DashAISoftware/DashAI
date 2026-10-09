from DashAI.back.core.utils import MultilingualString
from DashAI.back.statistical_tests.base_statistical_test import BaseStatisticalTest
from DashAI.back.statistical_tests.statistical_test_result import (
    PairwiseResult,
    StatisticalTestResult,
)
from DashAI.back.statistical_tests.utils import CorrectionMethod, correct_p_values


class PairedTTest(BaseStatisticalTest):
    """Parametric test for comparing two related model evaluations.

    This implementation uses SciPy's paired t-test on the differences between
    paired scores from two models evaluated on the same folds. It is appropriate
    when the differences are approximately normally distributed and the samples
    are paired, which is the usual case for cross-validated comparisons.

    References
    ----------
    - https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_rel.html
    - Student. (1908). The probable error of a mean. Biometrika, 6(1), 1-25.
    """

    DISPLAY_NAME: str = MultilingualString(
        en="Paired t-test",
        es="Prueba t pareada",
        pt="Teste t pareado",
        de="Gepaarter t-Test",
        zh="配对 t 检验",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Parametric test for comparing two related groups. Requires "
            "normality of pairwise differences and independence between "
            "observations.",
        ),
        es=(
            "Prueba paramétrica para comparar dos grupos relacionados. Requiere ",
            "normalidad de las diferencias entre pares e independencia entre ",
            "observaciones.",
        ),
        pt=(
            "Teste paramétrico para comparar dois grupos relacionados. Requer ",
            "normalidade das diferenças entre pares e independência entre ",
            "observações.",
        ),
        de=(
            "Parametrischer Test zum Vergleich zweier verbundener Gruppen. ",
            "Erfordert Normalverteilung der paarweisen Differenzen und Unabhängigkeit ",
            "zwischen den Beobachtungen.",
        ),
        zh=(
            "用于比较两个相关组的参数检验。要求配对差值服从正态分布，",
            "并且观测值之间相互独立。",
        ),
    )
    ICON: str = "CompareArrows"
    COLOR: str = "#64B5F6"

    @classmethod
    def get_metadata(cls) -> dict:
        """Return UI metadata describing the test capabilities and interpretation."""
        return {
            "icon": cls.ICON,
            "is_parametric": True,
            "is_posthoc": False,
            "min_runs": 2,
            "max_runs": None,
            "supports_alternative": True,
            "supports_correction": True,
            "interpretation": MultilingualString(
                en={
                    "significant": (
                        "There is a significant difference between the two models. "
                        "The results are statistically significantly different."
                    ),
                    "not_significant": (
                        "No significant difference between the two models. "
                        "They perform similarly."
                    ),
                },
                es={
                    "significant": (
                        "Hay una diferencia significativa entre los dos modelos. "
                        "Los resultados son estadísticamente significativamente "
                        "diferentes."
                    ),
                    "not_significant": (
                        "No hay diferencia significativa entre los dos modelos. "
                        "Tienen un rendimiento similar."
                    ),
                },
                pt={
                    "significant": (
                        "Há uma diferença significativa entre os dois modelos. "
                        "Os resultados são estatisticamente significativamente "
                        "diferentes."
                    ),
                    "not_significant": (
                        "Não há diferença significativa entre os dois modelos. "
                        "Eles têm desempenho similar."
                    ),
                },
                de={
                    "significant": (
                        "Zwischen den beiden Modellen besteht ein signifikanter "
                        "Unterschied. Die Ergebnisse unterscheiden sich "
                        "statistisch signifikant."
                    ),
                    "not_significant": (
                        "Zwischen den beiden Modellen besteht kein signifikanter "
                        "Unterschied. Sie schneiden ähnlich ab."
                    ),
                },
                zh={
                    "significant": ("两个模型之间存在显著差异。结果在统计上显著不同。"),
                    "not_significant": ("两个模型之间没有显著差异。它们的表现相似。"),
                },
            ),
        }

    def run(
        self,
        scores: dict[str, list[float]],  # {run_name: [fold_scores]}
        alpha: float = 0.05,
        alternative: str = "two-sided",
        correction_method: str = None,
        **kwargs,
    ) -> StatisticalTestResult:
        """Run a paired t-test over two or more model score collections.

        Parameters
        ----------
        scores : dict[str, list[float]]
            Mapping from model/run names to paired score vectors.
        alpha : float, optional
            Significance level, by default 0.05.
        alternative : str, optional
            Direction of the hypothesis test: ``two-sided``, ``greater``, or
            ``less``.
        correction_method : str or None, optional
            Method used to adjust p-values when more than two models are being
            compared.

        Returns
        -------
        StatisticalTestResult
            A result object with the test statistic, adjusted or unadjusted
            p-values, and the overall significance decision.

        Raises
        ------
        ValueError
            If the input does not contain enough score sets, if the score lists
            are not aligned, or if the paired differences have zero variance.
        """
        import numpy as np
        from scipy.stats import ttest_rel

        if len(scores) < 2:
            raise ValueError("Paired T-Test requires at least two sets of scores.")

        run_names = list(scores.keys())

        # simple case: exactly two models, no correction needed
        if len(scores) == 2 and correction_method is None:
            scores1 = np.array(scores[run_names[0]])
            scores2 = np.array(scores[run_names[1]])

            if len(scores1) != len(scores2):
                raise ValueError(
                    "Both sets of scores must have the same number of observations."
                )

            # Ensure there are enough observations
            if len(scores1) < 2:
                raise ValueError(
                    "Paired T-Test requires at least 2 observations per group."
                )

            # Ensure there are no NaN values
            if np.isnan(scores1).any() or np.isnan(scores2).any():
                raise ValueError(
                    "Scores contain NaN values. Please check your input data."
                )

            differences = scores1 - scores2

            # Ensure the paired differences have variance
            if np.var(differences, ddof=1) == 0:
                raise ValueError(
                    "The paired differences have zero variance. "
                    "All differences are identical, making the t-test undefined."
                )

            result = ttest_rel(scores1, scores2, alternative=alternative)
            statistic = result.statistic
            p_value = result.pvalue
            deg = getattr(result, "df", len(scores1) - 1)

            significant = p_value < alpha

            return StatisticalTestResult(
                statistic=float(statistic),
                p_value=float(p_value),
                significant=significant,
                alpha=alpha,
                details={
                    "degrees_of_freedom": deg,
                    "alternative": alternative,
                },
            )

        # more than two models: perform pairwise comparisons with correction
        preliminary_results = []
        pre_correction_p_values = []

        for i in range(len(run_names)):
            for j in range(i + 1, len(run_names)):
                scores1 = np.array(scores[run_names[i]])
                scores2 = np.array(scores[run_names[j]])

                if len(scores1) != len(scores2):
                    raise ValueError(
                        f"Both sets of scores for {run_names[i]} and {run_names[j]} "
                        "must have the same number of observations."
                    )

                # Ensure there are enough observations
                if len(scores1) < 2:
                    raise ValueError(
                        f"Paired T-Test requires at least 2 observations per group for "
                        f"{run_names[i]} and {run_names[j]}."
                    )

                # Ensure there are no NaN values
                if np.isnan(scores1).any() or np.isnan(scores2).any():
                    raise ValueError(
                        f"Scores for {run_names[i]} and {run_names[j]} contain NaN "
                        "values. Please check your input data."
                    )

                differences = scores1 - scores2

                # Ensure the paired differences have variance
                if np.var(differences, ddof=1) == 0:
                    raise ValueError(
                        f"The paired differences for {run_names[i]} and {run_names[j]} "
                        "have zero variance. All differences are identical, "
                        "making the t-test undefined."
                    )

                result = ttest_rel(scores1, scores2, alternative=alternative)
                statistic = result.statistic
                p_value = result.pvalue

                preliminary_results.append((run_names[i], run_names[j], statistic))
                pre_correction_p_values.append(p_value)

        # Apply correction to the p-values
        corrected_p_values = correct_p_values(
            p_values=pre_correction_p_values,
            method=CorrectionMethod[correction_method.upper()],
            alpha=alpha,
        )

        results = [
            (a, b, stat, p)
            for (a, b, stat), p in zip(
                preliminary_results, corrected_p_values, strict=False
            )
        ]

        overall_significant = any(p < alpha for _, _, _, p in results)
        pairwise = []

        for a, b, stat, p in results:
            pairwise.append(
                PairwiseResult(
                    run_1=a,
                    run_2=b,
                    statistic=stat,
                    p_value=p,
                    significant=p < alpha,
                )
            )

        return StatisticalTestResult(
            statistic=float("nan"),  # no single omnibus statistic
            p_value=float("nan"),
            significant=overall_significant,
            alpha=alpha,
            details={},
            posthoc=pairwise,
        )
