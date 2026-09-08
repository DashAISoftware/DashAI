from sklearn.ensemble import GradientBoostingRegressor as _GBRegressor

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    float_field,
    int_field,
    none_type,
    schema_field,
    search_space,
    union_type,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.regression_model import RegressionModel
from DashAI.back.models.scikit_learn.model_artifact_mixins import (
    TreeEnsembleArtifactsMixin,
)
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor


class GradientBoostingRSchema(BaseSchema):
    """Schema that configures the Gradient Boosting Regressor.

    Gradient Boosting is a sequential ensemble regression method that fits a new
    decision tree at each stage to the negative gradient (pseudo-residuals) of a
    differentiable loss function. The underlying implementation is
    ``sklearn.ensemble.GradientBoostingRegressor``.
    """

    loss: search_space(
        enum_field(enum=["squared_error", "absolute_error", "huber", "quantile"]),
        fixed="squared_error",
        description=MultilingualString(
            en="Loss function to be optimized.",
            es="Función de pérdida a optimizar.",
            pt="Função de perda a ser otimizada.",
            de="Zu optimierende Verlustfunktion.",
            zh="待优化的损失函数。",
        ),
        alias=MultilingualString(
            en="Loss", es="Pérdida", pt="Perda", de="Verlust", zh="损失函数"
        ),
    )  # type: ignore

    learning_rate: search_space(
        float_field(ge=0.01),
        fixed=0.1,
        low=0.01,
        high=1.0,
        description=MultilingualString(
            en="Learning rate shrinks the contribution of each tree.",
            es="La tasa de aprendizaje reduce la contribución de cada árbol.",
            pt="A taxa de aprendizado reduz a contribuição de cada árvore.",
            de="Die Lernrate verringert den Beitrag jedes Baums.",
            zh="学习率缩小每棵树的贡献。",
        ),
        alias=MultilingualString(
            en="Learning rate",
            es="Tasa de aprendizaje",
            pt="Taxa de aprendizado",
            de="Lernrate",
            zh="学习率",
        ),
    )  # type: ignore

    n_estimators: search_space(
        int_field(ge=1),
        fixed=100,
        low=10,
        high=1000,
        description=MultilingualString(
            en="The number of boosting stages to be run.",
            es="El número de etapas de boosting a ejecutar.",
            pt="O número de etapas de boosting a executar.",
            de="Die Anzahl der auszuführenden Boosting-Stufen.",
            zh="要运行的提升阶段数。",
        ),
        alias=MultilingualString(
            en="N estimators",
            es="N estimadores",
            pt="N estimadores",
            de="Anzahl Schätzer",
            zh="估计器数量",
        ),
    )  # type: ignore

    subsample: search_space(
        float_field(ge=0.1, le=1.0),
        fixed=1.0,
        low=0.1,
        high=1.0,
        description=MultilingualString(
            en=(
                "The fraction of samples to be used for fitting the "
                "individual base learners."
            ),
            es=(
                "La fracción de muestras a usar para ajustar los "
                "aprendices base individuales."
            ),
            pt=(
                "A fração de amostras a usar para ajustar os "
                "aprendizes base individuais."
            ),
            de=("Der Anteil der Stichproben zum Anpassen der einzelnen Basislerner."),
            zh="用于拟合各基学习器的样本比例。",
        ),
        alias=MultilingualString(
            en="Subsample",
            es="Submuestreo",
            pt="Subamostra",
            de="Teilstichprobe",
            zh="子样本比例",
        ),
    )  # type: ignore

    criterion: search_space(
        # "mse" and "mae" were deprecated in scikit-learn 1.0 and removed in
        # 1.2; picking either raised InvalidParameterError at fit time, inside a
        # worker. "squared_error" is what replaced them.
        enum_field(enum=["friedman_mse", "squared_error"]),
        fixed="friedman_mse",
        description=MultilingualString(
            en="The function to measure the quality of a split.",
            es="La función para medir la calidad de una división.",
            pt="A função para medir a qualidade de uma divisão.",
            de="Die Funktion zur Messung der Qualität einer Aufteilung.",
            zh="衡量分裂质量的函数。",
        ),
        alias=MultilingualString(
            en="Criterion", es="Criterio", pt="Critério", de="Kriterium", zh="分裂准则"
        ),
    )  # type: ignore

    min_samples_split: search_space(
        float_field(gt=0.0, le=1.0),
        fixed=0.5,
        low=0.1,
        high=1.0,
        description=MultilingualString(
            en="The minimum number of samples required to split an internal node.",
            es="El número mínimo de muestras requeridas para dividir un nodo interno.",
            pt="O número mínimo de amostras necessárias para dividir um nó interno.",
            de="Mindestanzahl von Stichproben zum Aufteilen eines internen Knotens.",
            zh="分裂内部节点所需的最少样本数。",
        ),
        alias=MultilingualString(
            en="Min samples split",
            es="Mínimas muestras de división",
            pt="Mínimas amostras de divisão",
            de="Minimale Aufteilungsstichproben",
            zh="最小分裂样本数",
        ),
    )  # type: ignore

    min_samples_leaf: search_space(
        int_field(ge=1),
        fixed=1,
        low=1,
        high=20,
        description=MultilingualString(
            en="The minimum number of samples required to be at a leaf node.",
            es="El número mínimo de muestras requeridas para estar en una hoja.",
            pt="O número mínimo de amostras necessárias para estar em um nó folha.",
            de="Mindestanzahl von Stichproben an einem Blattknoten.",
            zh="叶节点所需的最少样本数。",
        ),
        alias=MultilingualString(
            en="Min samples leaf",
            es="Mínimas muestras para hoja",
            pt="Mínimas amostras para folha",
            de="Minimale Stichproben für Blatt",
            zh="最小叶节点样本数",
        ),
    )  # type: ignore

    min_weight_fraction_leaf: schema_field(
        float_field(ge=0.0, le=0.5),
        placeholder=0.0,
        description=MultilingualString(
            en=(
                "The minimum weighted fraction of the sum total of weights "
                "(of all the input samples) required to be at a leaf node."
            ),
            es=(
                "La fracción ponderada mínima de la suma total de pesos "
                "(de todas las muestras de entrada) requerida para estar en una hoja."
            ),
            pt=(
                "A fração ponderada mínima da soma total de pesos "
                "(de todas as amostras de entrada) necessária para estar em "
                "um nó folha."
            ),
            de=(
                "Der minimale gewichtete Anteil der Gesamtgewichte "
                "(aller Eingangsstichproben), der an einem Blattknoten erforderlich "
                "ist."
            ),
            zh="叶节点所需的所有输入样本总权重的最小加权比例。",
        ),
        alias=MultilingualString(
            en="Min weight fraction leaf",
            es="Fracción de peso mínima para hoja",
            pt="Fração mínima de peso para folha",
            de="Minimaler Gewichtsanteil für Blatt",
            zh="最小权重比例叶节点",
        ),
    )  # type: ignore

    max_depth: search_space(
        none_type(int_field(ge=1)),
        fixed=3,
        low=1,
        high=32,
        description=MultilingualString(
            en="The maximum depth of the individual regression estimators.",
            es="La profundidad máxima de los estimadores de regresión individuales.",
            pt="A profundidade máxima dos estimadores de regressão individuais.",
            de="Die maximale Tiefe der einzelnen Regressionsschätzer.",
            zh="各回归估计器的最大深度。",
        ),
        alias=MultilingualString(
            en="Max depth",
            es="Profundidad máxima",
            pt="Profundidade máxima",
            de="Maximale Tiefe",
            zh="最大深度",
        ),
    )  # type: ignore

    min_impurity_decrease: schema_field(
        float_field(ge=0.0),
        placeholder=0.0,
        description=MultilingualString(
            en=(
                "A node will be split if this split induces a decrease of "
                "the impurity greater than or equal to this value."
            ),
            es=(
                "Un nodo se dividirá si esta división induce una disminución de "
                "la impureza mayor o igual a este valor."
            ),
            pt=(
                "Um nó será dividido se esta divisão induzir uma diminuição da "
                "impureza maior ou igual a este valor."
            ),
            de=(
                "Ein Knoten wird aufgeteilt, wenn diese Aufteilung eine Verringerung "
                "der Unreinheit größer oder gleich diesem Wert bewirkt."
            ),
            zh="若分裂导致的不纯度降低大于或等于此值，则对节点进行分裂。",
        ),
        alias=MultilingualString(
            en="Min impurity decrease",
            es="Disminución mínima de impureza",
            pt="Diminuição mínima de impureza",
            de="Minimale Unreinheitsabnahme",
            zh="最小不纯度降低",
        ),
    )  # type: ignore

    random_state: schema_field(
        none_type(int_field(ge=0)),
        placeholder=None,
        description=MultilingualString(
            en=(
                "The seed of the pseudo-random number generator to use "
                "when shuffling the data."
            ),
            es=(
                "La semilla del generador de números pseudoaleatorios a usar "
                "al mezclar los datos."
            ),
            pt=(
                "A semente do gerador de números pseudoaleatórios a usar "
                "ao embaralhar os dados."
            ),
            de=("Der Seed des Pseudozufallszahlengenerators beim Mischen der Daten."),
            zh="打乱数据时使用的伪随机数生成器种子。",
        ),
        alias=MultilingualString(
            en="Random state",
            es="Estado aleatorio",
            pt="Estado aleatório",
            de="Zufallszustand",
            zh="随机状态",
        ),
    )  # type: ignore

    max_features: search_space(
        # None belongs outside the enum: enum_field is str-typed, so a None
        # member is advertised in the JSON Schema and then rejected by the
        # field's own validator, which made this field's default unsubmittable.
        none_type(
            union_type(
                float_field(gt=0.0, le=1.0),
                enum_field(enum=["sqrt", "log2"]),
            )
        ),
        fixed=None,
        description=MultilingualString(
            en=("The number of features to consider when looking for the best split."),
            es=(
                "El número de características a considerar al buscar la mejor división."
            ),
            pt=("O número de características a considerar ao buscar a melhor divisão."),
            de=(
                "Die Anzahl der Merkmale, die bei der Suche nach der besten Aufteilung "
                "berücksichtigt werden."
            ),
            zh="寻找最佳分裂时考虑的特征数量。",
        ),
        alias=MultilingualString(
            en="Max features",
            es="Máximas características",
            pt="Máximo de características",
            de="Maximale Merkmale",
            zh="最大特征数",
        ),
    )  # type: ignore

    alpha: search_space(
        float_field(gt=0.0, le=1.0),
        fixed=0.9,
        low=0.1,
        high=1.0,
        description=MultilingualString(
            en=(
                "The alpha-quantile of the Huber loss function and the "
                "quantile loss function."
            ),
            es=(
                "El alfa-cuantil de la función de pérdida de Huber y "
                "la función de pérdida cuantil."
            ),
            pt=(
                "O quantil alfa da função de perda de Huber e "
                "da função de perda quantil."
            ),
            de=(
                "Das Alpha-Quantil der Huber-Verlustfunktion und "
                "der Quantil-Verlustfunktion."
            ),
            zh="Huber损失函数和分位数损失函数的alpha分位数。",
        ),
        alias=MultilingualString(
            en="Alpha", es="Alfa", pt="Alfa", de="Alpha", zh="Alpha"
        ),
    )  # type: ignore

    verbose: schema_field(
        int_field(ge=0),
        placeholder=0,
        description=MultilingualString(
            en="Enable verbose output.",
            es="Habilitar salida detallada.",
            pt="Habilitar saída detalhada.",
            de="Ausführliche Ausgabe aktivieren.",
            zh="启用详细输出。",
        ),
        alias=MultilingualString(
            en="Verbose", es="Verboso", pt="Verboso", de="Ausführlich", zh="详细输出"
        ),
    )  # type: ignore

    max_leaf_nodes: search_space(
        none_type(int_field(ge=1)),
        fixed=None,
        low=2,
        high=255,
        description=MultilingualString(
            en="Grow trees with max_leaf_nodes in best-first fashion.",
            es="Crecer árboles con max_leaf_nodes de manera best-first.",
            pt="Crescer árvores com max_leaf_nodes de maneira melhor-primeiro.",
            de="Bäume mit max_leaf_nodes nach dem Best-First-Verfahren wachsen lassen.",
            zh="以最优优先方式生长最多含max_leaf_nodes个叶节点的树。",
        ),
        alias=MultilingualString(
            en="Max leaf nodes",
            es="Máximos nodos hoja",
            pt="Máximos nós folha",
            de="Maximale Blattknoten",
            zh="最大叶节点数",
        ),
    )  # type: ignore

    warm_start: schema_field(
        bool_field(),
        placeholder=False,
        description=MultilingualString(
            en=(
                "When set to True, reuse the solution of the previous call "
                "to fit and add more estimators to the ensemble."
            ),
            es=(
                "Cuando se establece en True, reutiliza la solución de la llamada "
                "anterior a fit y agrega más estimadores al conjunto."
            ),
            pt=(
                "Quando definido como True, reutiliza a solução da chamada anterior "
                "a fit e adiciona mais estimadores ao conjunto."
            ),
            de=(
                "Wenn True, wird die Lösung des vorherigen fit-Aufrufs wiederverwendet "
                "und dem Ensemble weitere Schätzer hinzugefügt."
            ),
            zh="设为True时，复用上次fit调用的结果并向集成中添加更多估计器。",
        ),
        alias=MultilingualString(
            en="Warm start",
            es="Inicio en caliente",
            pt="Início a quente",
            de="Warmer Start",
            zh="热启动",
        ),
    )  # type: ignore

    validation_fraction: search_space(
        float_field(gt=0.0, le=1.0),
        fixed=0.1,
        low=0.1,
        high=0.5,
        description=MultilingualString(
            en=(
                "The proportion of training data to set aside as "
                "validation set for early stopping."
            ),
            es=(
                "La proporción de datos de entrenamiento a reservar como "
                "conjunto de validación para detención temprana."
            ),
            pt=(
                "A proporção dos dados de treinamento a reservar como "
                "conjunto de validação para parada antecipada."
            ),
            de=(
                "Der Anteil der Trainingsdaten, der als Validierungsmenge "
                "für frühzeitigen Stopp zurückgehalten wird."
            ),
            zh="用于早停验证集的训练数据比例。",
        ),
        alias=MultilingualString(
            en="Validation fraction",
            es="Fracción de validación",
            pt="Fração de validação",
            de="Validierungsanteil",
            zh="验证集比例",
        ),
    )  # type: ignore

    n_iter_no_change: search_space(
        none_type(int_field(ge=1)),
        fixed=None,
        low=1,
        high=20,
        description=MultilingualString(
            en=(
                "The number of iterations with no improvement to wait "
                "before stopping the training."
            ),
            es=(
                "El número de iteraciones sin mejora a esperar "
                "antes de detener el entrenamiento."
            ),
            pt=(
                "O número de iterações sem melhora a aguardar "
                "antes de interromper o treinamento."
            ),
            de=(
                "Die Anzahl der Iterationen ohne Verbesserung, die "
                "vor dem Trainingsabbruch abgewartet werden."
            ),
            zh="停止训练前无改善的迭代次数。",
        ),
        alias=MultilingualString(
            en="N iterations no change",
            es="N iteraciones sin cambio",
            pt="N iterações sem mudança",
            de="N Iterationen ohne Änderung",
            zh="无改善迭代次数",
        ),
    )  # type: ignore

    tol: search_space(
        float_field(ge=0.0),
        fixed=0.0001,
        low=1e-05,
        high=0.1,
        description=MultilingualString(
            en="Tolerance for the early stopping.",
            es="Tolerancia para la detención temprana.",
            pt="Tolerância para a parada antecipada.",
            de="Toleranz für den frühzeitigen Stopp.",
            zh="早停的容忍度。",
        ),
        alias=MultilingualString(
            en="Tolerance", es="Tolerancia", pt="Tolerância", de="Toleranz", zh="容忍度"
        ),
    )  # type: ignore

    ccp_alpha: search_space(
        float_field(ge=0.0),
        fixed=0.0,
        low=0.0,
        high=1.0,
        description=MultilingualString(
            en="Complexity parameter used for Minimal Cost-Complexity Pruning.",
            es="Parámetro de complejidad usado para poda de costo-complejidad mínima.",
            pt=(
                "Parâmetro de complexidade usado para poda de "
                "custo-complexidade mínima."
            ),
            de="Komplexitätsparameter für minimales Kosten-Komplexitäts-Pruning.",
            zh="用于最小代价复杂度剪枝的复杂度参数。",
        ),
        alias=MultilingualString(
            en="CCP alpha", es="CCP alfa", pt="CCP alfa", de="CCP Alpha", zh="CCP Alpha"
        ),
    )  # type: ignore


class GradientBoostingR(
    TreeEnsembleArtifactsMixin,
    RegressionModel,
    SklearnLikeRegressor,
    _GBRegressor,
):
    """Gradient boosting regressor that builds
    an ensemble of decision trees sequentially.

    Gradient Boosting builds an additive model in a forward stage-wise fashion. At
    each stage a shallow decision tree is fitted to the negative gradient of the
    chosen loss function with respect to the current ensemble prediction. A
    ``learning_rate`` shrinkage factor scales the contribution of each new tree,
    trading a slower learning process for better generalisation.

    Key hyperparameters include ``n_estimators`` (number of boosting stages),
    ``learning_rate``, ``max_depth``, ``subsample`` (fraction of training samples
    per tree, enabling stochastic gradient boosting), ``loss``, and
    ``min_samples_split``. The implementation wraps scikit-learn's
    ``GradientBoostingRegressor``.

    References
    ----------
    - [1] Friedman, J.H. (2001). "Greedy function approximation: a gradient
           boosting machine." Annals of Statistics, 29(5), 1189-1232.
           https://doi.org/10.1214/aos/1013203451
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html
    """

    SCHEMA = GradientBoostingRSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Gradient Boosting Regression",
        es="Regresión Gradient Boosting",
        pt="Regressor por Gradient Boosting",
        de="Gradient-Boosting-Regression",
        zh="梯度提升回归",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Ensemble method that builds trees sequentially to correct previous errors."
        ),
        es=(
            "Método de conjunto que construye árboles secuencialmente para corregir "
            "errores anteriores."
        ),
        pt=(
            "Método de conjunto que constrói árvores sequencialmente para corrigir "
            "erros anteriores."
        ),
        de=(
            "Ensemble-Methode, die Bäume sequenziell aufbaut, um vorherige Fehler zu "
            "korrigieren."
        ),
        zh="顺序构建决策树以纠正前次误差的集成回归方法。",
    )
    COLOR: str = "#4CAF50"
    ICON: str = "AutoGraph"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.  See
            the associated schema class for available keys and their defaults.
        """
        super().__init__(**kwargs)
