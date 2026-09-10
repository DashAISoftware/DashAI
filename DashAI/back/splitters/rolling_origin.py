from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

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


class RollingOriginSplitterSchema(BaseSchema):
    """Schema that configures the rolling origin splitter."""

    n_splits: schema_field(
        int_field(ge=2),
        placeholder=5,
        description=MultilingualString(
            en=(
                "How many times the model is refitted and scored, each time "
                "with more history than the last."
            ),
            es=(
                "Cuantas veces se reentrena y evalua el modelo, cada vez con "
                "mas historia que la anterior."
            ),
            pt=(
                "Quantas vezes o modelo e retreinado e avaliado, cada vez com "
                "mais historia que a anterior."
            ),
            de=(
                "Wie oft das Modell neu angepasst und bewertet wird, jedes Mal "
                "mit mehr Vergangenheit als zuvor."
            ),
            zh="模型被重新拟合并评估的次数，每次使用的历史数据都比上一次更多。",
        ),
        alias=MultilingualString(
            en="Number of origins",
            es="Numero de origenes",
            pt="Numero de origens",
            de="Anzahl der Ursprunge",
            zh="origin 数量",
        ),
    )  # type: ignore
    horizon: schema_field(
        int_field(ge=1),
        placeholder=1,
        description=MultilingualString(
            en="How many steps ahead each refit is scored on.",
            es="Cuantos pasos hacia adelante se evalua cada reentrenamiento.",
            pt="Quantos passos a frente cada retreinamento e avaliado.",
            de="Wie viele Schritte voraus jede Anpassung bewertet wird.",
            zh="每次重新拟合后向前评估的步数。",
        ),
        alias=MultilingualString(
            en="Horizon", es="Horizonte", pt="Horizonte", de="Horizont", zh="预测步长"
        ),
    )  # type: ignore
    step: schema_field(
        int_field(ge=1),
        placeholder=1,
        description=MultilingualString(
            en="How many rows the origin advances between one refit and the next.",
            es=(
                "Cuantas filas avanza el origen entre un reentrenamiento y el "
                "siguiente."
            ),
            pt=("Quantas linhas o origem avanca entre um retreinamento e o seguinte."),
            de=(
                "Um wie viele Zeilen der Ursprung zwischen zwei Anpassungen vorrueckt."
            ),
            zh="两次重新拟合之间 origin 前移的行数。",
        ),
        alias=MultilingualString(
            en="Step", es="Paso", pt="Passo", de="Schritt", zh="步进"
        ),
    )  # type: ignore
    test_size: schema_field(
        float_field(ge=0, lt=1),
        placeholder=0.1,
        description=MultilingualString(
            en=(
                "Proportion of the most recent rows held back from every "
                "origin, used once to score the final model."
            ),
            es=(
                "Proporcion de las filas mas recientes reservadas de todos los "
                "origenes, usada una sola vez para evaluar el modelo final."
            ),
            pt=(
                "Proporcao das linhas mais recentes reservadas de todas as "
                "origens, usada uma unica vez para avaliar o modelo final."
            ),
            de=(
                "Anteil der neuesten Zeilen, der von allen Ursprungen "
                "zurueckgehalten und einmal zur Bewertung des endgueltigen "
                "Modells verwendet wird."
            ),
            zh="从所有 origin 中保留的最近行的比例，仅用于最终模型的一次评估。",
        ),
        alias=MultilingualString(
            en="Test size",
            es="Tamano de prueba",
            pt="Tamanho de teste",
            de="Testgroesse",
            zh="测试集比例",
        ),
    )  # type: ignore


class RollingOriginSplitter(FoldSplitter):
    """Cross-validate a series by walking the origin forward through time.

    Each fold trains on everything up to a point and is scored on the rows
    just after it, then the point moves forward and the model is refitted with
    more history. The training window only ever grows.

    With four origins, a horizon of one and a reserved tail::

        Reserved test, in no fold:              Nov Dec

        Fold 1:  train Jan Feb Mar      | validation Apr
        Fold 2:  train Jan .. Apr       | validation May
        Fold 3:  train Jan .. May       | validation Jun
        Fold 4:  train Jan .. Jun       | validation Jul

        Final:   train Jan .. Oct       | test Nov Dec

    This is what k-fold cannot do for a series: its folds train on rows that
    come after the ones they score, which measures interpolation rather than
    forecasting and reports a number that will not survive contact with real
    use.

    The size of the first training window is not asked for. It follows from the
    other three settings, since the last origin has to leave a full horizon of
    rows to score::

        initial_train_size = n - horizon - (n_splits - 1) * step

    Row order is taken as time order, and the reserved rows are the tail rather
    than a random sample, which is what ``TEST_SPLIT_STRATEGY = "temporal"``
    selects in the base class.
    """

    SCHEMA = RollingOriginSplitterSchema
    TEST_SPLIT_STRATEGY: str = "temporal"
    COMPATIBLE_COMPONENTS = ["ForecastingTask"]
    COMPATIBLE_INNER_SPLITTERS = ["RollingOriginSplitter"]
    DISPLAY_NAME: str = MultilingualString(
        en="Rolling Origin",
        es="Origen Movil",
        pt="Origem Movel",
        de="Rollierender Ursprung",
        zh="滚动起点",
    )

    def __init__(self, splits_data):
        """Initialize the splitter with the requested origins and horizon.

        Parameters
        ----------
        splits_data : dict
            Configuration dictionary with the number of origins, the horizon,
            the step between origins and the reserved proportion.
        """
        super().__init__(splits_data)
        self.horizon = splits_data.get("horizon", 1)
        self.step = splits_data.get("step", 1)
        # Nothing here is random, and the base class defaults shuffling on.
        self.shuffle = False

    def split_indexes(
        self, x: "DashAIDataset", y: "DashAIDataset"
    ) -> List[Tuple[List, List]]:
        """Build one expanding train and validation pair per origin.

        Parameters
        ----------
        x : DashAIDataset
            The rows left after the reserved tail was carved off.
        y : DashAIDataset
            Target values associated with ``x``. Unused: where the cuts fall
            depends only on position, never on the target.

        Returns
        -------
        list[tuple[List, List]]
            One ``(train, validation)`` pair per origin, as positions within
            the pool. The caller maps them back to original rows.

        Raises
        ------
        ValueError
            If the requested origins, horizon and step do not fit in the rows
            available. The message names what to change.
        """
        total_rows = len(x)
        initial_train_size = total_rows - self.horizon - (self.n_splits - 1) * self.step

        if initial_train_size <= 0:
            raise ValueError(
                f"{self.n_splits} origins with a horizon of {self.horizon} and "
                f"a step of {self.step} need more than {total_rows} rows: the "
                "first one would train on nothing. Reduce n_splits, horizon or "
                "step, or reserve a smaller test set."
            )

        folds = []
        for fold in range(self.n_splits):
            origin = initial_train_size + fold * self.step
            folds.append(
                (list(range(origin)), list(range(origin, origin + self.horizon)))
            )

        return folds
