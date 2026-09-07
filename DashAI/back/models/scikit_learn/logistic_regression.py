from sklearn.linear_model import LogisticRegression as _LogisticRegression

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    none_type,
    search_space,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class LogisticRegressionSchema(BaseSchema):
    """Schema that configures the Logistic Regression classifier.

    Logistic Regression is a supervised classification method that fits a linear
    decision boundary using a logistic (sigmoid) function. It supports binary and
    multiclass classification via the one-vs-rest strategy and optional L1, L2, or
    Elastic-Net regularisation. The underlying implementation is
    ``sklearn.linear_model.LogisticRegression``.
    """

    penalty: search_space(
        enum_field(enum=["l2", "l1", "elasticnet"]),
        fixed="l2",
        description=MultilingualString(
            en="Specify the norm of the penalty",
            es="Especifica la norma de la penalización",
            pt="Especifica a norma da penalidade",
            de="Gibt die Norm der Bestrafung an",
            zh="指定惩罚项的范数",
        ),
        alias=MultilingualString(
            en="Penalty",
            es="Penalización",
            pt="Penalidade",
            de="Bestrafung",
            zh="惩罚项",
        ),
    )  # type: ignore
    tol: search_space(
        float_field(ge=0.0),
        fixed=0.0,
        low=0.0,
        high=5.0,
        description=MultilingualString(
            en="Tolerance for stopping criteria.",
            es="Tolerancia para el criterio de detención.",
            pt="Tolerância para o critério de parada.",
            de="Toleranz für das Abbruchkriterium.",
            zh="停止准则的容差。",
        ),
        alias=MultilingualString(
            en="Tolerance", es="Tolerancia", pt="Tolerância", de="Toleranz", zh="容差"
        ),
    )  # type: ignore
    C: search_space(
        float_field(gt=0.0),
        fixed=1.0,
        low=1.0,
        high=7.0,
        description=MultilingualString(
            en=(
                "Inverse of regularization strength, smaller values specify stronger "
                "regularization. Must be a positive number."
            ),
            es=(
                "Inverso de la fuerza de regularización, valores más pequeños "
                "especifican una regularización más fuerte. Debe ser un número "
                "positivo."
            ),
            pt=(
                "Inverso da força de regularização, valores menores especificam "
                "regularização mais forte. Deve ser um número positivo."
            ),
            de=(
                "Kehrwert der Regularisierungsstärke; kleinere Werte bedeuten stärkere "
                "Regularisierung. Muss eine positive Zahl sein."
            ),
            zh=("正则化强度的倒数，较小的值表示更强的正则化。必须为正数。"),
        ),
        alias=MultilingualString(en="C", es="C", pt="C", de="C", zh="C"),
    )  # type: ignore
    max_iter: search_space(
        int_field(ge=50),
        fixed=100,
        low=50,
        high=250,
        description=MultilingualString(
            en=("Maximum number of iterations taken for the solvers to converge."),
            es=("Número máximo de iteraciones para que los solucionadores converjan."),
            pt=("Número máximo de iterações para os solvers convergirem."),
            de=("Maximale Anzahl von Iterationen für die Konvergenz der Löser."),
            zh=("求解器收敛所需的最大迭代次数。"),
        ),
        alias=MultilingualString(
            en="Max iterations",
            es="Máximas iteraciones",
            pt="Máximas iterações",
            de="Maximale Iterationen",
            zh="最大迭代次数",
        ),
    )  # type: ignore
    class_weight: search_space(
        none_type(enum_field(enum=["balanced"])),
        fixed=None,
        description=MultilingualString(
            en=(
                "Weights associated with classes, used to correct for class "
                "imbalance. 'balanced' automatically adjusts weights inversely "
                "proportional to class frequencies. Use None for no weighting."
            ),
            es=(
                "Pesos asociados a las clases, usados para corregir el desbalance "
                "de clases. 'balanced' ajusta automáticamente los pesos de forma "
                "inversamente proporcional a la frecuencia de cada clase. Use None "
                "para no aplicar ponderación."
            ),
            pt=(
                "Pesos associados às classes, usados para corrigir o "
                "desbalanceamento de classes. 'balanced' ajusta automaticamente os "
                "pesos de forma inversamente proporcional à frequência de cada "
                "classe. Use None para não aplicar ponderação."
            ),
            de=(
                "Gewichte, die den Klassen zugeordnet sind, um "
                "Klassenungleichgewichte auszugleichen. 'balanced' passt die "
                "Gewichte automatisch umgekehrt proportional zur "
                "Klassenhäufigkeit an. Verwenden Sie None für keine Gewichtung."
            ),
            zh=(
                "与类别关联的权重，用于纠正类别不平衡。'balanced'会根据类别频率的"
                "反比自动调整权重。使用None表示不加权。"
            ),
        ),
        alias=MultilingualString(
            en="Class weight",
            es="Peso de clase",
            pt="Peso da classe",
            de="Klassengewicht",
            zh="类别权重",
        ),
    )  # type: ignore


class LogisticRegression(
    TabularClassificationModel, SklearnLikeClassifier, _LogisticRegression
):
    """Logistic regression classifier with L1, L2, or Elastic-Net regularisation.

    Logistic Regression models the probability that a sample belongs to a given
    class by applying the logistic (sigmoid) function to a linear combination of
    input features. The decision boundary is linear in the feature space. For
    multiclass problems the model applies a one-vs-rest (OvR) strategy by default.

    Regularisation is controlled by the penalty (L1, L2, or Elastic-Net) and the
    inverse-strength parameter ``C``. The solver is selected automatically based on
    the chosen penalty. Key hyperparameters are ``penalty``, ``C``, ``tol``, and
    ``max_iter``. The implementation wraps scikit-learn's ``LogisticRegression``.

    References
    ----------
    - [1] Cox, D.R. (1958). "The regression analysis of binary sequences."
           Journal of the Royal Statistical Society, Series B, 20(2), 215-242.
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
    """

    SCHEMA = LogisticRegressionSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Logistic Regression",
        es="Regresión Logística",
        pt="Regressão Logística",
        de="Logistische Regression",
        zh="逻辑回归",
    )
    DESCRIPTION: str = MultilingualString(
        en="Linear model for classification using logistic function.",
        es="Modelo lineal para clasificación usando la función logística.",
        pt="Modelo linear para classificação usando a função logística.",
        de="Lineares Modell zur Klassifikation mit der logistischen Funktion.",
        zh="使用逻辑函数进行分类的线性模型。",
    )
    COLOR: str = "#64B5F6"
    ICON: str = "TrendingUp"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.  See
            the associated schema class for available keys and their defaults.
        """
        super().__init__(**kwargs)
