from DashAI.back.core.utils import MultilingualString
from DashAI.back.statistical_tests.base_statistical_test import BaseStatisticalTest
from DashAI.back.statistical_tests.statistical_test_result import StatisticalTestResult


class AnovaTest(BaseStatisticalTest):
    """Parametric omnibus test for comparing three or more models on identical data.

    This implementation wraps SciPy's ``f_oneway`` and is suitable when the
    compared models are evaluated on the same folds and the assumptions of
    normality and homoscedasticity are reasonable. It is typically followed by
    a post-hoc test such as Tukey HSD to identify which pairs of models differ.

    References
    ----------
    - https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.f_oneway.html
    - Fisher, R. A. (1925). Statistical Methods for Research Workers.
    """

    DISPLAY_NAME: str = MultilingualString(
        en="ANOVA",
        es="ANOVA",
        pt="ANOVA",
        de="ANOVA",
        zh="方差分析（ANOVA）",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Parametric test for comparing the means of three or more groups. ",
            "Requires normality and homoscedasticity.",
        ),
        es=(
            "Prueba paramétrica para comparar las medias de tres o más grupos. ",
            "Requiere normalidad y homocedasticidad.",
        ),
        pt=(
            "Teste paramétrico para comparar as médias de três ou mais grupos. ",
            "Requer normalidade e homocedasticidade.",
        ),
        de=(
            "Parametrischer Test zum Vergleich der Mittelwerte von drei oder mehr ",
            "Gruppen. Erfordert Normalverteilung und Varianzhomogenität.",
        ),
        zh=(
            "用于比较三个或更多组均值的参数检验。",
            "要求正态性和方差齐性。",
        ),
    )
    ICON: str = "BarChart"
    COLOR: str = "#64B5F6"
    COMPATIBLE_COMPONENTS = ["TukeyHSDTest"]

    @classmethod
    def get_metadata(cls) -> dict:
        """Return UI metadata describing the test capabilities and interpretation."""
        return {
            "icon": cls.ICON,
            "is_parametric": True,
            "is_posthoc": False,
            "min_runs": 3,
            "max_runs": None,
            "supports_alternative": False,
            "supports_correction": False,
            "interpretation": MultilingualString(
                en={
                    "significant": (
                        "There are significant differences between the models. "
                        "Post-hoc pairwise comparisons (Tukey HSD) identify which "
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
                        "Las comparaciones post-hoc (Tukey HSD) identifican qué "
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
                        "Comparações post-hoc (Tukey HSD) identificam quais "
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
                        "Post-hoc-Paarvergleiche (Tukey HSD) zeigen, welche "
                        "Paare sich unterscheiden."
                    ),
                    "not_significant": (
                        "Zwischen den Modellen bestehen keine signifikanten "
                        "Unterschiede. Sie schneiden ähnlich ab."
                    ),
                },
                zh={
                    "significant": (
                        "模型之间存在显著差异。事后两两比较（Tukey HSD）"
                        "可识别哪些配对不同。"
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
        """Run a one-way ANOVA over the provided score collections.

        Parameters
        ----------
        scores : dict[str, list[float]]
            Mapping from model/run names to lists of scores collected over the
            same folds or repeated evaluations.
        alpha : float, optional
            Significance level used to decide whether the omnibus null
            hypothesis is rejected, by default 0.05.

        Returns
        -------
        StatisticalTestResult
            A result object with the ANOVA statistic, p-value, and a boolean
            flag indicating whether the differences are significant.

        Raises
        ------
        ValueError
            If fewer than three score sets are provided or if the score vectors
            do not contain the same number of observations.
        """
        import numpy as np
        from scipy.stats import f_oneway

        if len(scores) < 3:
            raise ValueError(
                "ANOVA Test requires at least three sets of scores. "
                "For comparing two models use Paired t-test instead."
            )

        run_names = list(scores.keys())
        score_arrays = [np.array(scores[run_name]) for run_name in run_names]

        # Check that all score arrays have the same number of observations
        num_observations = len(score_arrays[0])
        for arr in score_arrays:
            if len(arr) != num_observations:
                raise ValueError(
                    "All sets of scores must have the same number of observations."
                )

        statistic, p_value = f_oneway(*score_arrays)

        significant = p_value < alpha

        return StatisticalTestResult(
            statistic=float(statistic),
            p_value=float(p_value),
            significant=significant,
            alpha=alpha,
            details={},
        )
