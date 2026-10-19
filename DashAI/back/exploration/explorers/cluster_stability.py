import json
from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.clustering_explorer import ClusteringExplorer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

_CLUSTER_COLORS = [
    "#4472C4",
    "#ED7D31",
    "#A9D18E",
    "#E00000",
    "#7030A0",
    "#00B0F0",
    "#FFC000",
    "#70AD47",
    "#FF7F50",
    "#9DC3E6",
]


class ClusterStabilitySchema(BaseExplorerSchema):
    """Schema for ClusterStabilityExplorer — no parameters needed."""


class ClusterStabilityExplorer(ClusteringExplorer):
    """Cluster persistence bar chart for HDBSCAN.

    Reads the ``cluster_persistence_`` attribute stored by the ``Clustering``
    converter when run with the ``hdbscan`` algorithm.

    Each bar represents one cluster; its height is the persistence score —
    a measure of how long that cluster survives across the range of density
    thresholds explored by HDBSCAN.  A higher persistence indicates a more
    robust, stable cluster; a low persistence means the cluster appears only
    in a narrow density window and may be unreliable.

    A dashed horizontal line marks the mean persistence across all clusters.
    The result also includes a summary table with min, max, and mean values.

    This explorer raises an informative error if the last ``Clustering``
    converter was **not** run with HDBSCAN.  No column selection is required.
    """

    DISPLAY_NAME = MultilingualString(
        en="Cluster Stability (HDBSCAN)",
        es="Estabilidad de Clústeres (HDBSCAN)",
        pt="Estabilidade de Clusters (HDBSCAN)",
        de="Cluster-Stabilität (HDBSCAN)",
        zh="聚类稳定性（HDBSCAN）",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Shows the persistence score for each cluster discovered by HDBSCAN. "
            "Persistence measures how long a cluster survives across density "
            "thresholds. Higher values indicate more robust, stable clusters. "
            "Only available after running HDBSCAN clustering."
        ),
        es=(
            "Muestra la puntuación de persistencia de cada clúster descubierto por "
            "HDBSCAN. La persistencia mide cuánto tiempo sobrevive un clúster a través"
            " de los umbrales de densidad. Valores más altos indican clústeres más "
            "robustos y estables. Solo disponible tras ejecutar agrupamiento HDBSCAN."
        ),
        pt=(
            "Mostra a pontuação de persistência para cada cluster descoberto pelo "
            "HDBSCAN. A persistência mede por quanto tempo um cluster sobrevive nos "
            "limiares de densidade. Valores mais altos indicam clusters mais robustos "
            "e estáveis. Disponível apenas após executar o HDBSCAN."
        ),
        de=(
            "Zeigt den Persistenz-Score für jeden von HDBSCAN entdeckten Cluster. "
            "Persistenz misst, wie lange ein Cluster über Dichteschwellenwerte hinweg "
            "überlebt. Höhere Werte zeigen robustere, stabilere Cluster an. "
            "Nur nach HDBSCAN-Clustering verfügbar."
        ),
        zh=(
            "显示HDBSCAN发现的每个聚类的持久性得分。持久性衡量一个聚类在不同密度阈值"
            "范围内存续的时长，值越高表示聚类越稳健、越稳定。仅在运行HDBSCAN聚类后可用。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Per-cluster persistence scores from HDBSCAN.",
        es="Puntuaciones de persistencia por clúster de HDBSCAN.",
        pt="Pontuações de persistência por cluster do HDBSCAN.",
        de="Pro-Cluster-Persistenzwerte von HDBSCAN.",
        zh="HDBSCAN每个聚类的持久性得分。",
    )
    IMAGE_PREVIEW = "cluster_stability.png"
    SCHEMA = ClusterStabilitySchema
    metadata: Dict[str, Any] = {
        "allowed_types": [],
        "allowed_dtypes": [],
        "input_cardinality": {"exact": 0},
        "requires_algorithm": "hdbscan",
    }

    def prepare_dataset(
        self, loaded_dataset: "DashAIDataset", _columns: List[Dict[str, Any]]
    ) -> "DashAIDataset":
        """Return the dataset unchanged.

        No columns are needed — all data is read from the converter report's
        ``fit_attributes``.

        Parameters
        ----------
        loaded_dataset : DashAIDataset
            The full dataset.
        _columns : List[Dict[str, Any]]
            Ignored. Present for API compatibility.

        Returns
        -------
        DashAIDataset
            The dataset as received, unmodified.
        """
        return loaded_dataset

    def launch_exploration(
        self, _dataset: "DashAIDataset", explorer_info: Explorer
    ) -> Dict[str, Any]:
        """Build a bar chart of HDBSCAN cluster persistence scores.

        Reads ``cluster_persistence`` from the converter report's
        ``fit_attributes`` and renders a bar chart where each bar represents
        one cluster. A dashed horizontal line marks the mean persistence
        across all clusters.

        Parameters
        ----------
        _dataset : DashAIDataset
            Not used. All data is read from the converter report.
        explorer_info : Explorer
            Explorer record, used for the optional custom title.

        Returns
        -------
        Dict[str, Any]
            Dictionary with keys ``"figure"`` (JSON-serialised Plotly figure)
            and ``"summary"`` (dict with ``n_clusters``, ``min_persistence``,
            ``max_persistence``, ``mean_persistence``, and ``per_cluster`` list).

        Raises
        ------
        ValueError
            If the converter report does not contain ``cluster_persistence``
            data, indicating the converter was not run with HDBSCAN.
        """
        import numpy as np
        import plotly.graph_objects as go

        cr = self.context.get("converter_report", {})
        algorithm = cr.get("algorithm", "unknown")
        fit_attributes = cr.get("fit_attributes", {})

        if "cluster_persistence" not in fit_attributes:
            raise ValueError(
                f"Cluster Stability requires HDBSCAN clustering, but the last "
                f"converter ran '{algorithm}' and did not produce cluster persistence "
                f"data. Re-run the Clustering converter with the HDBSCAN algorithm."
            )

        persistence = np.array(fit_attributes["cluster_persistence"])
        n_clusters = len(persistence)
        cluster_labels = [f"Cluster {i}" for i in range(n_clusters)]
        bar_colors = [
            _CLUSTER_COLORS[i % len(_CLUSTER_COLORS)] for i in range(n_clusters)
        ]
        mean_val = float(np.mean(persistence))

        fig = go.Figure(
            go.Bar(
                x=cluster_labels,
                y=persistence.tolist(),
                marker_color=bar_colors,
                text=[f"{v:.4f}" for v in persistence],
                textposition="outside",
            )
        )
        fig.add_hline(
            y=mean_val,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Mean = {mean_val:.4f}",
            annotation_position="top right",
        )

        title = (
            explorer_info.name if explorer_info.name else "Cluster Stability — HDBSCAN"
        )
        fig.update_layout(
            title=title,
            xaxis_title="Cluster",
            yaxis_title="Persistence Score",
            yaxis={"range": [0, float(np.max(persistence)) * 1.2]},
        )

        summary = {
            "n_clusters": n_clusters,
            "min_persistence": float(np.min(persistence)),
            "max_persistence": float(np.max(persistence)),
            "mean_persistence": mean_val,
            "per_cluster": [
                {"cluster": i, "persistence": float(v)}
                for i, v in enumerate(persistence)
            ],
        }

        return {"figure": fig.to_json(), "summary": summary}

    def save_notebook(
        self,
        __notebook_info__: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Save the stability result (figure + summary) to disk as a JSON file.

        Parameters
        ----------
        __notebook_info__ : Notebook
            The notebook database record (unused).
        explorer_info : Explorer
            The explorer record used for filename generation.
        save_path : Path
            Directory where the file will be saved.
        result : Any
            The dict returned by ``launch_exploration``, containing
            ``"figure"`` and ``"summary"`` keys.

        Returns
        -------
        str
            The path of the saved JSON file as a POSIX string.
        """
        import os
        from pathlib import Path

        filename = f"{explorer_info.id}.json"
        path = Path(os.path.join(save_path, filename))

        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
        return path.as_posix()

    def get_results(
        self, exploration_path: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Load the saved stability result and return it for the frontend.

        Parameters
        ----------
        exploration_path : str
            Path to the JSON file saved by ``save_notebook``.
        options : Dict[str, Any]
            Rendering options from the frontend (unused).

        Returns
        -------
        Dict[str, Any]
            Dictionary with keys ``"data"`` (Plotly figure JSON string),
            ``"type"`` (``"plotly_json"``), and ``"config"`` (empty dict).
        """
        with open(exploration_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "data": data["figure"],
            "type": "plotly_json",
            "config": {},
        }
