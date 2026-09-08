from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

import numpy as np
from sklearn.model_selection import RepeatedKFold

from DashAI.back.core.schema_fields import (
    BaseSchema,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString

from .fold_splitter import FoldSplitter

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class RepeatedKFoldSplitterSchema(BaseSchema):
    n_splits: schema_field(
        int_field(ge=2, le=20),
        placeholder=5,
        description=MultilingualString(
            en="Number of folds. Must be an integer between 2 and 20.",
            es="Número de particiones. Debe ser un entero entre 2 y 20.",
            pt="Número de partições. Deve ser um inteiro entre 2 e 20.",
            de="Anzahl der Folds. Muss eine ganze Zahl zwischen 2 und 20 sein.",
            zh="折数，必须为2到20之间的整数。",
        ),
        alias=MultilingualString(
            en="Number of folds",
            es="Número de particiones",
            pt="Número de partições",
            de="Anzahl der Folds",
            zh="折数",
        ),
    )  # type: ignore
    n_repeats: schema_field(
        int_field(ge=2, le=10),
        placeholder=2,
        description=MultilingualString(
            en=(
                "Number of times the K-Fold procedure is repeated. Must be an "
                "integer between 2 and 10."
            ),
            es=(
                "Número de veces que se repite el procedimiento K-Fold. Debe "
                "ser un entero entre 2 y 10."
            ),
            pt=(
                "Número de vezes que o procedimento K-Fold é repetido. Deve "
                "ser um inteiro entre 2 e 10."
            ),
            de=(
                "Anzahl der Wiederholungen des K-Fold-Verfahrens. Muss eine "
                "ganze Zahl zwischen 2 und 10 sein."
            ),
            zh="K折过程重复的次数，必须为2到10之间的整数。",
        ),
        alias=MultilingualString(
            en="Number of repeats",
            es="Número de repeticiones",
            pt="Número de repetições",
            de="Anzahl der Wiederholungen",
            zh="重复次数",
        ),
    )  # type: ignore
    random_state: schema_field(
        int_field(ge=0),
        placeholder=42,
        description=MultilingualString(
            en="Seed used to make the repeated split reproducible.",
            es="Semilla utilizada para que la división repetida sea reproducible.",
            pt="Semente usada para tornar a divisão repetida reproduzível.",
            de="Seed, um die wiederholte Aufteilung reproduzierbar zu machen.",
            zh="用于使重复划分可复现的随机种子。",
        ),
        alias=MultilingualString(
            en="Random state",
            es="Estado aleatorio",
            pt="Estado aleatório",
            de="Zufallszustand",
            zh="随机状态",
        ),
    )  # type: ignore
    test_size: schema_field(
        float_field(ge=0, le=0.5),
        placeholder=0.1,
        description=MultilingualString(
            en=(
                "Proportion of the dataset set aside as a test set. No fold and no "
                "hyperparameter search ever sees those rows, so they are scored once "
                "by the final model and are the data it can be explained on. Set it to "
                "0 to cross-validate every row, which leaves the run without a test "
                "metric and without data to explain, and note that the fold metrics "
                "are validation estimates that may carry an optimistic bias if they "
                "are used as the final evaluation of the model."
            ),
            es=(
                "Proporción del dataset que se aparta como conjunto de prueba. Ningún "
                "pliegue ni búsqueda de hiperparámetros ve esas filas, por lo que el "
                "modelo final las evalúa una sola vez y son los datos con los que se "
                "puede explicar. Use 0 para validar de forma cruzada todas las filas, "
                "lo que deja la ejecución sin métrica de prueba y sin datos que "
                "explicar, y tenga en cuenta que las métricas de los pliegues son "
                "estimaciones de validación que pueden presentar un sesgo optimista si "
                "se utilizan como evaluación final del modelo."
            ),
            pt=(
                "Proporção do dataset reservada como conjunto de teste. Nenhuma dobra "
                "nem busca de hiperparâmetros vê essas linhas, portanto o modelo final "
                "as avalia uma única vez e são os dados com os quais ele pode ser "
                "explicado. Use 0 para validar de forma cruzada todas as linhas, o que "
                "deixa a execução sem métrica de teste e sem dados para explicar, e "
                "tenha em conta que as métricas das dobras são estimativas de "
                "validação que podem apresentar um viés otimista se forem utilizadas "
                "como avaliação final do modelo."
            ),
            de=(
                "Anteil des Datensatzes, der als Testmenge zurückgehalten wird. Weder "
                "ein Fold noch die Hyperparametersuche sieht diese Zeilen; das finale "
                "Modell bewertet sie genau einmal und kann anhand von ihnen erklärt "
                "werden. Mit 0 werden alle Zeilen kreuzvalidiert, wodurch der Lauf "
                "weder eine Testmetrik noch Daten zum Erklären hat. Beachten Sie "
                "zudem, dass die Fold-Metriken Validierungsschätzungen sind und einen "
                "optimistischen Bias aufweisen können, wenn sie als endgültige "
                "Bewertung des Modells verwendet werden."
            ),
            zh=(
                "作为测试集保留的数据集比例。任何折和超参数搜索都不会看到这些行，因此最"
                "终模型只对它们评估一次，并可用于解释该模型。设为 0 时全部行都参与交"
                "叉验证，该运行将没有测试指标也没有可解释的数据；另请注意各折的指标属于"
                "验证估计，若将其用作模型的最终评估，可能存在乐观偏差。"
            ),
        ),
        alias=MultilingualString(
            en="Test set",
            es="Conjunto de prueba",
            pt="Conjunto de teste",
            de="Testmenge",
            zh="测试集",
        ),
    )  # type: ignore


class RepeatedKFoldSplitter(FoldSplitter):
    """Splitter that repeats the K-fold procedure multiple times.

    Repeating the folds helps reduce the variance of the performance estimate by
    averaging over several random resamplings of the same evaluation scheme. This
    is useful when a single K-fold run is too noisy or when more stable estimates
    are needed for model comparison.

    References
    ----------
    - https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.RepeatedKFold.html
    """

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "RegressionTask",
        "TranslationTask",
        "ImageClassificationTask",
    ]
    DISPLAY_NAME: str = MultilingualString(
        en="Repeated K-Fold",
        es="K-Fold Repetido",
        pt="K-Fold Repetido",
        de="Wiederholtes K-Fold",
        zh="重复 K 折交叉验证",
    )
    COMPATIBLE_INNER_SPLITTERS = ["KFoldSplitter", "StratifiedKFoldSplitter"]
    SCHEMA = RepeatedKFoldSplitterSchema

    def __init__(self, splits_data):
        """Initialize the repeated K-fold splitter.

        Parameters
        ----------
        splits_data : dict
            Configuration dictionary that may include the number of repeats.
        """
        super().__init__(splits_data)
        self.n_repeats = splits_data.get("n_repeats", 2)

    def split_indexes(
        self, x: DashAIDataset, y: DashAIDataset
    ) -> List[Tuple[List, List]]:
        """Generate train/test index pairs for each repetition of the K-fold split.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset whose length determines the number of available samples.
        y : DashAIDataset
            Target values associated with ``x``. This argument is accepted for
            interface consistency but is not used directly by the splitter.

        Returns
        -------
        list[tuple]
            A list of train/test index pairs for all folds and repeats.
        """
        indexes = np.arange(len(x))

        try:
            rkf = RepeatedKFold(
                n_splits=self.n_splits,
                n_repeats=self.n_repeats,
                random_state=self.random_state,
            )
            folds = list(rkf.split(indexes))

        except ValueError as e:
            raise ValueError(f"Error in RepeatedKFold splitting: {e}") from e

        return folds
