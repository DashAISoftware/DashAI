import json
from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.clustering_explorer import ClusteringExplorer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


_METRIC_LABELS = {
    "Silhouette": "Silhouette Score",
    "DaviesBouldin": "Davies-Bouldin Index",
    "CalinskiHarabasz": "Calinski-Harabasz Index",
}

_METRIC_BETTER = {
    "Silhouette": "higher is better (range −1 to 1)",
    "DaviesBouldin": "lower is better (≥ 0)",
    "CalinskiHarabasz": "higher is better (≥ 0)",
}


class ClusteringProfileSchema(BaseExplorerSchema):
    """Schema for ClusteringProfileExplorer — no parameters needed."""


class ClusteringProfileExplorer(ClusteringExplorer):
    """Structured summary of the last clustering run.

    Shows cluster sizes, internal evaluation metrics (Silhouette,
    Davies-Bouldin, Calinski-Harabasz), and the distinctive feature
    profile of each cluster. All data comes from the converter report —
    no column selection required.
    """

    DISPLAY_NAME = MultilingualString(
        en="Clustering Profile",
        es="Perfil de Agrupamiento",
        pt="Perfil de Agrupamento",
        de="Clustering-Profil",
        zh="聚类概况",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Structured summary of the last clustering run: algorithm used, "
            "internal evaluation metrics, cluster sizes, and per-cluster feature "
            "profiles with the most distinctive features ranked by distance from "
            "the global mean."
        ),
        es=(
            "Resumen estructurado de la última ejecución de clustering: algoritmo "
            "utilizado, métricas de evaluación interna, tamaños de clúster y perfiles "
            "de características por clúster con las más distintivas ordenadas por "
            "distancia a la media global."
        ),
        pt=(
            "Resumo estruturado da última execução de agrupamento: algoritmo "
            "utilizado, métricas de avaliação interna, tamanhos de cluster e perfis "
            "de características por cluster com as mais distintivas ordenadas por "
            "distância à média global."
        ),
        de=(
            "Strukturierte Zusammenfassung des letzten Clustering-Durchlaufs: "
            "verwendeter Algorithmus, interne Bewertungsmetriken, Clustergrößen und "
            "Merkmalsprofile pro Cluster mit den markantesten Merkmalen, geordnet "
            "nach Abstand vom globalen Mittelwert."
        ),
        zh=(
            "上一次聚类运行的结构化摘要：使用的算法、内部评估指标、聚类大小，以及"
            "按与全局均值距离排序的每个聚类的特征概况。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Metrics, cluster sizes, and distinctive feature profiles.",
        es="Métricas, tamaños de clúster y perfiles de características distintivas.",
        pt="Métricas, tamanhos de cluster e perfis de características distintivas.",
        de="Metriken, Clustergrößen und markante Merkmalsprofile.",
        zh="指标、聚类大小和代表性特征概况。",
    )
    IMAGE_PREVIEW = "clustering_profile.png"

    SCHEMA = ClusteringProfileSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [],
        "allowed_dtypes": [],
        "input_cardinality": {"exact": 0},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize ClusteringProfileExplorer.

        Parameters
        ----------
        **kwargs
            No schema parameters are defined for this explorer.
        """
        super().__init__(**kwargs)

    def prepare_dataset(
        self, loaded_dataset: "DashAIDataset", _columns: List[Dict[str, Any]]
    ) -> "DashAIDataset":
        """Return the dataset unchanged.

        This explorer reads entirely from the converter report so the dataset
        is not used. The method is overridden to avoid the default
        ``select_columns([])`` call that would occur when no columns are selected.

        Parameters
        ----------
        loaded_dataset : DashAIDataset
            The full dataset loaded from storage.
        _columns : List[Dict[str, Any]]
            Ignored — no columns are selected for this explorer.

        Returns
        -------
        DashAIDataset
            The dataset as received, unmodified.
        """
        return loaded_dataset

    def launch_exploration(
        self, _dataset: "DashAIDataset", _explorer_info: Explorer
    ) -> Dict[str, Any]:
        """Build a structured profile from the clustering converter report.

        Reads metrics, cluster sizes, and per-cluster feature profiles from
        ``self.context["converter_report"]``. Standard metrics are annotated
        with human-readable labels and interpretation hints. Inertia (KMeans
        only) is extracted from ``fit_attributes`` into a separate section.
        Each cluster's distinctive features are enriched with a direction
        label (``"above average"`` / ``"below average"``) based on whether
        the cluster mean is above or below the global mean.

        Parameters
        ----------
        _dataset : DashAIDataset
            Ignored — all data comes from the converter report.
        _explorer_info : Explorer
            Ignored — no per-instance configuration is needed.

        Returns
        -------
        Dict[str, Any]
            Dictionary with keys: ``algorithm``, ``cluster_column``,
            ``n_clusters``, ``metrics``, ``algorithm_extras``,
            ``noise_info``, ``cluster_sizes``, ``cluster_profiles``.
        """
        cr = self.context.get("converter_report", {})
        fit_attributes = cr.get("fit_attributes", {})

        metrics: Dict[str, Any] = {}
        for key, value in cr.get("metrics", {}).items():
            entry: Dict[str, Any] = {"value": value}
            if key in _METRIC_LABELS:
                entry["label"] = _METRIC_LABELS[key]
                entry["interpretation"] = _METRIC_BETTER[key]
            metrics[key] = entry

        # Algorithm-specific extras from fit_attributes (inertia: KMeans only)
        algorithm_extras: Dict[str, Any] = {}
        if "inertia" in fit_attributes:
            algorithm_extras["inertia"] = fit_attributes["inertia"]

        # Noise points count (DBSCAN / HDBSCAN only)
        noise_info: Dict[str, Any] = {}
        if "n_noise_points" in fit_attributes:
            noise_info["n_noise_points"] = fit_attributes["n_noise_points"]

        # Enrich distinctive features with a direction label
        raw_profiles = cr.get("cluster_profiles", [])
        enriched_profiles = []
        for profile in raw_profiles:
            enriched_features = []
            for feat in profile.get("distinctive_features", []):
                enriched_feat = dict(feat)
                enriched_feat["direction"] = (
                    "above average"
                    if feat.get("cluster_mean", 0) > feat.get("global_mean", 0)
                    else "below average"
                )
                enriched_features.append(enriched_feat)
            enriched_profiles.append(
                {
                    "cluster": profile["cluster"],
                    "size": profile.get("size", 0),
                    "feature_stats": profile.get("feature_stats", {}),
                    "distinctive_features": enriched_features,
                }
            )

        return {
            "algorithm": cr.get("algorithm", "unknown"),
            "cluster_column": cr.get("cluster_column", "cluster"),
            "n_clusters": cr.get("n_clusters"),
            "metrics": metrics,
            "algorithm_extras": algorithm_extras,
            "noise_info": noise_info,
            "cluster_sizes": cr.get("cluster_sizes", {}),
            "cluster_profiles": enriched_profiles,
        }

    def save_notebook(
        self,
        __notebook_info__: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Save the profile result to a JSON file on disk.

        Parameters
        ----------
        __notebook_info__ : Notebook
            The notebook database record (unused).
        explorer_info : Explorer
            The explorer record used for filename generation.
        save_path : Path
            Directory where the file will be saved.
        result : Any
            The dict returned by ``launch_exploration``.

        Returns
        -------
        str
            The path of the saved JSON file as a POSIX string.
        """
        import os
        from pathlib import Path as _Path

        filename = f"{explorer_info.id}.json"
        path = _Path(os.path.join(save_path, filename))

        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, default=str)
        return path.as_posix()

    def get_results(
        self, exploration_path: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Load the saved profile and return it to the frontend.

        Parameters
        ----------
        exploration_path : str
            Path to the JSON file saved by ``save_notebook``.
        options : Dict[str, Any]
            Rendering options from the frontend (unused).

        Returns
        -------
        Dict[str, Any]
            Dictionary with keys ``"data"`` (the profile dict),
            ``"type"`` (``"clustering_profile"``), and ``"config"`` (empty dict).
        """
        resultType = "clustering_profile"
        config = {}

        with open(exploration_path, "r", encoding="utf-8") as f:
            result = json.load(f)
        return {"data": result, "type": resultType, "config": config}
