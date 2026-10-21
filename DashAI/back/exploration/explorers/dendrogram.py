from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.clustering_explorer import ClusteringExplorer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class DendrogramSchema(BaseExplorerSchema):
    """Schema for DendrogramExplorer — no parameters needed."""


class DendrogramExplorer(ClusteringExplorer):
    """Hierarchical dendrogram for Agglomerative clustering.

    Reconstructs the merge history stored in the ``Clustering`` converter
    report when run with the ``agglomerative`` algorithm and the
    ``Compute distances`` option enabled.

    The dendrogram shows the full cluster hierarchy: leaves represent
    individual samples, internal nodes represent merges, and the height of
    each merge reflects the linkage distance at which two sub-trees were
    joined.  Reading the dendrogram reveals:

    - The natural number of clusters (large gaps between consecutive merge
      heights suggest a good cut point).
    - Relative similarity between groups.
    - Potential outliers that merge last at very large distances.

    This explorer raises an informative error if the last ``Clustering``
    converter was **not** run with the Agglomerative algorithm and
    ``Compute distances`` enabled.  No column selection is required.
    """

    DISPLAY_NAME = MultilingualString(
        en="Dendrogram",
        es="Dendrograma",
        pt="Dendrograma",
        de="Dendrogramm",
        zh="树状图",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Renders the full merge hierarchy produced by Agglomerative clustering."
            " The height of each join reflects the linkage distance, making it easy"
            " to identify the natural number of clusters and detect outliers. "
            "Only available after running Agglomerative clustering with "
            "'Compute distances' enabled."
        ),
        es=(
            "Renderiza la jerarquía completa de fusiones del agrupamiento "
            "Aglomerativo. La altura de cada unión refleja la distancia de enlace, "
            "facilitando identificar el número natural de clústeres y detectar "
            "outliers. Solo disponible tras ejecutar agrupamiento Aglomerativo con "
            "'Calcular distancias' activado."
        ),
        pt=(
            "Renderiza a hierarquia completa de fusões do agrupamento Aglomerativo."
            " A altura de cada junção reflete a distância de ligação, facilitando "
            "identificar o número natural de clusters e detectar outliers. "
            "Disponível apenas após executar o agrupamento aglomerativo com "
            "'Calcular distâncias' habilitado."
        ),
        de=(
            "Rendert die vollständige Fusionshierarchie des agglomerativen "
            "Clusterings. Die Höhe jeder Verbindung spiegelt die Linkage-Distanz "
            "wider und erleichtert die Identifizierung der natürlichen Clusteranzahl "
            "sowie die Erkennung von Ausreißern. Nur verfügbar nach agglomerativem "
            "Clustering mit aktivierter 'Distanzberechnung'."
        ),
        zh=(
            "呈现层次聚类（Agglomerative）产生的完整合并层级。每次合并的高度反映"
            "了链接距离，便于识别自然的聚类数量并检测离群点。仅在启用"
            "'计算距离'运行层次聚类后可用。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Full merge hierarchy for Agglomerative clustering.",
        es="Jerarquía completa de fusiones para agrupamiento Aglomerativo.",
        pt="Hierarquia completa de fusões para agrupamento aglomerativo.",
        de="Vollständige Fusionshierarchie für agglomeratives Clustering.",
        zh="层次聚类的完整合并层级。",
    )
    IMAGE_PREVIEW = "dendrogram.png"
    SCHEMA = DendrogramSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [],
        "allowed_dtypes": [],
        "input_cardinality": {"exact": 0},
        "requires_algorithm": "agglomerative",
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
    ) -> Any:
        """Build a Plotly dendrogram from the Agglomerative linkage data.

        Reads ``linkage_data`` from the converter report's ``fit_attributes``,
        reconstructs the scipy-compatible linkage matrix, and draws the full
        merge hierarchy as a horizontal dendrogram (x-axis = linkage distance,
        y-axis = sample index).

        Parameters
        ----------
        _dataset : DashAIDataset
            Not used. All data is read from the converter report.
        explorer_info : Explorer
            Explorer record, used for the optional custom title.

        Returns
        -------
        plotly.graph_objects.Figure
            An interactive dendrogram figure.

        Raises
        ------
        ValueError
            If the converter report does not contain ``linkage_data``,
            indicating the converter was not run with Agglomerative clustering
            and ``Compute distances`` enabled.
        """
        import numpy as np
        import plotly.graph_objects as go
        from scipy.cluster.hierarchy import dendrogram

        cr = self.context.get("converter_report", {})
        algorithm = cr.get("algorithm", "unknown")
        fit_attributes = cr.get("fit_attributes", {})

        if "linkage_data" not in fit_attributes:
            raise ValueError(
                f"Dendrogram requires Agglomerative clustering with 'Compute "
                f"distances' enabled, but the last converter ran '{algorithm}' and "
                f"produced no linkage data. Re-run the Clustering converter with the "
                f"Agglomerative algorithm and enable the 'Compute distances' option."
            )

        linkage_data = fit_attributes["linkage_data"]
        children = np.array(linkage_data["children"])
        distances = np.array(linkage_data["distances"], dtype=float)
        n_leaves = int(linkage_data["n_leaves"])

        Z = self._build_linkage_matrix(children, distances, n_leaves)
        dendro = dendrogram(Z, no_plot=True, color_threshold=0)

        traces = []
        for xs, ys in zip(dendro["icoord"], dendro["dcoord"], strict=False):
            traces.append(
                go.Scatter(
                    x=ys,
                    y=xs,
                    mode="lines",
                    line={"color": "#4472C4", "width": 1},
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

        title = (
            explorer_info.name
            if explorer_info.name
            else f"Dendrogram — Agglomerative ({n_leaves} samples)"
        )
        fig = go.Figure(traces)
        fig.update_layout(
            title=title,
            xaxis_title="Linkage Distance",
            yaxis_title="Sample Index",
            height=600,
        )

        return fig

    @staticmethod
    def _build_linkage_matrix(children: Any, distances: Any, n_leaves: int) -> Any:
        """Convert sklearn ``children_`` + ``distances_`` into a scipy linkage matrix.

        Parameters
        ----------
        children : np.ndarray, shape (n-1, 2)
            Merge pairs from ``AgglomerativeClustering.children_``.
        distances : np.ndarray, shape (n-1,)
            Merge distances from ``AgglomerativeClustering.distances_``.
        n_leaves : int
            Number of original samples.

        Returns
        -------
        np.ndarray, shape (n-1, 4)
            Scipy-compatible linkage matrix [child_i, child_j, distance, count].
        """
        import numpy as np

        Z = np.zeros((n_leaves - 1, 4))
        cluster_sizes: Dict[int, int] = dict.fromkeys(range(n_leaves), 1)

        for i, (c1, c2) in enumerate(children):
            new_node = n_leaves + i
            Z[i, 0] = float(c1)
            Z[i, 1] = float(c2)
            Z[i, 2] = float(distances[i])
            size = cluster_sizes.get(int(c1), 1) + cluster_sizes.get(int(c2), 1)
            Z[i, 3] = float(size)
            cluster_sizes[new_node] = size

        return Z

    def save_notebook(
        self,
        __notebook_info__: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Save the dendrogram figure to disk as a JSON file.

        Parameters
        ----------
        __notebook_info__ : Notebook
            The notebook database record (unused).
        explorer_info : Explorer
            The explorer record used for filename generation.
        save_path : Path
            Directory where the file will be saved.
        result : Any
            The Plotly figure returned by ``launch_exploration``.

        Returns
        -------
        str
            The path of the saved JSON file as a POSIX string.
        """
        import os
        from pathlib import Path

        filename = f"{explorer_info.id}.json"
        path = Path(os.path.join(save_path, filename))

        result.write_json(path.as_posix())
        return path.as_posix()

    def get_results(
        self, exploration_path: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Load the saved dendrogram and return it for the frontend.

        Parameters
        ----------
        exploration_path : str
            Path to the JSON file saved by ``save_notebook``.
        options : Dict[str, Any]
            Rendering options from the frontend (unused).

        Returns
        -------
        Dict[str, Any]
            Dictionary with keys ``"data"`` (JSON-serialised Plotly figure),
            ``"type"`` (``"plotly_json"``), and ``"config"`` (empty dict).
        """
        from plotly.io import read_json

        fig = read_json(exploration_path)
        return {"data": fig.to_json(), "type": "plotly_json", "config": {}}
