"""Unit that parses a stored source file into a document."""

import logging

from DashAI.back.core.schema_fields import BaseSchema, component_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataloaders.classes.dataloader import (
    DataKindMismatchError,
    require_data_kind,
)
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)


class ParseDocumentSchema(BaseSchema):
    dataloader: schema_field(
        component_field(parent="BaseDataLoader"),
        placeholder={"component": "PlainTextDocumentDataLoader", "params": {}},
        description=MultilingualString(
            en="Document loader used to parse the file, together with its own "
            "configuration.",
            es="Cargador de documentos usado para interpretar el archivo, junto "
            "con su propia configuración.",
            pt="Carregador de documentos usado para interpretar o ficheiro, "
            "junto com a sua própria configuração.",
            de="Dokumentlader zum Parsen der Datei samt eigener Konfiguration.",
            zh="用于解析文件的文档加载器及其自身配置。",
        ),
        alias=MultilingualString(
            en="Document loader",
            es="Cargador de documentos",
            pt="Carregador de documentos",
            de="Dokumentlader",
            zh="文档加载器",
        ),
    )  # type: ignore


class ParseDocumentUnit(BaseUnit):
    """Parse ``source_path`` into a document with the chosen loader.

    Reads the source from the context rather than its configuration, so it
    composes after either source storing unit. Publishes only ``document``:
    where the result is stored is decided by whatever runs next.

    ``validate`` checks the loader without reading anything, so a caller can
    reject the request before it copies or writes a file.
    """

    SCHEMA = ParseDocumentSchema

    REQUIRES = ("source_path",)
    PROVIDES = ("document",)

    def _loader_class(self) -> type:
        """Resolve the configured loader and check that it loads documents.

        Returns
        -------
        type
            The registered document loader class.

        Raises
        ------
        JobError
            If the loader is not registered or does not produce documents.
        """
        from kink import di

        component_registry = di["component_registry"]
        dataloader_name = self.config["dataloader"].get("component")

        if not dataloader_name or dataloader_name not in component_registry:
            raise JobError(f"Document loader '{dataloader_name}' is not registered.")
        loader_class = component_registry[dataloader_name]["class"]
        try:
            require_data_kind(loader_class, "document")
        except DataKindMismatchError as e:
            raise JobError(str(e)) from e
        return loader_class

    def validate(self, ctx: ExecutionContext) -> None:
        """Reject a loader that is missing or does not produce documents.

        Parameters
        ----------
        ctx : ExecutionContext
            The shared execution context.

        Raises
        ------
        JobError
            If the loader is not registered or does not produce documents.
        """
        self._loader_class()

    def execute(self, ctx: ExecutionContext) -> None:
        loader_class = self._loader_class()
        source_path = ctx.require("source_path")
        params = self.config["dataloader"].get("params") or {}

        log.debug("Parsing %s with %s", source_path, loader_class.__name__)
        ctx.put("document", loader_class().load_document(source_path, params))
