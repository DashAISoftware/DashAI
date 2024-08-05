from sklearn.preprocessing import Binarizer as BinarizerOperation

from DashAI.back.converters.scikit_learn.sklearn_like_converter import SklearnLikeConverter


class Binarizer(SklearnLikeConverter, BinarizerOperation):
     """Scikit-learn's Binarizer wrapper for DashAI."""