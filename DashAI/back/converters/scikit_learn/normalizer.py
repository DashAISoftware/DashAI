from sklearn.preprocessing import Normalizer as NormalizerOperation

from DashAI.back.converters.category.scaling_and_normalization import (
    ScalingAndNormalizationConverter,
)
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import enum_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer


class NormalizerSchema(BaseSchema):
    """Schema for Normalizer hyperparameters.

    Configures the norm used for row wise unit norm scaling and the copy
    semantics for sklearn's ``Normalizer``. The ``norm`` field selects between
    the L1, L2, and max norms applied to each individual sample.
    """

    norm: schema_field(
        enum_field(["l1", "l2", "max"]),
        "l2",
        description=MultilingualString(
            en="The norm to use to normalize each non-zero sample.",
            es="La norma a usar para normalizar cada muestra no nula.",
            pt="A norma a usar para normalizar cada amostra não nula.",
            de=(
                "Die Norm, die zur Normalisierung jeder nicht-null Stichprobe verwendet"
                "wird."
            ),
            zh="用于归一化每个非零样本的范数。",
        ),
    )  # type: ignore


class Normalizer(ScalingAndNormalizationConverter, SklearnWrapper, NormalizerOperation):
    """Normalize each sample (row) independently to unit norm.

    Unlike column wise scalers such as ``StandardScaler`` or
    ``MinMaxScaler``, this transformer operates along the sample axis.
    For each row vector ``x`` the transformation is::

        x_normalized = x / ||x||_p

    where ``p`` is chosen by the ``norm`` parameter:

    * ``"l2"`` (default): Euclidean norm; the dot product of any two
      normalized samples equals the cosine of the angle between them.
    * ``"l1"``: Manhattan norm; useful when the direction of the feature
      vector matters more than relative magnitudes.
    * ``"max"``: divides by the largest absolute element; guarantees the
      output lies in [-1, 1].

    Row wise normalization is particularly effective for text classification
    and clustering algorithms that rely on the dot product or cosine
    similarity (e.g. k-means on TF-IDF vectors, linear SVMs on bag-of-words
    features).

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.Normalizer.html
    """

    SCHEMA = NormalizerSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Normalize each row (sample) to unit norm across the selected columns. "
            "Select two or more columns; a single column collapses to plus or minus 1."
        ),
        es=(
            "Normaliza cada fila (muestra) a norma unitaria a lo largo de las columnas "
            "seleccionadas. Selecciona dos o más columnas; una sola columna colapsa a "
            "más o menos 1."
        ),
        pt=(
            "Normaliza cada linha (amostra) para norma unitária ao longo das colunas "
            "selecionadas. Selecione duas ou mais colunas; uma única coluna colapsa "
            "para mais ou menos 1."
        ),
        de=(
            "Normalisiert jede Zeile (Stichprobe) über die ausgewählten Spalten auf "
            "Einheitsnorm. Mindestens zwei Spalten auswählen; eine einzelne Spalte "
            "kollabiert zu plus oder minus 1."
        ),
        zh=(
            "在所选列上将每一行（样本）归一化为单位范数。"
            "请选择两列或以上；单列会收敛为正负 1。"
        ),
    )
    DISPLAY_NAME = MultilingualString(
        en="Row Wise Normalizer",
        es="Normalizador por filas",
        pt="Normalizador por linhas",
        de="Zeilenweiser Normalisierer",
        zh="按行归一化器",
    )
    IMAGE_PREVIEW = "normalizer.png"

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
