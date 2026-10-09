from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.artifacts import (
    Artifact,
    PlotlyArtifact,
    TableArtifact,
    TablePayload,
)
from DashAI.back.core.schema_fields import (
    bool_field,
    enum_field,
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


class Method(Enum):
    pearson = "pearson"
    kendall = "kendall"
    spearman = "spearman"


class CorrelationMatrixExplorerSchema(BaseExplorerSchema):
    """Schema for CorrelationMatrixExplorer configuration.

    Controls the statistical method used to compute pairwise correlations, the
    minimum number of complete observations required per column pair, and
    whether the result is displayed as a heatmap or returned as a raw table.

    The ``method`` field selects between three estimators: ``"pearson"``
    measures linear association and assumes approximately normal distributions;
    ``"spearman"`` measures monotonic association using rank-transformed data
    and is more robust to nonlinear relationships and outliers; ``"kendall"``
    uses concordance/discordance counts and is preferred for small samples or
    heavily tied data.  Use ``"numeric_only"`` to exclude non-numeric columns
    from the calculation automatically.
    """

    method: schema_field(
        enum_field([e.value for e in Method]),
        Method.pearson.value,
        description=MultilingualString(
            en=("Correlation method to use: 'pearson', 'kendall', or 'spearman'."),
            es=("Método de correlación a usar: 'pearson', 'kendall' o 'spearman'."),
            pt=("Método de correlação a usar: 'pearson', 'kendall' ou 'spearman'."),
            de=("Korrelationsmethode: 'pearson', 'kendall' oder 'spearman'."),
            zh="使用的相关性方法：'pearson'、'kendall'或'spearman'。",
        ),
        alias=MultilingualString(
            en="Correlation method",
            es="Método de correlación",
            pt="Método de correlação",
            de="Korrelationsmethode",
            zh="相关性方法",
        ),
    )  # type: ignore
    min_periods: schema_field(
        int_field(gt=0),
        1,
        description=MultilingualString(
            en=(
                "Minimum observations required per column pair to have a valid "
                "result. Used only with 'pearson' or 'spearman'."
            ),
            es=(
                "Número mínimo de observaciones requeridas por par de columnas "
                "para obtener un resultado válido. Solo con 'pearson' o "
                "'spearman'."
            ),
            pt=(
                "Número mínimo de observações requeridas por par de colunas "
                "para obter um resultado válido. Usado apenas com 'pearson' ou "
                "'spearman'."
            ),
            de=(
                "Mindestanzahl der Beobachtungen pro Spaltenpaar für ein gültiges "
                "Ergebnis. Nur mit 'pearson' oder 'spearman' verwendet."
            ),
            zh="每列对获得有效结果所需的最小观测数。仅用于'pearson'或'spearman'。",
        ),
        alias=MultilingualString(
            en="Minimum periods",
            es="Períodos mínimos",
            pt="Períodos mínimos",
            de="Mindestperioden",
            zh="最小周期数",
        ),
    )  # type: ignore
    numeric_only: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en=(
                "If True, include only numeric columns when calculating "
                "correlation; otherwise include all columns."
            ),
            es=(
                "Si es True, incluye solo columnas numéricas al calcular la "
                "correlación; de lo contrario incluye todas."
            ),
            pt=(
                "Se True, inclui apenas colunas numéricas ao calcular a "
                "correlação; caso contrário, inclui todas."
            ),
            de=(
                "Wenn True, werden nur numerische Spalten bei der Berechnung "
                "der Korrelation berücksichtigt; sonst alle Spalten."
            ),
            zh="如果为True，计算相关性时仅包含数值列；否则包含所有列。",
        ),
        alias=MultilingualString(
            en="Numeric only",
            es="Solo numéricas",
            pt="Somente numéricas",
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
            pt=("Se True, o resultado será graficado."),
            de=("Wenn True, wird das Ergebnis dargestellt."),
            zh="如果为True，结果将以图表显示。",
        ),
        alias=MultilingualString(
            en="Plot result",
            es="Graficar resultado",
            pt="Graficar resultado",
            de="Ergebnis darstellen",
            zh="绘制结果",
        ),
    )  # type: ignore


class CorrelationMatrixExplorer(StatisticalExplorer):
    """Explorer that computes and visualises pairwise correlation coefficients.

    A correlation matrix contains one coefficient for every pair of selected
    columns.  Each coefficient ranges from -1 to +1: values near +1 indicate a
    strong positive relationship, values near -1 indicate a strong negative
    relationship, and values near 0 indicate little or no linear (or monotonic)
    association.

    By default the result is rendered as an annotated heatmap where warm colours
    represent high positive correlation and cool colours represent high negative
    correlation, making it easy to scan for strongly related feature pairs at a
    glance.  Setting ``plot=False`` returns the raw correlation DataFrame instead,
    which is useful for downstream numerical analysis.

    Use this explorer to detect multicollinearity between features before
    modelling, to identify the features most correlated with a target variable,
    or to understand the overall dependency structure of a dataset.
    """

    DISPLAY_NAME = MultilingualString(
        en="Correlation Matrix",
        es="Matriz de Correlación",
        pt="Matriz de Correlação",
        de="Korrelationsmatrix",
        zh="相关性矩阵",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Returns the correlation matrix of the dataset. The default output is "
            "a heatmap, but a tabular result can also be returned."
        ),
        es=(
            "Devuelve la matriz de correlación del dataset. Por defecto se "
            "muestra como mapa de calor, pero también puede retornarse en "
            "formato tabular."
        ),
        pt=(
            "Retorna a matriz de correlação do conjunto de dados. A saída "
            "padrão é um mapa de calor, mas também pode ser retornada em "
            "formato tabular."
        ),
        de=(
            "Gibt die Korrelationsmatrix des Datensatzes zurück. Die "
            "Standardausgabe ist eine Heatmap, aber es kann auch ein "
            "tabellarisches Ergebnis zurückgegeben werden."
        ),
        zh="返回数据集的相关性矩阵。默认输出为热图，也可返回表格形式。",
    )
    IMAGE_PREVIEW = "correlation_matrix.png"

    SCHEMA = CorrelationMatrixExplorerSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Float, Integer, Categorical],
        "allowed_dtypes": [],
        "non_allowed_dtypes": NON_NUMERIC_DTYPES,
        "input_cardinality": {"min": 2},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize CorrelationMatrixExplorer with correlation parameters.

        Parameters
        ----------
        **kwargs
            Keyword arguments matching
            ``CorrelationMatrixExplorerSchema`` fields:
            method (str): Correlation method, one of ``"pearson"``,
            ``"kendall"``, or ``"spearman"``.
            min_periods (int): Minimum observations required per column
            pair. Applied only for ``"pearson"`` and ``"spearman"``.
            numeric_only (bool): Whether to restrict calculation to
            numeric columns.
            plot (bool): Whether to render the result as a Plotly heatmap.
            When ``False`` the raw correlation DataFrame is returned.
        """
        self.method = kwargs.get("method")
        self.min_periods = kwargs.get("min_periods")
        self.numeric_only = kwargs.get("numeric_only")
        self.plot = kwargs.get("plot")
        super().__init__(**kwargs)

    def launch_exploration(
        self, dataset: "DashAIDataset", explorer_info: Explorer
    ) -> Any:
        """Compute a correlation matrix and optionally render it as a Plotly heatmap.

        Converts the dataset to a pandas DataFrame, computes pairwise column
        correlations using the configured method, and, when ``self.plot`` is
        ``True``, wraps the result in a Plotly ``imshow`` heatmap figure.

        Parameters
        ----------
        dataset : DashAIDataset
            The dataset whose columns will be
            correlated.
        explorer_info : Explorer
            The explorer database record used for
            the plot title and column count.

        Returns
        -------
        Any
            A ``plotly.graph_objs.Figure`` heatmap when ``self.plot`` is
            ``True``, or a ``pandas.DataFrame`` containing the correlation
            matrix when ``self.plot`` is ``False``.
        """
        import plotly.express as px

        result = dataset.to_pandas().corr(
            method=self.method,
            min_periods=(
                self.min_periods
                if self.method in [Method.pearson.value, Method.spearman.value]
                else None
            ),
            numeric_only=self.numeric_only,
        )

        if self.plot:
            result = px.imshow(
                result.round(4),
                text_auto=".4~f",
                aspect="auto",
                title=f"Correlation Matrix of {len(explorer_info.columns)} columns",
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
        """Save the correlation result to a JSON file on disk.

        When ``self.plot`` is ``True``, writes the Plotly figure as JSON using
        ``Figure.write_json``; otherwise writes the correlation DataFrame using
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
        import plotly.graph_objs as go

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
        """Load and return the saved correlation result for the frontend.

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
            correlation matrix otherwise.
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
