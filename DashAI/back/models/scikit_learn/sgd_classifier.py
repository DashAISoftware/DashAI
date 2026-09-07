from sklearn.linear_model import SGDClassifier as _SGDClassifier

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    none_type,
    optimizer_float_field,
    optimizer_int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class SGDClassifierSchema(BaseSchema):
    """Schema that configures the SGD Classifier.

    SGDClassifier implements regularised linear classifiers (SVM, logistic
    regression, etc.) with Stochastic Gradient Descent training. The loss function
    determines the model type. Because not all loss functions expose
    ``predict_proba``, this wrapper always uses CalibratedClassifierCV for
    consistent probability estimates. The underlying implementation is
    ``sklearn.linear_model.SGDClassifier``.
    """

    loss: schema_field(
        enum_field(
            enum=[
                "hinge",
                "log_loss",
                "modified_huber",
                "squared_hinge",
                "perceptron",
            ]
        ),
        placeholder="hinge",
        description=MultilingualString(
            en=(
                "The loss function to use. 'hinge' gives a linear SVM; 'log_loss' "
                "gives logistic regression; 'modified_huber' is smoother; "
                "'squared_hinge' is like hinge but quadratically penalised; "
                "'perceptron' is the linear loss used by the perceptron algorithm."
            ),
            es=(
                "La función de pérdida a usar. 'hinge' da un SVM lineal; 'log_loss' "
                "da regresión logística; 'modified_huber' es más suave; "
                "'squared_hinge' es como hinge pero penalizado cuadráticamente; "
                "'perceptron' es la pérdida lineal usada por el algoritmo perceptrón."
            ),
            pt=(
                "A função de perda a usar. 'hinge' dá um SVM linear; 'log_loss' "
                "dá regressão logística; 'modified_huber' é mais suave; "
                "'squared_hinge' é como hinge mas penalizado quadraticamente; "
                "'perceptron' é a perda linear usada pelo algoritmo perceptron."
            ),
            de=(
                "Die zu verwendende Verlustfunktion. 'hinge' ergibt ein lineares SVM; "
                "'log_loss' "
                "ergibt logistische Regression; 'modified_huber' ist glatter; "
                "'squared_hinge' ist wie hinge aber quadratisch bestraft; "
                "'perceptron' ist der lineare Verlust des Perceptron-Algorithmus."
            ),
            zh=(
                "使用的损失函数。'hinge'给出线性SVM；'log_loss'给出逻辑回归；"
                "'modified_huber'更平滑；'squared_hinge'类似hinge但使用二次惩罚；"
                "'perceptron'是感知机算法使用的线性损失。"
            ),
        ),
        alias=MultilingualString(
            en="Loss", es="Pérdida", pt="Perda", de="Verlustfunktion", zh="损失函数"
        ),
    )  # type: ignore

    alpha: schema_field(
        optimizer_float_field(ge=1e-6),
        placeholder={
            "optimize": False,
            "fixed_value": 0.0001,
            "lower_bound": 1e-6,
            "upper_bound": 1.0,
        },
        description=MultilingualString(
            en=(
                "Regularisation parameter. Higher values result in stronger "
                "regularisation."
            ),
            es=(
                "Parámetro de regularización. Valores más altos resultan en "
                "regularización más fuerte."
            ),
            pt=(
                "Parâmetro de regularização. Valores mais altos resultam em "
                "regularização mais forte."
            ),
            de=(
                "Regularisierungsparameter. Höhere Werte führen zu stärkerer "
                "Regularisierung."
            ),
            zh="正则化参数。值越大，正则化越强。",
        ),
        alias=MultilingualString(
            en="Alpha", es="Alfa", pt="Alfa", de="Alpha", zh="Alpha"
        ),
    )  # type: ignore

    max_iter: schema_field(
        optimizer_int_field(ge=1),
        placeholder={
            "optimize": False,
            "fixed_value": 1000,
            "lower_bound": 100,
            "upper_bound": 5000,
        },
        description=MultilingualString(
            en="The maximum number of passes over the training data (epochs).",
            es="El número máximo de pasadas sobre los datos de entrenamiento (épocas).",
            pt="O número máximo de passagens sobre os dados de treinamento (épocas).",
            de="Die maximale Anzahl von Durchläufen über die Trainingsdaten (Epochen).",
            zh="对训练数据的最大遍历次数（轮次）。",
        ),
        alias=MultilingualString(
            en="Max iterations",
            es="Máximas iteraciones",
            pt="Iterações máximas",
            de="Maximale Iterationen",
            zh="最大迭代次数",
        ),
    )  # type: ignore

    tol: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1e-3,
            "lower_bound": 1e-6,
            "upper_bound": 1e-1,
        },
        description=MultilingualString(
            en=("The stopping criterion. Training stops when loss > best_loss - tol."),
            es=(
                "El criterio de parada. El entrenamiento se detiene cuando "
                "pérdida > mejor_pérdida - tol."
            ),
            pt=(
                "O critério de parada. O treinamento para quando "
                "perda > melhor_perda - tol."
            ),
            de=(
                "Das Abbruchkriterium. Das Training stoppt, wenn Verlust > "
                "bester_Verlust - tol."
            ),
            zh="停止准则。当损失 > 最优损失 - tol 时训练停止。",
        ),
        alias=MultilingualString(
            en="Tolerance", es="Tolerancia", pt="Tolerância", de="Toleranz", zh="容差"
        ),
    )  # type: ignore

    learning_rate: schema_field(
        enum_field(enum=["constant", "optimal", "invscaling", "adaptive"]),
        placeholder="optimal",
        description=MultilingualString(
            en=(
                "The learning rate schedule. 'optimal' uses 1/(alpha*(t+t0)); "
                "'constant' keeps eta0 constant; 'invscaling' decreases as "
                "1/t^power; 'adaptive' halves the rate when training stops."
            ),
            es=(
                "El programa de tasa de aprendizaje. 'optimal' usa "
                "1/(alpha*(t+t0)); 'constant' mantiene eta0 constante; "
                "'invscaling' decrece como 1/t^power; 'adaptive' reduce a la "
                "mitad la tasa cuando el entrenamiento deja de mejorar."
            ),
            pt=(
                "O esquema de taxa de aprendizado. 'optimal' usa "
                "1/(alpha*(t+t0)); 'constant' mantém eta0 constante; "
                "'invscaling' decresce como 1/t^power; 'adaptive' reduz à "
                "metade a taxa quando o treinamento para de melhorar."
            ),
            de=(
                "Der Lernraten-Zeitplan. 'optimal' verwendet 1/(alpha*(t+t0)); "
                "'constant' hält eta0 konstant; 'invscaling' sinkt als "
                "1/t^power; 'adaptive' halbiert die Rate, wenn das Training stagniert."
            ),
            zh=(
                "学习率调度方案。'optimal'使用1/(alpha*(t+t0))；'constant'保持eta0不变；"
                "'invscaling'按1/t^power递减；'adaptive'在训练停滞时将学习率减半。"
            ),
        ),
        alias=MultilingualString(
            en="Learning rate",
            es="Tasa de aprendizaje",
            pt="Taxa de aprendizado",
            de="Lernrate",
            zh="学习率",
        ),
    )  # type: ignore

    random_state: schema_field(
        none_type(optimizer_int_field(ge=0)),
        placeholder=None,
        description=MultilingualString(
            en=(
                "The seed of the pseudo-random number generator. Pass an int for "
                "reproducible output, or None to not set a specific seed."
            ),
            es=(
                "La semilla del generador de números pseudoaleatorios. Pase un int "
                "para salida reproducible, o None para no fijar una semilla."
            ),
            pt=(
                "A semente do gerador de números pseudoaleatórios. Passe um int "
                "para saída reproduzível, ou None para não definir uma semente."
            ),
            de=(
                "Der Startwert des Pseudo-Zufallszahlengenerators. Übergeben Sie eine "
                "ganze Zahl für reproduzierbare Ausgaben oder None für keinen "
                "bestimmten Startwert."
            ),
            zh=(
                "伪随机数生成器的种子。传入整数以获得可复现的输出，"
                "传入None则不设置特定种子。"
            ),
        ),
        alias=MultilingualString(
            en="Random state",
            es="Estado aleatorio",
            pt="Estado aleatório",
            de="Zufallszustand",
            zh="随机状态",
        ),
    )  # type: ignore

    class_weight: schema_field(
        none_type(enum_field(enum=["balanced"])),
        placeholder=None,
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


class SGDClassifier(TabularClassificationModel, SklearnLikeClassifier, _SGDClassifier):
    """SGD classifier with probability calibration for consistent predict_proba output.

    SGDClassifier supports multiple loss functions that correspond to different
    linear models (SVM with 'hinge', logistic regression with 'log_loss', etc.).
    Stochastic Gradient Descent allows efficient training on large datasets. Because
    not all loss functions expose ``predict_proba`` natively, this wrapper
    consistently calibrates the model with ``CalibratedClassifierCV``.

    Key hyperparameters include ``loss``, ``alpha``, ``max_iter``, ``tol``, and
    ``learning_rate``. The implementation wraps scikit-learn's ``SGDClassifier``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.SGDClassifier.html
    """

    SCHEMA = SGDClassifierSchema
    DISPLAY_NAME: str = MultilingualString(
        en="SGD Classifier",
        es="Clasificador SGD",
        pt="Classificador SGD",
        de="SGD-Klassifikator",
        zh="随机梯度下降分类器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Linear classifier trained with stochastic gradient descent.",
        es="Clasificador lineal entrenado con descenso de gradiente estocástico.",
        pt="Classificador linear treinado com descida de gradiente estocástico.",
        de="Linearer Klassifikator, trainiert mit stochastischem Gradientenabstieg.",
        zh="使用随机梯度下降训练的线性分类器。",
    )
    COLOR: str = "#78909C"
    ICON: str = "TrendingDown"

    def __init__(self, **kwargs) -> None:
        """Initialise the model by forwarding all kwargs to the parent class.

        Parameters
        ----------
        **kwargs : dict
            Hyperparameter values forwarded to the parent sklearn wrapper.
        """
        super().__init__(**kwargs)
        self._calibrated = None

    def __sklearn_is_fitted__(self) -> bool:
        return self._calibrated is not None

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        """Train using CalibratedClassifierCV to guarantee predict_proba availability.

        Parameters
        ----------
        x_train : DashAIDataset
            The input features for training.
        y_train : DashAIDataset
            The target labels for training.
        x_validation : DashAIDataset, optional
            Unused (sklearn models ignore validation split).
        y_validation : DashAIDataset, optional
            Unused.

        Returns
        -------
        self
        """
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.linear_model import SGDClassifier as _SGDClassifierRaw

        x_processed = self.prepare_dataset(x_train, is_fit=True).to_pandas()
        y_processed = self.prepare_output(y_train, is_fit=True).to_pandas()
        y_arr = y_processed.values.ravel()

        params = {
            k: getattr(self, k)
            for k in [
                "loss",
                "alpha",
                "max_iter",
                "tol",
                "learning_rate",
                "random_state",
                "class_weight",
            ]
            if hasattr(self, k)
        }
        base = _SGDClassifierRaw(**params)
        self._calibrated = CalibratedClassifierCV(base, method="sigmoid", cv=3)
        self._calibrated.fit(x_processed, y_arr)
        return self

    def predict(self, x_pred) -> "ndarray":  # noqa: F821
        """Return class-probability matrix using the calibrated model.

        Parameters
        ----------
        x_pred : DashAIDataset
            Input data.

        Returns
        -------
        np.ndarray
            Class probability matrix.
        """
        return self.predict_prepared(
            self.prepare_dataset(x_pred, is_fit=False).to_pandas()
        )

    def predict_proba_prepared(self, features) -> "ndarray":  # noqa: F821
        """Return class probabilities for an already prepared feature matrix.

        Parameters
        ----------
        features : pandas.DataFrame or numpy.ndarray
            Feature matrix as produced by ``prepare_dataset``.

        Returns
        -------
        np.ndarray
            Class probability matrix.

        Raises
        ------
        NotFittedError
            If the calibrated classifier has not been trained yet.
        """
        from sklearn.exceptions import NotFittedError

        if self._calibrated is None:
            raise NotFittedError(
                f"This {self.__class__.__name__} instance is not fitted yet. "
                "Call 'train' with appropriate arguments before using this estimator."
            )
        return self._calibrated.predict_proba(features)
