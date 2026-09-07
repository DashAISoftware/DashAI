from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

import numpy as np
from sklearn.model_selection import KFold

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString

from .fold_splitter import FoldSplitter, sklearn_random_state

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class KFoldSplitterSchema(BaseSchema):
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
    shuffle: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en=(
                "Whether to shuffle the data before splitting it into folds. When "
                "shuffling is disabled, the random state has no effect."
            ),
            es=(
                "Si se deben mezclar los datos antes de dividirlos en particiones. "
                "Cuando la mezcla está desactivada, el estado aleatorio no tiene "
                "efecto."
            ),
            pt=(
                "Se os dados devem ser embaralhados antes de dividi-los em partições. "
                "Quando o embaralhamento está desativado, o estado aleatório não tem "
                "efeito."
            ),
            de=(
                "Ob die Daten vor der Aufteilung in Folds gemischt werden sollen. "
                "Wenn das Mischen deaktiviert ist, hat der Zufallszustand keine "
                "Wirkung."
            ),
            zh="划分为折之前是否打乱数据。关闭打乱时，随机状态不起作用。",
        ),
        alias=MultilingualString(
            en="Shuffle", es="Mezclar", pt="Embaralhar", de="Mischen", zh="打乱"
        ),
    )  # type: ignore
    random_state: schema_field(
        int_field(ge=0),
        placeholder=42,
        description=MultilingualString(
            en=(
                "Seed used to make the split reproducible when shuffle is enabled. It "
                "is ignored when shuffling is disabled."
            ),
            es=(
                "Semilla utilizada para que la división sea reproducible cuando se "
                "activa la mezcla. Se ignora cuando la mezcla está desactivada."
            ),
            pt=(
                "Semente usada para tornar a divisão reproduzível quando o "
                "embaralhamento está ativado. É ignorada quando o embaralhamento está "
                "desativado."
            ),
            de=(
                "Seed, um die Aufteilung reproduzierbar zu machen, wenn Mischen "
                "aktiviert ist. Wird ignoriert, wenn das Mischen deaktiviert ist."
            ),
            zh="启用打乱时，用于使划分可复现的随机种子。关闭打乱时将被忽略。",
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


class KFoldSplitter(FoldSplitter):
    """Splitter that generates K folds for cross-validation.

    This strategy is a standard choice for estimating model performance when the
    data is not naturally grouped and the goal is to obtain several
    semi-independent evaluation partitions. It is widely used in supervised
    learning tasks such as tabular classification, regression, text processing,
    and image classification.

    It is especially useful when a reliable estimate of generalization is needed
    without the additional complexity of group-aware or stratified schemes.

    References
    ----------
    - https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.KFold.html
    """

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "RegressionTask",
        "TranslationTask",
        "ImageClassificationTask",
    ]
    DISPLAY_NAME: str = MultilingualString(
        en="K-Fold",
        es="K-Fold",
        pt="K-Fold",
        de="K-Fold",
        zh="K 折交叉验证",
    )
    COMPATIBLE_INNER_SPLITTERS = ["KFoldSplitter", "StratifiedKFoldSplitter"]
    SCHEMA = KFoldSplitterSchema

    def split_indexes(
        self, x: DashAIDataset, y: DashAIDataset
    ) -> List[Tuple[List, List]]:
        """Generate train/test index pairs for each K-fold split.

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
            A list of train/test index pairs for every fold.
        """
        indexes = np.arange(len(x))

        try:
            kf = KFold(
                n_splits=self.n_splits,
                shuffle=self.shuffle,
                random_state=sklearn_random_state(self.shuffle, self.random_state),
            )
            folds = list(kf.split(indexes))
        except ValueError as e:
            raise ValueError(
                f"""Error in KFold splitting: {e}.
                Check if n_splits is less than or equal
                to the number of samples."""
            ) from e

        return folds
