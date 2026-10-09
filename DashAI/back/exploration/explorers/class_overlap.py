from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.schema_fields import (
    int_field,
    none_type,
    schema_field,
    string_field,
    union_type,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import (
    NON_NUMERIC_DTYPES,
    BaseExplorerSchema,
)
from DashAI.back.exploration.complexity_measures import (
    DEFAULT_MAX_SAMPLES,
    compute_class_overlap,
)
from DashAI.back.exploration.data_complexity_explorer import DataComplexityExplorer
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

# A target with more distinct values than this is almost certainly continuous,
# and the measures are only defined for discrete classes.
MAX_CLASSES = 50


class ClassOverlapExplorerSchema(BaseExplorerSchema):
    """Schema for ClassOverlapExplorer configuration.

    ``target_column`` names the column holding the class labels; it is
    mandatory, since the measures are supervised. The remaining selected
    columns are treated as the numeric features that describe each point.

    N1 and N2 both need a pairwise distance matrix, which grows with the square
    of the sample. ``max_samples`` caps the number of rows used for those two
    measures, drawing a class-proportional subsample when the dataset is
    larger; ``random_state`` makes that draw reproducible. F1 is linear in the
    sample and always uses every available row.
    """

    target_column: schema_field(
        union_type(string_field(), int_field(ge=0)),
        "",
        description=MultilingualString(
            en=(
                "Required. Name or index of the column holding the class "
                "labels. It is added to the exploration automatically, so it "
                "does not need to be selected as a column."
            ),
            es=(
                "Obligatorio. Nombre o índice de la columna que contiene las "
                "clases. Se agrega a la exploración automáticamente, así que "
                "no hace falta seleccionarla como columna."
            ),
            pt=(
                "Obrigatório. Nome ou índice da coluna que contém as classes. "
                "É adicionada à exploração automaticamente, portanto não "
                "precisa ser selecionada como coluna."
            ),
            de=(
                "Erforderlich. Name oder Index der Spalte mit den "
                "Klassenbezeichnungen. Sie wird der Exploration automatisch "
                "hinzugefügt und muss nicht als Spalte ausgewählt werden."
            ),
            zh=("必填。包含类别标签的列名或索引。该列会自动加入探索，无需作为列选中。"),
        ),
        alias=MultilingualString(
            en="Target column",
            es="Columna objetivo",
            pt="Coluna alvo",
            de="Zielspalte",
            zh="目标列",
        ),
    )  # type: ignore
    max_samples: schema_field(
        int_field(gt=1),
        DEFAULT_MAX_SAMPLES,
        description=MultilingualString(
            en=(
                "Maximum number of rows used for the distance-based measures "
                "N1 and N2. Larger datasets are subsampled keeping the class "
                "proportions."
            ),
            es=(
                "Número máximo de filas usadas en las medidas basadas en "
                "distancia N1 y N2. Los datasets más grandes se submuestrean "
                "manteniendo las proporciones de clase."
            ),
            pt=(
                "Número máximo de linhas usadas nas medidas baseadas em "
                "distância N1 e N2. Conjuntos maiores são subamostrados "
                "mantendo as proporções das classes."
            ),
            de=(
                "Maximale Anzahl Zeilen für die distanzbasierten Maße N1 und "
                "N2. Größere Datensätze werden unter Beibehaltung der "
                "Klassenanteile unterabgetastet."
            ),
            zh="用于基于距离的度量N1和N2的最大行数。更大的数据集将按类别比例进行子采样。",
        ),
        alias=MultilingualString(
            en="Maximum samples",
            es="Muestras máximas",
            pt="Amostras máximas",
            de="Maximale Stichproben",
            zh="最大样本数",
        ),
    )  # type: ignore
    random_state: schema_field(
        none_type(int_field(ge=0)),
        0,
        description=MultilingualString(
            en=("Seed used when the dataset has to be subsampled."),
            es=("Semilla usada cuando el dataset debe ser submuestreado."),
            pt=("Semente usada quando o conjunto precisa ser subamostrado."),
            de=("Startwert für die Unterabtastung des Datensatzes."),
            zh="数据集需要子采样时使用的随机种子。",
        ),
        alias=MultilingualString(
            en="Random state",
            es="Semilla aleatoria",
            pt="Semente aleatória",
            de="Zufallsstartwert",
            zh="随机种子",
        ),
    )  # type: ignore


class ClassOverlapExplorer(DataComplexityExplorer):
    """Explorer that measures how much the classes of a dataset overlap.

    It reports three of the geometrical complexity measures surveyed in Lorena
    et al. (2019), computed from the data alone, with no model involved:

    ``F1``
        Maximum Fisher discriminant ratio. Near 0 when at least one feature
        separates the classes on its own, near 1 when none does.
    ``N1``
        Fraction of points sitting on a class boundary, taken from a minimum
        spanning tree over the sample. A large value means a long, populated
        frontier between classes.
    ``N2``
        Ratio between the distance to the nearest same-class neighbour and the
        distance to the nearest different-class neighbour. A large value means
        the classes interleave rather than forming compact groups.

    All three are normalised so that **lower means easier to separate**.

    Use this explorer before training to tell an unpromising dataset from an
    unpromising model: if the classes already overlap heavily, a disappointing
    accuracy is a property of the data rather than of the learner, and the
    useful next step is feature engineering or relabelling rather than model
    search.
    """

    DISPLAY_NAME = MultilingualString(
        en="Class Overlap",
        es="Solapamiento de Clases",
        pt="Sobreposição de Classes",
        de="Klassenüberlappung",
        zh="类别重叠",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Measures how much the classes overlap using the F1, N1 and N2 "
            "complexity measures. Lower values mean the classes are easier to "
            "separate. No model is trained."
        ),
        es=(
            "Mide cuánto se solapan las clases usando las medidas de "
            "complejidad F1, N1 y N2. Valores más bajos indican clases más "
            "fáciles de separar. No se entrena ningún modelo."
        ),
        pt=(
            "Mede o quanto as classes se sobrepõem usando as medidas de "
            "complexidade F1, N1 e N2. Valores menores indicam classes mais "
            "fáceis de separar. Nenhum modelo é treinado."
        ),
        de=(
            "Misst die Überlappung der Klassen mit den Komplexitätsmaßen F1, "
            "N1 und N2. Niedrigere Werte bedeuten leichter trennbare Klassen. "
            "Es wird kein Modell trainiert."
        ),
        zh=(
            "使用F1、N1和N2复杂度度量衡量类别重叠程度。数值越低表示类别越容易分离。"
            "不训练任何模型。"
        ),
    )

    SCHEMA = ClassOverlapExplorerSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Float, Integer, Categorical],
        "allowed_dtypes": [],
        "non_allowed_dtypes": NON_NUMERIC_DTYPES,
        "input_cardinality": {"min": 1},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize ClassOverlapExplorer with its measurement parameters.

        Parameters
        ----------
        **kwargs
            Keyword arguments matching ``ClassOverlapExplorerSchema`` fields:
            target_column (str | int): Name or index of the label column.
            max_samples (int): Row budget for the distance-based measures.
            random_state (int | None): Seed used when subsampling.
        """
        self.target_column = kwargs.get("target_column")
        self.max_samples = kwargs.get("max_samples", DEFAULT_MAX_SAMPLES)
        self.random_state = kwargs.get("random_state")
        super().__init__(**kwargs)

    def prepare_dataset(
        self, loaded_dataset: "DashAIDataset", columns: List[Dict[str, Any]]
    ) -> "DashAIDataset":
        """Extend column selection to include the target column.

        The target is configured through the schema rather than picked as one
        of the explored columns, so it has to be appended to the selection
        before the dataset is narrowed down.

        Parameters
        ----------
        loaded_dataset : DashAIDataset
            The full dataset.
        columns : List[Dict[str, Any]]
            Explicitly selected column descriptors.

        Returns
        -------
        DashAIDataset
            Dataset containing the selected feature columns plus the target.

        Raises
        ------
        ValueError
            If no target column was configured.
        """
        if self.target_column is None or self.target_column == "":
            raise ValueError(
                "A target column is required to measure class overlap. Set it "
                "in the explorer parameters to the name or index of the column "
                "holding the class labels."
            )

        explorer_columns = [col["columnName"] for col in columns]
        dataset_columns = loaded_dataset.column_names

        if isinstance(self.target_column, int):
            index = self.target_column
            if index >= len(dataset_columns):
                raise ValueError(
                    f"Target column index {index} is out of range for a "
                    f"dataset with {len(dataset_columns)} columns."
                )
            name = dataset_columns[index]
            if name not in explorer_columns:
                columns.append({"id": index, "columnName": name})
        else:
            name = self.target_column
            if name not in dataset_columns:
                raise ValueError(f"Target column '{name}' is not in the dataset.")
            if name not in explorer_columns:
                columns.append({"columnName": name})

        self.target_column = name
        return super().prepare_dataset(loaded_dataset, columns)

    def launch_exploration(
        self, dataset: "DashAIDataset", __explorer_info__: Explorer
    ) -> Any:
        """Compute the complexity measures and lay them out as a table.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset holding the feature columns and the target column.
        __explorer_info__ : Explorer
            The explorer database record (unused).

        Returns
        -------
        Any
            A ``pandas.DataFrame`` indexed by row label, with a ``"value"``
            column and a ``"detail"`` column describing each entry.

        Raises
        ------
        ValueError
            If the target is missing, holds too many distinct values to be a
            class label, or leaves no numeric feature column behind.
        """
        import pandas as pd

        frame = dataset.to_pandas()

        if self.target_column not in frame.columns:
            raise ValueError(
                f"Target column '{self.target_column}' is not in the prepared dataset."
            )

        labels = frame[self.target_column]
        distinct = labels.nunique(dropna=True)
        if distinct > MAX_CLASSES:
            raise ValueError(
                f"The target column '{self.target_column}' has {distinct} "
                f"distinct values, which exceeds the limit of {MAX_CLASSES}. "
                "These measures apply to classification targets, so the target "
                "should be the column holding the class labels, not a feature. "
                "Note that an index refers to the position of the column in "
                "the dataset, not among the columns selected for the explorer."
            )

        features = frame.drop(columns=[self.target_column])
        features = features.select_dtypes(include="number")
        if features.shape[1] == 0:
            raise ValueError(
                "No numeric feature column is left after removing the target. "
                "The distance-based measures need numeric features."
            )

        summary = compute_class_overlap(
            features.to_numpy(),
            labels.to_numpy(),
            max_samples=self.max_samples,
            random_state=self.random_state,
        )

        rows = [
            (
                "F1",
                round(summary["measures"]["F1"], 6),
                "Maximum Fisher discriminant ratio. Lower is easier.",
            ),
            (
                "N1",
                round(summary["measures"]["N1"], 6),
                "Fraction of points on a class boundary. Lower is easier.",
            ),
            (
                "N2",
                round(summary["measures"]["N2"], 6),
                "Intra over extra class nearest neighbour ratio. Lower is easier.",
            ),
            ("Samples", summary["n_samples"], "Rows kept after dropping missing."),
            ("Features", summary["n_features"], "Numeric feature columns used."),
            ("Classes", summary["n_classes"], "Distinct labels in the target."),
            (
                "Rows dropped",
                summary["n_dropped_rows"],
                "Rows removed for holding a missing value.",
            ),
            (
                "Samples for N1 and N2",
                summary["n_samples_used_for_distances"],
                "Rows used by the distance-based measures.",
            ),
        ]

        # The column holds both measures and counts. Building it as object
        # keeps the counts as integers; a plain numeric column would upcast
        # them and render "10000.0" beside the measures.
        return pd.DataFrame(
            {
                "value": pd.Series(
                    [value for _, value, _ in rows],
                    index=[name for name, _, _ in rows],
                    dtype=object,
                ),
                "detail": [detail for _, _, detail in rows],
            }
        )

    def save_notebook(
        self,
        __notebook_info__: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Save the measures table to a JSON file on disk.

        Parameters
        ----------
        __notebook_info__ : Notebook
            The notebook database record (unused).
        explorer_info : Explorer
            The explorer record used for filename generation.
        save_path : Path
            Directory where the file will be saved.
        result : Any
            The ``pandas.DataFrame`` returned by ``launch_exploration``.

        Returns
        -------
        str
            The path of the saved JSON file as a POSIX string.
        """
        import os
        from pathlib import Path

        import pandas as pd

        filename = f"{explorer_info.id}.json"
        path = Path(os.path.join(save_path, filename))

        assert isinstance(result, pd.DataFrame)
        result.to_json(path)
        return path.as_posix()

    def get_results(
        self, exploration_path: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Load and return the saved measures table for the frontend.

        Parameters
        ----------
        exploration_path : str
            Path to the JSON file saved by ``save_notebook``.
        options : Dict[str, Any]
            Rendering options from the frontend (unused).

        Returns
        -------
        Dict[str, Any]
            Dictionary with keys ``"data"`` (nested dict of the table, keyed by
            column then row, which is the orientation the artifact conversion
            expects), ``"type"`` (``"tabular"``) and ``"config"``.
        """
        import json

        # Read with json rather than pandas. The table mixes measures with
        # counts in one column, and pandas would coerce the whole column to
        # float, turning a sample count of 10000 into 10000.0. The file on
        # disk already carries the right types.
        with open(exploration_path, "r", encoding="utf-8") as file:
            columns = json.load(file)

        return {"type": "tabular", "data": columns, "config": {"orient": "dict"}}
