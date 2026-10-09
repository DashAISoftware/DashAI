"""DashAI Excel Dataloader."""

from typing import TYPE_CHECKING, Any, Dict

from DashAI.back.core.schema_fields import (
    bool_field,
    int_field,
    none_type,
    schema_field,
    string_field,
    union_type,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ExcelDataloaderSchema(BaseSchema):
    """Schema for ExcelDataLoader hyperparameters.

    Configures the sheet selector, header row, columns to import,
    row-skipping and row-count limit, and the dataset split ratios.
    The sheet can be specified as a name string or a zero-based index;
    leaving the sheet field empty selects the first sheet.
    """

    sheet: schema_field(
        union_type(int_field(ge=0), string_field()),
        placeholder=0,
        description=MultilingualString(
            en=(
                "The name of the sheet to read or its zero-based index. "
                "If a string is provided, the reader will search for a sheet named "
                "exactly as the string. If an integer is provided, the reader will "
                "select the sheet at the corresponding index. By default, the first "
                "sheet will be read."
            ),
            es=(
                "El nombre de la hoja a leer o su índice basado en cero. "
                "Si se proporciona una cadena, el lector buscará una hoja con ese "
                "nombre exacto. Si se proporciona un entero, el lector seleccionará "
                "la hoja en el índice correspondiente. Por defecto, se leerá la "
                "primera hoja."
            ),
            pt=(
                "O nome da planilha a ser lida ou seu índice baseado em zero. "
                "Se uma string for fornecida, o leitor buscará uma planilha com esse "
                "nome exato. Se um inteiro for fornecido, o leitor selecionará a "
                "planilha no índice correspondente. Por padrão, a primeira planilha "
                "será lida."
            ),
            de=(
                "Der Name des zu lesenden Tabellenblatts oder sein nullbasierter Index."
                "Wenn eine Zeichenkette angegeben wird, sucht der Leser nach einem "
                "Blatt "
                "mit genau diesem Namen. Wenn eine Ganzzahl angegeben wird, wählt der "
                "Leser das Blatt am entsprechenden Index aus. Standardmäßig wird das "
                "erste Blatt gelesen."
            ),
            zh=(
                "要读取的工作表名称或其从零开始的索引。"
                "如果提供字符串，读取器将搜索同名工作表。"
                "如果提供整数，读取器将选择对应索引的工作表。默认读取第一个工作表。"
            ),
        ),
        alias=MultilingualString(
            en="Sheet", es="Hoja", pt="Planilha", de="Tabellenblatt", zh="工作表"
        ),
    )  # type: ignore
    header: schema_field(
        none_type(int_field(ge=0)),
        placeholder=0,
        description=MultilingualString(
            en=(
                "The row number where the column names are located, indexed from 0. "
                "If null, the file will be considered to have no column names."
            ),
            es=(
                "El número de fila donde se encuentran los nombres de columna, "
                "indexado desde 0. Si es null, se considerará que el archivo no "
                "tiene nombres de columna."
            ),
            pt=(
                "O número da linha onde os nomes de coluna estão localizados, "
                "indexado a partir de 0. Se nulo, o arquivo será considerado sem "
                "nomes de coluna."
            ),
            de=(
                "Die Zeilennummer, in der sich die Spaltennamen befinden, nullbasiert. "
                "Wenn null, wird angenommen, dass die Datei keine Spaltennamen hat."
            ),
            zh="列名所在的行号，从0开始索引。如果为null，则认为文件没有列名。",
        ),
        alias=MultilingualString(
            en="Header", es="Encabezado", pt="Cabeçalho", de="Kopfzeile", zh="标题行"
        ),
    )  # type: ignore
    usecols: schema_field(
        none_type(string_field()),
        placeholder=None,
        description=MultilingualString(
            en=(
                "If None, the reader will load all columns. If str, then indicates "
                "comma separated list of Excel column letters and column ranges "
                '(e.g. "A:E" or "A,C,E:F"). Ranges are inclusive of both sides.'
            ),
            es=(
                "Si es None, el lector cargará todas las columnas. Si es str, indica "
                "una lista separada por comas de letras de columna de Excel y rangos "
                'de columna (ej. "A:E" o "A,C,E:F"). Los rangos son inclusivos en '
                "ambos lados."
            ),
            pt=(
                "Se None, o leitor carregará todas as colunas. Se str, indica uma "
                "lista separada por vírgulas de letras de coluna do Excel e intervalos "
                'de coluna (ex. "A:E" ou "A,C,E:F"). Os intervalos são inclusivos em '
                "ambos os lados."
            ),
            de=(
                "Wenn None, lädt der Leser alle Spalten. Wenn str, gibt eine "
                "kommagetrennte Liste von Excel-Spaltenbuchstaben und -bereichen an "
                '(z.B. "A:E" oder "A,C,E:F"). Bereiche sind auf beiden Seiten inklusiv.'
            ),
            zh=(
                "如果为None，读取器将加载所有列。如果为字符串，则指定Excel列字母和列范围的"
                '逗号分隔列表（例如"A:E"或"A,C,E:F"）。范围两端均包含。'
            ),
        ),
        alias=MultilingualString(
            en="Use columns",
            es="Usar columnas",
            pt="Usar colunas",
            de="Spalten verwenden",
            zh="使用列",
        ),
    )  # type: ignore

    skiprows: schema_field(
        none_type(int_field(ge=0)),
        None,
        description=MultilingualString(
            en=(
                "Number of rows to skip at the start of the file. "
                "Leave empty to not skip any rows."
            ),
            es=(
                "Número de filas a omitir al inicio del archivo. "
                "Deje vacío para no omitir ninguna fila."
            ),
            pt=(
                "Número de linhas a pular no início do arquivo. "
                "Deixe vazio para não pular nenhuma linha."
            ),
            de=(
                "Anzahl der am Anfang der Datei zu überspringenden Zeilen. "
                "Leer lassen, um keine Zeilen zu überspringen."
            ),
            zh="文件开头要跳过的行数。留空则不跳过任何行。",
        ),
        alias=MultilingualString(
            en="Skip rows",
            es="Omitir filas",
            pt="Pular linhas",
            de="Zeilen überspringen",
            zh="跳过行",
        ),
    )  # type: ignore

    nrows: schema_field(
        none_type(int_field(ge=1)),
        None,
        description=MultilingualString(
            en="Number of rows to read. Leave empty to read all rows.",
            es="Número de filas a leer. Deje vacío para leer todas las filas.",
            pt="Número de linhas a ler. Deixe vazio para ler todas as linhas.",
            de="Anzahl der zu lesenden Zeilen. Leer lassen, um alle Zeilen zu lesen.",
            zh="要读取的行数。留空则读取所有行。",
        ),
        alias=MultilingualString(
            en="N rows", es="N filas", pt="N linhas", de="Anzahl Zeilen", zh="行数"
        ),
    )  # type: ignore

    names: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en=(
                "Comma-separated list of column names to use. "
                "Example: 'col1,col2,col3'. Leave empty to use header row."
            ),
            es=(
                "Lista de nombres de columna separados por comas. "
                "Ejemplo: 'col1,col2,col3'. Deje vacío para usar la fila de "
                "encabezado."
            ),
            pt=(
                "Lista de nomes de coluna separados por vírgulas. "
                "Exemplo: 'col1,col2,col3'. Deixe vazio para usar a linha de "
                "cabeçalho."
            ),
            de=(
                "Kommagetrennte Liste der zu verwendenden Spaltennamen. "
                "Beispiel: 'col1,col2,col3'. Leer lassen, um die Kopfzeile zu "
                "verwenden."
            ),
            zh="要使用的列名逗号分隔列表。示例：'col1,col2,col3'。留空则使用标题行。",
        ),
        alias=MultilingualString(
            en="Names", es="Nombres", pt="Nomes", de="Namen", zh="列名"
        ),
    )  # type: ignore

    na_values: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en=(
                "Comma-separated additional strings to recognize as NA/NaN. "
                "Example: 'NA,N/A,null'."
            ),
            es=(
                "Cadenas adicionales separadas por comas para reconocer como NA/NaN. "
                "Ejemplo: 'NA,N/A,null'."
            ),
            pt=(
                "Strings adicionais separadas por vírgulas para reconhecer "
                "como NA/NaN. Exemplo: 'NA,N/A,null'."
            ),
            de=(
                "Kommagetrennte zusätzliche Zeichenketten, die als NA/NaN erkannt "
                "werden. "
                "Beispiel: 'NA,N/A,null'."
            ),
            zh="识别为NA/NaN的逗号分隔附加字符串。示例：'NA,N/A,null'",
        ),
        alias=MultilingualString(
            en="NA values",
            es="Valores NA",
            pt="Valores ausentes",
            de="NA-Werte",
            zh="NA值",
        ),
    )  # type: ignore

    keep_default_na: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en="Whether to include the default NaN values when parsing the data.",
            es=(
                "Si se deben incluir los valores NaN predeterminados al analizar los "
                "datos."
            ),
            pt=("Se os valores NaN padrão devem ser incluídos ao analisar os dados."),
            de=(
                "Ob die Standard-NaN-Werte beim Parsen der Daten einbezogen werden "
                "sollen."
            ),
            zh="解析数据时是否包含默认的NaN值。",
        ),
        alias=MultilingualString(
            en="Keep default NA",
            es="Mantener NA predeterminado",
            pt="Manter NA padrão",
            de="Standard-NA behalten",
            zh="保留默认NA值",
        ),
    )  # type: ignore

    true_values: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en="Comma-separated values to consider as True. Example: 'yes,true,1'.",
            es=(
                "Valores separados por comas a considerar como True. "
                "Ejemplo: 'yes,true,1'."
            ),
            pt=(
                "Valores separados por vírgulas a considerar como True. "
                "Exemplo: 'yes,true,1'."
            ),
            de=(
                "Kommagetrennte Werte, die als True betrachtet werden. "
                "Beispiel: 'yes,true,1'."
            ),
            zh="视为True的逗号分隔值。示例：'yes,true,1'",
        ),
        alias=MultilingualString(
            en="True values",
            es="Valores verdaderos",
            pt="Valores verdadeiros",
            de="Wahr-Werte",
            zh="True值",
        ),
    )  # type: ignore

    false_values: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en="Comma-separated values to consider as False. Example: 'no,false,0'.",
            es=(
                "Valores separados por comas a considerar como False. "
                "Ejemplo: 'no,false,0'."
            ),
            pt=(
                "Valores separados por vírgulas a considerar como False. "
                "Exemplo: 'no,false,0'."
            ),
            de=(
                "Kommagetrennte Werte, die als False betrachtet werden. "
                "Beispiel: 'no,false,0'."
            ),
            zh="视为False的逗号分隔值。示例：'no,false,0'",
        ),
        alias=MultilingualString(
            en="False values",
            es="Valores falsos",
            pt="Valores falsos",
            de="Falsch-Werte",
            zh="False值",
        ),
    )  # type: ignore


class ExcelDataLoader(BaseDataLoader):
    """Data loader that ingests tabular data from Excel workbooks into DashAI datasets.

    Reads ``.xlsx`` / ``.xls`` files, optionally selecting a specific sheet,
    samples rows, and splits the result into train/validation/test
    ``DashAIDataset`` splits. Delegates to ``pandas.read_excel`` after
    normalising the schema parameters (sheet name/index, header row, column
    selection, row limits).

    Handles multifile uploads by concatenating all workbooks before splitting.
    """

    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".xlsx", ".xls", ".zip"})
    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]
    SCHEMA = ExcelDataloaderSchema

    DESCRIPTION: str = MultilingualString(
        en=(
            "Data loader for tabular data in Excel files. "
            "Supports xls, xlsx, xlsm, xlsb, odf, ods and odt file extensions."
        ),
        es=(
            "Cargador de datos para datos tabulares en archivos Excel. "
            "Soporta extensiones de archivo xls, xlsx, xlsm, xlsb, odf, ods y odt."
        ),
        pt=(
            "Carregador de dados para dados tabulares em arquivos Excel. "
            "Suporta extensões de arquivo xls, xlsx, xlsm, xlsb, odf, ods e odt."
        ),
        de=(
            "Datenlader für tabellarische Daten in Excel-Dateien. "
            "Unterstützt xls, xlsx, xlsm, xlsb, odf, ods und odt Dateierweiterungen."
        ),
        zh=(
            "Excel文件表格数据加载器。"
            "支持xls、xlsx、xlsm、xlsb、odf、ods和odt文件扩展名。"
        ),
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Excel Data Loader",
        es="Cargador de Datos Excel",
        pt="Carregador de Dados Excel",
        de="Excel Datenlader",
        zh="Excel数据加载器",
    )

    def _prepare_pandas_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert schema parameters into a dict suitable for ``pandas.read_excel``.

        Maps DashAI schema keys to their pandas equivalents and normalises
        comma-separated string fields (``names``, ``na_values``,
        ``true_values``, ``false_values``) into Python lists.

        Parameters
        ----------
        params : Dict[str, Any]
            Raw parameter dictionary from the schema (``sheet``, ``header``,
            ``usecols``, ``skiprows``, ``nrows``, ``names``, ``na_values``,
            ``keep_default_na``, ``true_values``, ``false_values``).

        Returns
        -------
        Dict[str, Any]
            Keyword-argument dict ready to be unpacked into ``pd.read_excel``.
        """
        pandas_params = {}

        if "sheet" in params and params["sheet"] is not None:
            pandas_params["sheet_name"] = params["sheet"]

        pandas_params["header"] = params.get("header", 0)

        if "usecols" in params and params["usecols"] is not None:
            pandas_params["usecols"] = params["usecols"]

        if "skiprows" in params and params["skiprows"] is not None:
            pandas_params["skiprows"] = params["skiprows"]

        if "nrows" in params and params["nrows"] is not None:
            pandas_params["nrows"] = params["nrows"]

        if "names" in params and params["names"] is not None:
            pandas_params["names"] = [
                name.strip() for name in params["names"].split(",")
            ]

        if "na_values" in params and params["na_values"] is not None:
            pandas_params["na_values"] = [
                val.strip() for val in params["na_values"].split(",")
            ]

        if "keep_default_na" in params and params["keep_default_na"] is not None:
            pandas_params["keep_default_na"] = params["keep_default_na"]

        if "true_values" in params and params["true_values"] is not None:
            pandas_params["true_values"] = [
                val.strip() for val in params["true_values"].split(",")
            ]

        if "false_values" in params and params["false_values"] is not None:
            pandas_params["false_values"] = [
                val.strip() for val in params["false_values"].split(",")
            ]

        return pandas_params

    def load_data(
        self,
        filepath_or_buffer: str,
        temp_path: str,
        params: Dict[str, Any],
        n_sample: int | None = None,
    ) -> "DashAIDataset":
        """Load the uploaded Excel files into a DatasetDict.

        Parameters
        ----------
        filepath_or_buffer : str
            An URL where the dataset is located or a FastAPI/Uvicorn uploaded file
            object.
        temp_path : str
            The temporary path where the files will be extracted and then uploaded.
        params : Dict[str, Any]
            Dict with the dataloader parameters.
        n_sample : int | None
            Indicates how many rows load from the dataset, all rows if null.

        Returns
        -------
        DatasetDict
            A HuggingFace's Dataset with the loaded data.
        """
        import glob
        import shutil

        import pandas as pd
        from datasets import Dataset, DatasetDict
        from datasets.builder import DatasetGenerationError

        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

        prepared_path = self.prepare_files(filepath_or_buffer, temp_path)
        print("path prepared", prepared_path)

        pandas_params = self._prepare_pandas_params(params)

        if prepared_path[1] == "file":
            try:
                dataset = pd.read_excel(
                    io=prepared_path[0], **pandas_params, nrows=n_sample
                )
            except ValueError as e:
                raise DatasetGenerationError from e
            dataset_dict = DatasetDict({"train": Dataset.from_pandas(dataset)})
        if prepared_path[1] == "dir":
            train_files = glob.glob(prepared_path[0] + "/train/*")
            test_files = glob.glob(prepared_path[0] + "/test/*")
            val_files = glob.glob(prepared_path[0] + "/val/*") + glob.glob(
                prepared_path[0] + "/validation/*"
            )
            try:
                train_df_list = [
                    pd.read_excel(io=file_path, **pandas_params, nrows=n_sample)
                    for file_path in sorted(train_files)
                ]

                train_df = pd.concat(train_df_list)
                test_df_list = [
                    pd.read_excel(io=file_path, **pandas_params, nrows=n_sample)
                    for file_path in sorted(test_files)
                ]
                test_df_list = pd.concat(test_df_list)

                val_df_list = [
                    pd.read_excel(io=file_path, **pandas_params, nrows=n_sample)
                    for file_path in sorted(val_files)
                ]
                val_df = pd.concat(val_df_list)

                dataset_dict = DatasetDict(
                    {
                        "train": Dataset.from_pandas(train_df, preserve_index=False),
                        "test": Dataset.from_pandas(test_df_list, preserve_index=False),
                        "validation": Dataset.from_pandas(val_df, preserve_index=False),
                    }
                )
            except ValueError as e:
                raise DatasetGenerationError from e
            finally:
                shutil.rmtree(prepared_path[0])
        return to_dashai_dataset(dataset_dict)

    def load_preview(
        self,
        filepath_or_buffer: str,
        params: Dict[str, Any],
        n_rows: int = 10,
    ):
        """
        Load a preview of the Excel dataset.

        Note: Excel doesn't support native streaming in the same way as CSV/JSON,
        so we use nrows parameter to limit memory usage.

        Parameters
        ----------
        filepath_or_buffer : str
            Path to the Excel file.
        params : Dict[str, Any]
            Parameters for loading Excel (sheet, header, etc.).
        n_rows : int, optional
            Number of rows to preview. Default is 10.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the preview rows.
        """
        pandas_params = self._prepare_pandas_params(params)
        pandas_params["nrows"] = n_rows

        import pandas as pd

        df_preview = pd.read_excel(
            io=filepath_or_buffer,
            **pandas_params,
        )

        return df_preview
