from sklearn.preprocessing import PolynomialFeatures as PolynomialFeaturesOperation

from DashAI.back.converters.category.polynomial_kernel import PolynomialKernelConverter
from DashAI.back.converters.sklearn_wrapper import SklearnWrapper
from DashAI.back.core.schema_fields import (
    bool_field,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer


class PolynomialFeaturesSchema(BaseSchema):
    """Schema for configuring the PolynomialFeatures converter.

    Wraps ``sklearn.preprocessing.PolynomialFeatures`` and exposes the
    polynomial degree, interaction-only flag, bias column inclusion, and
    output array memory order as schema fields validated before being
    forwarded to the underlying scikit-learn estimator.
    """

    degree: schema_field(
        int_field(ge=1),
        2,
        description=MultilingualString(
            en="The degree of the polynomial features.",
            es="El grado de las características polinomiales.",
            pt="O grau das características polinomiais.",
            de="Der Grad der polynomialen Merkmale.",
            zh="多项式特征的次数。",
        ),
    )  # type: ignore
    interaction_only: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en=(
                "If True, only interaction features are produced: features that "
                "are products of at most degree distinct input features."
            ),
            es=(
                "Si es True, solo se producen características de interacción: "
                "productos de hasta 'degree' características de entrada distintas."
            ),
            pt=(
                "Se True, somente características de interação são produzidas: "
                "produtos de até 'degree' características de entrada distintas."
            ),
            de=(
                "Wenn True, werden nur Interaktionsmerkmale erzeugt: Produkte von "
                "höchstens 'degree' verschiedenen Eingangsmerkmalen."
            ),
            zh="如果为 True，则只生成交叉特征：至多为 degree 个不同输入特征的乘积。",
        ),
    )  # type: ignore
    include_bias: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en=(
                "If True (default), then include a bias column (a column of ones "
                "that act as an intercept term)."
            ),
            es=(
                "Si es True (por defecto), incluye una columna de sesgo (columna "
                "de unos que actúa como término independiente)."
            ),
            pt=(
                "Se True (padrão), inclui uma coluna de viés (coluna de uns que "
                "atua como termo de intercepto)."
            ),
            de=(
                "Wenn True (Standard), wird eine Bias-Spalte einbezogen "
                "(eine Spalte aus Einsen, die als Achsenabschnitt wirkt)."
            ),
            zh="如果为 True（默认），则包含偏置列（全 1 列，用作截距项）。",
        ),
    )  # type: ignore
    order: schema_field(
        enum_field(["C", "F"]),
        "C",
        description=MultilingualString(
            en=(
                "Order of output array in the dense case. 'F' order is faster "
                "to compute, but may slow down subsequent estimators."
            ),
            es=(
                "Orden del arreglo de salida en el caso denso. El orden 'F' es "
                "más rápido de calcular, pero puede ralentizar estimadores "
                "posteriores."
            ),
            pt=(
                "Ordem do array de saída no caso denso. A ordem 'F' é mais "
                "rápida de calcular, mas pode lentificar estimadores posteriores."
            ),
            de=(
                "Reihenfolge des Ausgabe-Arrays im dichten Fall. Reihenfolge 'F' "
                "ist schneller zu berechnen, kann aber nachfolgende Schätzer "
                "verlangsamen."
            ),
            zh="稠密情况下输出数组的存储顺序。'F' 顺序计算更快，但可能减慢后续估计器。",
        ),
    )  # type: ignore


class PolynomialFeatures(
    PolynomialKernelConverter, SklearnWrapper, PolynomialFeaturesOperation
):
    """Generate polynomial and interaction features up to a specified degree.

    Given *d* input features, this converter produces all monomials of the
    form ``x_1^p_1 * x_2^p_2 * … * x_d^p_d`` where ``p_1 + … + p_d <= degree``
    (and each ``p_i >= 0``). For example, with two input features ``[a, b]``
    and ``degree=2``, the output is ``[1, a, b, a², ab, b²]``.

    When ``interaction_only=True`` only cross-terms are retained (no squared
    or higher pure-power terms), which is useful when features are already on
    a meaningful scale and self-interactions are not informative.

    Setting ``include_bias=True`` (the default) prepends a column of ones,
    acting as an intercept term for linear models that lack an explicit bias.

    The ``order`` parameter controls whether the dense output array is stored
    in C (row-major) or Fortran (column-major) order. ``"F"`` order can speed
    up the transformation itself but may slow downstream estimators.

    Output columns are typed as ``Float64`` in DashAI.

    Wraps ``sklearn.preprocessing.PolynomialFeatures``.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.PolynomialFeatures.html
    """

    SCHEMA = PolynomialFeaturesSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Generate polynomial and interaction features. For example, if an "
            "input sample is [a, b], the degree-2 polynomial features are "
            "[1, a, b, a^2, ab, b^2]."
        ),
        es=(
            "Genera características polinomiales e interacciones. Por ejemplo, "
            "si una muestra de entrada es [a, b], las características de grado 2 "
            "son [1, a, b, a^2, ab, b^2]."
        ),
        pt=(
            "Gera características polinomiais e de interação. Por exemplo, se "
            "uma amostra de entrada é [a, b], as características de grau 2 são "
            "[1, a, b, a^2, ab, b^2]."
        ),
        de=(
            "Polynomiale und Interaktionsmerkmale generieren. Zum Beispiel, wenn "
            "eine Eingabe [a, b] ist, sind die Grad-2-Polynommerkmale "
            "[1, a, b, a^2, ab, b^2]."
        ),
        zh=(
            "生成多项式特征和交叉特征。例如，输入样本为 [a, b] 时，"
            "2 次多项式特征为 [1, a, b, a^2, ab, b^2]。"
        ),
    )
    DISPLAY_NAME = MultilingualString(
        en="Polynomial Features",
        es="Características Polinomiales",
        pt="Características Polinomiais",
        de="Polynomiale Merkmale",
        zh="多项式特征",
    )
    IMAGE_PREVIEW = "polynomial_features.png"

    metadata = {"allowed_types": [Float, Integer], "allowed_dtypes": []}

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return ``Float64`` as the output type for all polynomial feature columns.

        Parameters
        ----------
        column_name : str or None, optional
            Name of the output column. Not used, since all columns receive the
            same ``Float64`` type. Default ``None``.

        Returns
        -------
        Float
            A DashAI ``Float`` type backed by ``pyarrow.float64()``.
        """
        import pyarrow as pa

        return Float(arrow_type=pa.float64())
