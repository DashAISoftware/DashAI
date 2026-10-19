import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.schema_fields import enum_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.clustering_explorer import ClusteringExplorer
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ClusteringScatterSchema(BaseExplorerSchema):
    """Schema for ClusteringScatterExplorer."""

    reduction_method: schema_field(
        enum_field(["pca", "tsne"]),
        "pca",
        description=MultilingualString(
            en=(
                "Dimensionality reduction method used to project the selected "
                "features onto two dimensions. 'pca' is fast and deterministic; "
                "'tsne' can better reveal non-linear cluster structure but is "
                "slower and stochastic."
            ),
            es=(
                "Método de reducción de dimensionalidad para proyectar las columnas"
                " seleccionadas en dos dimensiones. 'pca' es rápido y determinista;"
                " 'tsne' puede revelar mejor la estructura no lineal pero es más "
                "lento."
            ),
            pt=(
                "Método de redução de dimensionalidade para projetar as colunas "
                "selecionadas em duas dimensões. 'pca' é rápido e determinístico; "
                "'tsne' pode revelar melhor a estrutura não linear, mas é mais "
                "lento."
            ),
            de=(
                "Dimensionsreduzierungsmethode zur Projektion der ausgewählten "
                "Merkmale auf zwei Dimensionen. 'pca' ist schnell und "
                "deterministisch; 'tsne' kann nicht-lineare Clusterstrukturen "
                "besser aufdecken, ist aber langsamer."
            ),
            zh=(
                "用于将所选特征投影到二维平面的降维方法。'pca'速度快且结果确定；"
                "'tsne'能更好地揭示非线性聚类结构，但速度较慢且具有随机性。"
            ),
        ),
        alias=MultilingualString(
            en="Reduction method",
            es="Método de reducción",
            pt="Método de redução",
            de="Reduktionsmethode",
            zh="降维方法",
        ),
    )  # type: ignore


class ClusteringScatterExplorer(ClusteringExplorer):
    """2-D scatter plot of clustering results coloured by cluster label.

    Projects the selected numeric feature columns onto a 2-D plane using either
    PCA or t-SNE, then colours each point by its assigned cluster label.

    When the converter report contains cluster centres (K-Means, Faiss K-Means,
    Gaussian Mixture), the centres are projected through the same PCA reducer
    and rendered as distinct ``×`` markers — only available with PCA because
    t-SNE does not support out-of-sample transforms.

    Noise points produced by density-based algorithms (DBSCAN / HDBSCAN,
    label ``-1``) receive the dedicated label ``"Noise"`` and a neutral colour.

    Select at least two numeric columns that were used to fit the clustering
    algorithm.  The cluster label column is added automatically from the
    converter report and must **not** be included in the selection.
    """

    DISPLAY_NAME = MultilingualString(
        en="Clustering Scatter Plot",
        es="Gráfico de Dispersión de Agrupamiento",
        pt="Gráfico de Dispersão de Agrupamento",
        de="Clustering-Streudiagramm",
        zh="聚类散点图",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Projects the selected numeric features onto 2D using PCA or t-SNE "
            "and colours each point by its cluster assignment. Cluster centres are "
            "overlaid when available (K-Means, GMM). Noise points are highlighted."
        ),
        es=(
            "Proyecta las columnas numéricas seleccionadas en 2D usando PCA o t-SNE"
            " y colorea cada punto según su clúster asignado. Superpone los centros "
            "de clúster cuando están disponibles (K-Means, GMM). Los puntos de ruido"
            " se destacan."
        ),
        pt=(
            "Projeta as colunas numéricas selecionadas em 2D usando PCA ou t-SNE e "
            "colore cada ponto pelo cluster atribuído. Centros de cluster são "
            "sobrepostos quando disponíveis (K-Means, GMM). Pontos de ruído são "
            "destacados."
        ),
        de=(
            "Projiziert die ausgewählten numerischen Merkmale mit PCA oder t-SNE in"
            " 2D und färbt jeden Punkt nach seiner Clusterzuordnung. Clusterzentren"
            " werden überlagert, wenn verfügbar (K-Means, GMM). Rauschpunkte werden"
            " hervorgehoben."
        ),
        zh=(
            "使用PCA或t-SNE将所选数值特征投影到二维平面，并按聚类分配为每个点着色。"
            "如有可用的聚类中心（K-Means、GMM）会一并叠加显示。噪声点会被高亮标出。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="2D projection of features coloured by cluster label.",
        es="Proyección 2D de características coloreada por etiqueta de clúster.",
        pt="Projeção 2D de características colorida por rótulo de cluster.",
        de="2D-Projektion der Merkmale, eingefärbt nach Clusterzuordnung.",
        zh="按聚类标签着色的特征二维投影。",
    )
    IMAGE_PREVIEW = "clustering_scatter.png"
    SCHEMA = ClusteringScatterSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Float, Integer],
        "allowed_dtypes": [],
        "input_cardinality": {"min": 2},
        "restricts_to_converter_columns": True,
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the ClusteringScatterExplorer.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments. Recognized keys:
            reduction_method (str, optional): ``"pca"`` for Principal Component
            Analysis (fast, deterministic, supports centroid projection) or
            ``"tsne"`` for t-SNE (better for non-linear structure, slower,
            stochastic). Defaults to ``"pca"``.
        """
        self.reduction_method: str = kwargs.get("reduction_method", "pca")
        super().__init__(**kwargs)

    def prepare_dataset(
        self, loaded_dataset: "DashAIDataset", columns: List[Dict[str, Any]]
    ) -> "DashAIDataset":
        """Extend column selection to include the cluster label column.

        Reads the cluster column name from the converter report and appends
        it to the user's selection if not already present, so that
        ``launch_exploration`` can colour points by cluster.

        Parameters
        ----------
        loaded_dataset : DashAIDataset
            The full dataset.
        columns : List[Dict[str, Any]]
            Feature column descriptors selected by the user (a subset of the
            columns used during the last Clustering converter fit).

        Returns
        -------
        DashAIDataset
            Dataset restricted to the selected feature columns plus the
            cluster label column.
        """
        cr = self.context.get("converter_report", {})
        cluster_column = cr.get("cluster_column", "cluster")
        column_names = {col["columnName"] for col in columns}
        if cluster_column not in column_names:
            columns = list(columns) + [{"columnName": cluster_column}]
        return super().prepare_dataset(loaded_dataset, columns)

    def launch_exploration(
        self, dataset: "DashAIDataset", explorer_info: Explorer
    ) -> Any:
        """Project features to 2D and build a scatter plot coloured by cluster.

        Applies PCA or t-SNE to the selected feature columns, then renders a
        Plotly scatter plot where each point is coloured by its cluster label.
        When ``reduction_method`` is ``"pca"`` and the converter report contains
        cluster centres, the centres are projected through the same reducer and
        overlaid as ``×`` markers.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset with the selected feature columns and the cluster label
            column (injected by ``prepare_dataset``).
        explorer_info : Explorer
            Explorer record with column descriptors and optional custom title.

        Returns
        -------
        plotly.graph_objects.Figure
            An interactive 2-D scatter plot figure.

        Raises
        ------
        ValueError
            If fewer than two numeric feature columns are provided after
            excluding the cluster label column.
        """
        import numpy as np
        import pandas as pd
        import plotly.express as px
        import plotly.graph_objects as go
        from sklearn.decomposition import PCA
        from sklearn.manifold import TSNE

        cr = self.context.get("converter_report", {})
        cluster_column = cr.get("cluster_column", "cluster")
        algorithm = cr.get("algorithm", "unknown")
        converter_feature_cols = set(cr.get("feature_columns", []))

        feature_cols = [
            c["columnName"]
            for c in explorer_info.columns
            if c["columnName"] != cluster_column
        ]

        if converter_feature_cols:
            invalid = [c for c in feature_cols if c not in converter_feature_cols]
            if invalid:
                raise ValueError(
                    f"The following columns were not used by the Clustering converter "
                    f"and cannot be plotted: {invalid}. Select only columns from the "
                    f"converter scope: {sorted(converter_feature_cols)}."
                )

        if len(feature_cols) < 2:
            raise ValueError(
                "At least 2 feature columns are required for dimensionality reduction."
            )

        data = dataset.to_pandas()

        X = data[feature_cols].dropna()
        cluster_labels = (
            data.loc[X.index, cluster_column].astype(str).replace({"-1": "Noise"})
        )

        if self.reduction_method == "pca":
            reducer = PCA(n_components=2, random_state=42)
            coords = reducer.fit_transform(X)
            x_label = f"PC1 ({reducer.explained_variance_ratio_[0]:.1%})"
            y_label = f"PC2 ({reducer.explained_variance_ratio_[1]:.1%})"
        else:
            perplexity = min(30.0, max(5.0, len(X) / 5.0))
            reducer = TSNE(n_components=2, random_state=42, perplexity=perplexity)
            coords = reducer.fit_transform(X)
            x_label, y_label = "t-SNE 1", "t-SNE 2"

        plot_df = pd.DataFrame(
            {x_label: coords[:, 0], y_label: coords[:, 1], "Cluster": cluster_labels}
        )

        fig = px.scatter(
            plot_df,
            x=x_label,
            y=y_label,
            color="Cluster",
            title=f"Cluster Scatter ({self.reduction_method.upper()}) — {algorithm}",
            color_discrete_sequence=px.colors.qualitative.Set1,
        )

        # Overlay cluster centres only when PCA is used (TSNE has no transform)
        fit_attributes = cr.get("fit_attributes", {})
        if "cluster_centers" in fit_attributes and self.reduction_method == "pca":
            centers = np.array(fit_attributes["cluster_centers"])
            if centers.shape[1] == len(feature_cols):
                centers_2d = reducer.transform(centers)
                for i, center in enumerate(centers_2d):
                    fig.add_trace(
                        go.Scatter(
                            x=[center[0]],
                            y=[center[1]],
                            mode="markers",
                            marker={
                                "symbol": "x",
                                "size": 14,
                                "color": "black",
                                "line": {"width": 2},
                            },
                            name=f"Centroid {i}",
                            showlegend=True,
                        )
                    )

        if explorer_info.name:
            fig.update_layout(title=explorer_info.name)

        return fig

    def save_notebook(
        self,
        __notebook_info__: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Save the scatter plot figure to disk as a JSON file.

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
        from pathlib import Path

        filename = f"{explorer_info.id}.json"
        path = Path(os.path.join(save_path, filename))

        result.write_json(path.as_posix())
        return path.as_posix()

    def get_results(
        self, exploration_path: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Load the saved scatter plot and return it for the frontend.

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

        result = read_json(exploration_path)
        result = result.to_json()

        return {"data": result, "type": "plotly_json", "config": {}}
