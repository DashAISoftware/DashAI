from sklearn.inspection import partial_dependence

from DashAI.back.explainability.global_explainer import GlobalExplainer


# Compatible con Tabular Classification Task
def PartialDependence(GlobalExplainer):
    def __init__(self, predictor, feature_names, categorical_features):
        self.predictor = predictor
        self.feature_names = feature_names
        self.categorical_features = categorical_features

    def explain(self, X, features, percentiles, grid_resolution):
        """_summary_

        Args:
            X (_type_): _description_
            features (_type_): _description_
            percentiles : tuple of float, default=(0.05, 0.95)
                The lower and upper percentile used to create the extreme values
                for the grid. Must be in [0, 1].

            grid_resolution : int, default=100
                The number of equally spaced points on the grid, for each target
                feature.
        """
