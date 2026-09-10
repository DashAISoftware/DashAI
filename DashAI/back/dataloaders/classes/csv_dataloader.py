"""DashAI CSV Dataloader."""

import shutil
from itertools import islice
from typing import TYPE_CHECKING, Any, Dict

from DashAI.back.core.schema_fields import (
    bool_field,
    enum_field,
    int_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class CSVDataloaderSchema(BaseSchema):
    """Schema for CSVDataLoader hyperparameters.

    Configures the field separator, header row index, columns to import,
    row-skipping and sampling parameters, and the dataset split ratios.
    The separator can be specified as an exact character or as the aliases
    ``"blank space"`` or ``"tab"`` which are normalised before passing to
    ``pandas.read_csv``.
    """

    separator: schema_field(
        enum_field([",", ";", "blank space", "tab"]),
        ",",
        description=MultilingualString(
            en="A separator character delimits the data in a CSV file.",
            es="Un carácter separador delimita los datos en un archivo CSV.",
            pt="Um caractere separador delimita os dados em um arquivo CSV.",
            de="Ein Trennzeichen begrenzt die Daten in einer CSV-Datei.",
            zh="分隔符字符用于分隔CSV文件中的数据。",
        ),
        alias=MultilingualString(
            en="Separator",
            es="Separador",
            pt="Separador",
            de="Trennzeichen",
            zh="分隔符",
        ),
    )  # type: ignore

    header: schema_field(
        string_field(),
        "infer",
        description=MultilingualString(
            en=(
                "Row number(s) containing column labels and marking the start of the "
                "data (zero-indexed). Default behavior is to infer the column names. "
                "If column names are passed explicitly, this should be set to '0'. "
                "Header can also be a list of integers that specify row locations "
                "for MultiIndex on the columns."
            ),
            es=(
                "Número(s) de fila que contienen las etiquetas de columna y marcan "
                "el inicio de los datos (indexado desde cero). El comportamiento "
                "predeterminado es inferir los nombres de columna. Si los nombres de "
                "columna se pasan explícitamente, esto debe establecerse en '0'. "
                "Header también puede ser una lista de enteros que especifican las "
                "ubicaciones de fila para MultiIndex en las columnas."
            ),
            pt=(
                "Número(s) de linha que contêm os rótulos de coluna e marcam "
                "o início dos dados (indexado a partir de zero). O comportamento "
                "padrão é inferir os nomes de coluna. Se os nomes de coluna forem "
                "passados explicitamente, isso deve ser definido como '0'. O "
                "cabeçalho também pode ser uma lista de inteiros que especificam "
                "as localizações de linha para MultiIndex nas colunas."
            ),
            de=(
                "Zeilennummer(n) mit Spaltenbezeichnungen, die den Beginn der Daten "
                "markieren (nullbasiert). Standardverhalten ist das Ableiten der "
                "Spaltennamen. Wenn Spaltennamen explizit übergeben werden, sollte "
                "dies auf '0' gesetzt werden. Header kann auch eine Liste von "
                "Ganzzahlen "
                "sein, die Zeilenpositionen für MultiIndex auf den Spalten angeben."
            ),
            zh=(
                "包含列标签并标记数据起始位置的行号（从零开始索引）。"
                "默认行为是推断列名。如果显式传递列名，应设置为'0'。"
                "也可以是整数列表，指定列的多级索引行位置。"
            ),
        ),
        alias=MultilingualString(
            en="Header", es="Encabezado", pt="Cabeçalho", de="Kopfzeile", zh="标题行"
        ),
    )  # type: ignore

    names: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en=(
                "Comma-separated list of column names to use. If the file contains a "
                "header row, then you should explicitly pass header=0 to override the "
                "column names. Example: 'col1,col2,col3'. Leave empty to use file "
                "headers."
            ),
            es=(
                "Lista de nombres de columna separados por comas. Si el archivo "
                "contiene una fila de encabezado, debe pasar explícitamente header=0 "
                "para sobrescribir los nombres de columna. Ejemplo: 'col1,col2,col3'. "
                "Deje vacío para usar los encabezados del archivo."
            ),
            pt=(
                "Lista de nomes de coluna separados por vírgulas. Se o arquivo "
                "contiver uma linha de cabeçalho, você deve passar explicitamente "
                "header=0 para substituir os nomes de coluna. "
                "Exemplo: 'col1,col2,col3'. Deixe vazio para usar os cabeçalhos."
            ),
            de=(
                "Kommagetrennte Liste der zu verwendenden Spaltennamen. Wenn die Datei "
                "eine Kopfzeile enthält, sollte header=0 explizit übergeben werden, "
                "um die Spaltennamen zu überschreiben. Beispiel: 'col1,col2,col3'. "
                "Leer lassen, um die Datei-Kopfzeilen zu verwenden."
            ),
            zh=(
                "要使用的列名逗号分隔列表。如果文件包含标题行，应显式传递header=0来覆盖列名。"
                "示例：'col1,col2,col3'。留空则使用文件标题。"
            ),
        ),
        alias=MultilingualString(
            en="Names", es="Nombres", pt="Nomes", de="Namen", zh="列名"
        ),
    )  # type: ignore

    encoding: schema_field(
        enum_field(["utf-8", "latin1", "cp1252", "iso-8859-1"]),
        "utf-8",
        description=MultilingualString(
            en=(
                "Encoding to use for UTF when reading/writing. Most common encodings "
                "provided."
            ),
            es=(
                "Codificación a usar para UTF al leer/escribir. Se proporcionan las "
                "codificaciones más comunes."
            ),
            pt=(
                "Codificação a usar para UTF ao ler/escrever. As codificações mais "
                "comuns são fornecidas."
            ),
            de=(
                "Kodierung für UTF beim Lesen/Schreiben. Die gängigsten "
                "Kodierungen sind verfügbar."
            ),
            zh="读写时使用的UTF编码。提供了最常用的编码。",
        ),
        alias=MultilingualString(
            en="Encoding",
            es="Codificación",
            pt="Codificação",
            de="Kodierung",
            zh="编码",
        ),
    )  # type: ignore

    na_values: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en=(
                "Comma-separated additional strings to recognize as NA/NaN. "
                "Example: 'NULL,missing,n/a'"
            ),
            es=(
                "Cadenas adicionales separadas por comas para reconocer como NA/NaN. "
                "Ejemplo: 'NULL,missing,n/a'"
            ),
            pt=(
                "Strings adicionais separadas por vírgulas para reconhecer "
                "como NA/NaN. Exemplo: 'NULL,missing,n/a'"
            ),
            de=(
                "Kommagetrennte zusätzliche Zeichenketten, die als NA/NaN erkannt "
                "werden. "
                "Beispiel: 'NULL,missing,n/a'"
            ),
            zh="识别为NA/NaN的逗号分隔附加字符串。示例：'NULL,missing,n/a'",
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
            en=(
                "Whether to include the default NaN values when parsing the data "
                "(True recommended)."
            ),
            es=(
                "Si se deben incluir los valores NaN predeterminados al analizar los "
                "datos (se recomienda True)."
            ),
            pt=(
                "Se os valores NaN padrão devem ser incluídos ao analisar os dados "
                "(True recomendado)."
            ),
            de=(
                "Ob die Standard-NaN-Werte beim Parsen der Daten einbezogen werden "
                "sollen "
                "(True empfohlen)."
            ),
            zh="解析数据时是否包含默认的NaN值（建议True）。",
        ),
        alias=MultilingualString(
            en="Keep default NA",
            es="Mantener NA predeterminado",
            pt="Manter valores ausentes padrão",
            de="Standard-NA behalten",
            zh="保留默认NA值",
        ),
    )  # type: ignore

    true_values: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en="Comma-separated values to consider as True. Example: 'yes,true,1,on'",
            es=(
                "Valores separados por comas a considerar como True. "
                "Ejemplo: 'yes,true,1,on'"
            ),
            pt=(
                "Valores separados por vírgulas a considerar como True. "
                "Exemplo: 'yes,true,1,on'"
            ),
            de=(
                "Kommagetrennte Werte, die als True betrachtet werden. "
                "Beispiel: 'yes,true,1,on'"
            ),
            zh="视为True的逗号分隔值。示例：'yes,true,1,on'",
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
            en="Comma-separated values to consider as False. Example: 'no,false,0,off'",
            es=(
                "Valores separados por comas a considerar como False. "
                "Ejemplo: 'no,false,0,off'"
            ),
            pt=(
                "Valores separados por vírgulas a considerar como False. "
                "Exemplo: 'no,false,0,off'"
            ),
            de=(
                "Kommagetrennte Werte, die als False betrachtet werden. "
                "Beispiel: 'no,false,0,off'"
            ),
            zh="视为False的逗号分隔值。示例：'no,false,0,off'",
        ),
        alias=MultilingualString(
            en="False values",
            es="Valores falsos",
            pt="Valores falsos",
            de="Falsch-Werte",
            zh="False值",
        ),
    )  # type: ignore

    skip_blank_lines: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en="If True, skip over blank lines rather than interpreting as NaN values.",
            es=(
                "Si es True, omitir líneas en blanco en lugar de interpretarlas como "
                "valores NaN."
            ),
            pt=(
                "Se True, ignorar linhas em branco em vez de interpretá-las como "
                "valores NaN."
            ),
            de=(
                "Wenn True, leere Zeilen überspringen anstatt sie als NaN-Werte "
                "zu interpretieren."
            ),
            zh="如果为True，跳过空行而不是将其解释为NaN值。",
        ),
        alias=MultilingualString(
            en="Skip blank lines",
            es="Omitir líneas en blanco",
            pt="Ignorar linhas em branco",
            de="Leerzeilen überspringen",
            zh="跳过空行",
        ),
    )  # type: ignore

    skiprows: schema_field(
        none_type(int_field()),
        None,
        description=MultilingualString(
            en=(
                "Number of data rows to skip after reading the header. "
                "Leave empty to skip none."
            ),
            es=(
                "Número de filas de datos a omitir después de leer el encabezado. "
                "Deje vacío para no omitir ninguna."
            ),
            pt=(
                "Número de linhas de dados a pular após a leitura do cabeçalho. "
                "Deixe vazio para não pular nenhuma."
            ),
            de=(
                "Anzahl der Datenzeilen, die nach dem Lesen der Kopfzeile übersprungen "
                "werden. "
                "Leer lassen, um keine zu überspringen."
            ),
            zh="读取标题后要跳过的数据行数。留空则不跳过任何行。",
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
        none_type(int_field()),
        None,
        description=MultilingualString(
            en="Number of rows to read from the file. Leave empty to read all rows.",
            es=(
                "Número de filas a leer del archivo. Deje vacío para leer todas las "
                "filas."
            ),
            pt=(
                "Número de linhas a ler do arquivo. Deixe vazio para ler todas as "
                "linhas."
            ),
            de=(
                "Anzahl der aus der Datei zu lesenden Zeilen. Leer lassen, "
                "um alle Zeilen zu lesen."
            ),
            zh="从文件中读取的行数。留空则读取所有行。",
        ),
        alias=MultilingualString(
            en="N rows", es="N filas", pt="N linhas", de="Anzahl Zeilen", zh="行数"
        ),
    )  # type: ignore


class CSVDataLoader(BaseDataLoader):
    """Data loader that ingests tabular data from CSV files into DashAI datasets.

    Reads one or more CSV files, optionally samples rows, and splits the result
    into train/validation/test ``DashAIDataset`` splits according to the ratios
    specified in the schema. The separator is normalised from human readable
    aliases (``"blank space"``, ``"tab"``) to Python character literals before
    delegating to ``pandas.read_csv``.

    Handles multifile uploads by concatenating all CSVs before splitting,
    and supports header detection, column selection, and row skipping via the
    ``CSVDataloaderSchema`` parameters.
    """

    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]
    SCHEMA = CSVDataloaderSchema
    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".csv", ".zip"})

    DESCRIPTION: str = MultilingualString(
        en=(
            "Data loader for tabular data in CSV files. "
            "All uploaded CSV files must have the same column structure and use "
            "consistent separators."
        ),
        es=(
            "Cargador de datos para datos tabulares en archivos CSV. "
            "Todos los archivos CSV subidos deben tener la misma estructura de "
            "columnas y usar separadores consistentes."
        ),
        pt=(
            "Carregador de dados para dados tabulares em arquivos CSV. "
            "Todos os arquivos CSV enviados devem ter a mesma estrutura de colunas "
            "e usar separadores consistentes."
        ),
        de=(
            "Datenlader für tabellarische Daten in CSV-Dateien. "
            "Alle hochgeladenen CSV-Dateien müssen die gleiche Spaltenstruktur "
            "und konsistente Trennzeichen verwenden."
        ),
        zh=(
            "CSV文件表格数据加载器。"
            "所有上传的CSV文件必须具有相同的列结构并使用一致的分隔符。"
        ),
    )
    DISPLAY_NAME: str = MultilingualString(
        en="CSV Data Loader",
        es="Cargador de Datos CSV",
        pt="Carregador de Dados CSV",
        de="CSV Datenlader",
        zh="CSV数据加载器",
    )

    def _check_params(
        self,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate and normalise CSV dataloader parameters before loading.

        Converts human readable separator names (``"blank space"``, ``"tab"``)
        to their Python equivalents and copies recognised keys into a clean
        parameter dictionary suitable for ``pandas.read_csv``.

        Parameters
        ----------
        params : Dict[str, Any]
            Raw parameter dictionary.  Must contain ``"separator"`` (str).

        Returns
        -------
        Dict[str, Any]
            Normalised parameter dict with pandas-compatible keys.

        Raises
        ------
        ValueError
            If ``"separator"`` is not present in ``params``.
        TypeError
            If ``separator`` is not a string after name resolution.
        """
        if "separator" not in params:
            raise ValueError(
                "Error trying to load the CSV dataset: "
                "separator parameter was not provided."
            )

        clean_params = {}

        separator = params["separator"]
        if separator == "blank space":
            separator = " "
        elif separator == "tab":
            separator = "\t"
        if not isinstance(separator, str):
            raise TypeError(
                f"Param separator should be a string, got {type(params['separator'])}"
            )
        clean_params["delimiter"] = separator

        if params.get("header") is not None:
            clean_params["header"] = params["header"]

        list_params = ["names", "na_values", "true_values", "false_values"]
        for param in list_params:
            if param in params and params[param]:
                clean_params[param] = [val.strip() for val in params[param].split(",")]

        bool_params = ["keep_default_na", "skip_blank_lines"]
        for param in bool_params:
            if param in params and params[param] is not None:
                clean_params[param] = params[param]

        if params.get("nrows") is not None:
            if not isinstance(params["nrows"], int):
                raise TypeError(
                    f"Param nrows should be an integer, got {type(params['nrows'])}"
                )
            if params["nrows"] < 0:
                raise ValueError("Param nrows should be greater than or equal to 0")

        if params.get("skiprows") is not None:
            if not isinstance(params["skiprows"], int):
                raise TypeError(
                    "Param skiprows should be an integer, "
                    f"got {type(params['skiprows'])}"
                )
            if params["skiprows"] < 0:
                raise ValueError("Param skiprows should be greater than or equal to 0")

        if "encoding" in params and params["encoding"]:
            valid_encodings = ["utf-8", "latin1", "cp1252", "iso-8859-1"]
            if params["encoding"] not in valid_encodings:
                raise ValueError(f"Invalid encoding: {params['encoding']}")
            clean_params["encoding"] = params["encoding"]

        return clean_params

    def load_data(
        self,
        filepath_or_buffer: str,
        temp_path: str,
        params: Dict[str, Any],
        n_sample: int | None = None,
    ) -> "DashAIDataset":
        """Load the uploaded CSV files into a DatasetDict.

        Parameters
        ----------
        filepath_or_buffer : str, optional
            An URL where the dataset is located or a FastAPI/Uvicorn uploaded file
            object.
        temp_path : str
            The temporary path where the files will be extracted and then uploaded.
        params : Dict[str, Any]
            Dict with the dataloader parameters. The options are:
            - `separator` (str): The character that delimits the CSV data.
        n_sample : int | None
            Indicates how many rows load from the dataset, all rows if null.

        Returns
        -------
        DatasetDict
            A HuggingFace's Dataset with the loaded data.
        """
        from datasets import Dataset, IterableDatasetDict, load_dataset

        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

        clean_params = self._check_params(params)
        data_skiprows = params.get("skiprows") or 0
        data_nrows = params.get("nrows")
        prepared_path = self.prepare_files(filepath_or_buffer, temp_path)
        if prepared_path[1] == "file":
            dataset = load_dataset(
                "csv",
                data_files=prepared_path[0],
                **clean_params,
                streaming=bool(n_sample),
                cache_dir=temp_path,
            )
        else:
            dataset = load_dataset(
                "csv",
                data_dir=prepared_path[0],
                **clean_params,
                streaming=bool(n_sample),
                cache_dir=temp_path,
            )
            shutil.rmtree(prepared_path[0])
        if n_sample:
            if type(dataset) is IterableDatasetDict:
                dataset = dataset["train"]
            if data_skiprows > 0:
                dataset = dataset.skip(data_skiprows)
            rows_iterator = iter(dataset)
            if data_nrows is not None:
                rows_iterator = islice(rows_iterator, data_nrows)
            rows_iterator = islice(rows_iterator, n_sample)
            dataset = Dataset.from_list(list(rows_iterator))
        elif data_skiprows > 0:
            train_dataset = dataset["train"]
            end = (
                min(train_dataset.num_rows, data_skiprows + data_nrows)
                if data_nrows is not None
                else train_dataset.num_rows
            )
            if data_skiprows >= end:
                dataset["train"] = Dataset.from_dict(train_dataset[0:0])
            else:
                dataset["train"] = Dataset.from_dict(train_dataset[data_skiprows:end])
        elif data_nrows is not None:
            train_dataset = dataset["train"]
            end = min(train_dataset.num_rows, data_nrows)
            dataset["train"] = Dataset.from_dict(train_dataset[0:end])
        return to_dashai_dataset(dataset)

    def load_preview(
        self,
        filepath_or_buffer: str,
        params: Dict[str, Any],
        n_rows: int = 100,
    ):
        """
        Load a preview of the CSV dataset using streaming.

        Parameters
        ----------
        filepath_or_buffer : str
            Path to the CSV file.
        params : Dict[str, Any]
            Parameters for loading the CSV (separator, encoding, etc.).
        n_rows : int, optional
            Number of rows to preview. Default is 100.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the preview rows.
        """
        import pandas as pd
        from datasets import load_dataset

        clean_params = self._check_params(params)
        data_skiprows = params.get("skiprows") or 0
        data_nrows = params.get("nrows")

        dataset_stream = load_dataset(
            "csv",
            data_files=filepath_or_buffer,
            streaming=True,
            split="train",
            **clean_params,
        )
        if data_skiprows > 0:
            dataset_stream = dataset_stream.skip(data_skiprows)

        preview_limit = data_nrows if data_nrows is not None else n_rows
        preview_limit = min(preview_limit, n_rows)

        sample_rows = list(islice(dataset_stream, preview_limit))

        df_preview = pd.DataFrame(sample_rows)

        return df_preview
