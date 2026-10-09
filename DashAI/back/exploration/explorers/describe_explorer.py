from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.artifacts import Artifact, TableArtifact, TablePayload
from DashAI.back.core.schema_fields import (
    enum_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.preview_inspection_explorer import (
    PreviewInspectionExplorer,
)

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class DescribeExplorerSchema(BaseExplorerSchema):
    """Schema for DescribeExplorer configuration.

    Controls which statistics are computed and which columns are included.
    ``percentiles`` accepts a comma-separated list of integers between 0 and 100
    (e.g. ``"25, 50, 75"``); these are converted to fractional quantiles and
    inserted as additional rows in the output table alongside the fixed statistics.
    ``include`` restricts the summary to a particular dtype group (``"all"``,
    ``"number"``, ``"object"``, ``"category"``, or ``"datetime"``), while
    ``exclude`` removes a dtype group from consideration, mirroring the
    behaviour of ``pandas.DataFrame.describe``.
    """

    percentiles: schema_field(
        none_type(string_field()),
        "25, 50, 75",
        description=MultilingualString(
            en=(
                "Percentiles to include in the exploration. Use integers between "
                "0 and 100. Example: '25, 50, 75'"
            ),
            es=(
                "Percentiles a incluir en la exploración. Use enteros entre 0 y "
                "100. Ejemplo: '25, 50, 75'"
            ),
            pt=(
                "Percentis a incluir na exploração. Use inteiros entre 0 e "
                "100. Exemplo: '25, 50, 75'"
            ),
            zh="探索中包含的百分位数。使用0到100之间的整数。示例：'25, 50, 75'",
            de=(
                "Perzentile, die in die Exploration einbezogen werden. "
                "Verwenden Sie ganze Zahlen zwischen 0 und 100. Beispiel: '25, 50, 75'"
            ),
        ),
        alias=MultilingualString(
            en="Percentiles",
            es="Percentiles",
            pt="Percentis",
            zh="百分位数",
            de="Perzentile",
        ),
    )  # type: ignore
    include: schema_field(
        none_type(enum_field(["all", "number", "object", "category", "datetime"])),
        "all",
        description=MultilingualString(
            en=("Data types to include in the exploration."),
            es=("Tipos de datos a incluir en la exploración."),
            pt=("Tipos de dados a incluir na exploração."),
            zh="探索中包含的数据类型。",
            de="Datentypen, die in die Exploration einbezogen werden.",
        ),
        alias=MultilingualString(
            en="Include dtypes",
            es="Incluir tipos",
            pt="Incluir tipos",
            zh="包含数据类型",
            de="Typen einschließen",
        ),
    )  # type: ignore
    exclude: schema_field(
        none_type(enum_field(["object", "number", "category", "datetime"])),
        None,
        description=MultilingualString(
            en=("Data types to exclude from the exploration."),
            es=("Tipos de datos a excluir de la exploración."),
            pt=("Tipos de dados a excluir da exploração."),
            zh="探索中排除的数据类型。",
            de="Datentypen, die von der Exploration ausgeschlossen werden.",
        ),
        alias=MultilingualString(
            en="Exclude dtypes",
            es="Excluir tipos",
            pt="Excluir tipos",
            zh="排除数据类型",
            de="Typen ausschließen",
        ),
    )  # type: ignore


class DescribeExplorer(PreviewInspectionExplorer):
    """Explorer that generates a statistical summary table using pandas describe.

    For numeric columns the output includes: ``count`` (number of non-missing
    values), ``mean``, ``std`` (standard deviation), ``min``, the requested
    percentile rows (defaulting to 25 %, 50 %, and 75 %), and ``max``.  For
    object and categorical columns it reports ``count``, ``unique`` (number of
    distinct values), ``top`` (most frequent value), and ``freq`` (frequency of
    the most common value).

    This explorer is a fast first step when exploring a new dataset: it
    immediately surfaces the central tendency, spread, and range of each column,
    flags potential data quality issues (e.g. unexpectedly low counts indicating
    missing values), and helps decide which transformations or visualisations to
    apply next.

    Users can customise which percentiles appear in the output and restrict or
    expand the dtype groups that are summarised via the ``include`` and
    ``exclude`` parameters.
    """

    DISPLAY_NAME = MultilingualString(
        en="Describe Dataset",
        es="Describir Dataset",
        pt="Explorador de Descrição Estatística",
        zh="统计描述数据集",
        de="Datensatz beschreiben",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Generates a statistical summary of the dataset. For numeric "
            "columns: count, mean, std, min, 25%, 50%, 75%, and max. For "
            "object columns: count, unique, top, and freq. You can choose "
            "percentiles and which dtypes to include or exclude."
        ),
        es=(
            "Genera un resumen estadístico del dataset. Para columnas "
            "numéricas: count, mean, std, min, 25%, 50%, 75% y max. Para "
            "columnas de tipo objeto: count, unique, top y freq. Puede elegir "
            "percentiles y qué tipos incluir o excluir."
        ),
        pt=(
            "Gera um resumo estatístico do conjunto de dados. Para colunas "
            "numéricas: count, mean, std, min, 25%, 50%, 75% e max. Para "
            "colunas de objeto: count, unique, top e freq. Você pode escolher "
            "percentis e quais tipos incluir ou excluir."
        ),
        zh=(
            "生成数据集的统计摘要。数值列：count、mean、std、min、25%、50%、75%和max。"
            "对象列：count、unique、top和freq。可选择百分位数和包含或排除的数据类型。"
        ),
        de=(
            "Erzeugt eine statistische Zusammenfassung des Datensatzes. Für "
            "numerische Spalten: Anzahl, Mittelwert, Standardabweichung, Min, "
            "25%, 50%, 75% und Max. Für Objektspalten: Anzahl, eindeutige Werte, "
            "häufigster Wert und Häufigkeit. Perzentile und Datentypen können "
            "ein- oder ausgeschlossen werden."
        ),
    )

    SHORT_DESCRIPTION = MultilingualString(
        en="Generate a statistical summary of the dataset.",
        es="Genera un resumen estadístico del dataset.",
        pt="Gera um resumo estatístico do conjunto de dados.",
        zh="生成数据集的统计摘要。",
        de="Erstellt eine statistische Zusammenfassung des Datensatzes.",
    )
    IMAGE_PREVIEW = "describe_explorer.png"

    SCHEMA = DescribeExplorerSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [],
        "allowed_dtypes": [],
        "input_cardinality": {"min": 1},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize DescribeExplorer with percentile and dtype filter parameters.

        Converts the comma-separated ``percentiles`` string to a list of floats
        in the range [0, 1], and normalizes ``include`` and ``exclude`` dtype
        values to the list format expected by ``pandas.DataFrame.describe``.

        Parameters
        ----------
        **kwargs
            Keyword arguments matching ``DescribeExplorerSchema`` fields:
            percentiles (str | None): Comma-separated integers 0-100 (e.g.
            ``"25, 50, 75"``). Converted to floats (e.g. ``[0.25, 0.5,
            0.75]``). Pass an empty string or ``None`` to use pandas
            defaults.
            include (str | None): Dtype selection string (``"all"``,
            ``"number"``, ``"object"``, ``"category"``, or
            ``"datetime"``). ``"all"`` is passed through; other values
            are wrapped in a list.
            exclude (str | None): Dtype to exclude, wrapped in a list when
            provided.
        """
        # transform percentiles to list of floats for describe (e.g., [0.25, 0.5, 0.75])
        if kwargs.get("percentiles"):
            percentiles = kwargs["percentiles"].strip().split(",")
            percentiles = [percentile.strip() for percentile in percentiles]

            if percentiles == [""]:
                percentiles = None
            else:
                percentiles = [float(percentile) / 100 for percentile in percentiles]
            kwargs["percentiles"] = percentiles

        if kwargs.get("include") and kwargs["include"] != "all":
            kwargs["include"] = [kwargs["include"]]

        if kwargs.get("exclude"):
            kwargs["exclude"] = [kwargs["exclude"]]

        self.percentiles = kwargs["percentiles"]
        self.include = kwargs["include"]
        self.exclude = kwargs["exclude"]
        super().__init__(**kwargs)

    @classmethod
    def validate_parameters(cls, params: Dict[str, Any]) -> bool:
        """Validate explorer parameters against the schema and business rules.

        Checks that ``params`` passes Pydantic schema validation and that any
        provided percentiles are integers in the range [0, 100].

        Parameters
        ----------
        cls : type
            The explorer class (injected automatically by Python for
            classmethods).
        params : Dict[str, Any]
            Parameter dictionary to validate (must match
            ``DescribeExplorerSchema``).

        Returns
        -------
        bool
            ``True`` if all validations pass, ``False`` if any percentile
            value is outside [0, 100] or cannot be parsed as an integer.

        Raises
        ------
        ValidationError
            If ``params`` does not conform to the Pydantic schema.
        """
        # Validate schema
        cls.SCHEMA.model_validate(params)

        # Validate percentiles (must be int between 0 and 100)
        if params.get("percentiles"):
            percentiles = params["percentiles"].strip().split(",")
            for percentile in percentiles:
                try:
                    int_percentile = int(percentile)
                    if not 0 <= int_percentile <= 100:
                        return False
                except ValueError:
                    return False
        return True

    def launch_exploration(
        self, dataset: "DashAIDataset", __explorer_info__: Explorer
    ) -> Any:
        """Compute a statistical summary of the dataset using pandas describe.

        Calls ``pandas.DataFrame.describe`` on the full dataset converted to a
        pandas DataFrame, applying the percentile and dtype filter settings
        configured on this instance.

        Parameters
        ----------
        dataset : DashAIDataset
            The dataset to summarize.
        __explorer_info__ : Explorer
            The explorer database record (unused).

        Returns
        -------
        Any
            A ``pandas.DataFrame`` containing descriptive statistics (count,
            mean, std, min, percentiles, max for numeric columns; count,
            unique, top, freq for object columns).
        """
        return dataset.to_pandas().describe(
            percentiles=self.percentiles, include=self.include, exclude=self.exclude
        )

    def save_notebook(
        self,
        __notebook_info__: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Save the descriptive statistics DataFrame to a JSON file on disk.

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
            The ``pandas.DataFrame`` returned by
            ``launch_exploration``.

        Returns
        -------
        str
            The path of the saved JSON file as a POSIX string.
        """
        import os
        from pathlib import Path

        filename = f"{explorer_info.id}.json"
        path = Path(os.path.join(save_path, filename))

        result.to_json(path)
        return path.as_posix()

    def get_results(
        self, exploration_path: str, options: Dict[str, Any]
    ) -> List[Artifact]:
        """Load and return the saved statistical summary for the frontend.

        Reads the JSON file written by ``save_notebook``, transposes the
        DataFrame so that statistics become columns, and returns it as a
        table artifact with the feature names in an index column.

        Parameters
        ----------
        exploration_path : str
            Path to the JSON file saved by ``save_notebook``.
        options : Dict[str, Any]
            Rendering options from the frontend (unused).

        Returns
        -------
        List[Artifact]
            A single-element list with the table artifact of the summary.
        """
        from pathlib import Path

        import numpy as np
        import pandas as pd

        summary = pd.read_json(Path(exploration_path)).replace({np.nan: None}).T
        return [
            TableArtifact(
                payload=TablePayload(
                    columns=["index", *summary.columns.astype(str)],
                    rows=[
                        [str(index), *row]
                        for index, row in zip(
                            summary.index, summary.to_numpy().tolist(), strict=True
                        )
                    ],
                )
            )
        ]
