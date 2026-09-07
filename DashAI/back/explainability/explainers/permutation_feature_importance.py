import re
from typing import Dict, List, Optional, Union

from DashAI.back.core.artifacts import (
    Artifact,
    ArtifactGroup,
    GroupedArtifacts,
    PlotlyArtifact,
)
from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.explainability.global_explainer import BaseGlobalExplainer
from DashAI.back.explainability.story import concat_stories, format_story
from DashAI.back.models.base_model import BaseModel


class PermutationFeatureImportanceSchema(BaseSchema):
    """Schema for PermutationFeatureImportance explainer hyperparameters.

    Configures the scoring metric (``"accuracy"`` or ``"balanced_accuracy"``),
    the number of permutation repeats per feature (``n_repeats``), the random
    seed (``random_state``), and the fraction of test samples to use per repeat
    (``max_samples_fraction``). More repeats reduce variance in importance
    estimates at the cost of additional model evaluations.
    """

    scoring: schema_field(
        enum_field(enum=["accuracy", "balanced_accuracy"]),
        placeholder="accuracy",
        description=MultilingualString(
            en=(
                "Metric used to evaluate how the model's performance changes when "
                "a particular feature is shuffled."
            ),
            es=(
                "Métrica utilizada para evaluar cómo cambia el rendimiento del "
                "modelo cuando se baraja una característica particular."
            ),
            pt=(
                "Métrica usada para avaliar como o desempenho do modelo muda "
                "quando uma característica particular é embaralhada."
            ),
            de=(
                "Metrik zur Bewertung, wie sich die Modellleistung ändert, wenn "
                "ein bestimmtes Merkmal permutiert wird."
            ),
            zh="用于评估特定特征被打乱时模型性能变化的指标。",
        ),
        alias=MultilingualString(
            en="Scoring metric",
            es="Métrica de evaluación",
            pt="Métrica de avaliação",
            de="Bewertungsmetrik",
            zh="评分指标",
        ),
    )  # type: ignore

    n_repeats: schema_field(
        int_field(ge=1),
        placeholder=20,
        description=MultilingualString(
            en=("Number of times to permute a feature."),
            es=("Número de veces que se permuta una característica."),
            pt=("Número de vezes que uma característica é permutada."),
            de=("Anzahl der Permutationen eines Merkmals."),
            zh="对特征进行排列的次数。",
        ),
        alias=MultilingualString(
            en="Number of repeats",
            es="Número de repeticiones",
            pt="Número de repetições",
            de="Anzahl der Wiederholungen",
            zh="重复次数",
        ),
    )  # type: ignore

    random_state: schema_field(
        int_field(),
        placeholder=0,
        description=MultilingualString(
            en=(
                "Seed for the random number generator to control permutations of "
                "each feature."
            ),
            es=(
                "Semilla del generador aleatorio para controlar las permutaciones "
                "de cada característica."
            ),
            pt=(
                "Semente do gerador de números aleatórios para controlar as "
                "permutações de cada característica."
            ),
            de=(
                "Startwert für den Zufallszahlengenerator zur Steuerung der "
                "Permutationen jedes Merkmals."
            ),
            zh="用于控制每个特征排列的随机数生成器种子。",
        ),
        alias=MultilingualString(
            en="Random state",
            es="Semilla aleatoria",
            pt="Estado aleatório",
            de="Zufallszustand",
            zh="随机状态",
        ),
    )  # type: ignore

    max_samples_fraction: schema_field(
        float_field(ge=0.0, le=1.0),
        placeholder=1.0,
        description=MultilingualString(
            en=(
                "Fraction of samples to draw from the test set to calculate "
                "feature importance at each repetition."
            ),
            es=(
                "Fracción de muestras a extraer del conjunto de prueba para "
                "calcular la importancia en cada repetición."
            ),
            pt=(
                "Fração de amostras a extrair do conjunto de teste para "
                "calcular a importância das características a cada repetição."
            ),
            de=(
                "Anteil der aus dem Testdatensatz gezogenen Stichproben zur "
                "Berechnung der Merkmalswichtigkeit bei jeder Wiederholung."
            ),
            zh="每次重复时从测试集中抽取的样本比例，用于计算特征重要性。",
        ),
        alias=MultilingualString(
            en="Max samples fraction",
            es="Fracción máxima de muestras",
            pt="Fração máxima de amostras",
            de="Maximaler Stichprobenanteil",
            zh="最大样本比例",
        ),
    )  # type: ignore


class PermutationFeatureImportance(BaseGlobalExplainer):
    """Global explainer that ranks features by the drop
    in model performance when permuted.

    Permutation Feature Importance (PFI) measures the importance of a feature by
    randomly shuffling its values across the test set and recording the resulting
    decrease in a scoring metric. A large decrease indicates that the model relies
    heavily on that feature; a small (or zero) decrease indicates the feature
    contributes little. The process is repeated ``n_repeats`` times to produce a
    mean importance and standard deviation, which quantify both rank order and
    uncertainty.

    Unlike impurity-based importance (from decision trees), PFI is computed on
    held out data and is therefore not biased towards high cardinality features.
    It is model agnostic and captures interaction effects, but assumes that
    permuting a feature does not violate important correlations in the data.

    References
    ----------
    - [1] Breiman, L. (2001). "Random Forests." Machine Learning, 45(1), 5-32.
    - [2] Fisher, A. et al. (2019). "All Models are Wrong, but Many are Useful."
           JMLR, 20(177), 1-81. https://arxiv.org/abs/1801.01489
    - [3] https://scikit-learn.org/stable/modules/permutation_importance.html
    """

    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]
    DISPLAY_NAME = MultilingualString(
        en="Permutation Feature Importance",
        es="Importancia por Permutación",
        pt="Importância por Permutação",
        de="Permutations-Merkmalswichtigkeit",
        zh="排列特征重要性",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Assesses feature importance by measuring the drop in model "
            "performance when a feature's values are randomly shuffled."
        ),
        es=(
            "Evalúa la importancia de las características midiendo la caída en el "
            "rendimiento del modelo cuando los valores de una característica se "
            "barajan aleatoriamente."
        ),
        pt=(
            "Avalia a importância das características medindo a queda no "
            "desempenho do modelo quando os valores de uma característica são "
            "embaralhados aleatoriamente."
        ),
        de=(
            "Bewertet die Merkmalswichtigkeit durch Messung des Leistungsabfalls "
            "des Modells, wenn die Werte eines Merkmals zufällig permutiert werden."
        ),
        zh="通过测量特征值被随机打乱时模型性能的下降来评估特征重要性。",
    )
    COLOR = "#800080"
    SCHEMA = PermutationFeatureImportanceSchema

    def __init__(
        self,
        model: BaseModel,
        scoring: Union[str, List[str], None] = None,
        n_repeats: int = 5,
        random_state: Union[int, None] = None,
        max_samples_fraction: float = 0.5,
    ):
        """Initialise the Permutation Feature Importance explainer.

        Parameters
        ----------
        model : BaseModel
            The trained DashAI model to be explained.
        scoring : str or List[str] or None, optional
            Name of the metric used to evaluate performance changes.  Must be
            one of ``"accuracy"`` or ``"balanced_accuracy"``.
        n_repeats : int, optional
            Number of times each feature is permuted.  Higher values give more
            stable estimates but increase computation time.  Default is ``5``.
        random_state : int or None, optional
            Seed for the random number generator controlling permutations.
            Pass an integer for reproducible results.  Default is ``None``.
        max_samples_fraction : float, optional
            Fraction of the test set to sample at each repetition, in the
            range ``[0.0, 1.0]``.  Default is ``0.5``.
        """
        super().__init__(model)

        # Lazy import metrics only during initialization
        from sklearn.metrics import accuracy_score, balanced_accuracy_score

        metrics = {
            "accuracy": accuracy_score,
            "balanced_accuracy": balanced_accuracy_score,
        }

        self.scoring = metrics[scoring]
        self.n_repeats = n_repeats
        self.random_state = random_state
        self.max_samples_fraction = max_samples_fraction

    def _get_feature_groups(self, columns: List[str]) -> Dict[str, List[int]]:
        """Map logical feature names to their column indices, grouping OHE columns.

        When the underlying model has a ``one_hot_encoder`` attribute, all
        one hot encoded dummy columns that originated from the same categorical
        feature are collected into a single group so that permutation importance
        is computed jointly. Non-encoded columns get a single-element group.

        Parameters
        ----------
        columns : list of str
            Ordered list of column names in the input feature matrix.

        Returns
        -------
        dict of {str: list of int}
            Mapping from logical feature name to the list of column indices
            that belong to that feature.
        """
        feature_groups = {}

        if (
            hasattr(self.model, "one_hot_encoder")
            and self.model.one_hot_encoder is not None
            and hasattr(self.model, "categorical_columns")
            and self.model.categorical_columns
        ):
            encoder = self.model.one_hot_encoder
            original_cat_cols = self.model.categorical_columns

            encoded_feature_names = list(
                encoder.get_feature_names_out(original_cat_cols)
            )

            for orig_col in original_cat_cols:
                prefix = f"{orig_col}_"
                indices = [
                    columns.index(enc_col)
                    for enc_col in encoded_feature_names
                    if enc_col.startswith(prefix) and enc_col in columns
                ]
                if indices:
                    feature_groups[orig_col] = indices

            # Add non-categorical columns
            for idx, col in enumerate(columns):
                if col not in encoded_feature_names:
                    feature_groups[col] = [idx]
        else:
            for idx, col in enumerate(columns):
                feature_groups[col] = [idx]

        return feature_groups

    def _calculate_grouped_importance(
        self,
        x_data,
        y,
        feature_groups: Dict[str, List[int]],
        max_samples: int,
    ):
        """Compute permutation importance for grouped (possibly OHE) features.

        Randomly subsamples up to ``max_samples`` rows, then for each feature
        group permutes all columns in the group simultaneously across
        ``self.n_repeats`` trials, measuring the drop in the configured
        scoring metric to estimate importance.

        Parameters
        ----------
        x_data : pandas.DataFrame
            Full feature matrix.
        y : pandas.DataFrame
            Target column aligned with ``x_data``.
        feature_groups : dict of {str: list of int}
            Mapping from logical feature name to column indices, as returned
            by :meth:`_get_feature_groups`.
        max_samples : int
            Maximum number of rows to use for the importance calculation.

        Returns
        -------
        dict
            Dictionary with keys ``"features"``, ``"importances_mean"``, and
            ``"importances_std"``, each a list of length ``len(feature_groups)``.
        """
        # Lazy imports
        import numpy as np

        rng = np.random.RandomState(self.random_state)

        n_samples = min(max_samples, len(x_data))
        sample_indices = rng.choice(len(x_data), size=n_samples, replace=False)
        x_sample = x_data.iloc[sample_indices].copy().reset_index(drop=True)
        y_sample = y.iloc[sample_indices].copy().reset_index(drop=True)

        y_array = y_sample.to_numpy().ravel()
        column_names = list(x_sample.columns)

        def get_predictions(data):
            """Obtain predicted class probabilities for the given data.

            Parameters
            ----------
            data : pandas.DataFrame
                Input features as a DataFrame with the original column names,
                already in the model feature space.

            Returns
            -------
            numpy.ndarray
                Array of shape ``(n_samples, n_classes)`` with predicted
                probabilities for each class.
            """
            # Keep as DataFrame to preserve column names
            return self.model.predict_proba_prepared(data)

        def calc_score(y_true, y_pred_probas):
            """Compute the scoring metric from probability predictions.

            Converts probability predictions to hard class labels via
            ``argmax`` before passing them to the configured scoring function.

            Parameters
            ----------
            y_true : array-like of shape (n_samples,)
                True class labels.
            y_pred_probas : numpy.ndarray of shape (n_samples, n_classes)
                Predicted class probabilities.

            Returns
            -------
            float
                Scalar score produced by the configured scoring function.
            """
            y_pred = np.argmax(y_pred_probas, axis=1)
            return self.scoring(y_true, y_pred)

        baseline_predictions = get_predictions(x_sample)
        baseline_score = calc_score(y_array, baseline_predictions)

        results = {"features": [], "importances_mean": [], "importances_std": []}

        for feature_name, col_indices in feature_groups.items():
            importances = []

            # Get column names for this group
            group_cols = [column_names[i] for i in col_indices]

            for _ in range(self.n_repeats):
                # Work with DataFrame to preserve column names
                x_permuted = x_sample.copy()

                # Permute rows for this group of columns
                permutation = rng.permutation(n_samples)

                # Get the block of columns, permute rows, put back
                original_block = x_sample[group_cols].to_numpy()
                permuted_block = original_block[permutation, :]
                x_permuted[group_cols] = permuted_block

                permuted_predictions = get_predictions(x_permuted)
                permuted_score = calc_score(y_array, permuted_predictions)

                importance = baseline_score - permuted_score
                importances.append(importance)

            results["features"].append(feature_name)
            results["importances_mean"].append(np.mean(importances))
            results["importances_std"].append(np.std(importances))

        return results

    def explain(self, dataset):
        """Compute permutation feature importance for the fitted model.

        Extracts the test split from ``dataset``, optionally encodes the
        target column, groups one hot encoded columns, and computes importance
        scores by permuting each feature group and measuring the resulting
        drop in the configured scoring metric.

        Parameters
        ----------
        dataset : tuple of (DatasetDict, DatasetDict)
            A ``(x, y)`` pair where each element is a DatasetDict with at
            least a ``"test"`` split.

        Returns
        -------
        dict
            Dictionary with keys ``"features"`` (list of str),
            ``"importances_mean"`` (list of float, rounded to 3 dp), and
            ``"importances_std"`` (list of float, rounded to 3 dp).
        """
        # Lazy imports
        import numpy as np
        import pandas as pd
        from sklearn.inspection import permutation_importance
        from sklearn.metrics import make_scorer
        from sklearn.preprocessing import LabelEncoder

        from DashAI.back.explainability.model_input import (
            as_sklearn_estimator,
            prepare_model_input,
        )

        x, y = dataset

        # permutation_importance permutes the frame and calls the estimator
        # with it, bypassing the model preparation.
        x_test = prepare_model_input(self.model, x["test"])
        y_test = y["test"]

        X_df = x_test.to_pandas()
        y_df = y_test.to_pandas()

        y_values = y_df.to_numpy().ravel()
        if y_values.dtype == object or y_values.dtype.kind in ("U", "S"):
            if (
                hasattr(self.model, "label_encoder")
                and self.model.label_encoder is not None
            ):
                y_encoded = self.model.label_encoder.transform(y_values)
            else:
                le = LabelEncoder()
                y_encoded = le.fit_transform(y_values)
            y_df = pd.DataFrame(y_encoded, columns=y_df.columns)

        input_columns = list(X_df.columns)

        feature_groups = self._get_feature_groups(input_columns)

        max_samples = max(int(len(x_test) * self.max_samples_fraction), 1)

        has_grouped_features = any(
            len(indices) > 1 for indices in feature_groups.values()
        )

        if has_grouped_features:
            results = self._calculate_grouped_importance(
                X_df, y_df, feature_groups, max_samples
            )
            return {
                "features": results["features"],
                "importances_mean": np.round(results["importances_mean"], 3).tolist(),
                "importances_std": np.round(results["importances_std"], 3).tolist(),
            }
        else:

            def patched_metric(y_true, y_pred_probas):
                """Wrap the scoring function to accept probability predictions.

                Converts probability predictions to hard class labels via
                ``argmax`` so that the configured scoring function (which
                expects class labels) can be used with scikit-learn's
                ``make_scorer`` / ``permutation_importance`` interface.

                Parameters
                ----------
                y_true : array-like of shape (n_samples,)
                    True class labels.
                y_pred_probas : numpy.ndarray of shape (n_samples, n_classes)
                    Predicted class probabilities output by the model.

                Returns
                -------
                float
                    Scalar score produced by the configured scoring function.
                """
                return self.scoring(y_true, np.argmax(y_pred_probas, axis=1))

            pfi = permutation_importance(
                estimator=as_sklearn_estimator(
                    self.model, classes=np.unique(y_df.to_numpy().ravel())
                ),
                X=X_df,
                y=y_df,
                scoring=make_scorer(patched_metric),
                n_repeats=self.n_repeats,
                random_state=self.random_state,
                max_samples=max_samples,
            )

            return {
                "features": input_columns,
                "importances_mean": np.round(pfi["importances_mean"], 3).tolist(),
                "importances_std": np.round(pfi["importances_std"], 3).tolist(),
            }

    def _create_plot(self, data) -> List[GroupedArtifacts]:
        """Build one selector over feature counts.

        Each count (from all features down to one) is a selectable group
        holding the horizontal bar chart of the top ``count`` most important
        features, so the frontend lists the counts in a selector instead of a
        dropdown embedded in a single figure.

        Parameters
        ----------
        data : pandas.DataFrame
            DataFrame with columns ``"features"``, ``"importances_mean"``, and
            ``"importances_std"``, sorted ascending by importance.

        Returns
        -------
        List[GroupedArtifacts]
            A single grouped artifact with one group (a bar chart) per feature
            count, most features first.
        """
        # Lazy imports
        import plotly.express as px

        groups = []
        for count in range(len(data), 0, -1):
            subset = data.iloc[-count:]
            fig = px.bar(
                subset,
                x=subset["importances_mean"],
                y=subset["features"],
                error_x=subset["importances_std"],
            )
            fig.update_layout(xaxis_title="Importance", yaxis_title=None)
            groups.append(
                ArtifactGroup(
                    title=f"Top {count} features",
                    artifacts=[PlotlyArtifact(payload=fig)],
                )
            )

        return [GroupedArtifacts(groups=groups)]

    def plot(self, explanation: dict) -> List[GroupedArtifacts]:
        """Create a Plotly bar chart from a feature importance explanation dict.

        Parameters
        ----------
        explanation : dict
            Output of :meth:`explain`: must contain ``"features"``,
            ``"importances_mean"``, and ``"importances_std"`` lists.

        Returns
        -------
        List[GroupedArtifacts]
            A single selector over the feature counts (built by
            :meth:`_create_plot`).
        """
        # Lazy import
        import pandas as pd

        data = pd.DataFrame.from_dict(explanation)
        data = data.sort_values(by=["importances_mean"], ascending=True)

        return self._create_plot(data)

    def story(
        self, explanation: dict, explainer_output: Union[Artifact, ArtifactGroup]
    ) -> Optional[MultilingualString]:
        """Describe, in words, the top features shown in one "Top N" group.

        Ranks the features by their mean importance (the same values plotted
        by :meth:`plot`) and names the ones shown in this group, calling out
        when the least important one among them showed no measurable effect
        (mean importance at or below zero).

        Parameters
        ----------
        explanation : dict
            Output of :meth:`explain`.
        explainer_output : Union[Artifact, ArtifactGroup]
            One of the groups previously returned by :meth:`plot`, titled
            ``"Top {count} features"``.

        Returns
        -------
        Optional[MultilingualString]
            The narrative in every supported language, or ``None`` if
            ``explainer_output`` is not a recognised "Top N features" group.
        """
        if not isinstance(explainer_output, ArtifactGroup):
            return None

        match = re.match(r"Top (\d+) features", explainer_output.title or "")
        if match is None:
            return None
        count = int(match.group(1))

        features = explanation["features"]
        means = explanation["importances_mean"]

        ranking = sorted(
            zip(features, means, strict=True), key=lambda pair: pair[1], reverse=True
        )
        top = ranking[:count]
        if not top:
            return None

        scoring_name = self.scoring.__name__.replace("_score", "").replace("_", " ")
        positive = [(name, mean) for name, mean in top if mean > 0]
        non_positive = [(name, mean) for name, mean in top if mean <= 0]

        # All shown features actually decreased the score when shuffled:
        # "relies most on" the whole ranked list is accurate as-is.
        if not non_positive:
            feature_list = ", ".join(f"{name} ({mean:.3f})" for name, mean in top)
            return format_story(
                {
                    "en": (
                        "Ranked by the drop in {scoring} caused by shuffling "
                        "each feature, the model relies most on: "
                        "{feature_list}."
                    ),
                    "es": (
                        "Ordenadas según la caída en {scoring} al barajar "
                        "cada característica, el modelo depende "
                        "principalmente de: {feature_list}."
                    ),
                    "pt": (
                        "Classificadas pela queda em {scoring} causada ao "
                        "embaralhar cada característica, o modelo depende "
                        "principalmente de: {feature_list}."
                    ),
                    "de": (
                        "Geordnet nach dem Rückgang von {scoring} durch das "
                        "Permutieren jedes Merkmals, verlässt sich das "
                        "Modell hauptsächlich auf: {feature_list}."
                    ),
                    "zh": (
                        "根据打乱各特征后{scoring}的下降程度排序，"
                        "模型主要依赖：{feature_list}。"
                    ),
                },
                scoring=scoring_name,
                feature_list=feature_list,
            )

        # None of the shown features had any measurable effect: saying the
        # model "relies on" them would be backwards.
        if not positive:
            feature_list = ", ".join(f"{name} ({mean:.3f})" for name, mean in top)
            return format_story(
                {
                    "en": (
                        "None of the top {count} features ({feature_list}) "
                        "showed measurable importance when shuffled — that "
                        "did not decrease {scoring}, or even improved it."
                    ),
                    "es": (
                        "Ninguna de las {count} características principales "
                        "({feature_list}) mostró una importancia medible al "
                        "barajarlas — no redujo {scoring}, o incluso lo "
                        "mejoró."
                    ),
                    "pt": (
                        "Nenhuma das {count} características principais "
                        "({feature_list}) mostrou importância mensurável ao "
                        "serem embaralhadas — não reduziu {scoring}, ou até "
                        "o melhorou."
                    ),
                    "de": (
                        "Keines der {count} wichtigsten Merkmale "
                        "({feature_list}) zeigte beim Permutieren eine "
                        "messbare Wichtigkeit — {scoring} sank dadurch "
                        "nicht oder verbesserte sich sogar."
                    ),
                    "zh": (
                        "打乱后，排名前{count}的特征（{feature_list}）均未"
                        "表现出可测量的重要性——并未降低{scoring}，甚至有所"
                        "提升。"
                    ),
                },
                count=count,
                scoring=scoring_name,
                feature_list=feature_list,
            )

        # Mixed: only some of the shown features had a measurable effect —
        # claim reliance on those, and separately note the rest showed none.
        positive_list = ", ".join(f"{name} ({mean:.3f})" for name, mean in positive)
        non_positive_list = ", ".join(name for name, _ in non_positive)
        story = format_story(
            {
                "en": (
                    "Ranked by the drop in {scoring} caused by shuffling "
                    "each feature, the model relies on: {positive_list}."
                ),
                "es": (
                    "Ordenadas según la caída en {scoring} al barajar cada "
                    "característica, el modelo depende de: {positive_list}."
                ),
                "pt": (
                    "Classificadas pela queda em {scoring} causada ao "
                    "embaralhar cada característica, o modelo depende de: "
                    "{positive_list}."
                ),
                "de": (
                    "Geordnet nach dem Rückgang von {scoring} durch das "
                    "Permutieren jedes Merkmals, verlässt sich das Modell "
                    "auf: {positive_list}."
                ),
                "zh": (
                    "根据打乱各特征后{scoring}的下降程度排序，"
                    "模型依赖：{positive_list}。"
                ),
            },
            scoring=scoring_name,
            positive_list=positive_list,
        )
        return concat_stories(
            story,
            format_story(
                {
                    "en": (
                        " The remaining features ({non_positive_list}) "
                        "showed no measurable importance when shuffled "
                        "(that did not decrease {scoring}, or even "
                        "improved it)."
                    ),
                    "es": (
                        " Las características restantes "
                        "({non_positive_list}) no mostraron una "
                        "importancia medible al barajarlas (no redujo "
                        "{scoring}, o incluso lo mejoró)."
                    ),
                    "pt": (
                        " As características restantes "
                        "({non_positive_list}) não mostraram importância "
                        "mensurável ao serem embaralhadas (não reduziu "
                        "{scoring}, ou até o melhorou)."
                    ),
                    "de": (
                        " Die übrigen Merkmale ({non_positive_list}) "
                        "zeigten beim Permutieren keine messbare "
                        "Wichtigkeit ({scoring} sank dadurch nicht oder "
                        "verbesserte sich sogar)."
                    ),
                    "zh": (
                        "其余特征（{non_positive_list}）在打乱后没有表现出"
                        "可测量的重要性（并未降低{scoring}，甚至有所"
                        "提升）。"
                    ),
                },
                non_positive_list=non_positive_list,
                scoring=scoring_name,
            ),
        )
