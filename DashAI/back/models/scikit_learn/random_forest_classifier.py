from sklearn.ensemble import RandomForestClassifier as _RandomForestClassifier

from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class RandomForestClassifier(
    TabularClassificationModel, SklearnLikeModel, _RandomForestClassifier
):
    """
    A random forest classifier. A random forest is a meta estimator that fits a number
    of decision tree classifiers on various sub-samples of the dataset and uses
    averaging to improve the predictive accuracy and control over-fitting.
    The sub-sample size is controlled with the max_samples parameter if
    bootstrap=True (default), otherwise the whole dataset is used to build each tree.
    """
