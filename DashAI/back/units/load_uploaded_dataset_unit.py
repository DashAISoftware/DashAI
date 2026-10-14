"""Unit that reads a dataset from an uploaded file or a URL."""

import logging

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    int_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)


class LoadUploadedDatasetSchema(BaseSchema):
    dataloader: schema_field(
        component_field(parent="BaseDataLoader"),
        placeholder={"component": "CSVDataLoader", "params": {"separator": ","}},
        description=MultilingualString(
            en="Reader used to parse the source, together with its own "
            "configuration (delimiter, sheet, encoding, and so on).",
            es="Lector usado para interpretar el origen, junto con su propia "
            "configuración (delimitador, hoja, codificación, etc.).",
            pt="Leitor usado para interpretar a origem, junto com a sua própria "
            "configuração (delimitador, folha, codificação, etc.).",
            de="Leser zum Parsen der Quelle samt eigener Konfiguration "
            "(Trennzeichen, Blatt, Kodierung usw.).",
            zh="用于解析数据源的读取器及其自身配置（分隔符、工作表、编码等）。",
        ),
        alias=MultilingualString(
            en="Data loader",
            es="Cargador de datos",
            pt="Carregador de dados",
            de="Datenlader",
            zh="数据加载器",
        ),
    )  # type: ignore
    source: schema_field(
        string_field(),
        placeholder="",
        description=MultilingualString(
            en="Where to read from: a path to a local file or a URL. Archives "
            "are downloaded and extracted before being parsed.",
            es="Desde dónde leer: una ruta a un archivo local o una URL. Los "
            "archivos comprimidos se descargan y extraen antes de interpretarse.",
            pt="De onde ler: um caminho para um ficheiro local ou um URL. Os "
            "arquivos comprimidos são descarregados e extraídos antes de serem "
            "interpretados.",
            de="Woher gelesen wird: ein Pfad zu einer lokalen Datei oder eine "
            "URL. Archive werden vor dem Parsen heruntergeladen und entpackt.",
            zh="读取来源：本地文件路径或 URL。压缩包会先下载并解压再解析。",
        ),
        alias=MultilingualString(
            en="Source",
            es="Origen",
            pt="Origem",
            de="Quelle",
            zh="来源",
        ),
    )  # type: ignore
    n_sample: schema_field(
        none_type(int_field(gt=0)),
        placeholder=None,
        description=MultilingualString(
            en="Read only this many rows instead of the whole source. Leave "
            "empty to read everything.",
            es="Leer solo esta cantidad de filas en vez de todo el origen. "
            "Dejar vacío para leer todo.",
            pt="Ler apenas esta quantidade de linhas em vez de toda a origem. "
            "Deixar vazio para ler tudo.",
            de="Nur so viele Zeilen lesen statt der gesamten Quelle. Leer "
            "lassen, um alles zu lesen.",
            zh="仅读取这么多行而非整个数据源。留空表示全部读取。",
        ),
        alias=MultilingualString(
            en="Row sample",
            es="Muestra de filas",
            pt="Amostra de linhas",
            de="Zeilenstichprobe",
            zh="行采样",
        ),
    )  # type: ignore


class LoadUploadedDatasetUnit(BaseUnit):
    """Parse a file or URL into a dataset with the chosen reader.

    The counterpart of ``LoadDatasetUnit``: that one materialises something DashAI
    already stores, this one brings in data that is not a dataset yet. So it
    publishes only ``dataset`` — there is no stored id to correlate against and no
    path to save back to, because nothing decided yet where the result belongs.

    Types are not applied here. What the reader produces is whatever the source
    suggests; declaring and casting types is a separate step, so the same load can
    be reviewed before anything is committed to.
    """

    SCHEMA = LoadUploadedDatasetSchema

    PROVIDES = ("dataset",)
    RUNTIME_PARAMS = ("temp_path",)

    def execute(self, ctx: ExecutionContext) -> None:
        from kink import di

        component_registry = di["component_registry"]

        dataloader_config = self.config["dataloader"]
        source = self.config["source"]

        # Raises KeyError with the registry's own wording when the reader does
        # not exist. That message reaches the user, so it is not reworded here.
        dataloader = component_registry[dataloader_config["component"]]["class"]()

        log.debug(
            "Loading dataset from %s using %s",
            source,
            dataloader_config["component"],
        )
        ctx.put(
            "dataset",
            dataloader.load_data(
                filepath_or_buffer=source,
                temp_path=self.config["temp_path"],
                params=dataloader_config.get("params") or {},
                n_sample=self.config.get("n_sample"),
            ),
        )
