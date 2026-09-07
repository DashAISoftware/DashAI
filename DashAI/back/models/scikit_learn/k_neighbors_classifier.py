from sklearn.neighbors import KNeighborsClassifier as _KNeighborsClassifier

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    optimizer_int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class KNeighborsClassifierSchema(BaseSchema):
    """Schema that configures the K-Nearest Neighbors Classifier.

    K-Nearest Neighbors (KNN) is a non-parametric supervised classification method
    that assigns a class to each sample by majority vote of its ``k`` closest
    training points in the feature space. It is used for tabular classification tasks.
    The underlying implementation is ``sklearn.neighbors.KNeighborsClassifier``.
    """

    n_neighbors: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 5,
            "lower_bound": 5,
            "upper_bound": 10,
        },
        description=MultilingualString(
            en=(
                "The number of neighbors to consider in each input for classification. "
            ),
            es=(
                "Es el número de vecinos a considerar en "
                "cada entrada para la clasificación. "
            ),
            pt=(
                "O número de vizinhos a considerar em "
                "cada entrada para a classificação. "
            ),
            de=(
                "Die Anzahl der Nachbarn, die für jede Eingabe bei der Klassifikation "
                "berücksichtigt werden. "
            ),
            zh="分类时每个输入所考虑的邻居数量。",
        ),
        alias=MultilingualString(
            en="N neighbors",
            es="N vecinos",
            pt="N vizinhos",
            de="Anzahl Nachbarn",
            zh="邻居数",
        ),
    )  # type: ignore
    weights: schema_field(
        enum_field(enum=["uniform", "distance"]),
        placeholder="uniform",
        description=MultilingualString(
            en="The parameter must be 'uniform' or 'distance'.",
            es="El parámetro debe ser 'uniform' o 'distance'.",
            pt="O parâmetro deve ser 'uniform' ou 'distance'.",
            de="Der Parameter muss 'uniform' oder 'distance' sein.",
            zh="参数必须为 'uniform' 或 'distance'。",
        ),
        alias=MultilingualString(
            en="Weights", es="Pesos", pt="Pesos", de="Gewichte", zh="权重"
        ),
    )  # type: ignore
    algorithm: schema_field(
        enum_field(enum=["auto", "ball_tree", "kd_tree", "brute"]),
        placeholder="auto",
        description=MultilingualString(
            en=("The parameter must be 'auto', 'ball_tree', 'kd_tree', or 'brute'."),
            es=("El parámetro debe ser 'auto', 'ball_tree', 'kd_tree' o 'brute'."),
            pt=("O parâmetro deve ser 'auto', 'ball_tree', 'kd_tree' ou 'brute'."),
            de=("Der Parameter muss 'auto', 'ball_tree', 'kd_tree' oder 'brute' sein."),
            zh="参数必须为 'auto'、'ball_tree'、'kd_tree' 或 'brute'。",
        ),
        alias=MultilingualString(
            en="Algorithm",
            es="Algoritmo",
            pt="Algoritmo",
            de="Algorithmus",
            zh="算法",
        ),
    )  # type: ignore


class KNeighborsClassifier(
    TabularClassificationModel, SklearnLikeClassifier, _KNeighborsClassifier
):
    """K-nearest neighbours classifier that predicts
    the majority class among neighbours.

    KNN is a lazy, instance-based learning algorithm: no explicit model is fitted
    during training. At prediction time the algorithm finds the ``k`` nearest training
    points (by Euclidean or another distance metric) and returns the majority class.
    When ``weights="distance"`` closer neighbours have a proportionally larger
    influence on the prediction.

    Key hyperparameters are ``n_neighbors`` (the number of neighbours ``k``),
    ``weights`` (uniform or distance-weighted voting), and ``algorithm`` (data
    structure used for neighbour lookup: ball tree, kd-tree, or brute force). The
    implementation wraps scikit-learn's ``KNeighborsClassifier``.

    References
    ----------
    - [1] Cover, T. & Hart, P. (1967). "Nearest neighbor pattern classification."
           IEEE Transactions on Information Theory, 13(1), 21-27.
           https://doi.org/10.1109/TIT.1967.1053964
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html
    """

    SCHEMA = KNeighborsClassifierSchema
    DISPLAY_NAME: str = MultilingualString(
        en="K-Nearest Neighbors (KNN)",
        es="K-Vecinos más Cercanos (KNN)",
        pt="Classificador K-Vizinhos",
        de="K-Nächste-Nachbarn (KNN)",
        zh="K 近邻分类器（KNN）",
    )
    DESCRIPTION: str = MultilingualString(
        en="Classification based on k nearest training examples in feature space.",
        es=(
            "Clasificación basada en los k ejemplos de entrenamiento más cercanos en "
            "el espacio de características."
        ),
        pt=(
            "Classificação baseada nos k exemplos de treinamento mais próximos no "
            "espaço de características."
        ),
        de=(
            "Klassifikation basierend auf den k nächsten Trainingsbeispielen im "
            "Merkmalsraum."
        ),
        zh="基于特征空间中 k 个最近训练样本的分类方法。",
    )
    COLOR: str = "#FFD54F"
    ICON: str = "ScatterPlot"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.  See
            the associated schema class for available keys and their defaults.
        """
        super().__init__(**kwargs)
