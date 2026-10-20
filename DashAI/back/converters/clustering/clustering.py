from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Union

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.converters.category.clustering import ClusteringConverter
from DashAI.back.core.schema_fields import (
    schema_field,
    string_field,
)
from DashAI.back.core.schema_fields.base_schema import (
    BaseSchema,
    replace_defs_in_schema,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.clustering_model import ClusteringModel
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ClusteringSchema(BaseSchema):
    """Schema for the generic clustering converter."""

    algorithm: schema_field(
        string_field(),
        "KMeansClustering",
        description=MultilingualString(
            en="Clustering algorithm to apply.",
            es="Algoritmo de clustering a aplicar.",
            pt="Algoritmo de clustering a ser aplicado.",
            de="Clustering-Algorithmus, der angewendet werden soll.",
            zh="要应用的聚类算法。",
        ),
    )  # type: ignore
    algorithm_params: schema_field(
        Dict[str, Any],
        {},
        description=MultilingualString(
            en="Parameters for the selected clustering algorithm.",
            es="Parametros del algoritmo de clustering seleccionado.",
            pt="Parâmetros para o algoritmo de clustering selecionado.",
            de="Parameter für den ausgewählten Clustering-Algorithmus.",
            zh="所选聚类算法的参数。",
        ),
    )  # type: ignore
    output_column_name: schema_field(
        string_field(),
        "cluster",
        description=MultilingualString(
            en="Name of the output column to store the cluster labels.",
            es="Nombre de la columna de salida para guardar las etiquetas de cluster.",
            pt="Nome da coluna de saída para armazenar as etiquetas de cluster.",
            de="Name der Ausgabespalte zum Speichern der Clusterbezeichnungen.",
            zh="用于存储聚类标签的输出列名称。",
        ),
    )  # type: ignore


class Clustering(ClusteringConverter, BaseConverter):
    """Apply a clustering algorithm to numeric columns and append a cluster label.

    Numeric columns in scope are passed to the selected algorithm, which assigns
    each row to a cluster without requiring a target column. The resulting label
    is stored in a new column appended to the original dataset.

    After fitting, a JSON-serializable report is available via ``get_report()``
    with per-cluster metrics, sizes, feature profiles, and algorithm-specific
    attributes (e.g. centroids for K-Means, linkage data for Agglomerative).
    """

    SCHEMA = ClusteringSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Groups dataset rows into clusters based on numeric feature similarity and "
            "adds a cluster label column. No target column is required, the algorithm "
            "finds natural groupings in the data on its own."
        ),
        es=(
            "Agrupa las filas del dataset en clusters según la similitud de sus "
            "características numéricas y agrega una columna de etiqueta. No requiere "
            "columna objetivo, el algoritmo descubre la estructura en los datos."
        ),
        pt=(
            "Agrupa linhas do dataset em clusters com base na similaridade das "
            "características numéricas e adiciona uma coluna de rótulo. Não requer "
            "coluna alvo, o algoritmo encontra estrutura nos dados."
        ),
        de=(
            "Gruppiert Datensatzzeilen nach Ähnlichkeit numerischer Merkmale in "
            "Cluster und fügt eine Cluster-Label-Spalte hinzu. Es wird keine "
            "Zielspalte benötigt, der Algorithmus findet die Struktur in den Daten."
        ),
        zh=(
            "根据数值特征的相似性将数据集的行分组为多个聚类，并添加一个聚类标签列。"
            "无需目标列，算法会自动发现数据中的自然分组。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Groups rows into clusters based on their numeric features.",
        es="Agrupa filas en clusters según sus características numéricas.",
        pt="Agrupa linhas em clusters com base em características numéricas.",
        de="Gruppiert Zeilen anhand numerischer Merkmale in Cluster.",
        zh="根据数值特征将行分组为多个聚类。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Clustering",
        es="Agrupamiento",
        pt="Agrupamento",
        de="Clustering",
        zh="聚类",
    )
    IMAGE_PREVIEW = "clustering.png"

    metadata = {
        "allowed_types": [Float, Integer],
        "allowed_dtypes": [],
    }

    @classmethod
    def get_schema(cls) -> dict:
        schema = super().get_schema()
        registry = ClusteringModel.get_registry()
        conditional_schemas = {}
        algorithm_keys = []
        algorithm_names = []
        algorithm_descriptions = []

        for algorithm_name, model_class in registry.items():
            algorithm_keys.append(algorithm_name)
            display_name = getattr(model_class, "DISPLAY_NAME", algorithm_name)
            algorithm_names.append(display_name)
            algorithm_descriptions.append(getattr(model_class, "DESCRIPTION", ""))
            model_schema = replace_defs_in_schema(
                model_class.SCHEMA.model_json_schema()
            )
            required = set(model_schema.get("required", []))
            properties = {
                name: dict(prop_schema)
                for name, prop_schema in model_schema.get("properties", {}).items()
            }

            for property_name, property_schema in properties.items():
                property_schema["required"] = property_name in required

            for property_name, schema_overrides in getattr(
                model_class, "UI_SCHEMA_OVERRIDES", {}
            ).items():
                if property_name in properties:
                    properties[property_name].update(schema_overrides)

            conditional_schemas[algorithm_name] = {"properties": properties}

        schema["properties"]["algorithm"]["enum"] = algorithm_keys
        schema["properties"]["algorithm"]["enumNames"] = algorithm_names
        schema["properties"]["algorithm"]["optionDescriptions"] = algorithm_descriptions
        default_algorithm = schema["properties"]["algorithm"].get(
            "placeholder", "KMeansClustering"
        )
        default_schema = conditional_schemas.get(default_algorithm, {})
        default_properties = default_schema.get("properties", {})
        default_algorithm_params = {
            key: value.get("placeholder") for key, value in default_properties.items()
        }

        schema["properties"]["algorithm_params"]["properties"] = default_properties
        schema["properties"]["algorithm_params"]["placeholder"] = (
            default_algorithm_params
        )
        schema["properties"]["algorithm_params"]["dependsOn"] = "algorithm"
        schema["properties"]["algorithm_params"]["conditionalSchemas"] = (
            conditional_schemas
        )
        return schema

    def __init__(self, **kwargs):
        """Initialise the clustering converter and build the selected model.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments validated by ``ClusteringSchema``.
            General parameters are consumed here, while model-specific
            parameters are forwarded to the corresponding clustering model.
        """
        self.algorithm_name = kwargs.get("algorithm", "KMeansClustering")
        self.algorithm_params = kwargs.get("algorithm_params", {})
        self.output_column_name = kwargs.get("output_column_name", "cluster")
        self._report: Dict[str, object] | None = None
        self._labels = None
        self._model = self._build_model()

    def _build_model(self) -> ClusteringModel:
        """Instantiate the selected DashAI clustering model.

        The model class is resolved from the live registry of
        ``ClusteringModel`` subclasses.  These are normal DashAI models, but
        this converter uses only the small clustering contract: ``train(x)``
        and ``get_cluster_labels(x)``.

        Returns
        -------
        ClusteringModel
            A clustering model compatible with the converter.

        Raises
        ------
        ValueError
            If the selected algorithm is not found in the registry.
        """
        registry = ClusteringModel.get_registry()
        if self.algorithm_name not in registry:
            raise ValueError(
                f"Unsupported clustering algorithm: {self.algorithm_name!r}. "
                f"Available: {list(registry)}"
            )
        return registry[self.algorithm_name](**self.algorithm_params)

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the DashAI type produced by the cluster label column.

        Parameters
        ----------
        column_name : str, optional
            Not used. Defaults to None.

        Returns
        -------
        DashAIDataType
            An Integer type backed by ``pyarrow.int64()``.
        """
        import pyarrow as pa

        return Integer(arrow_type=pa.int64())

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "Clustering":
        """Fit the selected clustering algorithm and store execution metadata.

        The clustering model is trained on the scoped dataset ``x``. Once fitted,
        the algorithm adapter must expose its execution report through
        ``get_report()``, which is wrapped using the common converter report
        structure defined in ``BaseConverter``.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset containing the scoped feature columns.
        y : DashAIDataset, optional
            Ignored. Present for API compatibility. Defaults to None.

        Returns
        -------
        Clustering
            The fitted converter instance (self).
        """
        numeric_dataset = self._select_numeric_dataset(x)
        self.output_column_name = self._make_unique_column_name(
            x.column_names, self.output_column_name
        )

        self._model.train(numeric_dataset)
        self._labels = self._model.get_cluster_labels()

        algorithm_key = self.algorithm_name.lower().removesuffix("clustering")
        self._report = self.build_report(
            {
                "algorithm": self.algorithm_name,
                "algorithm_key": algorithm_key,
                "cluster_column": self.output_column_name,
                **self._build_report_data(numeric_dataset),
            }
        )
        return self

    @staticmethod
    def _make_unique_column_name(existing_names: list, base_name: str) -> str:
        """Return ``base_name``, or a ``{base_name}_{n}`` variant if taken.

        Re-running the converter on a dataset that already carries a cluster
        label column (e.g. a previous run with the same output column name)
        would otherwise collide when ``transform`` appends the new column.

        Parameters
        ----------
        existing_names : list
            Column names already present in the dataset.
        base_name : str
            The configured output column name.

        Returns
        -------
        str
            ``base_name`` if unused, otherwise the first free
            ``{base_name}_{n}`` variant.
        """
        if base_name not in existing_names:
            return base_name

        counter = 1
        candidate = f"{base_name}_{counter}"
        while candidate in existing_names:
            counter += 1
            candidate = f"{base_name}_{counter}"
        return candidate

    def _select_numeric_dataset(self, x: "DashAIDataset") -> "DashAIDataset":
        """Select the numeric columns of ``x`` used to train the model.

        Clustering algorithms operate only on numeric features. Non-numeric
        columns are excluded here so that they are neither passed to the
        model nor included in the report, while remaining untouched in the
        dataset returned by ``transform``.

        Parameters
        ----------
        x : DashAIDataset
            Scoped dataset received by ``fit``.

        Returns
        -------
        DashAIDataset
            A dataset containing only the numeric columns of ``x``.

        Raises
        ------
        ValueError
            If ``x`` has no numeric column, or if the numeric columns
            contain NaN values.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        numeric_columns = [
            name
            for name, dtype in x.types.items()
            if isinstance(dtype, (Float, Integer))
        ]
        if not numeric_columns:
            raise ValueError(
                f"{self.__class__.__name__} requires at least one numeric "
                "column to fit."
            )

        x_pandas = x.to_pandas()
        if x_pandas[numeric_columns].isna().to_numpy().any():
            raise ValueError(
                f"{self.__class__.__name__} input contains NaN values in the "
                "numeric columns used for clustering."
            )

        numeric_table = x.arrow_table.select(numeric_columns)
        numeric_types = {name: x.types[name] for name in numeric_columns}
        return DashAIDataset(numeric_table, types=numeric_types, splits=x.splits)

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Append the cluster labels computed during ``fit`` to the dataset.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset to transform. Must have the same number of rows as
            the dataset used in ``fit``.
        y : DashAIDataset, optional
            Ignored. Present for API compatibility. Defaults to None.

        Returns
        -------
        DashAIDataset
            The original dataset with a new cluster label column appended.

        Raises
        ------
        ValueError
            If ``fit`` has not been called yet.
        """
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        if self._labels is None:
            raise ValueError(
                f"{self.__class__.__name__} must be fitted before transform."
            )

        result_table = x.arrow_table.append_column(
            self.output_column_name,
            pa.array(self._labels.tolist(), type=pa.int64()),
        )
        result_types = dict(x.types)
        result_types[self.output_column_name] = self.get_output_type()

        return DashAIDataset(result_table, types=result_types, splits=x.splits)

    def get_report(self) -> Dict[str, object] | None:
        """Return the report produced after the last ``fit``, or ``None``."""
        return self._report

    def _build_report_data(self, x: "DashAIDataset") -> Dict[str, object]:
        """Build the data included in the converter report after fitting.

        Fields present for every algorithm sit at the top level. Algorithm-specific
        attributes are obtained from the model via ``get_fit_attributes()`` and
        grouped under ``fit_attributes``.

        Parameters
        ----------
        x : DashAIDataset
            The scoped dataset used during ``fit``.

        Returns
        -------
        Dict[str, object]
            Dict merged into the top-level report by ``fit``.
        """

        import numpy as np

        x_pandas = x.to_pandas()
        labels = self._labels
        excluded_labels = [-1] if np.any(np.asarray(labels) == -1) else []
        unique_labels, counts = np.unique(labels, return_counts=True)
        cluster_sizes = {
            int(label): int(count)
            for label, count in zip(unique_labels, counts, strict=False)
            if int(label) not in excluded_labels
        }
        n_clusters = len(cluster_sizes)

        fit_attributes = self._model.get_fit_attributes()
        metrics = self._compute_metrics(x_pandas, labels)

        return {
            "n_clusters": n_clusters,
            "feature_columns": list(x_pandas.columns),
            "metrics": metrics,
            "cluster_sizes": cluster_sizes,
            "cluster_profiles": self._compute_cluster_profiles(
                x_pandas, labels, excluded_labels
            ),
            "fit_attributes": fit_attributes,
        }

    @staticmethod
    def _compute_metrics(
        x: "pd.DataFrame",
        labels: "np.ndarray",
    ) -> Dict[str, Any]:
        """Compute all registered clustering metrics.

        Discovers concrete ``ClusteringMetric`` subclasses at runtime, so new
        metrics are picked up automatically without changes here. Keys match
        the class name (consistent with the metrics ``ModelJob`` persists). Each score
        is ``None`` when undefined — handled by ``prepare_to_metric`` inside
        each metric class.

        Parameters
        ----------
        x : pd.DataFrame
            Numeric feature matrix used during fitting.
        labels : np.ndarray
            Cluster label assigned to each row (noise points are ``-1``).

        Returns
        -------
        Dict[str, Any]
            Metric class name → score. Any score is ``None`` when undefined.
        """
        from DashAI.back.metrics.clustering_metric import ClusteringMetric

        return {
            name: cls.score(x, labels)
            for name, cls in ClusteringMetric.get_registry().items()
        }

    @staticmethod
    def _compute_cluster_profiles(
        x: "pd.DataFrame",
        labels: "np.ndarray",
        excluded_labels: list,
    ) -> list:
        """Build per-cluster feature summaries for notebook exploration.

        For each cluster produces: label, size, per-feature descriptive statistics
        (mean, std, min, max), and the top features that deviate most from the global
        mean expressed as a z-score, which helps identify what makes each cluster
        distinctive.

        Parameters
        ----------
        x : pd.DataFrame
            Numeric feature matrix used during fitting.
        labels : np.ndarray
            Cluster label assigned to each row.
        excluded_labels : list
            Labels to skip (noise points).

        Returns
        -------
        list
            List of dicts, one per cluster, each with keys ``cluster``, ``size``,
            ``feature_stats``, and ``distinctive_features``.
        """
        import numpy as np
        import pandas as pd

        label_arr = np.asarray(labels)
        global_mean = x.mean()
        global_std = x.std().replace(0, 1)
        profiles = []

        for cluster_label in sorted(np.unique(label_arr)):
            if int(cluster_label) in excluded_labels:
                continue

            mask = label_arr == cluster_label
            cluster_x = x[mask]

            feature_stats: Dict[str, Any] = {}
            for col in x.columns:
                col_data = cluster_x[col].dropna()
                feature_stats[col] = {
                    "mean": float(col_data.mean()) if len(col_data) > 0 else None,
                    "std": float(col_data.std()) if len(col_data) > 1 else None,
                    "min": float(col_data.min()) if len(col_data) > 0 else None,
                    "max": float(col_data.max()) if len(col_data) > 0 else None,
                }

            cluster_mean = pd.Series(
                {col: feature_stats[col]["mean"] for col in x.columns}
            )
            z_scores = ((cluster_mean - global_mean) / global_std).abs()
            top_features = z_scores.nlargest(min(3, len(x.columns)))

            distinctive_features = [
                {
                    "feature": col,
                    "cluster_mean": feature_stats[col]["mean"],
                    "global_mean": float(global_mean[col]),
                    "z_score": float(z_scores[col]),
                }
                for col in top_features.index
                if feature_stats[col]["mean"] is not None
            ]

            profiles.append(
                {
                    "cluster": int(cluster_label),
                    "size": int(mask.sum()),
                    "feature_stats": feature_stats,
                    "distinctive_features": distinctive_features,
                }
            )

        return profiles
