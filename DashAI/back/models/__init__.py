# flake8: noqa
from DashAI.back.models.base_generative_model import BaseGenerativeModel
from DashAI.back.models.base_model import BaseModel
from DashAI.back.models.hugging_face.distilbert_transformer import DistilBertTransformer
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformer,
)
from DashAI.back.models.hugging_face.qwen_model import Qwen25_05BInstruct, Qwen25_15BInstruct
from DashAI.back.models.hugging_face.stable_diffusion_v1_depth_controlnet import (
    StableDiffusionXLV1ControlNet,
)
from DashAI.back.models.hugging_face.stable_diffusion_v2_model import (
    StableDiffusion2,
)
from DashAI.back.models.hugging_face.stable_diffusion_v3_model import (
    StableDiffusion3Medium,
)
from DashAI.back.models.scikit_learn.bow_text_classification_model import (
    BagOfWordsTextClassificationModel,
)
from DashAI.back.models.scikit_learn.decision_tree_classifier import (
    DecisionTreeClassifier,
)
from DashAI.back.models.scikit_learn.dummy_classifier import DummyClassifier
from DashAI.back.models.scikit_learn.gradient_boosting_regression import (
    GradientBoostingR,
)
from DashAI.back.models.scikit_learn.hist_gradient_boosting_classifier import (
    HistGradientBoostingClassifier,
)
from DashAI.back.models.scikit_learn.k_neighbors_classifier import KNeighborsClassifier
from DashAI.back.models.scikit_learn.linear_regression import LinearRegression
from DashAI.back.models.scikit_learn.linearSVR import LinearSVR
from DashAI.back.models.scikit_learn.logistic_regression import LogisticRegression
from DashAI.back.models.scikit_learn.mlp_regression import MLPRegression
from DashAI.back.models.scikit_learn.random_forest_classifier import (
    RandomForestClassifier,
)
from DashAI.back.models.scikit_learn.random_forest_regression import (
    RandomForestRegression,
)
from DashAI.back.models.scikit_learn.ridge_regression import RidgeRegression
from DashAI.back.models.scikit_learn.sklearn_like_classifier import (
    SklearnLikeClassifier,
)
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.scikit_learn.sklearn_like_regressor import SklearnLikeRegressor
from DashAI.back.models.scikit_learn.svc import SVC

from DashAI.back.models.RAG import RAGPipeline
from DashAI.back.models.hugging_face.phi_4_mini_instruct_model import Phi4MiniInstructModel
