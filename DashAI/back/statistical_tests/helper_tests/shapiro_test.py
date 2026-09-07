from DashAI.back.core.utils import MultilingualString
from DashAI.back.statistical_tests.base_statistical_test import BaseStatisticalTest
from DashAI.back.statistical_tests.statistical_test_result import StatisticalTestResult


class ShapiroTest(BaseStatisticalTest):
    """Test for normality of a single set of scores.

    This helper test assesses whether a sample is plausibly drawn from a normal
    distribution. It is frequently used as a diagnostic step before applying
    parametric tests that assume normality, such as ANOVA or paired t-tests.

    References
    ----------
    Shapiro, S. S., & Wilk, M. B. (1965). An analysis of variance test for
    normality (complete samples). Biometrika, 52(3/4), 591-611.
    """

    DISPLAY_NAME: str = MultilingualString(
        en="Shapiro-Wilk Test",
        es="Prueba de Shapiro-Wilk",
        pt="Teste de Shapiro-Wilk",
        de="Shapiro-Wilk-Test",
        zh="Shapiro-Wilk 检验",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Normality test that assesses whether the data comes from ",
            "a normal distribution.",
        ),
        es=(
            "Prueba de normalidad que evalúa si los datos provienen de ",
            "una distribución normal.",
        ),
        pt=(
            "Teste de normalidade que avalia se os dados vêm de uma",
            "distribuição normal.",
        ),
        de=(
            "Normalitätstest, der prüft, ob die Daten aus einer ",
            "Normalverteilung stammen.",
        ),
        zh=("用于评估数据是否来自正态分布的正态性检验。",),
    )
    ICON: str = "ShowChart"
    COLOR: str = "#4CAF50"

    @classmethod
    def get_metadata(cls) -> dict:
        """Metadata for Shapiro-Wilk Test."""
        return {
            "icon": cls.ICON,
            "is_parametric": None,
            "is_posthoc": False,
            "min_runs": 1,
            "max_runs": None,
            "per_run": True,
            "supports_alternative": False,
            "supports_correction": False,
            "interpretation": MultilingualString(
                en={
                    "significant": (
                        "Data does not follow a normal distribution. "
                        "The assumption of normality is violated."
                    ),
                    "not_significant": (
                        "Data appears to follow a normal distribution. "
                        "The assumption of normality is satisfied."
                    ),
                },
                es={
                    "significant": (
                        "Los datos no siguen una distribución normal. "
                        "Se viola el supuesto de normalidad."
                    ),
                    "not_significant": (
                        "Los datos parecen seguir una distribución normal. "
                        "Se cumple el supuesto de normalidad."
                    ),
                },
                pt={
                    "significant": (
                        "Os dados não seguem uma distribuição normal. "
                        "A suposição de normalidade é violada."
                    ),
                    "not_significant": (
                        "Os dados parecem seguir uma distribuição normal. "
                        "A suposição de normalidade é satisfeita."
                    ),
                },
                de={
                    "significant": (
                        "Die Daten folgen keiner Normalverteilung. "
                        "Die Normalitätsannahme ist verletzt."
                    ),
                    "not_significant": (
                        "Die Daten scheinen einer Normalverteilung zu folgen. "
                        "Die Normalitätsannahme ist erfüllt."
                    ),
                },
                zh={
                    "significant": ("数据不服从正态分布。正态性假设被违反。"),
                    "not_significant": ("数据看起来服从正态分布。正态性假设成立。"),
                },
            ),
        }

    def run(
        self,
        scores: dict[str, list[float]],  # {run_name: [fold_scores]}
        alpha: float = 0.05,
        **kwargs,
    ) -> StatisticalTestResult:
        """Run the Shapiro-Wilk test for normality of a single score sample.

        Parameters
        ----------
        scores : dict[str, list[float]]
            Mapping containing exactly one score vector to evaluate.
        alpha : float, optional
            Significance level used to judge the null hypothesis of normality,
            by default 0.05.

        Returns
        -------
        StatisticalTestResult
            A result object containing the Shapiro statistic, p-value, and the
            significance outcome.

        Raises
        ------
        ValueError
            If the input does not contain exactly one score set.
        """
        import numpy as np
        from scipy.stats import shapiro

        if len(scores) != 1:
            raise ValueError("Shapiro-Wilk Test requires exactly one set of scores.")

        run_name = list(scores.keys())[0]
        data = np.array(scores[run_name])

        statistic, p_value = shapiro(data)
        significant = p_value < alpha

        return StatisticalTestResult(
            statistic=statistic,
            p_value=float(p_value),
            significant=significant,
            alpha=alpha,
            details={"run": run_name, "data": data.tolist()},
        )
