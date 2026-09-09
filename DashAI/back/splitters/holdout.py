from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from DashAI.back.core.schema_fields import (
    Approx,
    BaseSchema,
    Check,
    F,
    Sum,
    bool_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataloaders.classes.dashai_dataset import split_dataset
from DashAI.back.splitters.rules import SEED_ONLY_MATTERS_WHEN_SHUFFLING

from .base_splitter import BaseSplitter

if TYPE_CHECKING:
    from datasets import DatasetDict

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class HoldoutSplitterSchema(BaseSchema):
    train: schema_field(
        float_field(ge=0, le=1),
        placeholder=0.6,
        description=MultilingualString(
            en="Proportion of the dataset assigned to the training partition.",
            es="Proporción del dataset asignada a la partición de entrenamiento.",
            pt="Proporção do dataset atribuída à partição de treinamento.",
            de="Anteil des Datensatzes für die Trainingspartition.",
            zh="分配给训练集的数据集比例。",
        ),
        alias=MultilingualString(
            en="Train", es="Entrenamiento", pt="Treinamento", de="Training", zh="训练集"
        ),
    )  # type: ignore
    test: schema_field(
        float_field(ge=0, le=1),
        placeholder=0.2,
        description=MultilingualString(
            en="Proportion of the dataset assigned to the test partition.",
            es="Proporción del dataset asignada a la partición de prueba.",
            pt="Proporção do dataset atribuída à partição de teste.",
            de="Anteil des Datensatzes für die Testpartition.",
            zh="分配给测试集的数据集比例。",
        ),
        alias=MultilingualString(
            en="Test", es="Prueba", pt="Teste", de="Test", zh="测试集"
        ),
    )  # type: ignore
    validation: schema_field(
        float_field(ge=0, le=1),
        placeholder=0.2,
        description=MultilingualString(
            en="Proportion of the dataset assigned to the validation partition.",
            es="Proporción del dataset asignada a la partición de validación.",
            pt="Proporção do dataset atribuída à partição de validação.",
            de="Anteil des Datensatzes für die Validierungspartition.",
            zh="分配给验证集的数据集比例。",
        ),
        alias=MultilingualString(
            en="Validation",
            es="Validación",
            pt="Validação",
            de="Validierung",
            zh="验证集",
        ),
    )  # type: ignore
    stratify: schema_field(
        bool_field(),
        placeholder=False,
        description=MultilingualString(
            en="Whether to preserve the class distribution across the splits.",
            es="Si se debe preservar la distribución de clases entre las particiones.",
            pt="Se a distribuição de classes deve ser preservada entre as partições.",
            de="Ob die Klassenverteilung über die Partitionen erhalten bleiben soll.",
            zh="是否在各分区之间保持类别分布。",
        ),
        alias=MultilingualString(
            en="Stratify",
            es="Estratificar",
            pt="Estratificar",
            de="Stratifizieren",
            zh="分层",
        ),
    )  # type: ignore
    shuffle: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en="Whether to shuffle the data before splitting it.",
            es="Si se deben mezclar los datos antes de dividirlos.",
            pt="Se os dados devem ser embaralhados antes de dividi-los.",
            de="Ob die Daten vor der Aufteilung gemischt werden sollen.",
            zh="划分前是否打乱数据。",
        ),
        alias=MultilingualString(
            en="Shuffle", es="Mezclar", pt="Embaralhar", de="Mischen", zh="打乱"
        ),
    )  # type: ignore
    random_state: schema_field(
        int_field(ge=0),
        placeholder=42,
        # The "ignored when shuffling is disabled" sentence this description
        # used to carry in five languages is now the Relevance rule below, so
        # the renderer disables the control instead of asking the user to read
        # about it.
        description=MultilingualString(
            en="Seed used to make the split reproducible.",
            es="Semilla utilizada para que la división sea reproducible.",
            pt="Semente usada para tornar a divisão reproduzível.",
            de="Seed, um die Aufteilung reproduzierbar zu machen.",
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

    # The three partitions must describe the whole dataset, and the seed is
    # meaningless without shuffling. Both were previously a `model_validator`
    # body plus a sentence in a description, which left the browser to
    # re-implement the first one by hand at a different tolerance and the
    # second one not at all.
    rules = [
        Check(
            Approx(Sum("train", "validation", "test"), 1.0, tol=1e-6),
            id="holdout.proportions_sum_to_one",
            targets=["train", "validation", "test"],
            message=MultilingualString(
                en=(
                    "Train, validation and test must sum to 1 "
                    "(they currently add up to {total})."
                ),
                es=(
                    "Entrenamiento, validación y prueba deben sumar 1 "
                    "(actualmente suman {total})."
                ),
                pt=(
                    "Treinamento, validação e teste devem somar 1 "
                    "(atualmente somam {total})."
                ),
                de=(
                    "Training, Validierung und Test müssen zusammen 1 ergeben "
                    "(aktuell ergeben sie {total})."
                ),
                zh="训练集、验证集和测试集的比例之和必须为 1（当前为 {total}）。",
            ),
            bindings={"total": Sum("train", "validation", "test")},
        ),
        Check(
            F("train") > 0,
            id="holdout.train_not_empty",
            targets=["train"],
            message=MultilingualString(
                en="The train proportion must be greater than 0.",
                es="La proporción de entrenamiento debe ser mayor que 0.",
                pt="A proporção de treinamento deve ser maior que 0.",
                de="Der Trainingsanteil muss größer als 0 sein.",
                zh="训练集比例必须大于 0。",
            ),
        ),
        # Shared with the four fold splitters, which carry the same dependency.
        SEED_ONLY_MATTERS_WHEN_SHUFFLING,
    ]


class PartitionSplitter(BaseSplitter):
    """Splitter that creates train, test, and validation partitions for holdout
    evaluation.

    This strategy is appropriate when a single representative split is sufficient
    for model selection or final assessment. It is commonly used for quick
    experiments, hyperparameter tuning, and production-ready evaluation where
    the computational cost of repeated cross-validation would be excessive.

    It is especially useful for large datasets and for workflows that require a
    simple partitioning scheme with clear train/test/validation boundaries.

    References
    ----------
    - https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html
    """

    @classmethod
    def explainable_partitions(cls, split_indexes):
        """Return the train, test and validation partitions of a holdout run.

        Parameters
        ----------
        split_indexes : dict
            The ``Run.split_indexes`` payload, already parsed.

        Returns
        -------
        dict
            Row indexes for the ``train``, ``test`` and ``val`` partitions.
        """
        return {
            "train": split_indexes["train_indexes"],
            "test": split_indexes["test_indexes"],
            "val": split_indexes.get("val_indexes", []),
        }

    def __init__(self, splits_data):
        """Initialize the holdout splitter with the requested proportions.

        Parameters
        ----------
        splits_data : dict
            Configuration dictionary containing train, test, and validation
            proportions, as well as optional custom indices and stratification
            settings.
        """
        super().__init__(splits_data)
        self.train_size = splits_data.get("train", None)
        self.test_size = splits_data.get("test", None)
        self.val_size = splits_data.get("validation", None)
        self.splitted_indexes = splits_data.get("splitted_indexes", {})
        self.stratify = splits_data.get("stratify", False)

    def split(
        self, x: DashAIDataset, y: DashAIDataset
    ) -> Tuple[DatasetDict, DatasetDict, Dict[str, Any]]:
        """Split the input data into holdout partitions and return the
        resulting datasets.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset to partition.
        y : DashAIDataset
            Target values associated with ``x``.

        Returns
        -------
        tuple
            A tuple containing the partitioned input and output datasets, along
            with the indices used for each split.
        """
        if all(idx is None for idx in [self.train_size, self.test_size, self.val_size]):
            train_indices = self.splitted_indexes.get("train_indexes", [])
            test_indices = self.splitted_indexes.get("test_indexes", [])
            val_indices = self.splitted_indexes.get("val_indexes", [])

            indices = self.splitted_indexes

        else:
            train_indices, test_indices, val_indices = self.split_indexes(x, y)

            indices = {
                "train_indexes": train_indices,
                "test_indexes": test_indices,
                "val_indexes": val_indices,
            }

        x_prepared = split_dataset(x, train_indices, test_indices, val_indices)
        y_prepared = split_dataset(y, train_indices, test_indices, val_indices)

        return x_prepared, y_prepared, indices

    def split_indexes(
        self,
        x: DashAIDataset,
        y: DashAIDataset,
    ) -> Tuple[List, List, List]:
        """Generate lists with train, test and validation indexes.

        The algorithm for splitting the dataset is as follows:

        1. The dataset is divided into a training and a test-validation split
            (sum of test_size and val_size).
        2. The test and validation set is generated from the test-validation set,
            where the size of the test-validation set is now considered to be 100%.
            Therefore, the sizes of the test and validation sets will now be
            calculated as 100%, i.e. as val_size/(test_size+val_size) and
            test_size/(test_size+val_size) respectively.

        Example:

        If we split a dataset into 0.8 training, a 0.1 test, and a 0.1 validation,
        in the first process we split the training data with 80% of the data, and
        the test-validation data with the remaining 20%; and then in the second
        process we split this 20% into 50% test and 50% validation.

        Parameters
        ----------
        x: DashAIDataset
            Input dataset to partition.
        y: DashAIDataset
        Target values associated with ``x``.

        Returns
        -------
        tuple[List, List, List]
            Lists of indices for the training, test, and validation partitions.
        """
        import numpy as np
        from sklearn.model_selection import train_test_split

        total_rows = len(x)
        indexes = np.arange(total_rows)
        stratify_labels = np.array(self.prepare_y(y)) if self.stratify else None

        if self.test_size == 0 and self.val_size == 0:
            return indexes.tolist(), [], []

        if self.test_size == 0:
            train_indexes, val_indexes = train_test_split(
                indexes,
                train_size=self.train_size,
                random_state=self.random_state,
                shuffle=self.shuffle,
                stratify=stratify_labels,
            )
            return train_indexes.tolist(), [], val_indexes.tolist()

        if self.val_size == 0:
            train_indexes, test_indexes = train_test_split(
                indexes,
                train_size=self.train_size,
                random_state=self.random_state,
                shuffle=self.shuffle,
                stratify=stratify_labels,
            )
            return train_indexes.tolist(), test_indexes.tolist(), []

        test_val = self.test_size + self.val_size
        val_proportion = self.test_size / test_val

        train_indexes, test_val_indexes = train_test_split(
            indexes,
            train_size=self.train_size,
            random_state=self.random_state,
            shuffle=self.shuffle,
            stratify=stratify_labels,
        )

        stratify_labels_test_val = (
            stratify_labels[test_val_indexes] if self.stratify else None
        )

        test_indexes, val_indexes = train_test_split(
            test_val_indexes,
            train_size=val_proportion,
            random_state=self.random_state,
            shuffle=self.shuffle,
            stratify=stratify_labels_test_val,
        )
        return train_indexes.tolist(), test_indexes.tolist(), val_indexes.tolist()


class HoldoutSplitter(PartitionSplitter):
    """Split the dataset into train, test and validation partitions at random.

    The ordinary holdout split: rows are sampled into three partitions, with
    optional shuffling, stratification and a seed to make the sample
    reproducible.

    Not offered for ``ForecastingTask``. Sampling rows out of a series lets a
    model train on its own future and report a score it could never reproduce
    in use, and nothing about that failure raises an error. Forecasting uses
    ``TemporalHoldoutSplitter``, which cuts the rows where they lie.
    """

    SCHEMA = HoldoutSplitterSchema
    # Listed per task rather than left universal, so the frontend can resolve
    # a holdout splitter from the task instead of hardcoding this class.
    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "ImageClassificationTask",
        "TranslationTask",
        "RegressionTask",
    ]
