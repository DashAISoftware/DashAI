from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.schema_fields import enum_field, schema_field
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


class ClusterDistributionSchema(BaseExplorerSchema):
    """Schema for ClusterDistributionExplorer."""

    plot_type: schema_field(
        enum_field(["violin", "box"]),
        "violin",
        description=MultilingualString(
            en=(
                "Type of plot used to display feature distributions within each "
                "cluster. 'violin' shows the full probability density shape "
                "alongside a box plot; 'box' shows quartiles, median, and outliers"
                " only."
            ),
            es=(
                "Tipo de gráfico usado para mostrar las distribuciones de "
                "características dentro de cada clúster. 'violin' muestra la forma "
                "completa de densidad de probabilidad junto con un diagrama de caja;"
                " 'box' muestra cuartiles, mediana y valores atípicos únicamente."
            ),
            pt=(
                "Tipo de gráfico usado para exibir distribuições de características "
                "dentro de cada cluster. 'violin' mostra a forma completa da "
                "densidade de probabilidade junto com um diagrama de caixa; 'box' "
                "mostra quartis, mediana e outliers apenas."
            ),
            de=(
                "Diagrammtyp zur Darstellung der Merkmalsverteilungen innerhalb "
                "jedes Clusters. 'violin' zeigt die vollständige "
                "Wahrscheinlichkeitsdichteform neben einem Boxplot; 'box' zeigt "
                "nur Quartile, Median und Ausreißer."
            ),
            zh=(
                "用于显示每个聚类内特征分布的图表类型。'violin'（小提琴图）在箱线图旁"
                "展示完整的概率密度形状；'box'（箱线图）仅展示四分位数、中位数和异常值。"
            ),
        ),
        alias=MultilingualString(
            en="Plot type",
            es="Tipo de gráfico",
            pt="Tipo de gráfico",
            de="Diagrammtyp",
            zh="图表类型",
        ),
    )  # type: ignore


class ClusterDistributionExplorer(ClusteringExplorer):
    """Violin or box plots of feature distributions grouped by cluster.

    Shows how the values of the selected numeric features are distributed
    within each cluster, using one subplot per feature.  This goes beyond
    the heatmap means: it reveals differences in spread, skewness, and
    outliers between clusters for each feature.

    The cluster label column is added automatically from the converter report
    and must **not** be included in the column selection.  Noise points
    (cluster ``-1``) are shown as a separate "Noise" group with a neutral colour.

    Select one or more numeric features to compare across clusters.  For the
    most informative view, choose features that appear in the top distinctive
    features reported by the Clustering Profile.
    """

    DISPLAY_NAME = MultilingualString(
        en="Cluster Feature Distribution",
        es="Distribución de Características por Clúster",
        pt="Distribuição de Características por Cluster",
        de="Cluster-Merkmalsverteilung",
        zh="聚类特征分布",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Shows the distribution of the selected numeric features within each "
            "cluster using violin or box plots. Reveals differences in spread, "
            "skewness, and outliers that are not visible in the heatmap means. "
            "One subplot per selected feature."
        ),
        es=(
            "Muestra la distribución de las características numéricas seleccionadas"
            " dentro de cada clúster usando gráficos de violín o de caja. Revela "
            "diferencias en dispersión, asimetría y valores atípicos que no son "
            "visibles en las medias del mapa de calor. Un subgráfico por "
            "característica."
        ),
        pt=(
            "Mostra a distribuição das características numéricas selecionadas "
            "dentro de cada cluster usando gráficos de violino ou de caixa. Revela "
            "diferenças em dispersão, assimetria e outliers não visíveis nas médias "
            "do mapa de calor. Um subgráfico por característica selecionada."
        ),
        de=(
            "Zeigt die Verteilung der ausgewählten numerischen Merkmale innerhalb "
            "jedes Clusters als Violin- oder Boxplots. Deckt Unterschiede in "
            "Streuung, Schiefe und Ausreißern auf, die in den Heatmap-Mittelwerten "
            "nicht sichtbar sind. Ein Teildiagramm pro ausgewähltem Merkmal."
        ),
        zh=(
            "使用小提琴图或箱线图展示所选数值特征在每个聚类内的分布。揭示热力图均值中"
            "看不到的离散度、偏度和异常值差异。每个所选特征对应一个子图。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Feature distributions per cluster as violin or box plots.",
        es="Distribuciones de características por clúster como violín o caja.",
        pt="Distribuições de características por cluster como violino ou caixa.",
        de="Merkmalsverteilungen pro Cluster als Violin- oder Boxplots.",
        zh="以小提琴图或箱线图展示每个聚类的特征分布。",
    )
    IMAGE_PREVIEW = "cluster_distribution.png"
    SCHEMA = ClusterDistributionSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Float, Integer],
        "allowed_dtypes": [],
        "input_cardinality": {"min": 1},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the ClusterDistributionExplorer.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments. Recognized keys:
            plot_type (str, optional): ``"violin"`` for violin plots with
            embedded box and mean line, or ``"box"`` for standard box plots.
            Defaults to ``"violin"``.
        """
        self.plot_type: str = kwargs.get("plot_type", "violin")
        super().__init__(**kwargs)

    def prepare_dataset(
        self, loaded_dataset: "DashAIDataset", columns: List[Dict[str, Any]]
    ) -> "DashAIDataset":
        """Extend column selection to include the cluster label column.

        Reads the cluster column name from the converter report and appends
        it to the selection if not already present, so that
        ``launch_exploration`` can group samples by cluster.

        Parameters
        ----------
        loaded_dataset : DashAIDataset
            The full dataset.
        columns : List[Dict[str, Any]]
            Explicitly selected column descriptors (numeric features only).

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
        """Build violin or box plot subplots for each selected feature.

        Creates one subplot per selected numeric feature. Within each subplot,
        each cluster is shown as a separate violin or box, sorted numerically
        with noise points last. The legend is shown once (on the first subplot)
        and shared across all subplots via ``legendgroup``.

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
            A multi-subplot figure with one panel per selected feature.

        Raises
        ------
        ValueError
            If no numeric feature columns remain after excluding the cluster
            label column.
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        cr = self.context.get("converter_report", {})
        cluster_column = cr.get("cluster_column", "cluster")
        algorithm = cr.get("algorithm", "unknown")

        data = dataset.to_pandas()
        feature_cols = [
            c["columnName"]
            for c in explorer_info.columns
            if c["columnName"] != cluster_column
        ]

        if not feature_cols:
            raise ValueError("At least one numeric feature column must be selected.")

        data[cluster_column] = data[cluster_column].astype(str).replace({"-1": "Noise"})

        # Sort clusters numerically, place Noise last
        unique_clusters = sorted(
            data[cluster_column].unique(),
            key=lambda x: (x == "Noise", int(x) if x != "Noise" else 0),
        )

        cluster_color = {
            c: (
                _CLUSTER_COLORS[i % len(_CLUSTER_COLORS)] if c != "Noise" else "#AAAAAA"
            )
            for i, c in enumerate(c for c in unique_clusters if c != "Noise")
        }
        cluster_color["Noise"] = "#AAAAAA"

        n_features = len(feature_cols)
        fig = make_subplots(
            rows=n_features,
            cols=1,
            subplot_titles=feature_cols,
            shared_xaxes=False,
            vertical_spacing=max(0.03, 0.15 / n_features),
        )

        for row_idx, feature in enumerate(feature_cols, start=1):
            for cluster_label in unique_clusters:
                mask = data[cluster_column] == cluster_label
                values = data.loc[mask, feature].dropna()
                color = cluster_color.get(cluster_label, "#888888")
                show_legend = row_idx == 1

                if self.plot_type == "violin":
                    trace: Any = go.Violin(
                        y=values,
                        name=cluster_label,
                        legendgroup=cluster_label,
                        showlegend=show_legend,
                        box_visible=True,
                        meanline_visible=True,
                        line_color=color,
                        fillcolor=color,
                        opacity=0.7,
                    )
                else:
                    trace = go.Box(
                        y=values,
                        name=cluster_label,
                        legendgroup=cluster_label,
                        showlegend=show_legend,
                        marker_color=color,
                        boxmean=True,
                    )

                fig.add_trace(trace, row=row_idx, col=1)

        title = (
            explorer_info.name
            if explorer_info.name
            else f"Feature Distribution by Cluster — {algorithm}"
        )
        layout_kwargs: Dict[str, Any] = {
            "title": title,
            "height": max(350, 280 * n_features),
        }
        if self.plot_type == "violin":
            layout_kwargs["violinmode"] = "group"
        else:
            layout_kwargs["boxmode"] = "group"

        fig.update_layout(**layout_kwargs)

        return fig

    def save_notebook(
        self,
        __notebook_info__: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Save the distribution figure to disk as a JSON file.

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
        """Load the saved distribution figure and return it for the frontend.

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
