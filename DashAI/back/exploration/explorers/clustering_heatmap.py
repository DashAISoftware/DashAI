from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.schema_fields import bool_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.clustering_explorer import ClusteringExplorer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ClusteringHeatmapSchema(BaseExplorerSchema):
    """Schema for ClusteringHeatmapExplorer."""

    normalize: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en=(
                "When enabled, cell colours represent z-score standardised values "
                "(how many standard deviations each cluster mean is from the global"
                " mean), making clusters with very different feature scales "
                "directly comparable. Raw mean values are always shown as cell "
                "annotations. When disabled, the colour scale uses raw means."
            ),
            es=(
                "Cuando está activado, los colores representan valores z-score "
                "estandarizados (cuántas desviaciones estándar se aleja la media de"
                " cada clúster de la media global), haciendo que los clústeres con "
                "escalas de características muy distintas sean directamente "
                "comparables. Los valores de media cruda siempre se muestran como "
                "anotaciones. Cuando está desactivado, la escala de colores usa las"
                " medias crudas."
            ),
            pt=(
                "Quando habilitado, as cores das células representam valores "
                "z-score padronizados, tornando clusters com escalas de "
                "características muito diferentes diretamente comparáveis. Os "
                "valores médios brutos sempre são mostrados como anotações. Quando "
                "desabilitado, a escala de cores usa as médias brutas."
            ),
            de=(
                "Wenn aktiviert, stellen die Zellenfarben z-score-standardisierte "
                "Werte dar, wodurch Cluster mit sehr unterschiedlichen "
                "Merkmalsskalen direkt vergleichbar werden. Rohe Mittelwerte werden"
                " immer als Zellenbeschriftung angezeigt. Wenn deaktiviert, "
                "verwendet die Farbskala die rohen Mittelwerte."
            ),
            zh=(
                "启用后，单元格颜色表示z-score标准化值（每个聚类均值与全局均值相差"
                "的标准差数），使特征尺度差异很大的聚类可以直接比较。原始均值始终以"
                "单元格标注形式显示。禁用时，颜色刻度使用原始均值。"
            ),
        ),
        alias=MultilingualString(
            en="Z-score normalisation",
            es="Normalización z-score",
            pt="Normalização z-score",
            de="Z-Score-Normalisierung",
            zh="Z-score标准化",
        ),
    )  # type: ignore


class ClusteringHeatmapExplorer(ClusteringExplorer):
    """Annotated heatmap of mean feature values per cluster.

    Reads the per-cluster feature profiles stored in the ``Clustering``
    converter report and renders an annotated heatmap where rows correspond
    to clusters and columns to the numeric features used during fitting.

    Each cell shows the raw mean value of a feature within a cluster as a
    number annotation.  The cell colour can optionally be z-score normalised
    (default), which maps how far each cluster mean is from the global feature
    mean in standard deviations — making features with very different scales
    visually comparable and highlighting which clusters are the most distinctive
    for each feature.

    A diverging red–blue colour scale is used: red cells indicate values well
    above the global mean, blue cells indicate values well below it.

    No column selection is required — all data comes from the converter report.
    """

    DISPLAY_NAME = MultilingualString(
        en="Cluster Feature Heatmap",
        es="Mapa de Calor de Características por Clúster",
        pt="Mapa de Calor de Características por Cluster",
        de="Cluster-Merkmals-Heatmap",
        zh="聚类特征热力图",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Heatmap where rows are clusters and columns are the numeric features "
            "used for clustering. Each cell shows the mean feature value within "
            "that cluster, with optional z-score normalisation so that distinctive "
            "features stand out regardless of their scale."
        ),
        es=(
            "Mapa de calor donde las filas son clústeres y las columnas son las "
            "características numéricas usadas para el agrupamiento. Cada celda "
            "muestra la media de la característica dentro de ese clúster, con "
            "normalización z-score opcional para que las características "
            "distintivas destaquen independientemente de su escala."
        ),
        pt=(
            "Mapa de calor onde as linhas são clusters e as colunas são as "
            "características numéricas usadas para o agrupamento. Cada célula "
            "mostra a média da característica dentro daquele cluster, com "
            "normalização z-score opcional."
        ),
        de=(
            "Heatmap, bei der Zeilen Cluster und Spalten die numerischen Merkmale "
            "darstellen. Jede Zelle zeigt den mittleren Merkmalswert innerhalb "
            "dieses Clusters, mit optionaler z-Score-Normalisierung, damit markante"
            " Merkmale unabhängig von ihrer Skala hervorstechen."
        ),
        zh=(
            "热力图中行代表聚类，列代表用于聚类的数值特征。每个单元格显示该特征在"
            "该聚类内的均值，可选z-score标准化，使具有代表性的特征不受量纲影响而"
            "更加突出。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Mean feature values per cluster with optional z-score normalisation.",
        es=(
            "Valores medios de características por clúster con normalización "
            "z-score opcional."
        ),
        pt=(
            "Valores médios de características por cluster com normalização "
            "z-score opcional."
        ),
        de="Mittlere Merkmalswerte pro Cluster mit optionaler z-Score-Normalisierung.",
        zh="每个聚类的平均特征值，可选z-score标准化。",
    )
    IMAGE_PREVIEW = "clustering_heatmap.png"

    SCHEMA = ClusteringHeatmapSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [],
        "allowed_dtypes": [],
        "input_cardinality": {"exact": 0},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the ClusteringHeatmapExplorer.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments. Recognized keys:
            normalize (bool, optional): When True, cell colours use z-score
            standardised values; raw means are always shown as annotations.
            Defaults to True.
        """
        self.normalize: bool = kwargs.get("normalize", True)
        super().__init__(**kwargs)

    def prepare_dataset(
        self, loaded_dataset: "DashAIDataset", _columns: List[Dict[str, Any]]
    ) -> "DashAIDataset":
        """Return the dataset unchanged.

        No column selection is needed — all data is read from the converter
        report's cluster profiles, not from the dataset itself.

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
        """Build an annotated heatmap of mean feature values per cluster.

        Reads cluster profiles from the converter report and constructs a
        Plotly heatmap where rows are clusters and columns are the numeric
        features used during fitting. Cell annotations always show raw means;
        cell colours use z-score normalised values when ``self.normalize`` is
        True, making features with very different scales visually comparable.

        Parameters
        ----------
        _dataset : DashAIDataset
            Not used. All data is read from the converter report.
        explorer_info : Explorer
            Explorer record, used for the optional custom title.

        Returns
        -------
        plotly.graph_objects.Figure
            An annotated heatmap figure.

        Raises
        ------
        ValueError
            If no cluster profiles are found in the converter report.
        """
        import numpy as np
        import pandas as pd
        import plotly.express as px

        cr = self.context.get("converter_report", {})
        cluster_profiles = cr.get("cluster_profiles", [])
        algorithm = cr.get("algorithm", "unknown")

        if not cluster_profiles:
            raise ValueError(
                "No cluster profiles found in the converter report. "
                "Make sure the Clustering converter ran successfully before "
                "launching this explorer."
            )

        rows = []
        for profile in cluster_profiles:
            row: Dict[str, Any] = {"Cluster": str(profile["cluster"])}
            for feature, stats in profile.get("feature_stats", {}).items():
                row[feature] = stats.get("mean")
            rows.append(row)

        means_df = pd.DataFrame(rows).set_index("Cluster")

        if self.normalize:
            col_means = means_df.mean()
            col_stds = means_df.std(ddof=0).replace(0, 1)
            color_df = (means_df - col_means) / col_stds
            color_label = "z-score"
        else:
            color_df = means_df.copy()
            color_label = "Mean"

        fig = px.imshow(
            color_df,
            text_auto=False,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            color_continuous_midpoint=0 if self.normalize else None,
            title=f"Cluster Feature Heatmap — {algorithm}",
            labels={"x": "Feature", "y": "Cluster", "color": color_label},
        )

        # Add raw mean annotations manually
        for r_idx, cluster in enumerate(means_df.index):
            for c_idx, feature in enumerate(means_df.columns):
                val = means_df.loc[cluster, feature]
                if val is not None and not np.isnan(val):
                    fig.add_annotation(
                        x=c_idx,
                        y=r_idx,
                        text=f"{val:.2f}",
                        showarrow=False,
                        font={"size": 11, "color": "black"},
                        xref="x",
                        yref="y",
                    )

        fig.update_xaxes(tickangle=45)

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
        """Save the heatmap figure to disk as a JSON file.

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
        """Load the saved heatmap and return it for the frontend.

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
