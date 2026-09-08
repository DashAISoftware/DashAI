from imblearn.over_sampling import SMOTE

from DashAI.back.converters.category.sampling import SamplingConverter
from DashAI.back.converters.imbalanced_learn_wrapper import ImbalancedLearnWrapper
from DashAI.back.core.schema_fields import (
    enum_field,
    float_field,
    int_field,
    none_type,
    schema_field,
    union_type,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.utils import NON_NUMERIC_DTYPES
from DashAI.back.types.value_types import Float, Integer


class SMOTESchema(BaseSchema):
    """Schema for SMOTEConverter hyperparameters.

    Configures the sampling strategy, random seed, and neighbourhood size for
    imbalanced-learn's ``SMOTE`` over-sampler. The key parameter is
    ``sampling_strategy``, which controls how many synthetic samples are created
    relative to the majority class.
    """

    sampling_strategy: schema_field(
        union_type(float_field(gt=0.0, le=1.0), enum_field(["auto"])),
        "auto",
        description=MultilingualString(
            en=(
                "Sampling strategy (float or 'auto') to determine minority class size."
            ),
            es=(
                "Estrategia de muestreo (float o 'auto') para determinar el "
                "tamaño de la clase minoritaria."
            ),
            pt=(
                "Estratégia de amostragem (float ou 'auto') para determinar o "
                "tamanho da classe minoritária."
            ),
            de=(
                "Abtaststrategie (float oder 'auto') zur Bestimmung der Größe "
                "der Minderheitsklasse."
            ),
            zh="采样策略（浮点数或'auto'），用于确定少数类的大小。",
        ),
    )  # type: ignore
    random_state: schema_field(
        none_type(int_field()),
        None,
        description=MultilingualString(
            en="Seed for reproducibility.",
            es="Semilla para reproducibilidad.",
            pt="Semente para reprodutibilidade.",
            de="Startwert für die Reproduzierbarkeit.",
            zh="用于可重复性的随机种子。",
        ),
    )  # type: ignore
    k_neighbors: schema_field(
        int_field(ge=1),
        5,
        description=MultilingualString(
            en="Number of neighbors to use for generating synthetic samples.",
            es="Número de vecinos para generar muestras sintéticas.",
            pt="Número de vizinhos a usar para gerar amostras sintéticas.",
            de="Anzahl der Nachbarn zur Erzeugung synthetischer Stichproben.",
            zh="用于生成合成样本的邻居数量。",
        ),
    )  # type: ignore


class SMOTEConverter(SamplingConverter, ImbalancedLearnWrapper, SMOTE):
    """Balances class distribution by generating synthetic minority-class samples.

    SMOTE (Synthetic Minority Over-sampling Technique) addresses class imbalance
    by creating new minority-class examples via linear interpolation between each
    minority sample and one of its ``k`` nearest minority-class neighbours. Unlike
    simple random over-sampling (which duplicates existing rows), SMOTE generates
    novel samples in the feature space, improving classifier generalisation.

    The technique is applied only during training; the test split is never resampled.
    All schema parameters are forwarded to imbalanced-learn's ``SMOTE`` estimator.

    References
    ----------
    - [1] Chawla, N.V. et al. (2002). "SMOTE: Synthetic Minority Over-sampling
           Technique." Journal of Artificial Intelligence Research, 16, 321-357.
           https://arxiv.org/abs/1106.1813
    - [2] https://imbalanced-learn.org/stable/references/generated/imblearn.over_sampling.SMOTE.html
    """

    SCHEMA = SMOTESchema
    DESCRIPTION = MultilingualString(
        en="SMOTE: Synthetic Minority Oversampling Technique.",
        es="SMOTE: Técnica de Sobremuestreo de la Minoría Sintética.",
        pt="SMOTE: Técnica de Superamostragem de Minoria Sintética.",
        de="SMOTE: Synthetische Überabtastungstechnik für die Minderheitsklasse.",
        zh="SMOTE（合成少数类过采样技术）。",
    )
    DISPLAY_NAME = MultilingualString(
        en="SMOTE (Oversampling)",
        es="SMOTE (Sobre-muestreo)",
        pt="SMOTE (Super-amostragem)",
        de="SMOTE (Überabtastung)",
        zh="SMOTE（过采样）",
    )
    IMAGE_PREVIEW = "smote.png"

    metadata = {
        "allowed_types": [Float, Integer, Categorical],
        "allowed_dtypes": [],
        "non_allowed_dtypes": NON_NUMERIC_DTYPES,
    }

    def __init__(self, **kwargs):
        """Initialise by forwarding kwargs to the imbalanced-learn wrapper.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments forwarded to :class:`ImbalancedLearnWrapper`.
        """
        super().__init__(**kwargs)

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Not implemented; type preservation is handled in ``transform``.

        SMOTE preserves the types of all input columns; type assignment is
        performed directly in ``transform`` rather than here.

        Parameters
        ----------
        column_name : str or None, optional
            Name of the column whose output type is queried. Ignored because
            this method always raises. Default ``None``.

        Raises
        ------
        NotImplementedError
            Always, because type determination is delegated to ``transform``.
        """
        raise NotImplementedError(
            "SMOTE preserves input types. Types are handled in the transform method."
        )
