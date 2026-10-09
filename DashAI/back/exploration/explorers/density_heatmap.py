from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.artifacts import Artifact, PlotlyArtifact
from DashAI.back.core.schema_fields import int_field, none_type, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.relationship_explorer import RelationshipExplorer
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class DensityHeatmapSchema(BaseExplorerSchema):
    """Schema for DensityHeatmapExplorer configuration.

    Controls the binning resolution of the 2-D density grid.  ``nbinsx`` sets
    the number of bins along the x-axis and ``nbinsy`` sets the number along the
    y-axis.  Leaving either value as ``None`` lets Plotly choose an automatic
    bin count based on the data range.  Increasing the bin count reveals finer
    detail in the joint distribution at the cost of sparser (noisier) bins when
    data are limited; decreasing it gives a smoother but coarser picture.
    """

    nbinsx: schema_field(
        none_type(int_field(ge=1)),
        None,
        description=MultilingualString(
            en=("Number of bins along the x axis."),
            es=("Número de bins a lo largo del eje x."),
            pt=("Número de bins ao longo do eixo x."),
            de=("Anzahl der Klassen entlang der x-Achse."),
            zh="沿x轴的分箱数量。",
        ),
        alias=MultilingualString(
            en="Bins (x)", es="Bins (x)", pt="Bins (x)", de="Klassen (x)", zh="分箱(x)"
        ),
    )  # type: ignore
    nbinsy: schema_field(
        none_type(int_field(ge=1)),
        None,
        description=MultilingualString(
            en=("Number of bins along the y axis."),
            es=("Número de bins a lo largo del eje y."),
            pt=("Número de bins ao longo do eixo y."),
            de=("Anzahl der Klassen entlang der y-Achse."),
            zh="沿y轴的分箱数量。",
        ),
        alias=MultilingualString(
            en="Bins (y)", es="Bins (y)", pt="Bins (y)", de="Klassen (y)", zh="分箱(y)"
        ),
    )  # type: ignore


class DensityHeatmapExplorer(RelationshipExplorer):
    """Explorer that visualises the joint distribution of two columns as a 2-D heatmap.

    The explorer partitions the value range of each selected column into a
    regular grid of rectangular bins and colours each cell according to the count
    of data points that fall inside it.  Darker or warmer colours (depending on
    the colour scale) indicate regions of higher data density, making it easy to
    identify modes, concentration areas, and gaps in the joint distribution of
    the two variables.

    This visualisation is especially useful when there are too many data points
    for a scatter plot to remain legible.  It provides a non-parametric estimate
    of the joint density and reveals whether the relationship between the two
    columns is concentrated around a single peak, multimodal, or approximately
    uniform.

    Exactly two columns must be selected: the first maps to the x-axis and the
    second to the y-axis.
    """

    DISPLAY_NAME = MultilingualString(
        en="Density Heatmap",
        es="Mapa de Calor de Densidad",
        pt="Mapa de Calor de Densidade",
        de="Dichte-Heatmap",
        zh="密度热图",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Returns a density heatmap for two selected columns to visualize the "
            "joint distribution."
        ),
        es=(
            "Devuelve un mapa de calor de densidad para dos columnas "
            "seleccionadas y visualizar su distribución conjunta."
        ),
        pt=(
            "Retorna um mapa de calor de densidade para duas colunas "
            "selecionadas para visualizar a distribuição conjunta."
        ),
        de=(
            "Gibt eine Dichte-Heatmap für zwei ausgewählte Spalten zurück, um "
            "die gemeinsame Verteilung zu visualisieren."
        ),
        zh="返回两个所选列的密度热图，以可视化联合分布。",
    )
    IMAGE_PREVIEW = "density_heatmap.png"

    SCHEMA = DensityHeatmapSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Float, Integer, Categorical],
        "allowed_dtypes": [],
        "input_cardinality": {"exact": 2},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the DensityHeatmapExplorer with optional bin counts.

        Parameters
        ----------
        **kwargs
            Configuration keyword arguments. Recognized keys:
            nbinsx (int, optional): Number of bins along the x axis.
            Defaults to None (auto).
            nbinsy (int, optional): Number of bins along the y axis.
            Defaults to None (auto).
        """
        self.nbinsx = kwargs.get("nbinsx")
        self.nbinsy = kwargs.get("nbinsy")
        super().__init__(**kwargs)

    def launch_exploration(self, dataset: "DashAIDataset", explorer_info: Explorer):
        """Generate a Plotly density heatmap for two selected columns.

        Parameters
        ----------
        dataset : DashAIDataset
            The prepared dataset with exactly two columns.
        explorer_info : Explorer
            Explorer record with column names and optional
            display name.

        Returns
        -------
        plotly.graph_objects.Figure
            An interactive density heatmap figure.
        """
        import plotly.express as px

        _df = dataset.to_pandas()
        columns = [col["columnName"] for col in explorer_info.columns]

        fig = px.density_heatmap(
            _df,
            x=columns[0],
            y=columns[1],
            nbinsx=self.nbinsx,
            nbinsy=self.nbinsy,
            title=f"Density Heatmap of {columns[0]} and {columns[1]}",
        )

        if explorer_info.name is not None and explorer_info.name != "":
            fig.update_layout(title=f"{explorer_info.name}")

        return fig

    def save_notebook(
        self,
        __notebook_info__: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Save the density heatmap figure to a JSON file on disk.

        Parameters
        ----------
        __notebook_info__ : Notebook
            The notebook database record (unused).
        explorer_info : Explorer
            The explorer record used for filename generation.
        save_path : Path
            Directory where the file will be saved.
        result : Any
            The Plotly figure returned by `launch_exploration`.

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
    ) -> List[Artifact]:
        """Load and return the saved density heatmap for the frontend.

        Parameters
        ----------
        exploration_path : str
            Path to the JSON file saved by `save_notebook`.
        options : Dict[str, Any]
            Rendering options from the frontend (unused).

        Returns
        -------
        List[Artifact]
            A single-element list with the plotly artifact of the saved
            figure.
        """
        with open(exploration_path, "r", encoding="utf-8") as f:
            result = f.read()

        return [PlotlyArtifact(payload=result)]
