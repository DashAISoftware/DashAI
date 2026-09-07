import logging

# Hugging Face module
from DashAI.back.converters.hugging_face.embedding import Embedding
from DashAI.back.converters.hugging_face.image_embedding import (
    ImageEmbeddingConverter,
)
from DashAI.back.converters.hugging_face.tokenizer import TokenizerConverter

# Imbalanced_learn
from DashAI.back.converters.imbalanced_learn.random_under_sampler_converter import (
    RandomUnderSamplerConverter,
)
from DashAI.back.converters.imbalanced_learn.smote_converter import SMOTEConverter
from DashAI.back.converters.imbalanced_learn.smoteenn_converter import SMOTEENNConverter

# Kernel approximation module
from DashAI.back.converters.scikit_learn.additive_chi_2_sampler import (
    AdditiveChi2Sampler,
)
from DashAI.back.converters.scikit_learn.bag_of_words import BagOfWordsConverter

# Preprocessing module
from DashAI.back.converters.scikit_learn.binarizer import Binarizer

# Decomposition module
from DashAI.back.converters.scikit_learn.fast_ica import FastICA

# Feature selection module
from DashAI.back.converters.scikit_learn.generic_univariate_select import (
    GenericUnivariateSelect,
)
from DashAI.back.converters.scikit_learn.incremental_pca import IncrementalPCA
from DashAI.back.converters.scikit_learn.knn_imputer import KNNImputer
from DashAI.back.converters.scikit_learn.label_encoder import LabelEncoder
from DashAI.back.converters.scikit_learn.max_abs_scaler import MaxAbsScaler
from DashAI.back.converters.scikit_learn.min_max_scaler import MinMaxScaler
from DashAI.back.converters.scikit_learn.missing_indicator import MissingIndicator
from DashAI.back.converters.scikit_learn.normalizer import Normalizer
from DashAI.back.converters.scikit_learn.nystroem import Nystroem
from DashAI.back.converters.scikit_learn.one_hot_encoder import OneHotEncoder
from DashAI.back.converters.scikit_learn.ordinal_encoder import OrdinalEncoder
from DashAI.back.converters.scikit_learn.pca import PCA
from DashAI.back.converters.scikit_learn.polynomial_features import PolynomialFeatures
from DashAI.back.converters.scikit_learn.rbf_sampler import RBFSampler
from DashAI.back.converters.scikit_learn.select_fdr import SelectFdr
from DashAI.back.converters.scikit_learn.select_fpr import SelectFpr
from DashAI.back.converters.scikit_learn.select_fwe import SelectFwe
from DashAI.back.converters.scikit_learn.select_k_best import SelectKBest
from DashAI.back.converters.scikit_learn.select_percentile import SelectPercentile

# Impute module
from DashAI.back.converters.scikit_learn.simple_imputer import SimpleImputer
from DashAI.back.converters.scikit_learn.skewed_chi_2_sampler import SkewedChi2Sampler
from DashAI.back.converters.scikit_learn.standard_scaler import StandardScaler
from DashAI.back.converters.scikit_learn.tf_idf import TFIDFConverter
from DashAI.back.converters.scikit_learn.truncated_svd import TruncatedSVD
from DashAI.back.converters.scikit_learn.variance_threshold import VarianceThreshold
from DashAI.back.converters.segmentation.sam3_segment_converter import (
    SAM3SegmentConverter,
)

# Simple converters
from DashAI.back.converters.simple_converters.character_replacer import (
    CharacterReplacer,
)
from DashAI.back.converters.simple_converters.column_arithmetic import ColumnArithmetic
from DashAI.back.converters.simple_converters.column_concat import ColumnConcat
from DashAI.back.converters.simple_converters.column_remover import ColumnRemover
from DashAI.back.converters.simple_converters.nan_remover import NanRemover
from DashAI.back.converters.simple_converters.numeric_expansion import NumericExpansion
from DashAI.back.converters.simple_converters.time_series_window import (
    TimeSeriesWindowConverter,
)
from DashAI.back.converters.simple_converters.type_cast import TypeCast

# Credentials
from DashAI.back.credentials.huggingface_credential import HuggingFaceCredential
from DashAI.back.credentials.kaggle_credential import KaggleCredential

# DataLoaders
from DashAI.back.dataloaders.classes.arff_dataloader import ARFFDataLoader
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.excel_dataloader import ExcelDataLoader
from DashAI.back.dataloaders.classes.image_dataloader import ImageDataLoader
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader

# Dataset Sources
from DashAI.back.dataset_sources.huggingface_dataset_source import (
    HuggingFaceDatasetSource,
)
from DashAI.back.dataset_sources.openml_dataset_source import OpenMLDatasetSource
from DashAI.back.dataset_sources.zenodo_dataset_source import ZenodoDatasetSource

# Evaluation Strategies
from DashAI.back.evaluation.cv import CrossValidationEvaluationStrategy
from DashAI.back.evaluation.forecasting_cv import (
    ForecastingCrossValidationEvaluationStrategy,
)
from DashAI.back.evaluation.forecasting_holdout import (
    ForecastingHoldoutEvaluationStrategy,
)
from DashAI.back.evaluation.holdout import HoldoutEvaluationStrategy

# Explainers
from DashAI.back.explainability.explainers.contrastive_shap import ContrastiveShap
from DashAI.back.explainability.explainers.dice_counterfactual import (
    DiceCounterfactual,
)
from DashAI.back.explainability.explainers.grad_cam import GradCam
from DashAI.back.explainability.explainers.kernel_shap import KernelShap
from DashAI.back.explainability.explainers.lime_text import LimeText
from DashAI.back.explainability.explainers.nearest_counterfactual import (
    NearestCounterfactual,
)
from DashAI.back.explainability.explainers.occlusion_saliency import OcclusionSaliency
from DashAI.back.explainability.explainers.partial_dependence import PartialDependence
from DashAI.back.explainability.explainers.permutation_feature_importance import (
    PermutationFeatureImportance,
)
from DashAI.back.explainability.explainers.regression_kernel_shap import (
    RegressionKernelShap,
)
from DashAI.back.explainability.explainers.regression_partial_dependence import (
    RegressionPartialDependence,
)
from DashAI.back.explainability.explainers.regression_permutation_feature_importance import (  # noqa: E501
    RegressionPermutationFeatureImportance,
)
from DashAI.back.explainability.explainers.token_ablation import TokenAblation

# Explorers
from DashAI.back.exploration.explorers.box_plot import BoxPlotExplorer
from DashAI.back.exploration.explorers.class_overlap import ClassOverlapExplorer
from DashAI.back.exploration.explorers.corr_matrix import CorrelationMatrixExplorer
from DashAI.back.exploration.explorers.cov_matrix import CovarianceMatrixExplorer
from DashAI.back.exploration.explorers.density_heatmap import DensityHeatmapExplorer
from DashAI.back.exploration.explorers.describe_explorer import DescribeExplorer
from DashAI.back.exploration.explorers.ecdf_plot import ECDFPlotExplorer
from DashAI.back.exploration.explorers.histogram_plot import HistogramPlotExplorer
from DashAI.back.exploration.explorers.multibox_plot import MultiColumnBoxPlotExplorer
from DashAI.back.exploration.explorers.parallel_categories import (
    ParallelCategoriesExplorer,
)
from DashAI.back.exploration.explorers.parallel_cordinates import (
    ParallelCordinatesExplorer,
)
from DashAI.back.exploration.explorers.scatter_matrix import ScatterMatrixExplorer
from DashAI.back.exploration.explorers.scatter_plot import ScatterPlotExplorer
from DashAI.back.exploration.explorers.time_series_plot import (
    TimeSeriesPlotExplorer,
)
from DashAI.back.exploration.explorers.wordcloud import WordcloudExplorer

# Jobs
from DashAI.back.job.component_download_job import ComponentDownloadJob
from DashAI.back.job.converter_job import ConverterJob
from DashAI.back.job.datafile_job import DatafileJob
from DashAI.back.job.dataset_job import DatasetJob
from DashAI.back.job.explainer_job import ExplainerJob
from DashAI.back.job.explorer_job import ExplorerJob
from DashAI.back.job.generative_job import GenerativeJob
from DashAI.back.job.model_job import ModelJob
from DashAI.back.job.pipeline_job import PipelineJob
from DashAI.back.job.predict_job import PredictJob
from DashAI.back.job.RAG_job import RAGJob

# Metrics
from DashAI.back.metrics.classification.accuracy import Accuracy
from DashAI.back.metrics.classification.balanced_accuracy import BalancedAccuracy
from DashAI.back.metrics.classification.cohen_kappa import CohenKappa
from DashAI.back.metrics.classification.f1 import F1
from DashAI.back.metrics.classification.hamming_distance import HammingDistance
from DashAI.back.metrics.classification.log_loss import LogLoss
from DashAI.back.metrics.classification.matthews_corrcoef import MatthewsCorrCoef
from DashAI.back.metrics.classification.precision import Precision
from DashAI.back.metrics.classification.recall import Recall
from DashAI.back.metrics.classification.roc_auc import ROCAUC
from DashAI.back.metrics.forecasting.mape import MAPE
from DashAI.back.metrics.forecasting.smape import SMAPE
from DashAI.back.metrics.regression.explained_variance import ExplainedVariance
from DashAI.back.metrics.regression.mae import MAE
from DashAI.back.metrics.regression.median_absolute_error import MedianAbsoluteError
from DashAI.back.metrics.regression.mse import MSE
from DashAI.back.metrics.regression.r2 import R2
from DashAI.back.metrics.regression.rmse import RMSE
from DashAI.back.metrics.translation.bleu import Bleu
from DashAI.back.metrics.translation.chrf import Chrf
from DashAI.back.metrics.translation.ter import Ter
from DashAI.back.models.cnn_image_classifier import CNNImageClassifier
from DashAI.back.models.efficientnet_b0_image_classifier import (
    EfficientNetB0ImageClassifier,
)
from DashAI.back.models.forecasting.arima import ARIMA
from DashAI.back.models.forecasting.exponential_smoothing import (
    ExponentialSmoothing,
)
from DashAI.back.models.forecasting.naive import NaiveForecaster
from DashAI.back.models.forecasting.seasonal_naive import (
    SeasonalNaiveForecaster,
)

# Models
from DashAI.back.models.hugging_face.albert_transformer import AlbertTransformer
from DashAI.back.models.hugging_face.bert_transformer import BertTransformer
from DashAI.back.models.hugging_face.bertin_transformer import BertinTransformer
from DashAI.back.models.hugging_face.beto_transformer import BetoTransformer
from DashAI.back.models.hugging_face.deberta_v3_transformer import DebertaV3Transformer
from DashAI.back.models.hugging_face.distilbert_transformer import DistilBertTransformer
from DashAI.back.models.hugging_face.electra_transformer import ElectraTransformer
from DashAI.back.models.hugging_face.llama_model import (
    Llama31_8BInstruct,
    Llama32_1BInstruct,
    Llama32_3BInstruct,
)
from DashAI.back.models.hugging_face.m2m100_transformer import M2M100Transformer
from DashAI.back.models.hugging_face.minilm_transformer import MiniLMTransformer
from DashAI.back.models.hugging_face.mistral_model import (
    Mistral7BInstructV03,
    MistralNemoInstruct2407,
)
from DashAI.back.models.hugging_face.mixtral_model import (
    Mixtral8x7BInstructQ2K,
    Mixtral8x7BInstructQ4KM,
)
from DashAI.back.models.hugging_face.modernbert_transformer import ModernBertTransformer
from DashAI.back.models.hugging_face.multilingual_bert_transformer import (
    MultilingualBertTransformer,
)
from DashAI.back.models.hugging_face.nllb_transformer import NllbTransformer
from DashAI.back.models.hugging_face.opus_mt_en_de_transformer import (
    OpusMtEnDeTransformer,
)
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformer,
)
from DashAI.back.models.hugging_face.opus_mt_en_fr_transformer import (
    OpusMtEnFrTransformer,
)
from DashAI.back.models.hugging_face.opus_mt_en_roa_transformer import (
    OpusMtEnRoaTransformer,
)
from DashAI.back.models.hugging_face.opus_mt_es_en_transformer import (
    OpusMtEsENTransformer,
)
from DashAI.back.models.hugging_face.opus_mt_fr_en_transformer import (
    OpusMtFrEnTransformer,
)
from DashAI.back.models.hugging_face.opus_mt_roa_en_transformer import (
    OpusMtRoaEnTransformer,
)
from DashAI.back.models.hugging_face.phi_4_mini_instruct_model import (
    Phi4MiniInstructModel,
)
from DashAI.back.models.hugging_face.pixart_sigma_model import PixArtSigma
from DashAI.back.models.hugging_face.qwen_model import (
    Qwen25_05BInstruct,
    Qwen25_15BInstruct,
)
from DashAI.back.models.hugging_face.roberta_transformer import RobertaTransformer
from DashAI.back.models.hugging_face.sd15_depth_controlnet_model import (
    SD15DepthControlNetModel,
)
from DashAI.back.models.hugging_face.sd15_hed_controlnet_model import (
    SD15HEDControlNetModel,
)
from DashAI.back.models.hugging_face.sd15_openpose_controlnet_model import (
    SD15OpenPoseControlNetModel,
)
from DashAI.back.models.hugging_face.sdxl_canny_controlnet_model import (
    SDXLCannyControlNetModel,
)
from DashAI.back.models.hugging_face.sdxl_turbo_model import SDXLTurboModel
from DashAI.back.models.hugging_face.smol_lm_model import (
    SmolLM2_17BInstruct,
    SmolLM2_360MInstruct,
)
from DashAI.back.models.hugging_face.stable_diffusion_v1_depth_controlnet import (
    StableDiffusionXLV1ControlNet,
)
from DashAI.back.models.hugging_face.stable_diffusion_v2_model import (
    StableDiffusion2,
    StableDiffusion2_512,
    StableDiffusion21,
    StableDiffusion21_512,
)
from DashAI.back.models.hugging_face.stable_diffusion_v3_model import (
    StableDiffusion3Medium,
    StableDiffusion35Large,
    StableDiffusion35LargeTurbo,
    StableDiffusion35Medium,
)
from DashAI.back.models.hugging_face.stable_diffusion_xl_model import (
    RealVisXLV4,
    StableDiffusionXL,
)
from DashAI.back.models.hugging_face.t5_small_transformer import T5SmallTransformer
from DashAI.back.models.hugging_face.tongyi_z_image_model import (
    TongyiZImage,
    TongyiZImageTurbo,
)
from DashAI.back.models.hugging_face.xlm_roberta_transformer import (
    XlmRobertaTransformer,
)
from DashAI.back.models.hugging_face.xlnet_transformer import XlnetTransformer
from DashAI.back.models.lenet5_image_classifier import LeNet5ImageClassifier
from DashAI.back.models.mlp_image_classifier import MLPImageClassifier
from DashAI.back.models.pymc.bart_regression import BARTRegression
from DashAI.back.models.RAG import RAGPipeline
from DashAI.back.models.RAG.chunking_models import (
    CharacterChunkModel,
    RecursiveCharacterChunkModel,
    TokenChunkModel,
)
from DashAI.back.models.RAG.embeddings.dense import (
    BERTEmbedding,
    DistilBERTEmbedding,
    E5Embedding,
    InstructorEmbedding,
    LaBSEmbedding,
    RoBERTaEmbedding,
    SentenceTransformerEmbedding,
)
from DashAI.back.models.RAG.extractors import (
    EasyOCRExtractor,
    PlainTextExtractor,
    PyMuPDFExtractor,
    PypdfExtractor,
)
from DashAI.back.models.RAG.prompts import (
    CustomAugmentationPrompt,
    CustomRAGGenerationPrompt,
    DefaultAugmentationPrompt,
    DefaultQARAGGenerationPrompt,
    DefaultRAGGenerationPrompt,
)
from DashAI.back.models.RAG.retrievers.composite.mmr_reranker_retriever import (
    MMRRerankerRetriever,
)
from DashAI.back.models.RAG.retrievers.composite.parallel_retriever import (
    ParallelRetriever,
)
from DashAI.back.models.RAG.retrievers.composite.sequential_retriever import (
    SequentialRetriever,
)
from DashAI.back.models.RAG.retrievers.cross_encoder import (
    SentenceTransformerCrossEncoderRetriever,
)
from DashAI.back.models.RAG.retrievers.dense.dense_embedding_retriever import (
    DenseEmbeddingRetriever,
)
from DashAI.back.models.RAG.retrievers.sparse.bm25_retriever import (
    BM25Retriever,
    BM25VectorizerModel,
)
from DashAI.back.models.RAG.retrievers.sparse.tfidf_retriever import (
    TFIDFRetriever,
    TFIDFVectorizerModel,
)
from DashAI.back.models.resnet18_image_classifier import ResNet18ImageClassifier
from DashAI.back.models.resnet50_image_classifier import ResNet50ImageClassifier
from DashAI.back.models.scikit_learn.adaboost_classifier import AdaBoostClassifier
from DashAI.back.models.scikit_learn.adaboost_regression import AdaBoostRegression
from DashAI.back.models.scikit_learn.bagging_classifier import BaggingClassifier
from DashAI.back.models.scikit_learn.bayesian_ridge_regression import (
    BayesianRidgeRegression,
)
from DashAI.back.models.scikit_learn.bow_text_classification_model import (
    BagOfWordsTextClassificationModel,
)
from DashAI.back.models.scikit_learn.decision_tree_classifier import (
    DecisionTreeClassifier,
)
from DashAI.back.models.scikit_learn.decision_tree_regression import (
    DecisionTreeRegression,
)
from DashAI.back.models.scikit_learn.dummy_classifier import DummyClassifier
from DashAI.back.models.scikit_learn.elastic_net_regression import ElasticNetRegression
from DashAI.back.models.scikit_learn.extra_trees_classifier import ExtraTreesClassifier
from DashAI.back.models.scikit_learn.extra_trees_regression import ExtraTreesRegression
from DashAI.back.models.scikit_learn.gaussian_nb import GaussianNB
from DashAI.back.models.scikit_learn.gradient_boosting_classifier import (
    GradientBoostingClassifier,
)
from DashAI.back.models.scikit_learn.gradient_boosting_regression import (
    GradientBoostingR,
)
from DashAI.back.models.scikit_learn.hist_gradient_boosting_classifier import (
    HistGradientBoostingClassifier,
)
from DashAI.back.models.scikit_learn.hist_gradient_boosting_regression import (
    HistGradientBoostingRegression,
)
from DashAI.back.models.scikit_learn.k_neighbors_classifier import KNeighborsClassifier
from DashAI.back.models.scikit_learn.k_neighbors_regression import KNeighborsRegression
from DashAI.back.models.scikit_learn.lasso_regression import LassoRegression
from DashAI.back.models.scikit_learn.linear_regression import LinearRegression
from DashAI.back.models.scikit_learn.linear_svc_classifier import LinearSVCClassifier
from DashAI.back.models.scikit_learn.linearSVR import LinearSVR
from DashAI.back.models.scikit_learn.logistic_regression import LogisticRegression
from DashAI.back.models.scikit_learn.mlp_classifier import MLPClassifier
from DashAI.back.models.scikit_learn.mlp_regression import MLPRegression
from DashAI.back.models.scikit_learn.random_forest_classifier import (
    RandomForestClassifier,
)
from DashAI.back.models.scikit_learn.random_forest_regression import (
    RandomForestRegression,
)
from DashAI.back.models.scikit_learn.ridge_regression import RidgeRegression
from DashAI.back.models.scikit_learn.sgd_classifier import SGDClassifier
from DashAI.back.models.scikit_learn.svc import SVC
from DashAI.back.models.scikit_learn.svr import SVR
from DashAI.back.models.scikit_learn.tfidf_logreg_text_classification_model import (
    TfIdfLogRegTextClassificationModel,
)

# Optimizers
from DashAI.back.optimizers.hyperopt_optimizer import HyperOptOptimizer
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer

# Pipeline nodes
from DashAI.back.pipeline.data_selector_node import DataSelector
from DashAI.back.pipeline.exploration_node import DataExploration
from DashAI.back.pipeline.prediction_node import Prediction
from DashAI.back.pipeline.retrieve_model_node import RetrieveModel
from DashAI.back.pipeline.train_node import Train

# Plugins
from DashAI.back.plugins.utils import get_available_plugins
from DashAI.back.splitters.group_k_fold import GroupKFoldSplitter

# Splitters
from DashAI.back.splitters.holdout import HoldoutSplitter
from DashAI.back.splitters.k_fold import KFoldSplitter
from DashAI.back.splitters.leave_one_out import LeaveOneOutSplitter
from DashAI.back.splitters.repeated_k_fold import RepeatedKFoldSplitter
from DashAI.back.splitters.repeated_stratified_k_fold import (
    RepeatedStratifiedKFoldSplitter,
)
from DashAI.back.splitters.rolling_origin import RollingOriginSplitter
from DashAI.back.splitters.stratified_group_k_fold import StratifiedGroupKFoldSplitter
from DashAI.back.splitters.stratified_k_fold import StratifiedKFoldSplitter
from DashAI.back.splitters.temporal_holdout import TemporalHoldoutSplitter
from DashAI.back.statistical_tests.anova_test import AnovaTest
from DashAI.back.statistical_tests.corrected_paired_t_test import (
    CorrectedPairedTTest,
)
from DashAI.back.statistical_tests.friedman_test import (
    FriedmanTest,
)

# Statistical tests
from DashAI.back.statistical_tests.helper_tests.bartlett_test import BartlettTest
from DashAI.back.statistical_tests.helper_tests.levene_test import LeveneTest
from DashAI.back.statistical_tests.helper_tests.shapiro_test import ShapiroTest
from DashAI.back.statistical_tests.paired_t_test import PairedTTest
from DashAI.back.statistical_tests.post_hoc_tests.nemenyi_test import NemenyiTest
from DashAI.back.statistical_tests.post_hoc_tests.tukey_test import TukeyHSDTest
from DashAI.back.statistical_tests.wilcoxon_sr_test import (
    WilcoxonSRTest,
)
from DashAI.back.tasks.controlnet_task import ControlNetTask
from DashAI.back.tasks.forecasting_task import ForecastingTask
from DashAI.back.tasks.image_classification_task import ImageClassificationTask

# Tasks
from DashAI.back.tasks.RAG_task import RAGTask
from DashAI.back.tasks.regression_task import RegressionTask
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask
from DashAI.back.tasks.text_classification_task import TextClassificationTask
from DashAI.back.tasks.text_to_image_generation_task import TextToImageGenerationTask
from DashAI.back.tasks.text_to_text_generation_task import TextToTextGenerationTask
from DashAI.back.tasks.translation_task import TranslationTask

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def get_initial_components():
    """
    Obtiene todos los componentes iniciales, incluyendo los básicos
    y los plugins instalados.

    Returns
    -------
    List[type]
        Lista de todas las clases de componentes disponibles
    """
    # Componentes básicos que siempre deben estar disponibles
    basic_components = [
        # Tasks
        TabularClassificationTask,
        TextClassificationTask,
        TranslationTask,
        RegressionTask,
        ForecastingTask,
        NaiveForecaster,
        SeasonalNaiveForecaster,
        ARIMA,
        ExponentialSmoothing,
        TextToImageGenerationTask,
        TextToTextGenerationTask,
        ControlNetTask,
        RAGTask,
        ImageClassificationTask,
        # Models
        AdaBoostClassifier,
        AlbertTransformer,
        AdaBoostRegression,
        BaggingClassifier,
        BagOfWordsTextClassificationModel,
        BertTransformer,
        BertinTransformer,
        BetoTransformer,
        BayesianRidgeRegression,
        BARTRegression,
        DebertaV3Transformer,
        DecisionTreeClassifier,
        DecisionTreeRegression,
        DistilBertTransformer,
        DummyClassifier,
        ElasticNetRegression,
        ElectraTransformer,
        ExtraTreesClassifier,
        ExtraTreesRegression,
        GaussianNB,
        GradientBoostingClassifier,
        GradientBoostingR,
        HistGradientBoostingClassifier,
        HistGradientBoostingRegression,
        KNeighborsClassifier,
        RAGPipeline,
        KNeighborsRegression,
        LassoRegression,
        LinearRegression,
        LinearSVCClassifier,
        LinearSVR,
        Llama31_8BInstruct,
        Llama32_1BInstruct,
        Llama32_3BInstruct,
        LogisticRegression,
        M2M100Transformer,
        MiniLMTransformer,
        Mistral7BInstructV03,
        MistralNemoInstruct2407,
        Mixtral8x7BInstructQ2K,
        Mixtral8x7BInstructQ4KM,
        MultilingualBertTransformer,
        MLPClassifier,
        MLPRegression,
        ModernBertTransformer,
        NllbTransformer,
        OpusMtEnDeTransformer,
        OpusMtEnESTransformer,
        OpusMtEnFrTransformer,
        OpusMtEnRoaTransformer,
        OpusMtEsENTransformer,
        OpusMtFrEnTransformer,
        PixArtSigma,
        Qwen25_05BInstruct,
        Qwen25_15BInstruct,
        OpusMtRoaEnTransformer,
        RandomForestClassifier,
        RobertaTransformer,
        RandomForestRegression,
        RidgeRegression,
        SD15DepthControlNetModel,
        SD15HEDControlNetModel,
        SD15OpenPoseControlNetModel,
        SDXLCannyControlNetModel,
        SDXLTurboModel,
        SGDClassifier,
        SmolLM2_360MInstruct,
        SmolLM2_17BInstruct,
        StableDiffusion2,
        StableDiffusion2_512,
        StableDiffusion21,
        StableDiffusion21_512,
        StableDiffusion3Medium,
        StableDiffusion35Medium,
        StableDiffusion35Large,
        StableDiffusion35LargeTurbo,
        StableDiffusionXL,
        RealVisXLV4,
        StableDiffusionXLV1ControlNet,
        Phi4MiniInstructModel,
        SVC,
        SVR,
        T5SmallTransformer,
        TfIdfLogRegTextClassificationModel,
        TongyiZImage,
        TongyiZImageTurbo,
        XlmRobertaTransformer,
        XlnetTransformer,
        MLPImageClassifier,
        CNNImageClassifier,
        LeNet5ImageClassifier,
        ResNet18ImageClassifier,
        ResNet50ImageClassifier,
        EfficientNetB0ImageClassifier,
        # Dataloaders
        ARFFDataLoader,
        CSVDataLoader,
        ExcelDataLoader,
        ImageDataLoader,
        JSONDataLoader,
        # Dataset Sources
        HuggingFaceDatasetSource,
        OpenMLDatasetSource,
        ZenodoDatasetSource,
        # Credentials
        HuggingFaceCredential,
        KaggleCredential,
        # Metrics
        F1,
        Accuracy,
        BalancedAccuracy,
        Precision,
        Recall,
        Bleu,
        Ter,
        Chrf,
        MSE,
        RMSE,
        MAPE,
        SMAPE,
        MAE,
        R2,
        MedianAbsoluteError,
        ExplainedVariance,
        ROCAUC,
        LogLoss,
        HammingDistance,
        CohenKappa,
        MatthewsCorrCoef,
        # Optimizers
        OptunaOptimizer,
        HyperOptOptimizer,
        # Jobs
        ComponentDownloadJob,
        DatafileJob,
        ExplainerJob,
        ModelJob,
        ExplorerJob,
        PredictJob,
        ConverterJob,
        DatasetJob,
        GenerativeJob,
        PipelineJob,
        RAGJob,
        # Explainers
        ContrastiveShap,
        DiceCounterfactual,
        GradCam,
        KernelShap,
        LimeText,
        NearestCounterfactual,
        OcclusionSaliency,
        PartialDependence,
        PermutationFeatureImportance,
        RegressionKernelShap,
        RegressionPartialDependence,
        RegressionPermutationFeatureImportance,
        TokenAblation,
        # Explorers
        DescribeExplorer,
        ScatterPlotExplorer,
        WordcloudExplorer,
        BoxPlotExplorer,
        MultiColumnBoxPlotExplorer,
        CorrelationMatrixExplorer,
        CovarianceMatrixExplorer,
        DensityHeatmapExplorer,
        ECDFPlotExplorer,
        HistogramPlotExplorer,
        ScatterMatrixExplorer,
        TimeSeriesPlotExplorer,
        ParallelCategoriesExplorer,
        ParallelCordinatesExplorer,
        ClassOverlapExplorer,
        # Converters
        ColumnRemover,
        NanRemover,
        CharacterReplacer,
        ColumnArithmetic,
        ColumnConcat,
        NumericExpansion,
        TimeSeriesWindowConverter,
        TypeCast,
        FastICA,
        IncrementalPCA,
        PCA,
        TruncatedSVD,
        Binarizer,
        LabelEncoder,
        MaxAbsScaler,
        MinMaxScaler,
        Normalizer,
        OneHotEncoder,
        OrdinalEncoder,
        PolynomialFeatures,
        StandardScaler,
        Embedding,
        ImageEmbeddingConverter,
        SAM3SegmentConverter,
        TFIDFConverter,
        TokenizerConverter,
        BagOfWordsConverter,
        VarianceThreshold,
        SimpleImputer,
        MissingIndicator,
        KNNImputer,
        AdditiveChi2Sampler,
        RBFSampler,
        SkewedChi2Sampler,
        GenericUnivariateSelect,
        SelectPercentile,
        SelectKBest,
        SelectFpr,
        SelectFdr,
        SelectFwe,
        Nystroem,
        DataSelector,
        DataExploration,
        Train,
        RetrieveModel,
        Prediction,
        SMOTEConverter,
        SMOTEENNConverter,
        RandomUnderSamplerConverter,
        # Splitters
        HoldoutSplitter,
        TemporalHoldoutSplitter,
        RollingOriginSplitter,
        KFoldSplitter,
        StratifiedKFoldSplitter,
        StratifiedGroupKFoldSplitter,
        RepeatedStratifiedKFoldSplitter,
        GroupKFoldSplitter,
        LeaveOneOutSplitter,
        RepeatedKFoldSplitter,
        # Evaluation Strategies
        CrossValidationEvaluationStrategy,
        HoldoutEvaluationStrategy,
        ForecastingHoldoutEvaluationStrategy,
        ForecastingCrossValidationEvaluationStrategy,
        # Statistical tests
        AnovaTest,
        FriedmanTest,
        CorrectedPairedTTest,
        PairedTTest,
        WilcoxonSRTest,
        NemenyiTest,
        TukeyHSDTest,
        ShapiroTest,
        LeveneTest,
        BartlettTest,
        # Chunking Models
        CharacterChunkModel,
        RecursiveCharacterChunkModel,
        TokenChunkModel,
        # Extractors
        EasyOCRExtractor,
        PypdfExtractor,
        PyMuPDFExtractor,
        PlainTextExtractor,
        # Encodings
        SentenceTransformerEmbedding,
        BERTEmbedding,
        DistilBERTEmbedding,
        RoBERTaEmbedding,
        E5Embedding,
        InstructorEmbedding,
        LaBSEmbedding,
        # Prompts
        DefaultRAGGenerationPrompt,
        CustomRAGGenerationPrompt,
        DefaultQARAGGenerationPrompt,
        DefaultAugmentationPrompt,
        CustomAugmentationPrompt,
        # Retrievers
        BM25Retriever,
        BM25VectorizerModel,
        TFIDFRetriever,
        TFIDFVectorizerModel,
        DenseEmbeddingRetriever,
        SentenceTransformerCrossEncoderRetriever,
        MMRRerankerRetriever,
        SequentialRetriever,
        ParallelRetriever,
    ]

    # Obtener plugins instalados
    try:
        installed_plugins = get_available_plugins()
        log.info(f"Se cargaron {len(installed_plugins)} plugins instalados")
    except Exception as e:
        log.error(f"Error al cargar plugins instalados: {str(e)}")
        installed_plugins = []

    return basic_components + installed_plugins
