from sklearn.neighbors import KNeighborsRegressor as _KNeighborsRegressor

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    optimizer_int_field,
    schema_field,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class KNeighborsRegressionSchema(BaseSchema):
    """Schema that configures the K-Nearest Neighbours Regressor.

    KNeighborsRegressor predicts the target by averaging the targets of the
    ``n_neighbors`` nearest training samples. The underlying implementation is
    ``sklearn.neighbors.KNeighborsRegressor``.
    """

    n_neighbors: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 5,
            "lower_bound": 1,
            "upper_bound": 50,
        },
        description=MultilingualString(
            en="Number of neighbours to use for the prediction.",
            es="Número de vecinos a usar para la predicción.",
            pt="Número de vizinhos a usar para a previsão.",
            de="Anzahl der Nachbarn für die Vorhersage.",
            zh="用于预测的邻居数量。",
        ),
        alias=MultilingualString(
            en="N neighbors",
            es="N vecinos",
            pt="N vizinhos",
            de="Anzahl Nachbarn",
            zh="邻居数",
        ),
    )  # type: ignore

    weights: search_space(
        enum_field(enum=["uniform", "distance"]),
        fixed="uniform",
        description=MultilingualString(
            en=(
                "Weight function used in prediction. 'uniform' weights all "
                "neighbours equally; 'distance' weights by inverse distance."
            ),
            es=(
                "Función de pesos usada en la predicción. 'uniform' pondera igual "
                "todos los vecinos; 'distance' pondera por distancia inversa."
            ),
            pt=(
                "Função de pesos usada na previsão. 'uniform' pondera igualmente "
                "todos os vizinhos; 'distance' pondera pela distância inversa."
            ),
            de=(
                "Gewichtungsfunktion für die Vorhersage. 'uniform' gewichtet alle "
                "Nachbarn gleich; 'distance' gewichtet nach inverser Distanz."
            ),
            zh=(
                "预测中使用的权重函数。'uniform' 对所有邻居等权；"
                "'distance' 按距离倒数加权。"
            ),
        ),
        alias=MultilingualString(
            en="Weights", es="Pesos", pt="Pesos", de="Gewichte", zh="权重"
        ),
    )  # type: ignore

    algorithm: search_space(
        enum_field(enum=["auto", "ball_tree", "kd_tree", "brute"]),
        fixed="auto",
        description=MultilingualString(
            en=(
                "Algorithm used to compute nearest neighbours. 'auto' selects the "
                "best based on the values passed to fit."
            ),
            es=(
                "Algoritmo para computar los vecinos más cercanos. 'auto' selecciona "
                "el mejor en función de los valores pasados a fit."
            ),
            pt=(
                "Algoritmo para calcular os vizinhos mais próximos. 'auto' seleciona "
                "o melhor com base nos valores passados ao fit."
            ),
            de=(
                "Algorithmus zur Berechnung der nächsten Nachbarn. 'auto' wählt den "
                "besten basierend auf den an fit übergebenen Werten."
            ),
            zh=("用于计算最近邻的算法。'auto' 根据传入 fit 的值自动选择最优算法。"),
        ),
        alias=MultilingualString(
            en="Algorithm", es="Algoritmo", pt="Algoritmo", de="Algorithmus", zh="算法"
        ),
    )  # type: ignore

    leaf_size: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 30,
            "lower_bound": 5,
            "upper_bound": 100,
        },
        description=MultilingualString(
            en=(
                "Leaf size passed to BallTree or KDTree. Affects query speed "
                "and memory required to store the tree."
            ),
            es=(
                "Tamaño de hoja pasado a BallTree o KDTree. Afecta la velocidad "
                "de consulta y la memoria requerida para almacenar el árbol."
            ),
            pt=(
                "Tamanho de folha passado ao BallTree ou KDTree. Afeta a velocidade "
                "de consulta e a memória necessária para armazenar a árvore."
            ),
            de=(
                "Blattgröße für BallTree oder KDTree. Beeinflusst die "
                "Abfragegeschwindigkeit "
                "und den Speicherbedarf für den Baum."
            ),
            zh="传递给 BallTree 或 KDTree 的叶子大小，影响查询速度和树的内存占用。",
        ),
        alias=MultilingualString(
            en="Leaf size",
            es="Tamaño de hoja",
            pt="Tamanho de folha",
            de="Blattgröße",
            zh="叶子大小",
        ),
    )  # type: ignore

    metric: search_space(
        enum_field(enum=["minkowski", "euclidean", "manhattan", "chebyshev"]),
        fixed="minkowski",
        description=MultilingualString(
            en="Distance metric to use for the neighbour search.",
            es="Métrica de distancia para la búsqueda de vecinos.",
            pt="Métrica de distância para a busca de vizinhos.",
            de="Distanzmetrik für die Nachbarsuche.",
            zh="用于邻居搜索的距离度量。",
        ),
        alias=MultilingualString(
            en="Metric", es="Métrica", pt="Métrica", de="Metrik", zh="距离度量"
        ),
    )  # type: ignore


class KNeighborsRegression(RegressionModel, SklearnLikeRegressor, _KNeighborsRegressor):
    """K-Nearest Neighbours regressor that averages the targets of nearest samples.

    KNeighborsRegressor predicts the target value by computing the (weighted)
    mean of the ``n_neighbors`` closest training points. It is a non-parametric
    method: no training phase is needed, and predictions can capture nonlinear
    patterns. Performance degrades in high dimensional spaces.

    Key hyperparameters include ``n_neighbors``, ``weights``, ``algorithm``, and
    ``metric``. The implementation wraps scikit-learn's ``KNeighborsRegressor``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsRegressor.html
    """

    SCHEMA = KNeighborsRegressionSchema
    DISPLAY_NAME: str = MultilingualString(
        en="K-Nearest Neighbours Regression",
        es="Regresión K-Vecinos Más Cercanos",
        pt="Regressor K-Vizinhos",
        de="K-Nächste-Nachbarn-Regression",
        zh="K 近邻回归",
    )
    DESCRIPTION: str = MultilingualString(
        en="Non-parametric regression that predicts by averaging nearest neighbours.",
        es=(
            "Regresión no paramétrica que predice promediando los vecinos más cercanos."
        ),
        pt=(
            "Regressão não paramétrica que prevê calculando a média dos vizinhos "
            "mais próximos."
        ),
        de=(
            "Nicht-parametrische Regression, die durch Mittelung der nächsten "
            "Nachbarn vorhersagt."
        ),
        zh="通过对最近邻样本取平均进行预测的非参数回归方法。",
    )
    COLOR: str = "#FFA726"
    ICON: str = "ScatterPlot"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.
        """
        super().__init__(**kwargs)
