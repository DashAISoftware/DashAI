from imblearn.combine import SMOTEENN

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


class SMOTEENNSchema(BaseSchema):
    """Schema for SMOTEENNConverter hyperparameters.

    Configures the two-stage SMOTE-ENN hybrid: first the SMOTE oversampling pass
    (``sampling_strategy``, ``k_neighbors``, ``random_state``), then the ENN
    cleaning pass. Both passes share the same ``random_state``.
    """

    sampling_strategy: schema_field(
        union_type(float_field(gt=0.0, le=1.0), enum_field(["auto"])),
        "auto",
        description=MultilingualString(
            en="Sampling strategy to apply SMOTE and clean the dataset.",
            es=(
                "Estrategia de muestreo para aplicar SMOTE y limpiar el "
                "conjunto de datos."
            ),
            pt=(
                "Estratégia de amostragem para aplicar SMOTE e limpar o "
                "conjunto de dados."
            ),
            de=(
                "Abtaststrategie zur Anwendung von SMOTE und Bereinigung des "
                "Datensatzes."
            ),
            zh="应用SMOTE并清理数据集的采样策略。",
        ),
    )  # type: ignore
    random_state: schema_field(
        none_type(int_field()),
        None,
        description=MultilingualString(
            en="Seed used for reproducibility.",
            es="Semilla usada para reproducibilidad.",
            pt="Semente usada para reprodutibilidade.",
            de="Startwert für die Reproduzierbarkeit.",
            zh="用于可重复性的随机种子。",
        ),
    )  # type: ignore
    k_neighbors: schema_field(
        int_field(ge=1),
        5,
        description=MultilingualString(
            en="Number of neighbors used by SMOTE.",
            es="Número de vecinos utilizados por SMOTE.",
            pt="Número de vizinhos utilizados pelo SMOTE.",
            de="Anzahl der von SMOTE verwendeten Nachbarn.",
            zh="SMOTE使用的邻居数量。",
        ),
    )  # type: ignore


class SMOTEENNConverter(SamplingConverter, ImbalancedLearnWrapper, SMOTEENN):
    """Hybrid sampler combining SMOTE oversampling
    with Edited Nearest Neighbours cleaning.

    SMOTE-ENN is a two-stage resampling strategy for imbalanced classification:

    1. **Over-sampling**: SMOTE generates synthetic minority-class examples by
       interpolating between each minority sample and its k-nearest minority
       neighbours, increasing the minority class size.
    2. **Cleaning**: Edited Nearest Neighbours (ENN) removes any sample (from
       either class) whose class label disagrees with the majority vote of its
       nearest neighbours, reducing class overlap and borderline noise.

    The combined effect is a more balanced and cleaner decision boundary than either
    technique alone. All schema parameters are forwarded to imbalanced-learn's
    ``SMOTEENN`` and its internal ``SMOTE`` sub-estimator.

    References
    ----------
    - [1] Chawla, N.V. et al. (2002). "SMOTE: Synthetic Minority Over-sampling
           Technique." JAIR, 16, 321-357. https://arxiv.org/abs/1106.1813
    - [2] Batista, G.E.A.P.A. et al. (2004). "A study of the behaviour of several
           methods for balancing machine learning training data." ACM SIGKDD
           Explorations, 6(1), 20-29.
    - [3] https://imbalanced-learn.org/stable/references/generated/imblearn.combine.SMOTEENN.html
    """

    SCHEMA = SMOTEENNSchema
    DESCRIPTION = MultilingualString(
        en=("SMOTEENN: SMOTE with noise reduction via Edited Nearest Neighbors."),
        es=(
            "SMOTEENN: SMOTE con reducción de ruido mediante Vecinos Más "
            "Cercanos Editados."
        ),
        pt=(
            "SMOTEENN: SMOTE com redução de ruído via Vizinhos Mais Próximos Editados."
        ),
        de="SMOTEENN: SMOTE mit Rauschreduzierung durch Edited Nearest Neighbors.",
        zh="SMOTEENN：通过编辑最近邻进行降噪的SMOTE（合成少数类过采样技术）。",
    )
    DISPLAY_NAME = MultilingualString(
        en="SMOTE-ENN (Hybrid Sampling)",
        es="SMOTE-ENN (Muestreo Híbrido)",
        pt="SMOTEENN (Amostragem Híbrida)",
        de="SMOTE-ENN (Hybride Abtastung)",
        zh="SMOTE-ENN（混合采样）",
    )
    IMAGE_PREVIEW = "smoteenn.png"

    metadata = {
        "allowed_types": [Float, Integer, Categorical],
        "allowed_dtypes": [],
        "non_allowed_dtypes": NON_NUMERIC_DTYPES,
    }

    def __init__(self, **kwargs):
        """Initialise SMOTE-ENN with a SMOTE sub-instance and combined kwargs.

        A ``SMOTE`` instance is constructed first (to configure over-sampling),
        then passed as an argument to the underlying ``SMOTEENN`` estimator via
        the parent wrapper.

        Parameters
        ----------
        **kwargs : dict
            sampling_strategy : str or float or dict, optional
                Resampling strategy. Default ``"auto"``.
            random_state : int or None, optional
                Seed for the random number generator. Default ``None``.
            k_neighbors : int or None, optional
                Number of nearest neighbours for SMOTE. Default ``None``
                (uses the SMOTE default of 5).
        """
        from imblearn.over_sampling import SMOTE

        self.smote = SMOTE(
            sampling_strategy=kwargs.get("sampling_strategy", "auto"),
            random_state=kwargs.get("random_state"),
            k_neighbors=kwargs.get("k_neighbors"),
        )

        super().__init__(
            smote=self.smote,
            sampling_strategy=kwargs.get("sampling_strategy", "auto"),
            random_state=kwargs.get("random_state"),
        )

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Not implemented; type preservation is handled in ``transform``.

        SMOTEENN preserves the types of all input columns; type assignment is
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
            "SMOTEENN preserves input types. Types are handled in the transform method."
        )
