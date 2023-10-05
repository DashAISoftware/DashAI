# flake8: noqa
from DashAI.back.models.base_model import BaseModel
from DashAI.back.models.hugging_face.distilbert_transformer import DistilBertTransformer
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformer,
)
from DashAI.back.models.hugging_face.vit_transformer import ViTTransformer
from DashAI.back.models.scikit_learn.decision_tree_classifier import (
    DecisionTreeClassifier,
)
from DashAI.back.models.scikit_learn.dummy_classifier import DummyClassifier
from DashAI.back.models.scikit_learn.hist_gradient_boosting_classifier import (
    HistGradientBoostingClassifier,
)
from DashAI.back.models.scikit_learn.k_neighbors_classifier import KNeighborsClassifier
from DashAI.back.models.scikit_learn.logistic_regression import LogisticRegression
from DashAI.back.models.scikit_learn.random_forest_classifier import (
    RandomForestClassifier,
)
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.scikit_learn.svc import SVC
