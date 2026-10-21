"""Unit that writes the document in the context to a destination."""

import logging

from DashAI.back.core.schema_fields import BaseSchema, schema_field, string_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)


class SaveDocumentToPathSchema(BaseSchema):
    path: schema_field(
        string_field(),
        placeholder="",
        description=MultilingualString(
            en="Destination directory for the parsed document.",
            es="Directorio de destino del documento interpretado.",
            pt="Diretório de destino do documento interpretado.",
            de="Zielverzeichnis für das geparste Dokument.",
            zh="已解析文档的目标目录。",
        ),
        alias=MultilingualString(
            en="Destination path",
            es="Ruta de destino",
            pt="Caminho de destino",
            de="Zielpfad",
            zh="目标路径",
        ),
    )  # type: ignore


class SaveDocumentToPathUnit(BaseUnit):
    """Write the document to a destination given in the configuration.

    The document counterpart of ``SaveDatasetToPathUnit``. Declares no outputs:
    its result is on disk, not in the context.

    The error message keeps the original exception's text, since only the
    message of the outermost error reaches the user.
    """

    SCHEMA = SaveDocumentToPathSchema

    REQUIRES = ("document",)
    PROVIDES = ()

    def execute(self, ctx: ExecutionContext) -> None:
        from DashAI.back.dataloaders.classes.dashai_document import save_document

        document = ctx.require("document")
        path = self.config["path"]

        try:
            save_document(document, path)
        except Exception as e:
            log.exception(e)
            raise JobError(f"Can not save document to path {path}: {e}") from e
