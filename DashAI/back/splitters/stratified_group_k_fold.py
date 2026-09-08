from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    float_field,
    int_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.splitters.rules import SEED_ONLY_MATTERS_WHEN_SHUFFLING

from .fold_splitter import FoldSplitter, sklearn_random_state

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class StratifiedGroupKFoldSplitterSchema(BaseSchema):
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
    group_column: schema_field(
        none_type(string_field()),
        placeholder=None,
        description=MultilingualString(
            en=(
                "Name of the dataset column that identifies the group each "
                "sample belongs to. Samples that share the same group are "
                "always kept together in the same fold."
            ),
            es=(
                "Nombre de la columna del dataset que identifica el grupo al "
                "que pertenece cada muestra. Las muestras que comparten grupo "
                "siempre se mantienen juntas en la misma partición."
            ),
            pt=(
                "Nome da coluna do dataset que identifica o grupo ao qual "
                "cada amostra pertence. Amostras que compartilham o mesmo "
                "grupo permanecem sempre juntas na mesma partição."
            ),
            de=(
                "Name der Datensatzspalte, die die Gruppe jeder Probe "
                "identifiziert. Proben derselben Gruppe bleiben immer im "
                "selben Fold."
            ),
            zh="标识每个样本所属分组的数据集列名。同一分组的样本始终保持在同一折中。",
        ),
        alias=MultilingualString(
            en="Group column",
            es="Columna de grupo",
            pt="Coluna de grupo",
            de="Gruppenspalte",
            zh="分组列",
        ),
    )  # type: ignore
    shuffle: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en=("Whether to shuffle each group's samples before splitting."),
            es=("Si se deben mezclar las muestras de cada grupo antes de dividir."),
            pt=(
                "Se as amostras de cada grupo devem ser embaralhadas antes de dividir."
            ),
            de=(
                "Ob die Proben jeder Gruppe vor der Aufteilung gemischt werden sollen."
            ),
            zh="划分前是否打乱每个分组内的样本。",
        ),
        alias=MultilingualString(
            en="Shuffle", es="Mezclar", pt="Embaralhar", de="Mischen", zh="打乱"
        ),
    )  # type: ignore
    random_state: schema_field(
        int_field(ge=0),
        placeholder=42,
        description=MultilingualString(
            en=("Seed used to make the split reproducible."),
            es=("Semilla utilizada para que la división sea reproducible."),
            pt=("Semente usada para tornar a divisão reproduzível."),
            de=("Seed, um die Aufteilung reproduzierbar zu machen."),
            zh="用于使划分可复现的随机种子。",
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

    # The same dependency as every other splitter that takes a seed, declared
    # once in splitters/rules.py instead of copied here.
    rules = [SEED_ONLY_MATTERS_WHEN_SHUFFLING]


class StratifiedGroupKFoldSplitter(FoldSplitter):
    """Splitter that preserves both class balance and group membership in each fold.

    This strategy is particularly valuable for grouped classification tasks where
    the target labels are imbalanced and the samples are also organized into
    non-independent groups. It simultaneously prevents leakage across groups and
    keeps the class distribution similar across folds, which makes the
    evaluation more reliable and less biased.

    References
    ----------
    - https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html
    """

    TEST_SPLIT_STRATEGY: str = "group"
    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "ImageClassificationTask",
    ]
    DISPLAY_NAME: str = MultilingualString(
        en="Stratified Group K-Fold",
        es="K-Fold Estratificado por Grupos",
        pt="K-Fold Estratificado por Grupos",
        de="Stratifiziertes Gruppen-K-Fold",
        zh="分层分组 K 折交叉验证",
    )
    COMPATIBLE_INNER_SPLITTERS = ["GroupKFoldSplitter", "StratifiedGroupKFoldSplitter"]
    SCHEMA = StratifiedGroupKFoldSplitterSchema

    def __init__(self, splits_data):
        """Initialize the stratified group-based K-fold splitter.

        Parameters
        ----------
        splits_data : dict
            Configuration dictionary that may include the name of the group
            column used to define the groups.
        """
        super().__init__(splits_data)
        self.group_column = splits_data.get("group_column", None)

    def split_indexes(
        self, x: DashAIDataset, y: DashAIDataset
    ) -> List[Tuple[List, List]]:
        """Generate train/test index pairs preserving both labels and groups.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset that can be converted to a pandas DataFrame.
        y : DashAIDataset
            Target values used to preserve class balance across folds.

        Returns
        -------
        list[tuple]
            A list of train/test index pairs preserving group and label balance.
        """
        indexes = np.arange(len(x))

        try:
            try:
                dataset_df = x.to_pandas()
            except Exception as e:
                raise ValueError(
                    f"""Input x must be convertible
                    to a pandas DataFrame for StratifiedGroupKFold splitting: {e}"""
                ) from e

            try:
                y_labels = self.prepare_y(y)
            except Exception as e:
                raise ValueError(
                    f"""y must be convertible to a format suitable for
                    StratifiedGroupKFold splitting: {e}"""
                ) from e

            dataset_df_groups = dataset_df[self.group_column]

            sgkf = StratifiedGroupKFold(
                n_splits=self.n_splits,
                shuffle=self.shuffle,
                random_state=sklearn_random_state(self.shuffle, self.random_state),
            )
            folds = list(sgkf.split(indexes, y=y_labels, groups=dataset_df_groups))
        except ValueError as e:
            raise ValueError(f"Error in StratifiedGroupKFold splitting: {e}") from e

        return folds
