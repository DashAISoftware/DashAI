from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.clustering_explorer import ClusteringExplorer
from DashAI.back.types.value_types import Float, Integer

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


class SilhouettePlotSchema(BaseExplorerSchema):
    """Schema for SilhouettePlotExplorer.

    Select the same numeric feature columns that were passed to the clustering
    algorithm. No additional parameters are required.
    """


class SilhouettePlotExplorer(ClusteringExplorer):
    """Per-sample silhouette diagram coloured by cluster.

    Recomputes the silhouette coefficient for every sample using
    ``sklearn.metrics.silhouette_samples`` and renders a horizontal silhouette
    plot: each cluster occupies a vertical band, bars extend right (positive)
    or left (negative) according to each sample's score, and a vertical dashed
    line marks the dataset mean silhouette score.

    The plot reveals poorly separated clusters (many samples with low or
    negative silhouette), uneven cluster sizes, and samples that may be
    mis-assigned.

    Noise points produced by density-based algorithms (label ``-1``) are shown
    as a separate "Noise" band but are excluded from the mean score.

    Requires at least two valid (non-noise) clusters. Select the same numeric
    feature columns that were used to fit the clustering algorithm.
    """

    DISPLAY_NAME = MultilingualString(
        en="Silhouette Plot",
        es="Gráfico de Silueta",
        pt="Gráfico de Silhueta",
        de="Silhouette-Diagramm",
        zh="轮廓图",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Shows per-sample silhouette coefficients grouped by cluster. "
            "Each bar represents one sample; bars to the right indicate good "
            "cluster assignment, bars to the left indicate possible mis-assignment."
            " The dashed line marks the dataset mean silhouette score."
        ),
        es=(
            "Muestra los coeficientes de silueta por muestra agrupados por clúster."
            " Cada barra representa una muestra; barras a la derecha indican buena "
            "asignación al clúster, barras a la izquierda indican posible mala "
            "asignación. La línea punteada marca la media del conjunto de datos."
        ),
        pt=(
            "Mostra os coeficientes de silhueta por amostra agrupados por cluster. "
            "Barras à direita indicam boa atribuição ao cluster; à esquerda, "
            "possível atribuição incorreta. A linha tracejada marca a média do "
            "conjunto de dados."
        ),
        de=(
            "Zeigt Pro-Sample-Silhouette-Koeffizienten nach Cluster gruppiert. "
            "Balken nach rechts zeigen gute Clusterzuordnung an; Balken nach links "
            "mögliche Fehlzuordnung. Die gestrichelte Linie markiert den "
            "Datensatzmittelwert."
        ),
        zh=(
            "按聚类分组展示每个样本的轮廓系数。每根柱条代表一个样本；柱条向右表示"
            "聚类分配良好，向左表示可能分配错误。虚线标记数据集的平均轮廓系数。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Per-sample silhouette coefficients grouped by cluster.",
        es="Coeficientes de silueta por muestra agrupados por clúster.",
        pt="Coeficientes de silhueta por amostra agrupados por cluster.",
        de="Pro-Sample-Silhouette-Koeffizienten nach Cluster.",
        zh="按聚类分组的每个样本的轮廓系数。",
    )
    IMAGE_PREVIEW = "silhouette_plot.png"
    SCHEMA = SilhouettePlotSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Float, Integer],
        "allowed_dtypes": [],
        "input_cardinality": {"min": 1},
        "restricts_to_converter_columns": True,
    }

    def prepare_dataset(
        self, loaded_dataset: "DashAIDataset", columns: List[Dict[str, Any]]
    ) -> "DashAIDataset":
        """Extend column selection to include the cluster label column.

        Reads the cluster column name from the converter report and appends
        it to the selection if not already present, so that
        ``launch_exploration`` can group samples by cluster when recomputing
        the silhouette scores.

        Parameters
        ----------
        loaded_dataset : DashAIDataset
            The full dataset.
        columns : List[Dict[str, Any]]
            Explicitly selected column descriptors (numeric feature columns
            that were used to fit the clustering algorithm).

        Returns
        -------
        DashAIDataset
            Dataset restricted to the selected feature columns plus the
            cluster label column.
        """
        cluster_column = self.context.get("converter_report", {}).get(
            "cluster_column", "cluster"
        )
        column_names = {col["columnName"] for col in columns}
        if cluster_column not in column_names:
            columns = list(columns) + [{"columnName": cluster_column}]
        return super().prepare_dataset(loaded_dataset, columns)

    def launch_exploration(
        self, dataset: "DashAIDataset", explorer_info: Explorer
    ) -> Any:
        """Compute per-sample silhouette scores and render a horizontal silhouette plot.

        Recomputes silhouette coefficients from scratch using
        ``sklearn.metrics.silhouette_samples``. Each cluster occupies a
        vertical band; samples within a cluster are sorted by their score so
        the filled area reflects the score distribution. Clusters are separated
        by a small gap for readability. Noise points (label ``-1``) are shown
        as a separate band but excluded from the global mean score.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset with the selected feature columns and the cluster label
            column (injected by ``prepare_dataset``). The feature columns
            should be the same ones used to fit the clustering algorithm.
        explorer_info : Explorer
            Explorer record with column descriptors and optional custom title.

        Returns
        -------
        plotly.graph_objects.Figure
            A horizontal silhouette diagram.

        Raises
        ------
        ValueError
            If fewer than two valid (non-noise) clusters are present in the
            data after excluding noise points, or if a selected column was
            not part of the feature set used to fit the clustering algorithm.
        """
        import numpy as np
        import plotly.graph_objects as go
        from sklearn.metrics import silhouette_samples

        cr = self.context.get("converter_report", {})
        cluster_column = cr.get("cluster_column", "cluster")
        algorithm = cr.get("algorithm", "unknown")
        converter_feature_cols = set(cr.get("feature_columns", []))

        data = dataset.to_pandas()
        feature_cols = [
            c["columnName"]
            for c in explorer_info.columns
            if c["columnName"] != cluster_column
        ]

        if converter_feature_cols:
            invalid = [c for c in feature_cols if c not in converter_feature_cols]
            if invalid:
                raise ValueError(
                    f"The following columns were not used by the Clustering "
                    f"converter and cannot be used for the silhouette score: "
                    f"{invalid}. Select only columns from the converter scope: "
                    f"{sorted(converter_feature_cols)}."
                )

        X = data[feature_cols].dropna()
        labels = data.loc[X.index, cluster_column].values

        unique_labels = np.unique(labels)
        valid_labels = unique_labels[unique_labels != -1]

        if len(valid_labels) < 2:
            raise ValueError(
                f"Silhouette plot requires at least 2 valid clusters. "
                f"Found {len(valid_labels)} valid cluster(s) after excluding noise."
            )

        sample_scores = silhouette_samples(X, labels)
        valid_mask = labels != -1
        mean_score = float(np.mean(sample_scores[valid_mask]))

        fig = go.Figure()
        y_offset = 0
        cluster_tick_vals: List[float] = []
        cluster_tick_text: List[str] = []

        for _i, cluster_label in enumerate(sorted(valid_labels)):
            mask = labels == cluster_label
            cluster_scores = np.sort(sample_scores[mask])
            size = len(cluster_scores)
            y_vals = np.arange(y_offset, y_offset + size, dtype=float)
            color = _CLUSTER_COLORS[int(cluster_label) % len(_CLUSTER_COLORS)]

            fig.add_trace(
                go.Scatter(
                    x=np.concatenate([[0.0], cluster_scores, [0.0]]),
                    y=np.concatenate([[y_vals[0]], y_vals, [y_vals[-1]]]),
                    mode="lines",
                    fill="tozerox",
                    fillcolor=color,
                    line={"color": color, "width": 0.5},
                    name=f"Cluster {int(cluster_label)}",
                    showlegend=True,
                )
            )
            cluster_tick_vals.append(y_offset + size / 2)
            cluster_tick_text.append(f"Cluster {int(cluster_label)}")
            y_offset += size + 15

        # Noise band (if any)
        if -1 in unique_labels:
            noise_mask = labels == -1
            noise_scores = np.sort(sample_scores[noise_mask])
            size = len(noise_scores)
            y_vals = np.arange(y_offset, y_offset + size, dtype=float)
            fig.add_trace(
                go.Scatter(
                    x=np.concatenate([[0.0], noise_scores, [0.0]]),
                    y=np.concatenate([[y_vals[0]], y_vals, [y_vals[-1]]]),
                    mode="lines",
                    fill="tozerox",
                    fillcolor="#AAAAAA",
                    line={"color": "#AAAAAA", "width": 0.5},
                    name="Noise",
                    showlegend=True,
                )
            )
            cluster_tick_vals.append(y_offset + size / 2)
            cluster_tick_text.append("Noise")
            y_offset += size + 15

        fig.add_vline(
            x=mean_score,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Mean = {mean_score:.3f}",
            annotation_position="top right",
        )

        title = (
            explorer_info.name
            if explorer_info.name
            else f"Silhouette Plot — {algorithm}"
        )
        fig.update_layout(
            title=title,
            xaxis_title="Silhouette Coefficient",
            xaxis={"range": [-1.1, 1.1]},
            yaxis={
                "tickvals": cluster_tick_vals,
                "ticktext": cluster_tick_text,
                "showgrid": False,
            },
            height=max(400, y_offset + 60),
        )

        return fig

    def save_notebook(
        self,
        __notebook_info__: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Save the silhouette figure to disk as a JSON file.

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
        """Load the saved silhouette figure and return it for the frontend.

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
