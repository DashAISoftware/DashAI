"""Unit that keeps a copy of an uploaded file as a document's source."""

import logging

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.document_source import source_directory_field, store_source

log = logging.getLogger(__name__)


class StoreUploadedDocumentSourceSchema(BaseSchema):
    path: source_directory_field()  # type: ignore


class StoreUploadedDocumentSourceUnit(BaseUnit):
    """Copy an uploaded file into a directory of its own and hash it.

    The upload lives in a temporary directory that is removed once the job
    ends, so the copy is what the document keeps as its source. Publishes the
    copy's location as ``source_path`` and its sha256 as ``file_hash``.

    Where the upload landed and what it is called are known only to whatever
    received it, so both are runtime params.
    """

    SCHEMA = StoreUploadedDocumentSourceSchema

    PROVIDES = ("source_path", "file_hash")
    RUNTIME_PARAMS = ("upload_path", "file_name")

    def execute(self, ctx: ExecutionContext) -> None:
        log.debug("Storing uploaded document source in %s", self.config["path"])
        source_path, file_hash = store_source(
            self.config["upload_path"], self.config["path"], self.config["file_name"]
        )
        ctx.put_ref("source_path", source_path)
        ctx.put_ref("file_hash", file_hash)
