from DashAI.back.core.utils import MultilingualString
from DashAI.back.statistical_tests.base_statistical_test import BaseStatisticalTest
from DashAI.back.statistical_tests.statistical_test_result import StatisticalTestResult


class LeveneTest(BaseStatisticalTest):
    """Robust test for homogeneity of variances across groups.

    This test evaluates whether several independent samples share a common
    variance while being less sensitive to departures from normality than
    Bartlett's test. It is commonly used as a preliminary check before applying
    parametric analyses such as ANOVA or t-tests, especially when the data may
    be mildly non-normal.

    References
    ----------
    Levene, H. (1960). Robust Tests for Equality of Variances. In Olkin, I.
    et al. (eds.), Contributions to Probability and Statistics: Essays in
    Honor of Harold Hotelling, Stanford University Press.
    """

    DISPLAY_NAME: str = MultilingualString(
        en="Levene's Test",
        es="Prueba de Levene",
        pt="Teste de Levene",
        de="Levene-Test",
        zh="Levene 检验",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Test of homogeneity of variances between groups (homoscedasticity), "
            "robust to deviations from normality."
        ),
        es=(
            "Prueba de homogeneidad de varianzas entre grupos (homocedasticidad), "
            "robusta ante desviaciones de la normalidad."
        ),
        pt=(
            "Teste de homogeneidade de variâncias entre grupos (homocedasticidade), "
            "robusto contra desvios da normalidade."
        ),
        de=(
            "Test auf Varianzhomogenität zwischen Gruppen (Homoskedastizität), ",
            "robust gegenüber Abweichungen von der Normalverteilung.",
        ),
        zh=("用于检验组间方差齐性（同方差性）的检验，对偏离正态性的情况具有鲁棒性。",),
    )
    ICON: str = "Balance"
    COLOR: str = "#4CAF50"

    @classmethod
    def get_metadata(cls) -> dict:
        """Metadata for Levene's Test."""
        return {
            "icon": cls.ICON,
            "is_parametric": None,
            "is_posthoc": False,
            "min_runs": 2,
            "max_runs": None,
            "supports_alternative": False,
            "supports_correction": False,
            "interpretation": MultilingualString(
                en={
                    "significant": (
                        "No homogeneity of variances detected. "
                        "The samples have different variances (heteroscedasticity)."
                    ),
                    "not_significant": (
                        "Homogeneity of variances is supported. "
                        "The samples have similar variances (homoscedasticity)."
                    ),
                },
                es={
                    "significant": (
                        "No se detecta homogeneidad de varianzas. "
                        "Las muestras tienen varianzas diferentes (heterocedasticidad)."
                    ),
                    "not_significant": (
                        "Se confirma homogeneidad de varianzas. "
                        "Las muestras tienen varianzas similares (homocedasticidad)."
                    ),
                },
                pt={
                    "significant": (
                        "Não há homogeneidade de variâncias detectada. "
                        "As amostras têm variâncias diferentes (heterocedasticidade)."
                    ),
                    "not_significant": (
                        "Há homogeneidade de variâncias. "
                        "As amostras têm variâncias similares (homocedasticidade)."
                    ),
                },
                de={
                    "significant": (
                        "Es wurde keine Varianzhomogenität festgestellt. "
                        "Die Stichproben haben unterschiedliche Varianzen"
                        " (Heteroskedastizität)."
                    ),
                    "not_significant": (
                        "Die Varianzhomogenität ist gegeben. "
                        "Die Stichproben haben ähnliche Varianzen (Homoskedastizität)."
                    ),
                },
                zh={
                    "significant": (
                        "未检测到方差齐性。样本具有不同的方差（异方差性）。"
                    ),
                    "not_significant": (
                        "方差齐性成立。样本具有相似的方差（同方差性）。"
                    ),
                },
            ),
        }

    def run(
        self,
        scores: dict[str, list[float]],  # {run_name: [fold_scores]}
        alpha: float = 0.05,
        **kwargs,
    ) -> StatisticalTestResult:
        """Run Levene's test for equality of variances across groups.

        Parameters
        ----------
        scores : dict[str, list[float]]
            Mapping from group names to score vectors whose variances will be
            compared.
        alpha : float, optional
            Significance level used to decide whether the variance equality
            assumption is rejected, by default 0.05.

        Returns
        -------
        StatisticalTestResult
            A result object containing the Levene statistic, p-value, and the
            significance outcome.

        Raises
        ------
        ValueError
            If fewer than two score sets are provided.
        """
        import numpy as np
        from scipy.stats import levene

        if len(scores) < 2:
            raise ValueError("Levene's Test requires at least two sets of scores.")

        data = [np.array(scores[run_name]) for run_name in scores]
        statistic, p_value = levene(*data)

        significant = p_value < alpha

        return StatisticalTestResult(
            statistic=float(statistic),
            p_value=float(p_value),
            significant=significant,
            alpha=alpha,
            details={},
        )
