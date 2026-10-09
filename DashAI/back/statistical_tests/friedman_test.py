from DashAI.back.core.utils import MultilingualString
from DashAI.back.statistical_tests.base_statistical_test import BaseStatisticalTest
from DashAI.back.statistical_tests.statistical_test_result import StatisticalTestResult


class FriedmanTest(BaseStatisticalTest):
    """Non-parametric omnibus test for comparing three or more models.

    This test is the rank-based alternative to ANOVA for repeated-measures or
    paired evaluations such as cross-validation results. It is commonly used
    when the assumptions of normality are not satisfied and is typically paired
    with a post-hoc test such as Nemenyi.

    References
    ----------
    - https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.friedmanchisquare.html
    - Friedman, M. (1937). The use of ranks to avoid the assumption of
      normality implicit in the analysis of variance. Journal of the American
      Statistical Association, 32(200), 675-701.
    """

    DISPLAY_NAME: str = MultilingualString(
        en="Friedman Test",
        es="Prueba de Friedman",
        pt="Teste de Friedman",
        de="Friedman-Test",
        zh="Friedman 检验",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Non-parametric test for comparing multiple models on the same folds. ",
            "Does not assume normality.",
        ),
        es=(
            "Prueba no paramétrica para comparar múltiples modelos sobre ",
            "los mismos folds. No asume normalidad.",
        ),
        pt=(
            "Teste não-paramétrico para comparar múltiplos modelos sobre ",
            "as mesmas folds. Não assume normalidade.",
        ),
        de=(
            "Nichtparametrischer Test zum Vergleich mehrerer Modelle auf denselben",
            " Folds. Setzt keine Normalverteilung voraus.",
        ),
        zh=(
            "用于比较多个模型在相同折上的非参数检验。",
            "不要求正态性。",
        ),
    )
    ICON: str = "Leaderboard"
    COLOR: str = "#FFD54F"
    COMPATIBLE_COMPONENTS = ["NemenyiTest"]

    @classmethod
    def get_metadata(cls) -> dict:
        """Return UI metadata describing the test capabilities and interpretation."""
        return {
            "icon": cls.ICON,
            "is_parametric": False,
            "is_posthoc": False,
            "min_runs": 3,
            "max_runs": None,
            "supports_alternative": False,
            "supports_correction": False,
            "interpretation": MultilingualString(
                en={
                    "significant": (
                        "There are significant differences between the models. "
                        "Post-hoc pairwise comparisons (Nemenyi) identify which "
                        "pairs differ."
                    ),
                    "not_significant": (
                        "No significant differences between the models. "
                        "They perform similarly."
                    ),
                },
                es={
                    "significant": (
                        "Hay diferencias significativas entre los modelos. "
                        "Las comparaciones post-hoc (Nemenyi) identifican qué "
                        "pares difieren."
                    ),
                    "not_significant": (
                        "No hay diferencias significativas entre los modelos. "
                        "Tienen un rendimiento similar."
                    ),
                },
                pt={
                    "significant": (
                        "Há diferenças significativas entre os modelos. "
                        "Comparações post-hoc (Nemenyi) identificam quais "
                        "pares diferem."
                    ),
                    "not_significant": (
                        "Não há diferenças significativas entre os modelos. "
                        "Eles têm desempenho similar."
                    ),
                },
                de={
                    "significant": (
                        "Zwischen den Modellen bestehen signifikante Unterschiede. "
                        "Post-hoc-Vergleiche (Nemenyi) zeigen, welche Paare sich"
                        " unterscheiden."
                    ),
                    "not_significant": (
                        "Zwischen den Modellen bestehen keine signifikanten"
                        " Unterschiede. Sie schneiden ähnlich ab."
                    ),
                },
                zh={
                    "significant": (
                        "模型之间存在显著差异。事后比较（Nemenyi）可识别哪些配对不同。"
                    ),
                    "not_significant": ("模型之间没有显著差异。它们的表现相似。"),
                },
            ),
        }

    def run(
        self,
        scores: dict[str, list[float]],  # {run_name: [fold_scores]}
        alpha: float = 0.05,
        **kwargs,
    ) -> StatisticalTestResult:
        """Run the Friedman test over the provided score collections.

        Parameters
        ----------
        scores : dict[str, list[float]]
            Mapping from model/run names to score vectors evaluated on the same
            folds or repeated evaluation blocks.
        alpha : float, optional
            Significance level used to decide whether the omnibus null
            hypothesis is rejected, by default 0.05.

        Returns
        -------
        StatisticalTestResult
            A result object with the Friedman statistic, p-value, and the
            significance flag.

        Raises
        ------
        ValueError
            If fewer than three score sets are provided or if the score vectors
            do not contain the same number of observations.
        """
        import numpy as np
        from scipy.stats import friedmanchisquare

        if len(scores) < 3:
            raise ValueError("Friedman Test requires at least three sets of scores.")

        run_names = list(scores.keys())
        score_arrays = [np.array(scores[run_name]) for run_name in run_names]

        # Check that all score arrays have the same number of observations
        num_observations = len(score_arrays[0])
        for arr in score_arrays:
            if len(arr) != num_observations:
                raise ValueError(
                    "All sets of scores must have the same number of observations."
                )

        statistic, p_value = friedmanchisquare(*score_arrays)

        significant = p_value < alpha

        return StatisticalTestResult(
            statistic=float(statistic),
            p_value=float(p_value),
            significant=significant,
            alpha=alpha,
            details={},
        )
