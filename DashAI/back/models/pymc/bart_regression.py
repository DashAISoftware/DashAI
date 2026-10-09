"""DashAI Bayesian Additive Regression Trees (BART) regression model.

This module wraps ``pymc-bart`` behind a small scikit-learn-style estimator
(:class:`PyMCBARTRegressor`) so it can be plugged into the same
``RegressionModel`` / ``SklearnLikeRegressor`` machinery used by the other
DashAI tabular regressors.
"""

from typing import TYPE_CHECKING

from sklearn.base import BaseEstimator, RegressorMixin

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    none_type,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor

if TYPE_CHECKING:
    import numpy as np


class PyMCBARTRegressor(BaseEstimator, RegressorMixin):
    """A minimal scikit-learn-style wrapper around ``pymc_bart``.

    ``pymc-bart`` exposes BART as a PyMC distribution rather than as an
    estimator with ``fit`` / ``predict`` methods, and its sampled trees are the
    only object needed to predict on new data. This class hides that: ``fit``
    builds a PyMC model, samples the posterior with the PGBART sampler and keeps
    the sampled tree ensembles; ``predict`` evaluates those trees on new inputs
    and returns the posterior mean of the regression function.

    Only the sampled trees (plain Python/NumPy objects) are stored on the
    fitted instance, so the estimator serialises cleanly with ``joblib`` -- the
    heavy PyTensor graph is not retained.

    Parameters
    ----------
    m : int
        Number of trees in the ensemble.
    alpha : float
        Controls the prior probability over the depth of the trees. Must lie in
        the open interval (0, 1).
    beta : float
        Controls the prior probability over the number of leaves. Must be
        positive.
    response : str
        How leaf-node values are computed: ``constant`` (default), ``linear`` or
        ``mix``. The last two are experimental in ``pymc-bart``.
    draws : int
        Number of posterior samples to draw per chain.
    tune : int
        Number of tuning (burn-in) iterations per chain, discarded afterwards.
    chains : int
        Number of independent MCMC chains to run.
    random_seed : int, optional
        Seed for the sampler and the prediction RNG, for reproducibility.
    """

    def __init__(
        self,
        m: int = 50,
        alpha: float = 0.95,
        beta: float = 2.0,
        response: str = "constant",
        draws: int = 200,
        tune: int = 200,
        chains: int = 1,
        random_seed: int = 0,
    ) -> None:
        self.m = m
        self.alpha = alpha
        self.beta = beta
        self.response = response
        self.draws = draws
        self.tune = tune
        self.chains = chains
        self.random_seed = random_seed

    def fit(self, x, y) -> "PyMCBARTRegressor":
        """Sample the BART posterior for the regression of ``y`` on ``x``.

        Parameters
        ----------
        x : array-like of shape (n_samples, n_features)
            Training covariates.
        y : array-like of shape (n_samples,)
            Training targets.

        Returns
        -------
        PyMCBARTRegressor
            The fitted estimator.
        """
        import numpy as np
        import pymc as pm
        import pymc_bart as pmb

        x = np.asarray(x, dtype="float64")
        y = np.asarray(y, dtype="float64").ravel()

        sigma_prior = float(np.std(y))
        if not sigma_prior > 0:
            sigma_prior = 1.0

        with pm.Model():
            x_data = pm.Data("X", x)
            mu = pmb.BART(
                "mu",
                x_data,
                y,
                m=self.m,
                alpha=self.alpha,
                beta=self.beta,
                response=self.response,
            )
            sigma = pm.HalfNormal("sigma", sigma_prior)
            pm.Normal("y", mu=mu, sigma=sigma, observed=y, shape=mu.shape)
            pm.sample(
                draws=self.draws,
                tune=self.tune,
                chains=self.chains,
                cores=1,
                random_seed=self.random_seed,
                progressbar=False,
                compute_convergence_checks=False,
            )

        # Keep only the sampled tree ensembles: they are all that is needed to
        # predict, and they pickle cleanly (unlike the PyTensor graph).
        self.all_trees_ = list(mu.owner.op.all_trees)
        self.n_features_in_ = x.shape[1]
        self.y_mean_ = float(y.mean())
        return self

    def predict(self, x) -> "np.ndarray":
        """Predict the posterior mean of the BART function at ``x``.

        Parameters
        ----------
        x : array-like of shape (n_samples, n_features)
            Covariates to predict on.

        Returns
        -------
        np.ndarray of shape (n_samples,)
            Posterior mean regression estimates.
        """
        import numpy as np
        from pymc_bart.utils import _sample_posterior

        if not hasattr(self, "all_trees_"):
            raise RuntimeError(
                "This PyMCBARTRegressor instance is not fitted yet. "
                "Call 'fit' before using 'predict'."
            )

        x = np.asarray(x, dtype="float64")
        rng = np.random.default_rng(self.random_seed)
        # _sample_posterior draws `size` tree ensembles (with replacement) from
        # the posterior and evaluates them on x; averaging over them yields the
        # posterior mean of the regression function.
        posterior = _sample_posterior(
            self.all_trees_,
            X=x,
            rng=rng,
            size=len(self.all_trees_),
            shape=1,
        )
        return np.asarray(posterior).mean(axis=0).squeeze(-1)


class BARTRegressionSchema(BaseSchema):
    """Schema that configures the Bayesian Additive Regression Trees model.

    BART models the regression function as a sum of regression trees, each
    constrained by a regularising prior so that individual trees are weak
    learners. The posterior over the tree ensemble is sampled with MCMC,
    yielding both point predictions and a full predictive distribution. The
    underlying implementation is ``pymc-bart``.
    """

    m: schema_field(
        int_field(ge=1),
        placeholder=50,
        description=MultilingualString(
            en="The number of trees in the sum-of-trees ensemble.",
            es="El número de árboles en el ensamble de suma de árboles.",
            pt="O número de árvores no conjunto de soma de árvores.",
            de="Die Anzahl der Bäume im Summe-von-Bäumen-Ensemble.",
            zh="树集成中树的数量。",
        ),
        alias=MultilingualString(
            en="Number of trees",
            es="Número de árboles",
            pt="Número de árvores",
            de="Anzahl der Bäume",
            zh="树的数量",
        ),
    )  # type: ignore

    alpha: schema_field(
        float_field(gt=0.0, lt=1.0),
        placeholder=0.95,
        description=MultilingualString(
            en=(
                "Base of the tree-depth prior; the probability that a node at "
                "depth d is non-terminal is alpha * (1 + d) ** (-beta). Must be "
                "in (0, 1)."
            ),
            es=(
                "Base del prior de profundidad del árbol; la probabilidad de que "
                "un nodo a profundidad d no sea terminal es alpha * (1 + d) ** "
                "(-beta). Debe estar en (0, 1)."
            ),
            pt=(
                "Base do prior de profundidade da árvore; a probabilidade de um "
                "nó na profundidade d não ser terminal é alpha * (1 + d) ** "
                "(-beta). Deve estar em (0, 1)."
            ),
            de=(
                "Basis des Baumtiefen-Priors; die Wahrscheinlichkeit, dass ein "
                "Knoten in Tiefe d kein Endknoten ist, beträgt alpha * (1 + d) "
                "** (-beta). Muss in (0, 1) liegen."
            ),
            zh="树深度先验的基数；深度为 d 的节点为非终端节点的概率为 "
            "alpha * (1 + d) ** (-beta)。必须在 (0, 1) 区间内。",
        ),
        alias=MultilingualString(
            en="Alpha (depth prior)",
            es="Alfa (prior de profundidad)",
            pt="Alfa (prior de profundidade)",
            de="Alpha (Tiefen-Prior)",
            zh="Alpha（深度先验）",
        ),
    )  # type: ignore

    beta: schema_field(
        float_field(gt=0.0),
        placeholder=2.0,
        description=MultilingualString(
            en=(
                "Exponent of the tree-depth prior; larger values penalise deep "
                "trees more strongly. Must be positive."
            ),
            es=(
                "Exponente del prior de profundidad del árbol; valores mayores "
                "penalizan más los árboles profundos. Debe ser positivo."
            ),
            pt=(
                "Expoente do prior de profundidade da árvore; valores maiores "
                "penalizam mais as árvores profundas. Deve ser positivo."
            ),
            de=(
                "Exponent des Baumtiefen-Priors; größere Werte bestrafen tiefe "
                "Bäume stärker. Muss positiv sein."
            ),
            zh="树深度先验的指数；较大的值对深树的惩罚更强。必须为正。",
        ),
        alias=MultilingualString(
            en="Beta (depth prior)",
            es="Beta (prior de profundidad)",
            pt="Beta (prior de profundidade)",
            de="Beta (Tiefen-Prior)",
            zh="Beta（深度先验）",
        ),
    )  # type: ignore

    response: schema_field(
        enum_field(enum=["constant", "linear", "mix"]),
        placeholder="constant",
        description=MultilingualString(
            en=(
                "How leaf-node values are computed. 'constant' is recommended; "
                "'linear' and 'mix' are experimental."
            ),
            es=(
                "Cómo se calculan los valores de los nodos hoja. Se recomienda "
                "'constant'; 'linear' y 'mix' son experimentales."
            ),
            pt=(
                "Como os valores dos nós folha são calculados. 'constant' é "
                "recomendado; 'linear' e 'mix' são experimentais."
            ),
            de=(
                "Wie die Werte der Blattknoten berechnet werden. 'constant' wird "
                "empfohlen; 'linear' und 'mix' sind experimentell."
            ),
            zh="叶节点值的计算方式。推荐 'constant'；'linear' 和 'mix' 为实验性。",
        ),
        alias=MultilingualString(
            en="Leaf response",
            es="Respuesta de hoja",
            pt="Resposta de folha",
            de="Blatt-Antwort",
            zh="叶响应",
        ),
    )  # type: ignore

    draws: schema_field(
        int_field(ge=1),
        placeholder=200,
        description=MultilingualString(
            en="Number of posterior samples drawn per chain.",
            es="Número de muestras posteriores extraídas por cadena.",
            pt="Número de amostras posteriores extraídas por cadeia.",
            de="Anzahl der pro Kette gezogenen Posterior-Stichproben.",
            zh="每条链抽取的后验样本数量。",
        ),
        alias=MultilingualString(
            en="Posterior draws",
            es="Muestras posteriores",
            pt="Amostras posteriores",
            de="Posterior-Ziehungen",
            zh="后验抽样数",
        ),
    )  # type: ignore

    tune: schema_field(
        int_field(ge=0),
        placeholder=200,
        description=MultilingualString(
            en="Number of tuning (burn-in) iterations per chain, discarded.",
            es=("Número de iteraciones de ajuste (burn-in) por cadena, descartadas."),
            pt=("Número de iterações de ajuste (burn-in) por cadeia, descartadas."),
            de="Anzahl der Tuning-(Burn-in-)Iterationen pro Kette, verworfen.",
            zh="每条链的调优（预热）迭代次数，之后被丢弃。",
        ),
        alias=MultilingualString(
            en="Tuning iterations",
            es="Iteraciones de ajuste",
            pt="Iterações de ajuste",
            de="Tuning-Iterationen",
            zh="调优迭代次数",
        ),
    )  # type: ignore

    chains: schema_field(
        int_field(ge=1),
        placeholder=1,
        description=MultilingualString(
            en="Number of independent MCMC chains to run.",
            es="Número de cadenas MCMC independientes a ejecutar.",
            pt="Número de cadeias MCMC independentes a executar.",
            de="Anzahl der auszuführenden unabhängigen MCMC-Ketten.",
            zh="要运行的独立 MCMC 链的数量。",
        ),
        alias=MultilingualString(
            en="MCMC chains",
            es="Cadenas MCMC",
            pt="Cadeias MCMC",
            de="MCMC-Ketten",
            zh="MCMC 链数",
        ),
    )  # type: ignore

    random_seed: schema_field(
        none_type(int_field(ge=0)),
        placeholder=0,
        description=MultilingualString(
            en="Seed for the sampler and prediction RNG, for reproducibility.",
            es=(
                "Semilla para el muestreador y el RNG de predicción, para "
                "reproducibilidad."
            ),
            pt=(
                "Semente para o amostrador e o RNG de predição, para reprodutibilidade."
            ),
            de=(
                "Startwert für den Sampler und den Vorhersage-RNG, zur "
                "Reproduzierbarkeit."
            ),
            zh="采样器和预测随机数生成器的种子，用于可复现性。",
        ),
        alias=MultilingualString(
            en="Random seed",
            es="Semilla aleatoria",
            pt="Semente aleatória",
            de="Zufalls-Seed",
            zh="随机种子",
        ),
    )  # type: ignore


class BARTRegression(RegressionModel, SklearnLikeRegressor, PyMCBARTRegressor):
    """Bayesian Additive Regression Trees regressor.

    BART represents the regression function as a sum of ``m`` regression trees.
    A regularising prior keeps each tree shallow so that it acts as a weak
    learner, and the posterior distribution over the whole ensemble is explored
    with an MCMC sampler (Particle Gibbs for the trees). Predictions are the
    posterior mean of the sum-of-trees function, and the sampled posterior also
    provides a natural quantification of predictive uncertainty.

    Key hyperparameters are the number of trees ``m`` and the tree-structure
    prior parameters ``alpha`` and ``beta``, together with the MCMC controls
    ``draws``, ``tune`` and ``chains``. The implementation wraps ``pymc-bart``.

    References
    ----------
    - [1] Chipman, H.A., George, E.I. & McCulloch, R.E. (2010). "BART: Bayesian
           Additive Regression Trees." The Annals of Applied Statistics, 4(1),
           266-298. https://doi.org/10.1214/09-AOAS285
    - [2] https://www.pymc.io/projects/bart/
    """

    SCHEMA = BARTRegressionSchema
    DISPLAY_NAME: str = MultilingualString(
        en="BART Regression",
        es="Regresión BART",
        pt="Regressão BART",
        de="BART-Regression",
        zh="BART 回归",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Bayesian sum-of-trees regression that samples the posterior over a "
            "tree ensemble with MCMC."
        ),
        es=(
            "Regresión bayesiana de suma de árboles que muestrea la posterior "
            "sobre un ensamble de árboles con MCMC."
        ),
        pt=(
            "Regressão bayesiana de soma de árvores que amostra a posterior "
            "sobre um conjunto de árvores com MCMC."
        ),
        de=(
            "Bayessche Summe-von-Bäumen-Regression, die die Posterior über ein "
            "Baum-Ensemble mit MCMC abtastet."
        ),
        zh="贝叶斯树求和回归，使用 MCMC 对树集成的后验进行采样。",
    )
    COLOR: str = "#26A69A"
    ICON: str = "Park"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent wrapper. See the
            associated schema class for available keys and their defaults.
        """
        super().__init__(**kwargs)
