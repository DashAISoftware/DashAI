from imblearn.under_sampling import RandomUnderSampler

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
from DashAI.back.types.dashai_data_type import DashAIDataType


class RUSchema(BaseSchema):
    """Schema for configuring the RandomUnderSamplerConverter.

    Wraps ``imblearn.under_sampling.RandomUnderSampler`` and exposes the
    sampling strategy and random seed as schema fields validated before
    being forwarded to the underlying imbalanced-learn estimator.
    """

    sampling_strategy: schema_field(
        union_type(float_field(gt=0.0, le=1.0), enum_field(["auto"])),
        "auto",
        description=MultilingualString(
            en="Sampling strategy (float or 'auto') to reduce majority class.",
            es=(
                "Estrategia de muestreo (float o 'auto') para reducir la clase "
                "mayoritaria."
            ),
            pt=(
                "Estratégia de amostragem (float ou 'auto') para reduzir a classe "
                "majoritária."
            ),
            de=(
                "Abtaststrategie (float oder 'auto') zur Reduzierung der "
                "Mehrheitsklasse."
            ),
            zh="采样策略（浮点数或'auto'），用于减少多数类。",
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


class RandomUnderSamplerConverter(
    SamplingConverter, ImbalancedLearnWrapper, RandomUnderSampler
):
    """Balance class distribution by randomly discarding majority-class samples.

    Under-sampling addresses class imbalance by reducing the size of one or
    more over-represented classes rather than synthesising new minority-class
    examples. ``RandomUnderSampler`` achieves this by drawing a random subset
    of the majority class without replacement until the desired
    ``sampling_strategy`` ratio is reached.

    The ``sampling_strategy`` parameter controls the resulting ratio between
    the minority and majority class after resampling. When set to ``"auto"``,
    the majority class is down-sampled until it matches the size of the next
    largest class. A float value specifies the desired minority-to-majority
    ratio directly.

    Input column types are preserved in the output. Type determination is
    delegated to the ``transform`` method of the parent wrapper.

    Wraps ``imblearn.under_sampling.RandomUnderSampler``.

    References
    ----------
    - [1]https://imbalanced-learn.org/stable/references/generated/imblearn.under_sampling.RandomUnderSampler.html
    """

    SCHEMA = RUSchema
    DESCRIPTION = MultilingualString(
        en="Randomly remove samples from the majority class to balance the dataset.",
        es="Elimina aleatoriamente muestras de la clase mayoritaria para balancear.",
        pt=(
            "Remove aleatoriamente amostras da classe majoritária para "
            "balancear o conjunto de dados."
        ),
        de=(
            "Entfernt zufällig Stichproben der Mehrheitsklasse, um den "
            "Datensatz auszubalancieren."
        ),
        zh="随机删除多数类样本以平衡数据集。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Random Under-Sampler",
        es="Submuestreador Aleatorio",
        pt="Sub-amostrador Aleatório",
        de="Zufälliger Unterabtaster",
        zh="随机欠采样器",
    )
    IMAGE_PREVIEW = "random_under_sampler.png"

    metadata = {
        "allowed_types": [],
        "allowed_dtypes": [],
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

        RandomUnderSampler only removes rows; it does not change column types.
        Types from the input dataset are copied directly in ``transform``.

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
            "RandomUnderSampler preserves input types. "
            "Types are handled in the transform method."
        )
