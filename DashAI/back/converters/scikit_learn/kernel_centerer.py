from sklearn.preprocessing import KernelCenterer as KernelCentererOperation

from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class KernelCenterer(SklearnLikeConverter, KernelCentererOperation):
    """Scikit-learn's KernelCenterer wrapper for DashAI."""

    SCHEMA = None
    DESCRIPTION = "Center a kernel matrix."
