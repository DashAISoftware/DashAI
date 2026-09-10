from sklearn.ensemble import (
    HistGradientBoostingRegressor as _HistGradientBoostingRegressor,
)

from DashAI.back.core.schema_fields import (
    BaseSchema,
    float_field,
    int_field,
    none_type,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class HistGradientBoostingRegressionSchema(BaseSchema):
    """Schema that configures the Histogram-based Gradient Boosting Regressor.

    Histogram-based Gradient Boosting is a fast sequential ensemble method that
    bins features into histograms before building each tree, greatly reducing cost
    on large datasets. The underlying implementation is
    ``sklearn.ensemble.HistGradientBoostingRegressor``.
    """

    learning_rate: search_space(
        float_field(ge=0.0),
        fixed=0.1,
        low=0.01,
        high=1.0,
        description=MultilingualString(
            en=(
                "The learning rate (shrinkage). Used as a multiplicative factor "
                "for leaf values. Use 1 for no shrinkage."
            ),
            es=(
                "La tasa de aprendizaje (shrinkage). Se usa como factor multiplicativo "
                "para los valores de las hojas. Use 1 para no aplicar shrinkage."
            ),
            pt=(
                "A taxa de aprendizado (encolhimento). Usada como fator multiplicativo "
                "para os valores das folhas. Use 1 para não aplicar encolhimento."
            ),
            de=(
                "Die Lernrate (Schrumpfung). Wird als multiplikativer Faktor "
                "für Blattwerte verwendet. Verwenden Sie 1 für keine Schrumpfung."
            ),
            zh="学习率（收缩率）。用作叶节点值的乘法因子，设为1表示不收缩。",
        ),
        alias=MultilingualString(
            en="Learning rate",
            es="Tasa de aprendizaje",
            pt="Taxa de aprendizado",
            de="Lernrate",
            zh="学习率",
        ),
    )  # type: ignore

    max_iter: search_space(
        int_field(ge=1),
        fixed=100,
        low=50,
        high=500,
        description=MultilingualString(
            en="Maximum number of iterations (trees) of the boosting process.",
            es="Número máximo de iteraciones (árboles) del proceso de boosting.",
            pt="Número máximo de iterações (árvores) do processo de boosting.",
            de="Maximale Anzahl von Iterationen (Bäumen) des Boosting-Prozesses.",
            zh="提升过程的最大迭代次数（树的数量）。",
        ),
        alias=MultilingualString(
            en="Max iterations",
            es="Máximas iteraciones",
            pt="Máximas iterações",
            de="Maximale Iterationen",
            zh="最大迭代次数",
        ),
    )  # type: ignore

    max_depth: search_space(
        none_type(int_field(ge=1)),
        fixed=None,
        low=1,
        high=32,
        description=MultilingualString(
            en=("Maximum depth of each tree. If None, depth is not constrained."),
            es=(
                "Profundidad máxima de cada árbol. Si es None, la profundidad "
                "no está restringida."
            ),
            pt=(
                "Profundidade máxima de cada árvore. Se None, a profundidade "
                "não é restringida."
            ),
            de=("Maximale Tiefe jedes Baums. Bei None ist die Tiefe nicht begrenzt."),
            zh="每棵树的最大深度。若为None，则不限制深度。",
        ),
        alias=MultilingualString(
            en="Max depth",
            es="Profundidad máxima",
            pt="Profundidade máxima",
            de="Maximale Tiefe",
            zh="最大深度",
        ),
    )  # type: ignore

    max_leaf_nodes: search_space(
        none_type(int_field(ge=2)),
        fixed=31,
        low=2,
        high=255,
        description=MultilingualString(
            en=(
                "Maximum number of leaves for each tree. Must be strictly greater "
                "than 1. If None, no maximum limit."
            ),
            es=(
                "Número máximo de hojas para cada árbol. Debe ser estrictamente "
                "mayor que 1. Si es None, no hay límite."
            ),
            pt=(
                "Número máximo de folhas para cada árvore. Deve ser estritamente "
                "maior que 1. Se None, não há limite."
            ),
            de=(
                "Maximale Anzahl von Blättern für jeden Baum. Muss strikt größer "
                "als 1 sein. Bei None kein Maximallimit."
            ),
            zh="每棵树的最大叶节点数。必须严格大于1。若为None，则无上限。",
        ),
        alias=MultilingualString(
            en="Max leaf nodes",
            es="Máximos nodos hoja",
            pt="Máximos nós folha",
            de="Maximale Blattknoten",
            zh="最大叶节点数",
        ),
    )  # type: ignore

    min_samples_leaf: search_space(
        int_field(ge=1),
        fixed=20,
        low=1,
        high=100,
        description=MultilingualString(
            en="Minimum number of samples required to be at a leaf node.",
            es="Número mínimo de muestras requeridas para estar en una hoja.",
            pt="Número mínimo de amostras necessárias para estar em um nó folha.",
            de=(
                "Mindestanzahl von Stichproben, die an einem Blattknoten erforderlich "
                "sind."
            ),
            zh="叶节点所需的最少样本数。",
        ),
        alias=MultilingualString(
            en="Min samples leaf",
            es="Mínimas muestras para hoja",
            pt="Mínimas amostras para folha",
            de="Minimale Aufteilungsstichproben für Blatt",
            zh="叶节点最少样本数",
        ),
    )  # type: ignore

    l2_regularization: search_space(
        float_field(ge=0.0),
        fixed=0.0,
        low=0.0,
        high=1.0,
        description=MultilingualString(
            en="The L2 regularisation parameter. Use 0 for no regularisation.",
            es=(
                "El parámetro de regularización L2. "
                "Use 0 para no aplicar regularización."
            ),
            pt=(
                "O parâmetro de regularização L2. Use 0 para não aplicar regularização."
            ),
            de=(
                "Der L2-Regularisierungsparameter. Verwenden Sie 0 für keine "
                "Regularisierung."
            ),
            zh="L2正则化参数。设为0表示不正则化。",
        ),
        alias=MultilingualString(
            en="L2 regularization",
            es="Regularización L2",
            pt="Regularização L2",
            de="L2-Regularisierung",
            zh="L2正则化",
        ),
    )  # type: ignore


class HistGradientBoostingRegression(
    RegressionModel, SklearnLikeRegressor, _HistGradientBoostingRegressor
):
    """Histogram-based gradient boosting regressor for large datasets.

    This regressor discretises features into integer-valued bins before tree
    construction. The histogram representation reduces candidate split points and
    memory footprint, enabling efficient training on datasets with tens of thousands
    of samples or more. It natively supports missing values and is inspired by
    LightGBM.

    Key hyperparameters include ``learning_rate``, ``max_iter``, ``max_depth``,
    ``max_leaf_nodes``, ``min_samples_leaf``, and ``l2_regularization``. The
    implementation wraps scikit-learn's ``HistGradientBoostingRegressor``.

    References
    ----------
    - [1] Ke, G. et al. (2017). "LightGBM: A Highly Efficient Gradient Boosting
           Decision Tree." NeurIPS 30.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html
    """

    SCHEMA = HistGradientBoostingRegressionSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Histogram Gradient Boosting Regression",
        es="Regresión Gradient Boosting con Histogramas",
        pt="Regressor por Gradient Boosting Histogramado",
        de="Histogramm-Gradient-Boosting-Regression",
        zh="基于直方图的梯度提升回归",
    )
    DESCRIPTION: str = MultilingualString(
        en="Fast gradient boosting regression using histogram-based algorithms.",
        es=(
            "Regresión gradient boosting rápida usando algoritmos basados "
            "en histogramas."
        ),
        pt=(
            "Regressão gradient boosting rápida usando algoritmos baseados "
            "em histogramas."
        ),
        de=(
            "Schnelle Gradient-Boosting-Regression mit histogrammbasierten Algorithmen."
        ),
        zh="使用基于直方图算法的快速梯度提升回归。",
    )
    COLOR: str = "#9575CD"
    ICON: str = "RocketLaunch"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.
        """
        super().__init__(**kwargs)
