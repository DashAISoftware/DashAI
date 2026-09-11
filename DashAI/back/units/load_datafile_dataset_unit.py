"""Unit that reads a dataset out of an already downloaded datafile."""

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
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)


class LoadDatafileDatasetSchema(BaseSchema):
    dataloader: schema_field(
        component_field(parent="BaseDataLoader"),
        placeholder={"component": "CSVDataLoader", "params": {"separator": ","}},
        description=MultilingualString(
            en="Reader used to parse the downloaded file, together with its own "
            "configuration.",
            es="Lector usado para interpretar el archivo descargado, junto con "
            "su propia configuración.",
            pt="Leitor usado para interpretar o ficheiro descarregado, junto com "
            "a sua própria configuração.",
            de="Leser zum Parsen der heruntergeladenen Datei samt eigener "
            "Konfiguration.",
            zh="用于解析已下载文件的读取器及其自身配置。",
        ),
        alias=MultilingualString(
            en="Data loader",
            es="Cargador de datos",
            pt="Carregador de dados",
            de="Datenlader",
            zh="数据加载器",
        ),
    )  # type: ignore
    datafile_id: schema_field(
        int_field(gt=0),
        placeholder=1,
        description=MultilingualString(
            en="Identifier of the completed download to read from. It has to have "
            "finished successfully; a download still running has no files yet.",
            es="Identificador de la descarga completada desde la que leer. Tiene "
            "que haber terminado con éxito; una descarga en curso todavía no "
            "tiene archivos.",
            pt="Identificador da descarga concluída de onde ler. Tem de ter "
            "terminado com sucesso; uma descarga em curso ainda não tem "
            "ficheiros.",
            de="Kennung des abgeschlossenen Downloads, aus dem gelesen wird. Er "
            "muss erfolgreich beendet sein; ein laufender Download hat noch "
            "keine Dateien.",
            zh="要读取的已完成下载的标识符。必须已成功完成；仍在进行的下载尚无文件。",
        ),
        alias=MultilingualString(
            en="Downloaded file",
            es="Archivo descargado",
            pt="Ficheiro descarregado",
            de="Heruntergeladene Datei",
            zh="已下载文件",
        ),
    )  # type: ignore
    selected_file: schema_field(
        none_type(string_field()),
        placeholder=None,
        description=MultilingualString(
            en="Which file inside the download to read, relative to its root. "
            "Leave empty to take the first one, ignoring hidden files.",
            es="Qué archivo dentro de la descarga leer, relativo a su raíz. "
            "Dejar vacío para tomar el primero, ignorando archivos ocultos.",
            pt="Qual ficheiro dentro da descarga ler, relativo à sua raiz. "
            "Deixar vazio para tomar o primeiro, ignorando ficheiros ocultos.",
            de="Welche Datei innerhalb des Downloads gelesen wird, relativ zu "
            "dessen Wurzel. Leer lassen, um die erste zu nehmen; versteckte "
            "Dateien werden übersprungen.",
            zh="读取下载内容中的哪个文件（相对于其根目录）。留空则取第一个，忽略"
            "隐藏文件。",
        ),
        alias=MultilingualString(
            en="File",
            es="Archivo",
            pt="Ficheiro",
            de="Datei",
            zh="文件",
        ),
    )  # type: ignore


class LoadDatafileDatasetUnit(BaseUnit):
    """Parse a dataset out of a download that already completed.

    Separate from ``LoadUploadedDatasetUnit`` even though both end in the same
    reader call, because finding *what* to read is the whole job here: the
    download is a directory tree recorded in the database, not a file the caller
    hands over. The unit re-reads that row in its own read-only session, the same
    way ``LoadDatasetUnit`` does, and never writes to it.

    Publishes only ``dataset``, for the same reason as its sibling: an imported
    file is not a stored dataset yet, so there is no id to correlate and no path
    to save back to.
    """

    SCHEMA = LoadDatafileDatasetSchema

    PROVIDES = ("dataset",)

    def execute(self, ctx: ExecutionContext) -> None:
        from kink import di

        from DashAI.back.core.enums.status import DatafileStatus
        from DashAI.back.dependencies.database.models import Datafile

        component_registry = di["component_registry"]
        session_factory = di["session_factory"]

        datafile_id = self.config["datafile_id"]
        selected_file = self.config.get("selected_file")
        dataloader_config = self.config["dataloader"]

        with session_factory() as db:
            datafile = db.get(Datafile, datafile_id)
            # A missing row and an unfinished download are the same problem from
            # here: there are no files to read either way.
            if datafile is None or datafile.status != DatafileStatus.READY:
                raise JobError(f"Datafile {datafile_id} is not ready.")
            work_dir = datafile.local_path

        source = _resolve_source_file(work_dir, selected_file)

        # Looked up among the readers specifically, not with the registry's
        # global ``registry[name]``: that one walks every component type, so a
        # metric or a model whose name happened to be passed here would be
        # instantiated as if it could read a file instead of being rejected.
        dataloader_name = dataloader_config["component"]
        readers = component_registry.registry.get("DataLoader", {})
        if dataloader_name not in readers:
            raise JobError(f"DataLoader '{dataloader_name}' not found in registry.")
        dataloader = readers[dataloader_name]["class"]()

        log.debug("Loading hub dataset from %s using %s", source, dataloader_name)
        ctx.put(
            "dataset",
            dataloader.load_data(
                filepath_or_buffer=source,
                temp_path=work_dir,
                params=dataloader_config.get("params") or {},
                n_sample=None,
            ),
        )


def _resolve_source_file(work_dir: str, selected_file) -> str:
    """Pick the file to read inside a completed download.

    A plain helper: takes and returns values, never touches the context.

    With no explicit choice it walks the tree and takes the first file in sorted
    order, skipping anything under a dot-prefixed path component — download tools
    leave metadata directories (``.cache``, ``.git``) behind that sort before the
    real data and would otherwise win.
    """
    from pathlib import Path

    if selected_file:
        return str(Path(work_dir) / selected_file)

    base = Path(work_dir)
    files = sorted(
        str(path)
        for path in base.rglob("*")
        if path.is_file()
        and not any(part.startswith(".") for part in path.relative_to(base).parts)
    )
    if not files:
        raise JobError("Hub download directory is empty.")
    return files[0]
