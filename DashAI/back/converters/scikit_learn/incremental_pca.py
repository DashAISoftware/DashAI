from sklearn.decomposition import IncrementalPCA as IncrementalPCAOperation

from DashAI.back.converters.category.dimensionality_reduction import (
    DimensionalityReductionConverter,
)
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import (
    bool_field,
    int_field,
    none_type,
    schema_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer


class IncrementalPCASchema(BaseSchema):
    """Configuration schema for the IncrementalPCA converter.

    Defines and validates the hyperparameters passed to
    ``sklearn.decomposition.IncrementalPCA``.
    """

    n_components: schema_field(
        none_type(int_field(ge=1)),
        2,
        description=MultilingualString(
            en="Number of components to keep.",
            es="Número de componentes a conservar.",
            pt="Número de componentes a manter.",
            de="Anzahl der beizubehaltenden Komponenten.",
            zh="要保留的成分数量。",
        ),
    )  # type: ignore
    whiten: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en=(
                "When True the components_ are scaled to ensure uncorrelated "
                "outputs with unit variances."
            ),
            es=(
                "Cuando es True las componentes se escalan para asegurar salidas "
                "no correlacionadas con varianzas unitarias."
            ),
            pt=(
                "Quando True, os componentes são escalonados para garantir saídas "
                "não correlacionadas com variâncias unitárias."
            ),
            de=(
                "Wenn True werden die Komponenten skaliert, um unkorrellierte "
                "Ausgaben mit Einheitsvarianz zu gewährleisten."
            ),
            zh="为 True 时，缩放成分以确保输出不相关且方差为 1。",
        ),
    )  # type: ignore
    batch_size: schema_field(
        none_type(int_field(ge=1)),
        None,
        description=MultilingualString(
            en="The number of samples to use for each batch.",
            es="Número de muestras a usar por lote.",
            pt="O número de amostras a usar por lote.",
            de="Die Anzahl der Stichproben, die pro Stapel verwendet werden sollen.",
            zh="每个批次使用的样本数量。",
        ),
    )  # type: ignore


class IncrementalPCA(
    DimensionalityReductionConverter, SklearnWrapper, IncrementalPCAOperation
):
    """Reduce dimensionality using PCA computed incrementally over mini-batches.

    IncrementalPCA (IPCA) implements an online variant of PCA that processes
    data one batch at a time and updates the component estimates after each
    batch using a singular value merging strategy. This allows the algorithm
    to fit datasets that are too large to hold in memory simultaneously, while
    still converging to results that closely approximate full-batch PCA.

    The algorithm maintains a running estimate of the mean and the principal
    components, merging each new batch with the accumulated SVD from previous
    batches. When ``batch_size`` is ``None``, it defaults to ``5 * n_features``.

    Key properties:

    - Constant memory footprint regardless of dataset size.
    - Supports the ``partial_fit`` API for true out of core usage.
    - The ``whiten`` option rescales components to unit variance, which can
      improve downstream estimators that assume spherical features.
    - Produces output numerically close to full-batch PCA when the batch size
      is reasonably large relative to the number of components.

    Wraps scikit-learn's ``IncrementalPCA``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.IncrementalPCA.html
    """

    SCHEMA = IncrementalPCASchema
    DESCRIPTION = MultilingualString(
        en=(
            "Incremental PCA (IPCA) is typically used as a replacement for PCA "
            "when the dataset is too large to fit in memory."
        ),
        es=(
            "El PCA incremental (IPCA) se usa típicamente como reemplazo de PCA "
            "cuando el conjunto de datos es demasiado grande para caber en memoria."
        ),
        pt=(
            "O PCA Incremental (IPCA) é tipicamente usado como substituto do PCA "
            "quando o conjunto de dados é grande demais para caber na memória."
        ),
        de=(
            "Inkrementelle PCA (IPCA) wird typischerweise als Ersatz für PCA "
            "verwendet, wenn der Datensatz zu groß für den Arbeitsspeicher ist."
        ),
        zh="增量 PCA（IPCA）通常用于替代 PCA，适用于数据集太大而无法放入内存的情况。",
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Dimensionality reduction using Incremental PCA.",
        es="Reducción de dimensionalidad usando PCA incremental.",
        pt="Redução de dimensionalidade usando PCA Incremental.",
        de="Dimensionsreduktion mittels inkrementeller PCA.",
        zh="使用增量 PCA 进行降维。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Incremental PCA",
        es="PCA Incremental",
        pt="PCA Incremental",
        de="Inkrementelle PCA",
        zh="增量 PCA",
    )
    IMAGE_PREVIEW = "incremental_pca.png"

    metadata = {
        "allowed_types": [Float, Integer],
        "allowed_dtypes": [],
    }

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the DashAI data type produced by this converter for a column.

        Parameters
        ----------
        column_name : str, optional
            Not used; all output columns share the
            same type. Defaults to None.

        Returns
        -------
        DashAIDataType
            A Float type backed by ``pyarrow.float64()``.
        """
        import pyarrow as pa

        return Float(arrow_type=pa.float64())
