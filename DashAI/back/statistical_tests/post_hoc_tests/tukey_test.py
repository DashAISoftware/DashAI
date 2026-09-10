from DashAI.back.core.utils import MultilingualString
from DashAI.back.statistical_tests.base_statistical_test import BaseStatisticalTest
from DashAI.back.statistical_tests.statistical_test_result import (
    PairwiseResult,
    StatisticalTestResult,
)


class TukeyHSDTest(BaseStatisticalTest):
    """Tukey HSD post-hoc test for pairwise comparison after a significant ANOVA test.

    Controls the familywise error rate (FWER) when performing multiple pairwise
    comparisons. Assumes normality and homogeneity of variance (same assumptions
    as ANOVA). For non-normal data, use Nemenyi after Friedman instead.

    Requires the `statsmodels` package.

    References
    ----------
    - Tukey, J. W. (1949). Comparing individual means in the analysis of
      variance. Biometrics, 5(2), 99-114.
    """

    DISPLAY_NAME: str = MultilingualString(
        en="Tukey HSD Test",
        es="Prueba de Tukey HSD",
        pt="Teste de Tukey HSD",
        de="Tukey-HSD-Test",
        zh="Tukey HSD 检验",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Parametric post-hoc test for pairwise comparisons between groups. ",
            "Requires normality and homoscedasticity. Usually applied after a ",
            "significant ANOVA.",
        ),
        es=(
            "Prueba post-hoc paramétrica para comparaciones por pares entre grupos. ",
            "Requiere normalidad y homocedasticidad. Suele aplicarse después de un ",
            "ANOVA significativo.",
        ),
        de=(
            "Parametrischer Post-hoc-Test für paarweise Vergleiche zwischen Gruppen. ",
            "Erfordert Normalverteilung und Varianzhomogenität. Wird üblicherweise ",
            "nach einer signifikanten ANOVA angewendet.",
        ),
        zh=(
            "用于组间两两比较的参数事后检验。",
            "要求正态性和方差齐性。通常在显著的 ANOVA 之后使用。",
        ),
        pt=(
            "Teste post-hoc paramétrico para comparações pareadas de modelos. ",
            "Requer normalidade e homocedasticidade. Geralmente aplicado após um ",
            "ANOVA significativo.",
        ),
    )
    ICON: str = "CompareArrows"

    @classmethod
    def get_metadata(cls) -> dict:
        """Metadata for Tukey HSD Test."""
        return {
            "icon": cls.ICON,
            "is_parametric": True,
            "is_posthoc": True,
            "min_runs": 3,
            "max_runs": None,
            "supports_alternative": False,
            "supports_correction": False,
            "interpretation": MultilingualString(
                en={
                    "significant": (
                        "Pairwise comparisons are shown in the table. Pairs with "
                        "p < α indicate significant differences."
                    ),
                    "not_significant": (
                        "This is a post-hoc test automatically run after ANOVA. "
                        "Results appear only when ANOVA is significant."
                    ),
                },
                es={
                    "significant": (
                        "Las comparaciones pareadas se muestran en la tabla. Los "
                        "pares con p < α indican diferencias significativas."
                    ),
                    "not_significant": (
                        "Esta es una prueba post-hoc ejecutada automáticamente "
                        "después de ANOVA. Los resultados aparecen solo cuando "
                        "ANOVA es significativo."
                    ),
                },
                pt={
                    "significant": (
                        "Comparações pareadas são mostradas na tabela. Pares "
                        "com p < α indicam diferenças significativas."
                    ),
                    "not_significant": (
                        "Este é um teste post-hoc executado automaticamente "
                        "após ANOVA. Os resultados aparecem apenas quando ANOVA "
                        "é significativo."
                    ),
                },
                de={
                    "significant": (
                        "Paarvergleiche werden in der Tabelle angezeigt. "
                        "Pfade mit p < α weisen auf signifikante Unterschiede hin."
                    ),
                    "not_significant": (
                        "Dies ist ein Post-hoc-Test, der automatisch nach der ANOVA "
                        "ausgeführt wird. Ergebnisse erscheinen nur, wenn die ANOVA "
                        "signifikant ist."
                    ),
                },
                zh={
                    "significant": (
                        "两两比较会显示在表格中。p < α 的配对表示存在显著差异。"
                    ),
                    "not_significant": (
                        "这是一个在 ANOVA 之后自动执行的事后检验。只有当 ANOVA "
                        "显著时才会显示结果。"
                    ),
                },
            ),
        }

    def run(
        self,
        scores: dict[str, list[float]],
        alpha: float = 0.05,
        statistic: float = None,  # ANOVA F-statistic
        p_value: float = None,  # ANOVA p-value
        **kwargs,
    ) -> StatisticalTestResult:
        """Run Tukey's HSD post-hoc test after a significant ANOVA result.

        Parameters
        ----------
        scores : dict[str, list[float]]
            Mapping from model/run names to score vectors evaluated over the same
            folds.
        alpha : float, optional
            Significance level used to judge the adjusted pairwise comparisons,
            by default 0.05.
        statistic : float or None, optional
            Precomputed ANOVA statistic. If provided, it is reused instead of
            recomputing the omnibus statistic.
        p_value : float or None, optional
            Precomputed ANOVA p-value. If provided, it is reused instead of
            recomputing the omnibus statistic.

        Returns
        -------
        StatisticalTestResult
            A result object with the omnibus ANOVA decision and the pairwise
            Tukey HSD comparisons.

        Raises
        ------
        ValueError
            If fewer than three models are provided or if the score vectors are
            not aligned across models.
        """
        import numpy as np
        from scipy.stats import f_oneway
        from statsmodels.stats.multicomp import pairwise_tukeyhsd

        if len(scores) < 3:
            raise ValueError(
                "Tukey HSD test requires at least three sets of scores. "
                "For pairwise comparisons use paired t-test instead."
            )

        run_names = list(scores.keys())
        score_arrays = [np.array(scores[name]) for name in run_names]

        num_observations = len(score_arrays[0])
        for arr in score_arrays:
            if len(arr) != num_observations:
                raise ValueError(
                    "All sets of scores must have the same number of observations."
                )

        # Use precalculated ANOVA values if provided, otherwise compute
        if statistic is not None and p_value is not None:
            anova_stat, anova_p = statistic, p_value
        else:
            anova_stat, anova_p = f_oneway(*score_arrays)

        # Build flat arrays for statsmodels
        all_scores = np.concatenate(score_arrays)
        all_labels = np.concatenate(
            [
                np.full(len(arr), name)
                for name, arr in zip(run_names, score_arrays, strict=False)
            ]
        )

        tukey = pairwise_tukeyhsd(all_scores, all_labels, alpha=alpha)

        # Parse pairwise results from tukey summary
        pairwise = []
        for row in tukey.summary().data[1:]:  # skip header row
            run_1, run_2, _, _, _, _, reject = row
            # p-value not directly exposed, derive significance from reject flag
            # and get adjusted p-value from meandiffs table
            p_val = float(tukey.pvalues[len(pairwise)])
            pairwise.append(
                PairwiseResult(
                    run_1=str(run_1),
                    run_2=str(run_2),
                    p_value=p_val,
                    significant=bool(reject),
                )
            )

        overall_significant = anova_p < alpha

        return StatisticalTestResult(
            statistic=float(anova_stat),
            p_value=float(anova_p),
            significant=overall_significant,
            alpha=alpha,
            details={
                "runs": run_names,
                "score_arrays": [a.tolist() for a in score_arrays],
                "tukey_summary": str(tukey.summary()),
            },
            posthoc=pairwise,
        )
