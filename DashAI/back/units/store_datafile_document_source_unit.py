"""Unit that keeps a copy of a file from a hub download as a document's source."""

import logging
from pathlib import Path

from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.datafile_source import datafile_source_file
from DashAI.back.units.document_source import source_directory_field, store_source

log = logging.getLogger(__name__)


class StoreDatafileDocumentSourceSchema(BaseSchema):
    datafile_id: schema_field(
        int_field(gt=0),
        placeholder=1,
        description=MultilingualString(
            en="Identifier of the completed download to take the file from.",
            es="Identificador de la descarga completada de la que tomar el archivo.",
            pt="Identificador da descarga concluída de onde tirar o ficheiro.",
            de="Kennung des abgeschlossenen Downloads, aus dem die Datei "
            "genommen wird.",
            zh="要从中获取文件的已完成下载的标识符。",
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
            en="Which file inside the download to take, relative to its root. "
            "Leave empty to take the first one, ignoring hidden files.",
            es="Qué archivo dentro de la descarga tomar, relativo a su raíz. "
            "Dejar vacío para tomar el primero, ignorando archivos ocultos.",
            pt="Qual ficheiro dentro da descarga tirar, relativo à sua raiz. "
            "Deixar vazio para tomar o primeiro, ignorando ficheiros ocultos.",
            de="Welche Datei innerhalb des Downloads genommen wird, relativ zu "
            "dessen Wurzel. Leer lassen, um die erste zu nehmen; versteckte "
            "Dateien werden übersprungen.",
            zh="取下载内容中的哪个文件（相对于其根目录）。留空则取第一个，忽略隐藏文件。",
        ),
        alias=MultilingualString(
            en="File",
            es="Archivo",
            pt="Ficheiro",
            de="Datei",
            zh="文件",
        ),
    )  # type: ignore
    path: source_directory_field()  # type: ignore


class StoreDatafileDocumentSourceUnit(BaseUnit):
    """Copy a file out of a completed hub download and hash it.

    The hub counterpart of ``StoreUploadedDocumentSourceUnit``. The copy keeps
    the document independent of the download, which can be deleted on its own.
    The copy keeps the file's own name. Publishes the same keys as its sibling,
    so whatever parses the source does not care where it came from.
    """

    SCHEMA = StoreDatafileDocumentSourceSchema

    PROVIDES = ("source_path", "file_hash")

    def execute(self, ctx: ExecutionContext) -> None:
        source = datafile_source_file(
            self.config["datafile_id"], self.config.get("selected_file")
        )

        log.debug("Storing hub document source %s in %s", source, self.config["path"])
        source_path, file_hash = store_source(
            source, self.config["path"], Path(source).name
        )
        ctx.put_ref("source_path", source_path)
        ctx.put_ref("file_hash", file_hash)
