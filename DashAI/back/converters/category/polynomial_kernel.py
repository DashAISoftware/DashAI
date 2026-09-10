from typing import Final

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.core.utils import MultilingualString
from DashAI.back.static.icons import Icon


class PolynomialKernelConverter(BaseConverter):
    """Base class for converters that apply polynomial or kernel feature mappings.

    Polynomial kernel converters expand the feature space using explicit
    polynomial or kernel approximation methods. Examples include
    PolynomialFeatures and kernel samplers such as RBFSampler,
    AdditiveChi2Sampler, and SkewedChi2Sampler.

    Use these converters to enable linear models to learn nonlinear boundaries
    without switching to kernel SVMs.
    """

    CATEGORY = MultilingualString(
        en="Polynomial & Kernel Methods",
        es="Métodos Polinomiales y de Kernel",
        pt="Métodos Polinomiais e de Kernel",
        de="Polynomiale und Kernel-Methoden",
        zh="多项式与核方法",
    )
    ICON: Final[str] = Icon.Functions.value
    COLOR: Final[str] = "rgb(153, 102, 255)"
