from sklearn.preprocessing import LabelEncoder as LabelEncoderOperation

from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class LabelEncoder(SklearnLikeConverter, LabelEncoderOperation):
    """Scikit-learn's LabelEncoder wrapper for DashAI."""

    SCHEMA = None
    DESCRIPTION = "Encode target labels with value between 0 and n_classes-1."
