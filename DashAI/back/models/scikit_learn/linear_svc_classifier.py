from sklearn.svm import LinearSVC as _LinearSVC

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
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


class LinearSVCClassifierSchema(BaseSchema):
    """Schema that configures the Linear SVC Classifier.

    LinearSVC implements a linear Support Vector Classification trained with a
    linear kernel. It is faster than kernel SVC for large datasets. Because
    LinearSVC does not natively expose class probabilities, it is calibrated with
    Platt scaling (CalibratedClassifierCV). The underlying implementation is
    ``sklearn.svm.LinearSVC``.
    """

    C: schema_field(  # noqa: N815
        optimizer_float_field(ge=1e-4),
        placeholder={
            "optimize": False,
            "fixed_value": 1.0,
            "lower_bound": 0.01,
            "upper_bound": 100.0,
        },
        description=MultilingualString(
            en=(
                "Regularisation parameter. The strength of the regularisation is "
                "inversely proportional to C. Must be strictly positive."
            ),
            es=(
                "Parámetro de regularización. La fuerza de la regularización es "
                "inversamente proporcional a C. Debe ser estrictamente positivo."
            ),
            pt=(
                "Parâmetro de regularização. A força da regularização é "
                "inversamente proporcional a C. Deve ser estritamente positivo."
            ),
            de=(
                "Regularisierungsparameter. Die Stärke der Regularisierung ist "
                "umgekehrt proportional zu C. Muss strikt positiv sein."
            ),
            zh="正则化参数。正则化强度与C成反比，必须严格为正。",
        ),
        alias=MultilingualString(en="C", es="C", pt="C", de="C", zh="C"),
    )  # type: ignore

    loss: schema_field(
        enum_field(enum=["squared_hinge", "hinge"]),
        placeholder="squared_hinge",
        description=MultilingualString(
            en=(
                "Specifies the loss function. 'squared_hinge' is the default; "
                "'hinge' is the standard SVM loss."
            ),
            es=(
                "Especifica la función de pérdida. 'squared_hinge' es el "
                "predeterminado; 'hinge' es la pérdida estándar de SVM."
            ),
            pt=(
                "Especifica a função de perda. 'squared_hinge' é o padrão; "
                "'hinge' é a perda padrão do SVM."
            ),
            de=(
                "Gibt die Verlustfunktion an. 'squared_hinge' ist der Standard; "
                "'hinge' ist der Standard-SVM-Verlust."
            ),
            zh="指定损失函数。'squared_hinge'为默认值；'hinge'为标准SVM损失。",
        ),
        alias=MultilingualString(
            en="Loss", es="Pérdida", pt="Perda", de="Verlust", zh="损失函数"
        ),
    )  # type: ignore

    max_iter: schema_field(
        optimizer_int_field(ge=100),
        placeholder={
            "optimize": False,
            "fixed_value": 1000,
            "lower_bound": 100,
            "upper_bound": 10000,
        },
        description=MultilingualString(
            en="The maximum number of iterations to be run.",
            es="El número máximo de iteraciones a ejecutar.",
            pt="O número máximo de iterações a executar.",
            de="Die maximale Anzahl der auszuführenden Iterationen.",
            zh="最大迭代次数。",
        ),
        alias=MultilingualString(
            en="Max iterations",
            es="Máximas iteraciones",
            pt="Máximas iterações",
            de="Maximale Iterationen",
            zh="最大迭代次数",
        ),
    )  # type: ignore

    tol: schema_field(
        optimizer_float_field(ge=0.0),
        placeholder={
            "optimize": False,
            "fixed_value": 1e-4,
            "lower_bound": 1e-6,
            "upper_bound": 1e-1,
        },
        description=MultilingualString(
            en="Tolerance for stopping criteria.",
            es="Tolerancia para el criterio de parada.",
            pt="Tolerância para o critério de parada.",
            de="Toleranz für das Abbruchkriterium.",
            zh="停止准则的容差。",
        ),
        alias=MultilingualString(
            en="Tolerance", es="Tolerancia", pt="Tolerância", de="Toleranz", zh="容差"
        ),
    )  # type: ignore

    fit_intercept: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en=(
                "Whether to calculate the intercept for this model. If False, "
                "the data is expected to be already centred."
            ),
            es=(
                "Si se calcula el intercepto para este modelo. Si es False, "
                "se espera que los datos ya estén centrados."
            ),
            pt=(
                "Se o intercepto deve ser calculado para este modelo. Se False, "
                "espera-se que os dados já estejam centrados."
            ),
            de=(
                "Ob der Achsenabschnitt für dieses Modell berechnet werden soll. Bei "
                "False "
                "wird erwartet, dass die Daten bereits zentriert sind."
            ),
            zh="是否为模型计算截距。若为False，则数据应已中心化。",
        ),
        alias=MultilingualString(
            en="Fit intercept",
            es="Ajustar intercepto",
            pt="Ajustar intercepto",
            de="Achsenabschnitt anpassen",
            zh="拟合截距",
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
                "A semente do gerador de números pseudoaleatórios. Passe um int para "
                "saída reproduzível, ou None para não definir uma semente específica."
            ),
            de=(
                "Der Seed des Pseudozufallszahlengenerators. Übergeben Sie eine ganze "
                "Zahl für "
                "reproduzierbare Ausgaben oder None, um keinen bestimmten Seed "
                "festzulegen."
            ),
            zh="伪随机数生成器的随机种子。传入整数以获得可复现的输出，或传入None不固定种子。",
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


class LinearSVCClassifier(
    TabularClassificationModel, SklearnLikeClassifier, _LinearSVC
):
    """Linear SVC classifier with Platt-scaling calibration for class probabilities.

    LinearSVC uses a linear kernel and is trained with coordinate descent, making
    it considerably faster than kernel SVC on large datasets. Because LinearSVC
    does not expose ``predict_proba`` natively, this wrapper fits a
    ``CalibratedClassifierCV`` with sigmoid calibration so that probability
    estimates are available to the DashAI evaluation pipeline.

    Key hyperparameters include ``C`` (regularisation), ``loss``, ``max_iter``,
    and ``fit_intercept``. The implementation wraps scikit-learn's ``LinearSVC``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html
    - [2] https://scikit-learn.org/stable/modules/calibration.html
    """

    SCHEMA = LinearSVCClassifierSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Linear SVC",
        es="SVC Lineal",
        pt="Classificador SVC Linear",
        de="Linearer SVC",
        zh="线性支持向量分类器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Fast linear support vector classifier with probability calibration.",
        es=(
            "Clasificador de vectores de soporte lineal rápido con "
            "calibración de probabilidades."
        ),
        pt=(
            "Classificador de vetores de suporte linear rápido com "
            "calibração de probabilidades."
        ),
        de=(
            "Schneller linearer Stützvektor-Klassifikator mit "
            "Wahrscheinlichkeitskalibrierung."
        ),
        zh="带概率校准的快速线性支持向量分类器。",
    )
    COLOR: str = "#FF7043"
    ICON: str = "LinearScale"

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
        """Train using CalibratedClassifierCV to expose predict_proba.

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
        from sklearn.svm import LinearSVC as _LinearSVCRaw

        x_processed = self.prepare_dataset(x_train, is_fit=True).to_pandas()
        y_processed = self.prepare_output(y_train, is_fit=True).to_pandas()
        y_arr = y_processed.values.ravel()

        params = {
            k: getattr(self, k)
            for k in [
                "C",
                "loss",
                "max_iter",
                "tol",
                "fit_intercept",
                "random_state",
                "class_weight",
            ]
            if hasattr(self, k)
        }
        base = _LinearSVCRaw(**params)
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
