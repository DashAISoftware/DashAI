from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

from pydantic import model_validator

from DashAI.back.core.schema_fields import (
    BaseSchema,
    float_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString

from .holdout import PartitionSplitter

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class TemporalHoldoutSplitterSchema(BaseSchema):
    """Schema that configures the temporal holdout splitter.

    Deliberately smaller than the holdout schema it mirrors: there is no
    shuffle, no random state and no stratification, because nothing here is
    random and offering a seed that changes nothing would be a lie.
    """

    train: schema_field(
        float_field(ge=0, le=1),
        placeholder=0.6,
        description=MultilingualString(
            en="Proportion of the earliest rows used for training.",
            es="Proporcion de las filas mas antiguas usadas para entrenar.",
            pt="Proporcao das linhas mais antigas usadas para treinar.",
            de="Anteil der aeltesten Zeilen, der zum Training verwendet wird.",
            zh="用于训练的最早那部分行的比例。",
        ),
        alias=MultilingualString(
            en="Train", es="Entrenamiento", pt="Treinamento", de="Training", zh="训练集"
        ),
    )  # type: ignore
    validation: schema_field(
        float_field(ge=0, le=1),
        placeholder=0.2,
        description=MultilingualString(
            en="Proportion of the rows after training used for validation.",
            es=(
                "Proporcion de las filas posteriores al entrenamiento usadas "
                "para validacion."
            ),
            pt=(
                "Proporcao das linhas posteriores ao treinamento usadas para validacao."
            ),
            de=(
                "Anteil der auf das Training folgenden Zeilen, der zur "
                "Validierung verwendet wird."
            ),
            zh="训练之后那部分行中用于验证的比例。",
        ),
        alias=MultilingualString(
            en="Validation",
            es="Validacion",
            pt="Validacao",
            de="Validierung",
            zh="验证集",
        ),
    )  # type: ignore
    test: schema_field(
        float_field(ge=0, le=1),
        placeholder=0.2,
        description=MultilingualString(
            en="Proportion of the most recent rows used for testing.",
            es="Proporcion de las filas mas recientes usadas para prueba.",
            pt="Proporcao das linhas mais recentes usadas para teste.",
            de="Anteil der neuesten Zeilen, der zum Testen verwendet wird.",
            zh="用于测试的最近那部分行的比例。",
        ),
        alias=MultilingualString(
            en="Test", es="Prueba", pt="Teste", de="Test", zh="测试集"
        ),
    )  # type: ignore

    @model_validator(mode="after")
    def check_partitions(self):
        """Validate that the three partitions describe the whole dataset.

        Returns
        -------
        TemporalHoldoutSplitterSchema
            The validated schema instance.

        Raises
        ------
        ValueError
            If the proportions do not sum to one, or if the training partition
            is empty.
        """
        total = self.train + self.test + self.validation
        if abs(total - 1) > 1e-6:
            raise ValueError(
                f"train, test and validation proportions must sum to 1, got {total}."
            )
        if self.train <= 0:
            raise ValueError("The train proportion must be greater than 0.")
        return self


class TemporalHoldoutSplitter(PartitionSplitter):
    """Split a series in time order: train first, then validation, then test.

    Rows are cut where they lie rather than sampled, so every row a model is
    scored on comes after every row it was fitted on. That is the only honest
    way to estimate how a model will do on data it has not seen yet, because
    the alternative lets it learn from the future.

    Shuffling is not merely discouraged here, it is impossible: a request to
    shuffle is overruled. Two ways of getting it wrong are worth naming, since
    neither reports an error, they just return a score that is too good.

    * A random split of a series lets the model interpolate between rows it has
      already seen instead of extrapolating past them.
    * On the output of ``TimeSeriesWindowConverter`` it is worse still, because
      consecutive rows share ``window_size - 1`` of their values, so a random
      split puts near duplicates of the training rows into the test set. That
      route goes through ``RegressionTask``, which this splitter is not offered
      for; use ``HoldoutSplitter`` with shuffling turned off there.

    Row order is taken as time order. This splitter receives the selected input
    columns, which for a windowed dataset no longer include a date, so it
    cannot re-sort and does not try.
    """

    SCHEMA = TemporalHoldoutSplitterSchema
    COMPATIBLE_COMPONENTS = ["ForecastingTask"]
    DISPLAY_NAME: str = MultilingualString(
        en="Temporal Holdout",
        es="Holdout Temporal",
        pt="Holdout Temporal",
        de="Zeitlicher Holdout",
        zh="时序留出法",
    )

    def __init__(self, splits_data):
        """Initialize the splitter with the requested proportions.

        Parameters
        ----------
        splits_data : dict
            Configuration dictionary with the train, validation and test
            proportions, and optionally previously computed indexes.
        """
        super().__init__(splits_data)
        # The base class defaults these to values that would reintroduce
        # randomness, and the schema does not expose either, so they are
        # pinned here rather than trusted to arrive absent.
        self.shuffle = False
        self.stratify = False

    def split_indexes(
        self, x: "DashAIDataset", y: "DashAIDataset"
    ) -> Tuple[List, List, List]:
        """Cut the rows into three consecutive blocks in time order.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset to partition.
        y : DashAIDataset
            Target values associated with ``x``. Unused: nothing here depends
            on the target, unlike a stratified split.

        Returns
        -------
        tuple[List, List, List]
            Train, test and validation indexes. Note the return order matches
            the holdout contract, while the partitions themselves run
            train, validation, test along the timeline.
        """
        total_rows = len(x)
        n_train = int(round(total_rows * (self.train_size or 0)))
        n_validation = int(round(total_rows * (self.val_size or 0)))

        # Whatever rounding leaves over belongs to the test partition, which
        # keeps every row in exactly one place.
        train_indexes = list(range(n_train))
        validation_indexes = list(range(n_train, n_train + n_validation))
        test_indexes = list(range(n_train + n_validation, total_rows))

        return train_indexes, test_indexes, validation_indexes
