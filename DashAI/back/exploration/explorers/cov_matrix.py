from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.artifacts import (
    Artifact,
    PlotlyArtifact,
    TableArtifact,
    TablePayload,
)
from DashAI.back.core.schema_fields import (
    F,
    IsTrue,
    Relevance,
    bool_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import (
    NON_NUMERIC_DTYPES,
    BaseExplorerSchema,
)
from DashAI.back.exploration.statistical_explorer import StatisticalExplorer
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class CovarianceMatrixExplorerSchema(BaseExplorerSchema):
    """Schema for CovarianceMatrixExplorer configuration.

    Provides fine-grained control over the covariance calculation.
    ``min_periods`` sets the minimum number of non-missing observations that
    must be present for a column pair to receive a valid result rather than
    NaN.  ``delta_degree_of_freedom`` (ddof) adjusts the denominator of the
    estimator: ddof=1 gives the unbiased sample covariance, while ddof=0 gives
    the population covariance.  ``numeric_only`` restricts the calculation to
    numeric columns, and ``plot`` controls whether the result is displayed as
    an annotated heatmap or returned as a raw table.
    """

    min_periods: schema_field(
        int_field(gt=0),
        1,
        description=MultilingualString(
            en=(
                "Minimum observations required per column pair to have a valid result."
            ),
            es=(
                "Número mínimo de observaciones requeridas por par de columnas "
                "para obtener un resultado válido."
            ),
            pt=(
                "Número mínimo de observações requeridas por par de colunas "
                "para obter um resultado válido."
            ),
            de=(
                "Mindestanzahl der Beobachtungen pro Spaltenpaar für ein "
                "gültiges Ergebnis."
            ),
            zh="每列对获得有效结果所需的最小观测数。",
        ),
        alias=MultilingualString(
            en="Minimum periods",
            es="Períodos mínimos",
            pt="Períodos mínimos",
            de="Mindestperioden",
            zh="最小周期数",
        ),
    )  # type: ignore
    delta_degree_of_freedom: schema_field(
        int_field(gt=0),
        1,
        description=MultilingualString(
            # The "only used if numeric_only is True" sentence is the Relevance
            # rule at the end of this class now.
            en=(
                "Delta degrees of freedom to use when calculating the covariance "
                "matrix."
            ),
            es=("Grados de libertad delta a usar al calcular la matriz de covarianza."),
            pt=("Graus de liberdade delta a usar ao calcular a matriz de covariância."),
            de="Delta-Freiheitsgrade zur Berechnung der Kovarianzmatrix.",
            zh="计算协方差矩阵时使用的自由度delta。",
        ),
        alias=MultilingualString(
            en="Delta degrees of freedom",
            es="Grados de libertad delta",
            pt="Graus de liberdade delta",
            de="Delta-Freiheitsgrade",
            zh="自由度delta",
        ),
    )  # type: ignore
    numeric_only: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en=(
                "If True, include only numeric columns in the calculation; "
                "otherwise include all columns."
            ),
            es=(
                "Si es True, incluye solo columnas numéricas en el cálculo; de "
                "lo contrario incluye todas las columnas."
            ),
            pt=(
                "Se True, inclui apenas colunas numéricas no cálculo; "
                "caso contrário inclui todas as colunas."
            ),
            de=(
                "Wenn True, werden nur numerische Spalten in die Berechnung "
                "einbezogen; sonst alle Spalten."
            ),
            zh="如果为True，计算中仅包含数值列；否则包含所有列。",
        ),
        alias=MultilingualString(
            en="Numeric only",
            es="Solo numéricas",
            pt="Apenas numéricas",
            de="Nur numerisch",
            zh="仅数值列",
        ),
    )  # type: ignore
    plot: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en=("If True, the result will be plotted."),
            es=("Si es True, el resultado será graficado."),
            pt=("Se True, o resultado será plotado."),
            de=("Wenn True, wird das Ergebnis dargestellt."),
            zh="如果为True，结果将以图表显示。",
        ),
        alias=MultilingualString(
            en="Plot result",
            es="Graficar resultado",
            pt="Plotar resultado",
            de="Ergebnis darstellen",
            zh="绘制结果",
        ),
    )  # type: ignore

    # The delta degrees of freedom only apply to the numeric path. Declared
    # here rather than as a field_validator because the two fields are in the
    # wrong order for one: delta_degree_of_freedom is declared 30 lines above
    # numeric_only, and a field_validator reading info.data would find its
    # controller absent and silently do nothing. A rule runs on the complete
    # model, so declaration order cannot disable it.
    rules = [
        Relevance(
            "delta_degree_of_freedom",
            when=IsTrue(F("numeric_only")),
            effect="disable",
            reason=MultilingualString(
                en=(
                    "The delta degrees of freedom are only used when the "
                    "calculation is restricted to numeric columns."
                ),
                es=(
                    "Los grados de libertad delta solo se usan cuando el "
                    "cálculo se restringe a columnas numéricas."
                ),
                pt=(
                    "Os graus de liberdade delta só são usados quando o "
                    "cálculo é restrito a colunas numéricas."
                ),
                de=(
                    "Die Delta-Freiheitsgrade werden nur verwendet, wenn die "
                    "Berechnung auf numerische Spalten beschränkt ist."
                ),
                zh="自由度delta仅在计算限制为数值列时使用。",
            ),
        ),
    ]


class CovarianceMatrixExplorer(StatisticalExplorer):
    """Explorer that computes and visualises the pairwise covariance matrix.

    Unlike the correlation matrix, covariance values are not normalised to the
    [-1, 1] range, so they retain the original units of the features.  A large
    positive covariance between two columns means they tend to increase together,
    while a large negative covariance means they move in opposite directions.  The
    magnitude of each value depends on the scale and variance of the columns
    involved, making covariance useful for understanding the absolute spread and
    co-movement of features rather than just the direction of their relationship.

    By default the result is rendered as an annotated heatmap for quick visual
    inspection.  Setting ``plot=False`` returns the raw covariance DataFrame,
    which is appropriate for tasks such as constructing a regularised precision
    matrix or performing principal component analysis manually.

    Use this explorer when you need to understand the scale-sensitive relationships
    between features, or as a precursor to techniques that depend on the covariance
    structure of the data (e.g. PCA or Linear Discriminant Analysis).
    """

    DISPLAY_NAME = MultilingualString(
        en="Covariance Matrix",
        es="Matriz de Covarianza",
        pt="Matriz de Covariância",
        de="Kovarianzmatrix",
        zh="协方差矩阵",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Returns the covariance matrix of the dataset. The default output is "
            "a heatmap, but a tabular result can also be returned."
        ),
        es=(
            "Devuelve la matriz de covarianza del dataset. Por defecto se "
            "muestra como mapa de calor, pero también puede retornarse en "
            "formato tabular."
        ),
        pt=(
            "Retorna a matriz de covariância do conjunto de dados. O resultado "
            "padrão é um mapa de calor, mas também pode ser retornado em "
            "formato tabular."
        ),
        de=(
            "Gibt die Kovarianzmatrix des Datensatzes zurück. Die Standardausgabe "
            "ist eine Heatmap, aber es kann auch ein tabellarisches Ergebnis "
            "zurückgegeben werden."
        ),
        zh="返回数据集的协方差矩阵。默认输出为热图，也可返回表格形式。",
    )
    IMAGE_PREVIEW = "covariance_matrix.png"

    SCHEMA = CovarianceMatrixExplorerSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Float, Integer, Categorical],
        "allowed_dtypes": [],
        "non_allowed_dtypes": NON_NUMERIC_DTYPES,
        "input_cardinality": {"min": 2},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize CovarianceMatrixExplorer with covariance parameters.

        Parameters
        ----------
        **kwargs
            Keyword arguments matching
            ``CovarianceMatrixExplorerSchema`` fields:
            delta_degree_of_freedom (int): Delta degrees of freedom (ddof)
            used in the covariance calculation.
            min_periods (int): Minimum observations required per column
            pair to produce a valid result.
            numeric_only (bool): Whether to restrict the calculation to
            numeric columns only.
            plot (bool): Whether to render the result as a Plotly heatmap.
            When ``False`` the raw covariance DataFrame is returned.
        """
        self.ddof = kwargs.get("delta_degree_of_freedom")
        self.min_periods = kwargs.get("min_periods")
        self.numeric_only = kwargs.get("numeric_only")
        self.plot = kwargs.get("plot")
        super().__init__(**kwargs)

    def launch_exploration(
        self, dataset: "DashAIDataset", explorer_info: Explorer
    ) -> Any:
        """Compute a covariance matrix and optionally render it as a Plotly heatmap.

        Converts the dataset to a pandas DataFrame, computes pairwise column
        covariances, and, when ``self.plot`` is ``True``, wraps the result
        in a Plotly ``imshow`` heatmap figure.

        Parameters
        ----------
        dataset : DashAIDataset
            The dataset whose columns will be used
            for covariance computation.
        explorer_info : Explorer
            The explorer database record used for
            the plot title and column count.

        Returns
        -------
        Any
            A ``plotly.graph_objs.Figure`` heatmap when ``self.plot`` is
            ``True``, or a ``pandas.DataFrame`` containing the covariance
            matrix when ``self.plot`` is ``False``.
        """
        import plotly.express as px

        result = dataset.to_pandas().cov(
            min_periods=self.min_periods,
            ddof=self.ddof,
            numeric_only=self.numeric_only,
        )

        if self.plot:
            result = px.imshow(
                result,
                text_auto=True,
                aspect="auto",
                title=f"Covariance Matrix of {len(explorer_info.columns)} columns",
            )
            if explorer_info.name is not None and explorer_info.name != "":
                result.update_layout(title=f"{explorer_info.name}")

        return result

    def save_notebook(
        self,
        __notebook_info__: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Save the covariance result to a JSON file on disk.

        When ``self.plot`` is ``True``, writes the Plotly figure as JSON using
        ``Figure.write_json``; otherwise writes the covariance DataFrame using
        ``DataFrame.to_json``.

        Parameters
        ----------
        __notebook_info__ : Notebook
            The notebook database record (unused).
        explorer_info : Explorer
            The explorer record used for filename
            generation.
        save_path : Path
            Directory where the file will be saved.
        result : Any
            The result returned by ``launch_exploration``, either
            a ``plotly.graph_objs.Figure`` or a ``pandas.DataFrame``.

        Returns
        -------
        str
            The path of the saved JSON file as a POSIX string.
        """
        import os
        from pathlib import Path

        import pandas as pd
        import plotly.graph_objects as go

        filename = f"{explorer_info.id}.json"
        path = Path(os.path.join(save_path, filename))

        if self.plot:
            assert isinstance(result, go.Figure)
            result.write_json(path)
        else:
            assert isinstance(result, pd.DataFrame)
            result.to_json(path)
        return path.as_posix()

    def get_results(
        self, exploration_path: str, options: Dict[str, Any]
    ) -> List[Artifact]:
        """Load and return the saved covariance result for the frontend.

        When ``self.plot`` is ``True``, reads the raw Plotly JSON string from
        disk. Otherwise reads the JSON file as a pandas DataFrame, transposes
        it, and returns it as a table artifact with the column names in an
        index column.

        Parameters
        ----------
        exploration_path : str
            Path to the JSON file saved by ``save_notebook``.
        options : Dict[str, Any]
            Rendering options from the frontend (unused).

        Returns
        -------
        List[Artifact]
            A single-element list with the Plotly artifact of the heatmap
            when ``self.plot`` is ``True``, or the table artifact of the
            covariance matrix otherwise.
        """
        if self.plot:
            with open(exploration_path, "r", encoding="utf-8") as f:
                result = f.read()
            return [PlotlyArtifact(payload=result)]

        from pathlib import Path

        import numpy as np
        import pandas as pd

        matrix = pd.read_json(Path(exploration_path)).replace({np.nan: None}).T
        return [
            TableArtifact(
                payload=TablePayload(
                    columns=["index", *matrix.columns.astype(str)],
                    rows=[
                        [str(index), *row]
                        for index, row in zip(
                            matrix.index, matrix.to_numpy().tolist(), strict=True
                        )
                    ],
                )
            )
        ]
