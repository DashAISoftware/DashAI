from sklearn.inspection import partial_dependence

from DashAI.back.explainability.global_explainer import GlobalExplainer


# Compatible con Tabular Classification Task
def PartialDependence(GlobalExplainer):
    def __init__(self, predictor, feature_names, categorical_features):
        """_summary_

        Args:
            predictor (_type_): prediciton function o BaseEstimator
            feature_names (_type_): Nombre de los features
            categorical_names (_type_): Nombre de los features categóricos
        """
        self.predictor = predictor
        self.feature_names = feature_names
        self.categorical_features = categorical_features

    def explain(self, X, features, percentiles, grid_resolution):
        """_summary_

        Args:
            X (_type_): features_values
            features (_type_): features para calcular el PDP
            percentiles : tuple of float, default=(0.05, 0.95)
                The lower and upper percentile used to create the extreme values
                for the grid. Must be in [0, 1].

            grid_resolution : int, default=100
                The number of equally spaced points on the grid, for each target
                feature.
        """
