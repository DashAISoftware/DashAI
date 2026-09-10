from DashAI.back.core.utils import MultilingualString
from DashAI.back.statistical_tests.base_statistical_test import BaseStatisticalTest
from DashAI.back.statistical_tests.statistical_test_result import (
    PairwiseResult,
    StatisticalTestResult,
)


class NemenyiTest(BaseStatisticalTest):
    """Nemenyi post-hoc test for pairwise comparison after a significant Friedman test.

    Uses rank-based pairwise comparisons with a critical difference threshold.
    Recommended by Demsar (2006) as the standard post-hoc test for comparing
    multiple classifiers evaluated with cross-validation.

    Requires the `scikit-posthocs` package.

    References
    ----------
    Demsar, J. (2006). Statistical Comparisons of Classifiers over Multiple
    Data Sets. Journal of Machine Learning Research, 7, 1-30.
    """

    DISPLAY_NAME: str = MultilingualString(
        en="Nemenyi Test",
        es="Prueba de Nemenyi",
        pt="Teste de Nemenyi",
        de="Nemenyi-Test",
        zh="Nemenyi 检验",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Non-parametric post-hoc test for pairwise comparisons between groups. ",
            "Does not assume normality and is usually applied after Friedman test.",
        ),
        es=(
            "Prueba post-hoc no paramétrica para comparaciones por pares entre ",
            "grupos. No asume normalidad y suele aplicarse tras el test de Friedman.",
        ),
        pt=(
            "Teste post-hoc não-paramétrico para comparações por pares entre grupos. ",
            "Não assume normalidade e geralmente é aplicado após o teste de Friedman.",
        ),
        de=(
            "Nichtparametrischer Post-hoc-Test für paarweise Vergleiche zwischen ",
            "Gruppen. Setzt keine Normalverteilung voraus und wird üblicherweise ",
            "nach dem Friedman-Test angewendet.",
        ),
        zh=(
            "用于组间两两比较的非参数事后检验。",
            "不要求正态性，通常在 Friedman 检验之后使用。",
        ),
    )
    ICON: str = "CompareArrows"

    @classmethod
    def get_metadata(cls) -> dict:
        """Metadata for Nemenyi Test."""
        return {
            "icon": cls.ICON,
            "is_parametric": False,
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
                        "This is a post-hoc test automatically run after Friedman "
                        "test. Results appear only when Friedman is significant."
                    ),
                },
                es={
                    "significant": (
                        "Las comparaciones pareadas se muestran en la tabla. Los "
                        "pares con p < α indican diferencias significativas."
                    ),
                    "not_significant": (
                        "Esta es una prueba post-hoc ejecutada automáticamente "
                        "después de la prueba de Friedman. Los resultados "
                        "aparecen solo cuando Friedman es significativo."
                    ),
                },
                pt={
                    "significant": (
                        "Comparações pareadas são mostradas na tabela. Pares "
                        "com p < α indicam diferenças significativas."
                    ),
                    "not_significant": (
                        "Este é um teste post-hoc executado automaticamente após "
                        "o teste de Friedman. Os resultados aparecem apenas "
                        "quando Friedman é significativo."
                    ),
                },
                de={
                    "significant": (
                        "Paarweise Vergleiche werden in der Tabelle angezeigt. "
                        "Paare mit p < α zeigen signifikante Unterschiede an."
                    ),
                    "not_significant": (
                        "Dies ist ein Post-hoc-Test, der automatisch nach dem "
                        "Friedman-Test durchgeführt wird. Ergebnisse erscheinen "
                        "nur, wenn Friedman signifikant ist."
                    ),
                },
                zh={
                    "significant": (
                        "两两比较显示在表格中。p < α 的配对表示存在显著差异。"
                    ),
                    "not_significant": (
                        "这是一个在 Friedman 检验后自动运行的事后检验。"
                        "仅当 Friedman 显著时才会显示结果。"
                    ),
                },
            ),
        }

    def run(
        self,
        scores: dict[str, list[float]],
        alpha: float = 0.05,
        statistic: float = None,  # Friedman statistic
        p_value: float = None,  # Friedman p-value
        **kwargs,
    ) -> StatisticalTestResult:
        """Run the Nemenyi post-hoc test after a significant Friedman test.

        Parameters
        ----------
        scores : dict[str, list[float]]
            Mapping from model/run names to score vectors evaluated over the same
            folds.
        alpha : float, optional
            Significance level used to judge the pairwise p-values, by default 0.05.
        statistic : float or None, optional
            Precomputed Friedman statistic. If provided, it is reused instead of
            recomputing the omnibus statistic.
        p_value : float or None, optional
            Precomputed Friedman p-value. If provided, it is reused instead of
            recomputing the omnibus statistic.

        Returns
        -------
        StatisticalTestResult
            A result object with the omnibus Friedman outcome and the pairwise
            post-hoc comparisons.

        Raises
        ------
        ValueError
            If fewer than three models are provided or if the score vectors are
            not aligned across models.
        """
        import numpy as np
        import scikit_posthocs as sp
        from scipy.stats import friedmanchisquare

        if len(scores) < 3:
            raise ValueError(
                "Nemenyi post-hoc test requires at least three sets of scores. "
                "For pairwise comparisons use Wilcoxon or Paired t-test instead."
            )

        run_names = list(scores.keys())
        score_arrays = [np.array(scores[name]) for name in run_names]

        num_observations = len(score_arrays[0])
        for arr in score_arrays:
            if len(arr) != num_observations:
                raise ValueError(
                    "All sets of scores must have the same number of observations."
                )

        # Use precalculated Friedman values if provided, otherwise compute
        if statistic is not None and p_value is not None:
            friedman_stat, friedman_p = statistic, p_value
        else:
            friedman_stat, friedman_p = friedmanchisquare(*score_arrays)

        # Build data matrix for scikit-posthocs: shape (n_folds, n_models)
        data_matrix = np.column_stack(score_arrays)
        posthoc_matrix = sp.posthoc_nemenyi_friedman(data_matrix)

        # Build pairwise results from the matrix
        pairwise = []
        for i in range(len(run_names)):
            for j in range(i + 1, len(run_names)):
                p_val = float(posthoc_matrix.iloc[i, j])
                pairwise.append(
                    PairwiseResult(
                        run_1=run_names[i],
                        run_2=run_names[j],
                        p_value=p_val,
                        significant=p_val < alpha,
                    )
                )

        overall_significant = friedman_p < alpha

        return StatisticalTestResult(
            statistic=float(friedman_stat),
            p_value=float(friedman_p),
            significant=overall_significant,
            alpha=alpha,
            details={
                "runs": run_names,
                "score_arrays": [a.tolist() for a in score_arrays],
                "posthoc_matrix": posthoc_matrix.to_dict(),
            },
            posthoc=pairwise,
        )
