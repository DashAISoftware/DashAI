from DashAI.back.core.utils import MultilingualString
from DashAI.back.statistical_tests.base_statistical_test import BaseStatisticalTest
from DashAI.back.statistical_tests.statistical_test_result import (
    PairwiseResult,
    StatisticalTestResult,
)
from DashAI.back.statistical_tests.utils import CorrectionMethod, correct_p_values


class WilcoxonSRTest(BaseStatisticalTest):
    """Non-parametric alternative to the paired t-test for related samples.

    This implementation uses the Wilcoxon signed-rank test on the paired score
    differences between two models evaluated on the same folds. It is suitable
    when the paired differences are not approximately normal and is commonly
    used as a robust alternative to the paired t-test.

    References
    ----------
    - https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html
    - Wilcoxon, F. (1945). Individual comparisons by ranking methods.
      Biometrics Bulletin, 1(6), 80-83.
    """

    DISPLAY_NAME: str = MultilingualString(
        en="Wilcoxon Signed-Rank Test",
        es="Prueba de Rangos con signo de Wilcoxon",
        pt="Teste de Rangos com sinal de Wilcoxon",
        de="Wilcoxon-Vorzeichen-Rang-Test",
        zh="Wilcoxon 符号秩检验",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Non-parametric test for comparing two related groups. ",
            "Requires paired observations and does not assume normality.",
        ),
        es=(
            "Prueba no paramétrica para comparar dos grupos relacionados. "
            "Requiere observaciones emparejadas y no asume normalidad."
        ),
        pt=(
            "Alternativa não-paramétrica ao teste t pareado para dois modelos. "
            "Requer observações emparejadas e não assume normalidade."
        ),
        de=(
            "Nichtparametrische Alternative zum gepaarten t-Test für zwei Modelle. ",
            "Erfordert gepaarte Beobachtungen und setzt keine Normalverteilung voraus.",
        ),
        zh=("用于比较两个相关组的非参数检验。要求配对观测值，且不假设正态性。",),
    )
    ICON: str = "CompareArrows"
    COLOR: str = "#FFD54F"

    @classmethod
    def get_metadata(cls) -> dict:
        """Return UI metadata describing the test capabilities and interpretation."""
        return {
            "icon": cls.ICON,
            "is_parametric": False,
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
                        "Unterschied. Die Ergebnisse unterscheiden sich statistisch "
                        "signifikant."
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
        """Run the Wilcoxon signed-rank test on paired score differences.

        Parameters
        ----------
        scores : dict[str, list[float]]
            Mapping from model/run names to paired score vectors.
        alpha : float, optional
            Significance level used to decide whether the null hypothesis is
            rejected, by default 0.05.
        alternative : str, optional
            Direction of the alternative hypothesis: ``two-sided``, ``greater``,
            or ``less``.
        correction_method : str or None, optional
            Method used to adjust p-values when more than two models are being
            compared.

        Returns
        -------
        StatisticalTestResult
            A result object with the signed-rank statistic, p-value, and the
            significance decision.

        Raises
        ------
        ValueError
            If the input does not contain at least two score sets or if the
            score vectors are not aligned.
        """
        import numpy as np
        from scipy.stats import wilcoxon

        if len(scores) < 2:
            raise ValueError(
                "Wilcoxon Signed-Rank Test requires at least two sets of scores."
            )

        run_names = list(scores.keys())

        # simple case: exactly two models, no correction needed
        if len(scores) == 2:
            scores1 = np.array(scores[run_names[0]])
            scores2 = np.array(scores[run_names[1]])

            if len(scores1) != len(scores2):
                raise ValueError(
                    "Both sets of scores must have the same number of observations."
                )

            # we round the scores to 4 decimal places to avoid issues
            # with very small differences, according to scipy documentation
            score_differences = np.round(scores1 - scores2, decimals=4)
            statistic, p_value = wilcoxon(score_differences, alternative=alternative)

            significant = p_value < alpha

            return StatisticalTestResult(
                statistic=statistic,
                p_value=p_value,
                significant=significant,
                alpha=alpha,
                details={
                    "score_differences": score_differences.tolist(),
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

                score_differences = np.round(scores1 - scores2, decimals=4)
                statistic, p_value = wilcoxon(score_differences)

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
